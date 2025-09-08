"""
Code Assistant Agent - Main LangGraph Orchestrator

This is the main orchestrator that coordinates the RAG system, code generation,
and validation components to create a self-correcting Code Assistant Agent.

Architecture:
- document_loader.py: RAG system for retrieving relevant documentation
- code_generator.py: LLM-based code generation with structured output
- validators.py: Safe code execution and validation
- main.py: LangGraph workflow orchestrator (this file)
"""

import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# LangGraph imports
from langgraph.graph import StateGraph, START, END

# Local imports
from document_loader import DocumentProcessor
from code_generator import CodeGenerator, CodeSolution
from validators import CodeValidator, ExecutionResult

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class CodeAssistantState:
    """State object for the Code Assistant workflow"""

    user_request: str = ""
    context: str = ""
    source_docs: List[Any] = None
    code_solution: Optional[CodeSolution] = None
    validation_result: Optional[ExecutionResult] = None
    iteration_count: int = 0
    max_iterations: int = 3
    is_complete: bool = False
    error_history: List[str] = None

    def __post_init__(self):
        if self.source_docs is None:
            self.source_docs = []
        if self.error_history is None:
            self.error_history = []


class CodeAssistantAgent:
    """
    Main Code Assistant Agent using LangGraph for workflow orchestration.

    Implements a self-correcting workflow:
    1. Retrieve relevant documentation (RAG)
    2. Generate code based on context
    3. Validate and execute code safely
    4. If errors occur, iterate with corrections
    5. Return final working solution
    """

    def __init__(self):
        logger.info("🚀 Initializing Code Assistant Agent...")

        # Initialize components
        self.doc_processor = DocumentProcessor()
        self.code_generator = CodeGenerator()
        self.validator = CodeValidator()

        # Initialize documentation system
        logger.info("📚 Loading documentation...")
        self.doc_processor.load_documents()
        self.doc_processor.create_vector_store()

        # Build the LangGraph workflow
        self.workflow = self._build_workflow()

        logger.info("✅ Code Assistant Agent initialized successfully!")

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for the Code Assistant"""

        # Create the workflow graph
        workflow = StateGraph(CodeAssistantState)

        # Add nodes (workflow steps)
        workflow.add_node("retrieve_context", self._retrieve_context)
        workflow.add_node("generate_code", self._generate_code)
        workflow.add_node("validate_code", self._validate_code)
        workflow.add_node("iterate_correction", self._iterate_correction)
        workflow.add_node("finalize_result", self._finalize_result)

        # Define the workflow edges (control flow)
        workflow.add_edge(START, "retrieve_context")
        workflow.add_edge("retrieve_context", "generate_code")
        workflow.add_edge("generate_code", "validate_code")

        # Conditional edge: if validation passes or max iterations reached, finalize
        # Otherwise, iterate with corrections
        workflow.add_conditional_edges(
            "validate_code",
            self._should_continue_iteration,
            {"continue": "iterate_correction", "finalize": "finalize_result"},
        )

        workflow.add_edge("iterate_correction", "generate_code")
        workflow.add_edge("finalize_result", END)

        return workflow.compile()

    def _retrieve_context(self, state: CodeAssistantState) -> CodeAssistantState:
        """Retrieve relevant documentation context using RAG"""
        logger.info(f"🔍 Retrieving context for: {state.user_request[:50]}...")

        try:
            context, source_docs = self.doc_processor.search_relevant_docs(
                state.user_request
            )
            state.context = context
            state.source_docs = source_docs

            logger.info(f"📄 Retrieved {len(source_docs)} relevant documents")

        except Exception as e:
            logger.error(f"❌ Error retrieving context: {e}")
            state.context = ""
            state.source_docs = []

        return state

    def _generate_code(self, state: CodeAssistantState) -> CodeAssistantState:
        """Generate code based on context and any previous errors"""
        logger.info(f"⚙️ Generating code (iteration {state.iteration_count + 1})...")

        try:
            # Enhance user request with error history for corrections
            enhanced_request = state.user_request
            if state.error_history:
                enhanced_request += "\n\nPREVIOUS ERRORS TO FIX:\n" + "\n".join(
                    state.error_history[-2:]
                )

            # Generate code solution
            code_solution = self.code_generator.generate_code(
                enhanced_request, state.context
            )
            state.code_solution = code_solution

            logger.info("✅ Code generated successfully")

        except Exception as e:
            logger.error(f"❌ Error generating code: {e}")
            # Create a fallback solution
            state.code_solution = CodeSolution(
                code="# Error generating code",
                explanation=f"Code generation failed: {e}",
                imports=[],
                assumptions="Manual intervention required",
            )

        return state

    def _validate_code(self, state: CodeAssistantState) -> CodeAssistantState:
        """Validate and execute the generated code safely"""
        logger.info("🔬 Validating generated code...")

        try:
            if state.code_solution:
                validation_result = self.validator.execute_code_safely(
                    state.code_solution.code
                )
                state.validation_result = validation_result

                if validation_result.success:
                    logger.info("✅ Code validation successful!")
                    state.is_complete = True
                else:
                    logger.warning(
                        f"⚠️ Code validation failed: {validation_result.error}"
                    )
                    # Add error to history for next iteration
                    error_msg = f"Iteration {state.iteration_count + 1}: {validation_result.error}"
                    if (
                        hasattr(validation_result, "syntax_errors")
                        and validation_result.syntax_errors
                    ):
                        error_msg += f" | Syntax: {validation_result.syntax_errors}"
                    if (
                        hasattr(validation_result, "missing_imports")
                        and validation_result.missing_imports
                    ):
                        error_msg += (
                            f" | Missing imports: {validation_result.missing_imports}"
                        )
                    state.error_history.append(error_msg)

        except Exception as e:
            logger.error(f"❌ Error during validation: {e}")
            state.error_history.append(f"Validation error: {e}")

        state.iteration_count += 1
        return state

    def _should_continue_iteration(self, state: CodeAssistantState) -> str:
        """Determine whether to continue iteration or finalize result"""

        # Finalize if successful or max iterations reached
        if state.is_complete or state.iteration_count >= state.max_iterations:
            return "finalize"

        # Continue iteration if there are errors to fix
        return "continue"

    def _iterate_correction(self, state: CodeAssistantState) -> CodeAssistantState:
        """Prepare for the next iteration with error correction context"""
        logger.info(
            f"🔄 Preparing iteration {state.iteration_count + 1} with error corrections..."
        )

        # The actual correction happens in the next generate_code call
        # This node just logs the iteration
        return state

    def _finalize_result(self, state: CodeAssistantState) -> CodeAssistantState:
        """Finalize the result and prepare the response"""
        logger.info("🎯 Finalizing result...")

        if state.is_complete:
            logger.info("✅ Code Assistant completed successfully!")
        else:
            logger.warning(f"⚠️ Max iterations ({state.max_iterations}) reached")

        return state

    def process_request(
        self, user_request: str, max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Process a user request through the complete workflow

        Args:
            user_request: The user's code generation request
            max_iterations: Maximum number of correction iterations (default: 3)

        Returns:
            Dictionary with the final result and metadata
        """
        start_time = time.time()

        logger.info(f"🎯 Processing request: {user_request[:50]}...")

        # Initialize state
        initial_state = CodeAssistantState(
            user_request=user_request, max_iterations=max_iterations
        )

        try:
            # Execute the workflow
            final_state = self.workflow.invoke(initial_state)

            # Prepare the response
            result = {
                "success": final_state.is_complete,
                "code_solution": final_state.code_solution,
                "validation_result": final_state.validation_result,
                "iterations": final_state.iteration_count,
                "error_history": final_state.error_history,
                "source_documents": [
                    doc.metadata.get("source", "Unknown")
                    for doc in final_state.source_docs
                ],
                "processing_time": time.time() - start_time,
            }

            return result

        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
            }


