"""
IFC Door Accessibility Compliance Checker

Checks that IfcDoor elements meet minimum width requirements for accessibility.
Per EN 17210 / ADA standards, accessible doors require a clear opening width of
at least 850 mm (some standards require 900 mm for wheelchair access).
"""

import ifcopenshell
import ifcopenshell.util.unit as ifc_unit


MIN_ACCESSIBLE_WIDTH_MM = 850


def check_door_accessibility(model: ifcopenshell.file, min_width: int = MIN_ACCESSIBLE_WIDTH_MM, **kwargs) -> list[dict]:
    """
    Check that all doors in the model meet the minimum accessible width requirement.

    Args:
        model: An ifcopenshell.file object representing the IFC model
        min_width: Minimum door width in mm (default: 850 mm per EN 17210)

    Returns:
        List of result dicts following the required schema, one per door plus a summary.
    """
    results = []
    doors = model.by_type("IfcDoor")

    # Convert min_width from mm to the model's native length unit
    unit_scale = ifc_unit.calculate_unit_scale(model, "LENGTHUNIT")  # meters per model unit
    min_width_model = (min_width / 1000.0) / unit_scale if unit_scale else min_width

    pass_count = 0
    fail_count = 0
    warning_count = 0

    for door in doors:
        width = getattr(door, "OverallWidth", None)
        name = door.Name or f"Door #{door.id()}"

        if width is None:
            # No width data available — cannot assess compliance
            status = "warning"
            actual = "No width data"
            comment = "Door OverallWidth is not set; cannot verify accessibility compliance."
            warning_count += 1
        else:
            width_mm = round(width * unit_scale * 1000)
            if width >= min_width_model:
                status = "pass"
                actual = f"{width_mm} mm"
                comment = None
                pass_count += 1
            else:
                status = "fail"
                actual = f"{width_mm} mm"
                comment = f"Door width {width_mm} mm is below the minimum {min_width} mm required for accessibility."
                fail_count += 1

        results.append({
            "element_id": door.GlobalId,
            "element_type": "IfcDoor",
            "element_name": name,
            "element_name_long": None,
            "check_status": status,
            "actual_value": actual,
            "required_value": f">= {min_width} mm",
            "comment": comment,
            "log": None,
        })

    # Summary entry
    total = len(doors)
    if total == 0:
        summary_status = "warning"
        summary_comment = "No IfcDoor elements found in the model."
    elif fail_count > 0:
        summary_status = "fail"
        summary_comment = f"{fail_count} of {total} door(s) fail the minimum width requirement."
    elif warning_count > 0:
        summary_status = "warning"
        summary_comment = f"{warning_count} of {total} door(s) have no width data; compliance could not be verified."
    else:
        summary_status = "pass"
        summary_comment = f"All {total} door(s) meet the minimum width of {min_width} mm."

    results.append({
        "element_id": None,
        "element_type": "Summary",
        "element_name": "Door Accessibility Check",
        "element_name_long": None,
        "check_status": summary_status,
        "actual_value": f"{pass_count} pass / {fail_count} fail / {warning_count} warning",
        "required_value": f"All doors >= {min_width} mm wide",
        "comment": summary_comment,
        "log": None,
    })

    return results
