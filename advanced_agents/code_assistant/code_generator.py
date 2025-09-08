from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from config import get_llm
import re


class CodeSolution(BaseModel):
    """Structured output for generated code"""

    code: str = Field(description="The complete Python code solution")
    explanation: str = Field(description="Step-by-step explanation of the code")
    imports: List[str] = Field(description="List of required import statements")
    assumptions: Optional[str] = Field(
        description="Any assumptions made about the requirements"
    )


class CodeGenerator:
    def __init__(self):
        self.llm = get_llm()
        self.parser = PydanticOutputParser(pydantic_object=CodeSolution)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert Python programmer. Generate clean, efficient, and well-commented Python code.

IMPORTANT INSTRUCTIONS:
1. Always include ALL necessary import statements at the top
2. Write production-quality code with proper error handling
3. Add clear comments explaining the logic
4. Follow Python best practices and PEP 8 guidelines
5. Make reasonable assumptions if requirements are unclear

CONTEXT FROM DOCUMENTATION:
{context}

{format_instructions}""",
                ),
                (
                    "human",
                    """Create Python code for the following request:

REQUEST: {user_request}

Generate complete, runnable code that solves this request. Include proper imports, error handling, and comments.""",
                ),
            ]
        )

    def generate_code(self, user_request: str, context: str = "") -> CodeSolution:
        """Generate code based on user request and documentation context"""

        formatted_prompt = self.prompt.format(
            user_request=user_request,
            context=context,
            format_instructions=self.parser.get_format_instructions(),
        )

        response = self.llm.invoke(formatted_prompt)

        try:
            result = self.parser.parse(response.content)

            result.code = self._clean_code(result.code)
            result.imports = self._extract_imports(result.code)

            return result

        except Exception as e:
            print(f"⚠️ Error parsing LLM output: {e}")
            # Try to extract code from the raw response if JSON parsing fails
            return self._extract_code_from_response(response.content, user_request)

    def _clean_code(self, code: str) -> str:
        """Clean the generated code"""
        code = re.sub(r"^```python\n", "", code, flags=re.MULTILINE)
        code = re.sub(r"^```\n?$", "", code, flags=re.MULTILINE)

        lines = code.split("\n")
        cleaned_lines = []
        for line in lines:
            if line.strip():
                cleaned_lines.append(line)
            elif cleaned_lines and cleaned_lines[-1].strip():
                cleaned_lines.append("")

        return "\n".join(cleaned_lines)

    def _extract_imports(self, code: str) -> List[str]:
        """Extract import statements from code"""
        import_pattern = r"^(?:from\s+\S+\s+)?import\s+.+$"
        imports = []

        for line in code.split("\n"):
            line = line.strip()
            if re.match(import_pattern, line):
                imports.append(line)

        return imports

    def _extract_code_from_response(
        self, raw_response: str, user_request: str
    ) -> CodeSolution:
        """Extract code from response when JSON parsing fails"""
        import re

        json_match = re.search(r"```json\s*(.*?)\s*```", raw_response, re.DOTALL)
        if json_match:
            json_content = json_match.group(1)

            try:
                code_match = re.search(
                    r'"code":\s*"(.*?)"(?=,\s*"explanation")', json_content, re.DOTALL
                )
                code = ""
                if code_match:
                    code_str = code_match.group(1)
                    code = code_str.encode().decode("unicode_escape")

                explanation_match = re.search(
                    r'"explanation":\s*"(.*?)"(?=,\s*"imports")',
                    json_content,
                    re.DOTALL,
                )
                explanation = (
                    explanation_match.group(1)
                    if explanation_match
                    else f"Generated solution for: {user_request}"
                )

                imports_match = re.search(
                    r'"imports":\s*\[(.*?)\]', json_content, re.DOTALL
                )
                imports = []
                if imports_match:
                    imports_str = imports_match.group(1)
                    import_items = re.findall(r'"([^"]*)"', imports_str)
                    imports = import_items

                assumptions_match = re.search(
                    r'"assumptions":\s*"(.*?)"(?=\s*})', json_content, re.DOTALL
                )
                assumptions = assumptions_match.group(1) if assumptions_match else ""

                if code:
                    return CodeSolution(
                        code=self._clean_code(code),
                        explanation=explanation,
                        imports=imports,
                        assumptions=assumptions,
                    )

            except Exception as e:
                print(f"⚠️ Regex extraction failed: {e}")

        return self._create_fallback_solution(raw_response, user_request)

    def _create_fallback_solution(
        self, raw_response: str, user_request: str
    ) -> CodeSolution:
        """Create a fallback solution when parsing fails"""
        code_match = re.search(r"```python\n(.*?)```", raw_response, re.DOTALL)
        if code_match:
            code = code_match.group(1)
        else:
            lines = raw_response.split("\n")
            code_lines = []
            in_code = False

            for line in lines:
                if "import " in line or "def " in line or "class " in line:
                    in_code = True
                if in_code:
                    code_lines.append(line)
                if line.strip() == "" and in_code and len(code_lines) > 5:
                    break

            code = "\n".join(code_lines) if code_lines else raw_response

        return CodeSolution(
            code=self._clean_code(code),
            explanation=f"Generated solution for: {user_request}",
            imports=self._extract_imports(code),
            assumptions="Fallback parsing used - manual review recommended",
        )


# Test the code generator
if __name__ == "__main__":
    from document_loader import DocumentProcessor

    processor = DocumentProcessor()
    processor.load_documents()
    processor.create_vector_store()

    generator = CodeGenerator()

    test_requests = [
        "Create a function that reads a CSV file and returns basic statistics about numeric columns",
        "Write code to scrape a webpage and extract all links",
        "Make a bar chart showing the frequency of different values in a list",
        "Create a simple machine learning model to classify data",
    ]

    print("🧪 Testing Code Generator")
    print("=" * 50)

    for i, request in enumerate(test_requests, 1):
        print(f"\n  Test {i}: {request}")
        print("-" * 30)

        context, sources = processor.search_relevant_docs(request)

        solution = generator.generate_code(request, context)

        print("\n📝 Generated Code:")
        print("=" * 40)
        print(solution.code)
        print("=" * 40)
        print(f"\n💡 Explanation: {solution.explanation}")
        print(f"\n📦 Imports needed: {solution.imports}")
        print(
            f"\n📚 Sources used: {[doc.metadata.get('source', 'Unknown') for doc in sources]}"
        )

        if solution.assumptions:
            print(f"\n⚠️ Assumptions: {solution.assumptions}")

    print("\n🎉 Code Generator testing completed!")
