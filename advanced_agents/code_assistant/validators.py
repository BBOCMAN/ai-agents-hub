import ast
import sys
import subprocess
import tempfile
import os
import time
import signal
import threading
import importlib
import io
import traceback
import re
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import logging
from contextlib import redirect_stdout, redirect_stderr
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from config import get_llm

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationResult(BaseModel):
    """Structured validation result with AI analysis"""
    is_valid: bool = Field(description="Whether the code passed validation")
    error_type: str = Field(description="Type of error if validation failed")
    error_message: str = Field(description="Detailed error message")
    suggestions: List[str] = Field(description="AI-powered suggestions for fixing the code")
    execution_output: str = Field(description="Output from code execution")
    
class ImportValidationResult(BaseModel):
    """Result of import validation"""
    all_imports_valid: bool = Field(description="Whether all imports are valid")
    valid_imports: List[str] = Field(description="List of valid import statements")
    invalid_imports: List[str] = Field(description="List of invalid import statements")
    missing_packages: List[str] = Field(description="Packages that need to be installed")

@dataclass
class ExecutionResult:
    """Result of code execution with detailed information"""
    success: bool
    output: str = ""
    error: str = ""
    execution_time: float = 0.0
    exit_code: int = 0
    imports_missing: List[str] = None
    syntax_errors: List[str] = None
    runtime_errors: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.imports_missing is None:
            self.imports_missing = []
        if self.syntax_errors is None:
            self.syntax_errors = []
        if self.runtime_errors is None:
            self.runtime_errors = []
        if self.warnings is None:
            self.warnings = []

class CodeValidator:
    """
    Advanced code execution and validation system with AI-powered error analysis.
    Provides syntax checking, import validation, sandboxed execution, and intelligent error suggestions.
    """
    
    def __init__(self, timeout: int = 30, max_output_size: int = 10000):
        """
        Initialize the code validator with AI capabilities.
        
        Args:
            timeout: Maximum execution time in seconds
            max_output_size: Maximum output size to prevent memory issues
        """
        self.timeout = timeout
        self.max_output_size = max_output_size
        
        # Initialize LLM for error analysis
        try:
            self.llm = get_llm()
            self.validation_parser = PydanticOutputParser(pydantic_object=ValidationResult)
            self.ai_enabled = True
            logger.info("✅ AI error analysis enabled")
        except Exception as e:
            logger.warning(f"⚠️ AI error analysis disabled: {e}")
            self.ai_enabled = False
        
        # Error analysis prompt
        self.error_analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Python debugger. Analyze the given code and error to provide helpful suggestions.

ANALYSIS GUIDELINES:
1. Identify the root cause of the error
2. Provide specific, actionable suggestions
3. Consider common Python pitfalls and best practices
4. Suggest alternative approaches if needed
5. Be concise but thorough

{format_instructions}"""),
            ("human", """ORIGINAL CODE:
```python
{code}
```

ERROR ENCOUNTERED:
{error_type}: {error_message}

FULL TRACEBACK:
{traceback}

