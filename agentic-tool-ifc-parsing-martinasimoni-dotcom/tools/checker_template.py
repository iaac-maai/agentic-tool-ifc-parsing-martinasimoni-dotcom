"""
IFC Compliance Checker Template

This is a starter template for your IFC compliance check tool.
Replace the example check with your own compliance check logic.

REQUIREMENTS (from AGENTS.md):
- File must be named checker_*.py (e.g., checker_walls.py, checker_doors.py)
- Function must be named check_* (e.g., check_door_count, check_wall_fire_rating)
- First argument must be `model` (an ifcopenshell.file object)
- Return a list of dicts with ALL required keys (see below)

REQUIRED DICT KEYS:
| Key              | Type         | Notes                                          |
|------------------|--------------|------------------------------------------------|
| element_id       | str or None  | GlobalId of the IFC element                    |
| element_type     | str          | e.g. "IfcDoor", "IfcWall", "Summary"           |
| element_name     | str          | Short display name                             |
| element_name_long| str or None  | Full name if available                         |
| check_status     | str          | One of: pass, fail, warning, blocked, log      |
| actual_value     | str          | What was found                                 |
| required_value   | str          | What was expected                              |
| comment          | str or None  | Human-readable explanation                     |
| log              | str or None  | Debug info                                     |
"""

import ifcopenshell


def check_example(model: ifcopenshell.file, **kwargs) -> list[dict]:
    """
    Example compliance check - counts elements of a specific type.
    
    Replace this with your own compliance check logic!
    
    Args:
        model: An ifcopenshell.file object representing the IFC model
        **kwargs: Additional parameters for your check
        
    Returns:
        List of result dictionaries following the required schema
    """
    results = []
    
    # Example: Check all IfcBuildingStorey elements
    storeys = model.by_type("IfcBuildingStorey")
    
    for storey in storeys:
        results.append({
            "element_id": storey.GlobalId,
            "element_type": "IfcBuildingStorey",
            "element_name": storey.Name or f"Storey #{storey.id()}",
            "element_name_long": getattr(storey, "LongName", None),
            "check_status": "pass" if storey.Name else "warning",
            "actual_value": storey.Name or "No name",
            "required_value": "Named storey",
            "comment": "Storey should have a name for clarity" if not storey.Name else None,
            "log": None,
        })
    
    # Add a summary result
    results.append({
        "element_id": None,
        "element_type": "Summary",
        "element_name": "Storey Count Check",
        "element_name_long": None,
        "check_status": "pass" if len(storeys) > 0 else "fail",
        "actual_value": str(len(storeys)),
        "required_value": ">= 1 storey",
        "comment": f"Found {len(storeys)} building storey(s)",
        "log": None,
    })
    
    return results


# =============================================================================
# YOUR COMPLIANCE CHECK IMPLEMENTATION GOES HERE
# =============================================================================
#
# Instructions:
# 1. Rename this file to checker_yourcheck.py (e.g., checker_walls.py)
# 2. Rename the function to check_yourcheck (e.g., check_wall_thickness)
# 3. Implement your compliance check logic
# 4. Make sure to return results in the required format
#
# Example ideas for compliance checks:
# - check_door_accessibility: Verify door widths meet accessibility standards
# - check_wall_fire_rating: Verify walls have proper fire rating properties
# - check_window_thermal: Verify window U-values meet energy standards
# - check_room_heights: Verify ceiling heights meet minimum requirements
# - check_stair_dimensions: Verify stair treads and risers meet code
#
# =============================================================================
