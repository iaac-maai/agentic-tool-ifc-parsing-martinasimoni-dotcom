"""
Autograding tests for IFC Compliance Checker assignment.

These tests validate that the student's implementation follows the required contract:
1. File naming: checker_*.py
2. Function naming: check_*
3. Function signature: takes `model` as first argument
4. Return type: list of dicts
5. Required keys in each dict
6. Valid check_status values
"""

import pytest
import importlib
import importlib.util
import inspect
import sys
from pathlib import Path


# =============================================================================
# CONFIGURATION
# =============================================================================

REQUIRED_KEYS = {
    "element_id",
    "element_type", 
    "element_name",
    "element_name_long",
    "check_status",
    "actual_value",
    "required_value",
    "comment",
    "log",
}

VALID_STATUS_VALUES = {"pass", "fail", "warning", "blocked", "log"}


# =============================================================================
# DISCOVERY HELPERS
# =============================================================================

def discover_checker_modules():
    """Find all checker_*.py files in the tools/ directory."""
    tools_dir = Path(__file__).parent.parent / "tools"
    if not tools_dir.exists():
        return []
    
    checker_files = list(tools_dir.glob("checker_*.py"))
    # Exclude template file from grading
    checker_files = [f for f in checker_files if f.name != "checker_template.py"]
    return checker_files


def load_module_from_path(path: Path):
    """Dynamically load a Python module from a file path."""
    module_name = path.stem
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def find_check_functions(module):
    """Find all check_* functions in a module."""
    functions = []
    for name, obj in inspect.getmembers(module):
        if name.startswith("check_") and callable(obj):
            functions.append((name, obj))
    return functions


# =============================================================================
# TEST: MODULE DISCOVERY
# =============================================================================

class TestModuleDiscovery:
    """Tests for proper file naming and structure."""
    
    def test_checker_file_exists(self):
        """At least one checker_*.py file must exist in tools/ directory."""
        checker_files = discover_checker_modules()
        assert len(checker_files) > 0, (
            "No checker_*.py file found in tools/ directory. "
            "Create a file named 'checker_yourcheck.py' (e.g., checker_walls.py). "
            "Note: checker_template.py is excluded from grading."
        )
    
    def test_checker_file_naming(self):
        """Checker files must follow naming convention."""
        tools_dir = Path(__file__).parent.parent / "tools"
        all_py_files = list(tools_dir.glob("*.py")) if tools_dir.exists() else []
        # Exclude __init__.py and checker_template.py from consideration
        non_checker_files = [
            f.name for f in all_py_files 
            if not f.name.startswith("checker_") 
            and f.name != "__init__.py"
        ]
        
        # Fail only if there are non-checker python files (excluding special files)
        assert len(non_checker_files) == 0, (
            f"Found Python files not following naming convention: {non_checker_files}. "
            "Rename them to checker_*.py for the orchestrator to discover them."
        )


# =============================================================================
# TEST: FUNCTION DISCOVERY
# =============================================================================

class TestFunctionDiscovery:
    """Tests for proper function naming and signature."""
    
    def test_check_function_exists(self):
        """At least one check_* function must exist."""
        checker_files = discover_checker_modules()
        if not checker_files:
            pytest.skip("No checker files found")
        
        total_functions = 0
        for checker_file in checker_files:
            module = load_module_from_path(checker_file)
            functions = find_check_functions(module)
            total_functions += len(functions)
        
        assert total_functions > 0, (
            "No check_* functions found in checker files. "
            "Functions must be named 'check_something' (e.g., check_door_count)"
        )
    
    def test_check_function_signature(self):
        """Check functions must accept 'model' as first parameter."""
        checker_files = discover_checker_modules()
        if not checker_files:
            pytest.skip("No checker files found")
        
        for checker_file in checker_files:
            module = load_module_from_path(checker_file)
            functions = find_check_functions(module)
            
            for func_name, func in functions:
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                
                assert len(params) >= 1, (
                    f"Function {func_name} in {checker_file.name} must accept at least one parameter"
                )
                assert params[0] == "model", (
                    f"First parameter of {func_name} in {checker_file.name} must be 'model', "
                    f"got '{params[0]}'"
                )


# =============================================================================
# TEST: RETURN TYPE AND STRUCTURE
# =============================================================================