Analyze this error and provide specific suggestions for fixing the code.""")
        ])
        
        # Define safe and dangerous imports
        self.safe_imports = {
            'math', 'random', 'datetime', 'json', 'csv', 're',
            'collections', 'itertools', 'functools', 'operator',
            'pandas', 'numpy', 'matplotlib', 'seaborn', 'plotly',
            'sklearn', 'scipy', 'statsmodels', 'beautifulsoup4',
            'typing', 'dataclasses', 'enum', 'abc', 'statistics',
            'decimal', 'fractions', 'string', 'textwrap', 'unicodedata',
            'bisect', 'heapq', 'copy', 'pprint', 'reprlib'
        }
        self.builtin_modules = {
            'math', 'random', 'datetime', 'json', 'csv', 're',
            'collections', 'itertools', 'functools', 'operator',
            'typing', 'dataclasses', 'enum', 'abc', 'statistics',
            'decimal', 'fractions', 'string', 'textwrap', 'unicodedata',
            'bisect', 'heapq', 'copy', 'pprint', 'reprlib', 'sys',
            'time', 'calendar', 'hashlib', 'hmac', 'secrets', 'uuid'
        }
        self.dangerous_imports = {
            'os', 'subprocess', 'sys', 'shutil', 'socket', 'urllib',
            'requests', 'eval', 'exec', '__import__', 'compile',
            'open', 'file', 'input', 'raw_input'
        }

    def validate_syntax(self, code: str) -> Tuple[bool, List[str]]:
        """
        Check if the code has valid Python syntax.
        
        Args:
            code: Python code to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            ast.parse(code)
            return True, []
        except SyntaxError as e:
            error_msg = f"Syntax Error at line {e.lineno}: {e.msg}"
            return False, [error_msg]
        except Exception as e:
            return False, [f"Parse Error: {str(e)}"]

    def validate_imports(self, code: str) -> ImportValidationResult:
        """Validate all import statements in the code with enhanced analysis"""
        import_lines = []
        for line in code.split('\n'):
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                import_lines.append(line)
        
        valid_imports = []
        invalid_imports = []
        missing_packages = []
        
        for import_line in import_lines:
            try:
                # Extract module name
                if import_line.startswith('from '):
                    module_name = import_line.split(' import ')[0].replace('from ', '').strip()
                else:
                    module_name = import_line.replace('import ', '').split('.')[0].strip()
                
                # Check if it's a dangerous import
                if module_name in self.dangerous_imports:
                    invalid_imports.append(f"Dangerous import: {import_line}")
                    continue
                
                # Check if it's a builtin or safe module
                if module_name in self.builtin_modules or module_name in self.safe_imports:
                    valid_imports.append(import_line)
                    continue
                
                # Test import
                temp_code = f"{import_line}\nprint('Import successful')"
                result = subprocess.run(
                    [sys.executable, '-c', temp_code],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    valid_imports.append(import_line)
                else:
                    invalid_imports.append(import_line)
                    # Try to extract package name for installation suggestion
                    if 'ModuleNotFoundError' in result.stderr:
                        package_name = self._extract_package_name(result.stderr)
                        if package_name and package_name not in missing_packages:
                            missing_packages.append(package_name)
                            
            except subprocess.TimeoutExpired:
                invalid_imports.append(import_line)
            except Exception as e:
                invalid_imports.append(import_line)
        
        return ImportValidationResult(
            all_imports_valid=len(invalid_imports) == 0,
            valid_imports=valid_imports,
            invalid_imports=invalid_imports,
            missing_packages=missing_packages
        )

    def execute_code_safely(self, code: str) -> ExecutionResult:
        """
        Execute code safely with AI-powered error analysis
        """
        start_time = time.time()
        
        # First, validate syntax
        syntax_valid, syntax_errors = self.validate_syntax(code)
        if not syntax_valid:
            return ExecutionResult(
                success=False,
                error="Syntax validation failed",
                syntax_errors=syntax_errors,
                execution_time=time.time() - start_time
            )

        # Validate imports
        import_result = self.validate_imports(code)
        if not import_result.all_imports_valid:
            return ExecutionResult(
                success=False,
                error="Import validation failed",
                imports_missing=import_result.missing_packages,
                execution_time=time.time() - start_time
            )

        # Execute code in subprocess for safety
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
                
            # Execute in subprocess
            result = subprocess.run(
                [sys.executable, temp_file_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            execution_time = time.time() - start_time
            
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except (OSError, PermissionError):
                pass  # Ignore cleanup errors
            
            if result.returncode == 0:
                return ExecutionResult(
                    success=True,
                    output=result.stdout[:self.max_output_size],
                    execution_time=execution_time
                )
            else:
                return ExecutionResult(
                    success=False,
                    error=result.stderr[:self.max_output_size],
                    execution_time=execution_time,
                    exit_code=result.returncode
                )
                
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                error=f"Code execution timed out after {self.timeout} seconds",
                execution_time=self.timeout
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=f"Execution error: {str(e)}",
                execution_time=time.time() - start_time
            )

    def analyze_error(self, code: str, error_type: str, error_message: str, full_traceback: str = "") -> ValidationResult:
        """Use LLM to analyze errors and provide intelligent suggestions"""
        
        if not self.ai_enabled:
            # Fallback analysis without AI
            return ValidationResult(
                is_valid=False,
                error_type=error_type,
                error_message=error_message,
                suggestions=[
                    "Check for syntax errors and missing imports",
                    "Verify all required packages are installed",
                    "Review variable names and function calls",
                    "Consider breaking down complex operations"
                ],
                execution_output=""
            )
        
        formatted_prompt = self.error_analysis_prompt.format(
            code=code,
            error_type=error_type,
            error_message=error_message,
            traceback=full_traceback,
            format_instructions=self.validation_parser.get_format_instructions()
        )
        
        try:
            response = self.llm.invoke(formatted_prompt)
            result = self.validation_parser.parse(response.content)
            return result
        except Exception as e:
            logger.warning(f"AI analysis failed: {e}")
            # Fallback analysis
            return ValidationResult(
                is_valid=False,
                error_type=error_type,
                error_message=error_message,
                suggestions=[
                    "Check for syntax errors and missing imports",
                    "Verify all required packages are installed",
                    "Review variable names and function calls",
                    "Consider breaking down complex operations"
                ],
                execution_output=""
            )

    def comprehensive_validation(self, code: str) -> ValidationResult:
        """Perform comprehensive code validation with AI analysis"""
        
        # Step 1: Syntax validation
        syntax_valid, syntax_messages = self.validate_syntax(code)
        if not syntax_valid:
            if self.ai_enabled:
                return self.analyze_error(code, "SyntaxError", "; ".join(syntax_messages))
            else:
                return ValidationResult(
                    is_valid=False,
                    error_type="SyntaxError",
                    error_message="; ".join(syntax_messages),
                    suggestions=["Fix syntax errors before proceeding"],
                    execution_output=""
                )
        
        # Step 2: Import validation
        import_result = self.validate_imports(code)
        if not import_result.all_imports_valid:
            suggestions = ["Fix import issues:"]
            if import_result.missing_packages:
                suggestions.append(f"Install missing packages: {', '.join(import_result.missing_packages)}")
            if import_result.invalid_imports:
                suggestions.extend([f"Fix import: {imp}" for imp in import_result.invalid_imports])
            
            if self.ai_enabled:
                return self.analyze_error(code, "ImportError", f"Invalid imports: {import_result.invalid_imports}")
            else:
                return ValidationResult(
                    is_valid=False,
                    error_type="ImportError",
                    error_message=f"Invalid imports: {import_result.invalid_imports}",
                    suggestions=suggestions,
                    execution_output=""
                )
        
        # Step 3: Execution validation
        execution_result = self.execute_code_safely(code)
        
        if execution_result.success:
            return ValidationResult(
                is_valid=True,
                error_type="",
                error_message="",
                suggestions=["Code executed successfully!"],
                execution_output=execution_result.output
            )
        else:
            # Step 4: AI-powered error analysis
            if self.ai_enabled:
                return self.analyze_error(code, "RuntimeError", execution_result.error, execution_result.error)
            else:
                return ValidationResult(
                    is_valid=False,
                    error_type="RuntimeError",
                    error_message=execution_result.error,
                    suggestions=["Review the error message and fix the issue"],
                    execution_output=""
                )

    def _extract_package_name(self, error_message: str) -> Optional[str]:
        """Extract package name from ModuleNotFoundError message"""
        patterns = [
            r"No module named '([^']+)'",
            r"ModuleNotFoundError: No module named '([^']+)'",
            r"cannot import name '([^']+)'"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_message)
            if match:
                package_name = match.group(1)
                # Handle submodules (e.g., 'sklearn.metrics' -> 'sklearn')
                return package_name.split('.')[0]
        
        return None

# Test the enhanced validation system
if __name__ == "__main__":
    validator = CodeValidator()
    
    # Test cases
    test_codes = [
        # Valid code
        """
import math
import statistics

def calculate_stats(numbers):
    if not numbers:
        return None
    return {
        'mean': statistics.mean(numbers),
        'median': statistics.median(numbers),
        'std': statistics.stdev(numbers) if len(numbers) > 1 else 0
    }

result = calculate_stats([1, 2, 3, 4, 5])
print(f"Statistics: {result}")
""",
        # Code with syntax error
        """
def broken_function(:
    print("This has a syntax error")
    return "broken"
""",
        # Code with dangerous import
        """
import os

def dangerous_function():
    return os.system("ls")
""",
        # Code with runtime error
        """
def division_error():
    x = 10
    y = 0
    return x / y

result = division_error()
"""
    ]
    
    print("🧪 Testing Enhanced Code Validation System")
    print("="*60)
    
    for i, test_code in enumerate(test_codes, 1):
        print(f"\n📋 Test Case {i}:")
        print("Code snippet:")
        print(test_code[:100] + "..." if len(test_code) > 100 else test_code)
        
        # Test both execution and comprehensive validation
        print("\n🔬 Basic Execution Test:")
        exec_result = validator.execute_code_safely(test_code)
        print(f"✅ Success: {exec_result.success}")
        if not exec_result.success:
            print(f"❌ Error: {exec_result.error[:200]}...")
        else:
            print(f"📤 Output: {exec_result.output[:200]}...")
        
        print("\n🧠 AI-Enhanced Validation:")
        validation_result = validator.comprehensive_validation(test_code)
        print(f"✅ Valid: {validation_result.is_valid}")
        
        if not validation_result.is_valid:
            print(f"❌ Error Type: {validation_result.error_type}")
            print(f"❌ Error: {validation_result.error_message[:200]}...")
            print("💡 AI Suggestions:")
            for suggestion in validation_result.suggestions:
                print(f"   - {suggestion}")
        else:
            print("🎉 Code executed successfully!")
            if validation_result.execution_output:
                print(f"📤 Output: {validation_result.execution_output[:200]}...")
        
        print("-" * 40)
    
    print("\n🎯 Enhanced validation system testing complete!")