def main():
    """Interactive demo of the Code Assistant Agent"""
    print("🤖 Code Assistant Agent - Interactive Demo")
    print("=" * 50)

    # Initialize the agent
    agent = CodeAssistantAgent()

    # Demo requests
    demo_requests = [
        "Create a function to read a CSV file and calculate column statistics",
        "Write code that creates a simple plot showing data trends",
        "Build a function that validates email addresses using regex",
        "Create a class to manage a simple task list with add/remove functionality",
    ]

    print("\n🚀 Running demo requests...\n")

    for i, request in enumerate(demo_requests, 1):
        print(f"📋 Demo {i}: {request}")
        print("-" * 40)

        # Process the request
        result = agent.process_request(request)

        # Display results
        if result["success"]:
            print("✅ SUCCESS!")
            print(f"⚡ Completed in {result['iterations']} iterations")
            print(f"⏱️ Processing time: {result['processing_time']:.2f}s")

            if result["code_solution"]:
                print("\n📝 Generated Code:")
                print("=" * 30)
                print(result["code_solution"].code)
                print("=" * 30)

                print(f"\n💡 Explanation: {result['code_solution'].explanation}")
                print(f"📦 Required imports: {result['code_solution'].imports}")
        else:
            print("❌ FAILED!")
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            if result.get("error_history"):
                print(f"📝 Error history: {result['error_history']}")

        print(f"\n📚 Sources used: {result.get('source_documents', [])}")
        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