class TestReturnStructure:
    """Tests for proper return type and required keys."""
    
    def test_returns_list(self, simple_ifc_model):
        """Check functions must return a list."""
        checker_files = discover_checker_modules()
        if not checker_files:
            pytest.skip("No checker files found")
        
        for checker_file in checker_files:
            module = load_module_from_path(checker_file)
            functions = find_check_functions(module)
            
            for func_name, func in functions:
                result = func(simple_ifc_model)
                assert isinstance(result, list), (
                    f"Function {func_name} must return a list, got {type(result).__name__}"
                )
    
    def test_returns_dicts(self, simple_ifc_model):
        """Each item in the returned list must be a dict."""
        checker_files = discover_checker_modules()
        if not checker_files:
            pytest.skip("No checker files found")
        
        for checker_file in checker_files:
            module = load_module_from_path(checker_file)
            functions = find_check_functions(module)
            
            for func_name, func in functions:
                result = func(simple_ifc_model)
                
                if len(result) == 0:
                    continue  # Empty list is valid
                    
                for i, item in enumerate(result):
                    assert isinstance(item, dict), (
                        f"Function {func_name} returned list item [{i}] is not a dict, "
                        f"got {type(item).__name__}"
                    )
    
    def test_required_keys_present(self, simple_ifc_model):
        """All required keys must be present in each result dict."""
        checker_files = discover_checker_modules()
        if not checker_files:
            pytest.skip("No checker files found")
        
        for checker_file in checker_files:
            module = load_module_from_path(checker_file)
            functions = find_check_functions(module)
            
            for func_name, func in functions:
                result = func(simple_ifc_model)
                
                for i, item in enumerate(result):
                    if not isinstance(item, dict):
                        continue
                    
                    missing_keys = REQUIRED_KEYS - set(item.keys())
                    assert len(missing_keys) == 0, (
                        f"Function {func_name} result[{i}] missing required keys: {missing_keys}"
                    )
    
    def test_check_status_valid(self, simple_ifc_model):
        """check_status must be one of: pass, fail, warning, blocked, log."""
        checker_files = discover_checker_modules()
        if not checker_files:
            pytest.skip("No checker files found")
        
        for checker_file in checker_files:
            module = load_module_from_path(checker_file)
            functions = find_check_functions(module)
            
            for func_name, func in functions:
                result = func(simple_ifc_model)
                
                for i, item in enumerate(result):
                    if not isinstance(item, dict):
                        continue
                    
                    status = item.get("check_status")
                    assert status in VALID_STATUS_VALUES, (
                        f"Function {func_name} result[{i}] has invalid check_status '{status}'. "
                        f"Must be one of: {VALID_STATUS_VALUES}"
                    )


# =============================================================================
# TEST: VALUE TYPES
# =============================================================================

class TestValueTypes:
    """Tests for proper types of required keys."""
    
    def test_element_id_type(self, simple_ifc_model):
        """element_id must be str or None."""
        checker_files = discover_checker_modules()
        if not checker_files:
            pytest.skip("No checker files found")
        
        for checker_file in checker_files:
            module = load_module_from_path(checker_file)
            functions = find_check_functions(module)
            
            for func_name, func in functions:
                result = func(simple_ifc_model)
                
                for i, item in enumerate(result):
                    if not isinstance(item, dict):
                        continue
                    
                    element_id = item.get("element_id")
                    assert element_id is None or isinstance(element_id, str), (
                        f"Function {func_name} result[{i}] element_id must be str or None, "
                        f"got {type(element_id).__name__}"
                    )
    
    def test_string_fields_are_strings(self, simple_ifc_model):
        """String fields must be str type."""
        string_fields = ["element_type", "element_name", "check_status", "actual_value", "required_value"]
        
        checker_files = discover_checker_modules()
        if not checker_files:
            pytest.skip("No checker files found")
        
        for checker_file in checker_files:
            module = load_module_from_path(checker_file)
            functions = find_check_functions(module)
            
            for func_name, func in functions:
                result = func(simple_ifc_model)
                
                for i, item in enumerate(result):
                    if not isinstance(item, dict):
                        continue
                    
                    for field in string_fields:
                        value = item.get(field)
                        assert isinstance(value, str), (
                            f"Function {func_name} result[{i}] {field} must be str, "
                            f"got {type(value).__name__}: {value}"
                        )
    
    def test_nullable_fields(self, simple_ifc_model):
        """Nullable fields must be str or None."""
        nullable_fields = ["element_name_long", "comment", "log"]
        
        checker_files = discover_checker_modules()
        if not checker_files:
            pytest.skip("No checker files found")
        
        for checker_file in checker_files:
            module = load_module_from_path(checker_file)
            functions = find_check_functions(module)
            
            for func_name, func in functions:
                result = func(simple_ifc_model)
                
                for i, item in enumerate(result):
                    if not isinstance(item, dict):
                        continue
                    
                    for field in nullable_fields:
                        value = item.get(field)
                        assert value is None or isinstance(value, str), (
                            f"Function {func_name} result[{i}] {field} must be str or None, "
                            f"got {type(value).__name__}: {value}"
                        )


# =============================================================================
# TEST: FUNCTIONALITY (BASIC)
# =============================================================================

class TestFunctionality:
    """Tests for basic functionality."""
    
    def test_handles_empty_model(self, empty_ifc_model):
        """Check functions should handle models with minimal content."""
        checker_files = discover_checker_modules()
        if not checker_files:
            pytest.skip("No checker files found")
        
        for checker_file in checker_files:
            module = load_module_from_path(checker_file)
            functions = find_check_functions(module)
            
            for func_name, func in functions:
                # Should not raise an exception
                try:
                    result = func(empty_ifc_model)
                    assert isinstance(result, list), f"{func_name} should return a list"
                except Exception as e:
                    pytest.fail(
                        f"Function {func_name} raised exception on empty model: {e}"
                    )
    
    def test_produces_results(self, simple_ifc_model):
        """Check functions should produce results on a model with content."""
        checker_files = discover_checker_modules()
        if not checker_files:
            pytest.skip("No checker files found")
        
        results_produced = False
        for checker_file in checker_files:
            module = load_module_from_path(checker_file)
            functions = find_check_functions(module)
            
            for func_name, func in functions:
                result = func(simple_ifc_model)
                if len(result) > 0:
                    results_produced = True
                    break
            if results_produced:
                break
        
        assert results_produced, (
            "No check function produced any results. "
            "Your check should analyze the IFC model and return at least one result."
        )
