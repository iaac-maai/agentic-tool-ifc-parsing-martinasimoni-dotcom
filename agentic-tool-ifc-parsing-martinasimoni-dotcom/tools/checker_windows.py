"""
IFC Window Minimum Area Compliance Checker

Checks that IfcWindow elements meet minimum glazing area requirements for natural light.
Per EN 17037 (Daylight in Buildings), windows should provide adequate daylight;
a common simplified rule requires a minimum glazing area of 0.5 m² per window.
"""

import ifcopenshell
import ifcopenshell.util.unit as ifc_unit


MIN_GLAZING_AREA_M2 = 0.5


def check_window_min_area(model: ifcopenshell.file, min_area: float = MIN_GLAZING_AREA_M2, **kwargs) -> list[dict]:
    """
    Check that all windows in the model meet the minimum glazing area requirement.

    Args:
        model: An ifcopenshell.file object representing the IFC model
        min_area: Minimum window area in m² (default: 0.5 m² per EN 17037)

    Returns:
        List of result dicts following the required schema, one per window plus a summary.
    """
    results = []
    windows = model.by_type("IfcWindow")

    # Get model unit scale (meters per model unit) for unit-safe conversion
    unit_scale = ifc_unit.calculate_unit_scale(model, "LENGTHUNIT")

    pass_count = 0
    fail_count = 0
    warning_count = 0

    for window in windows:
        width = getattr(window, "OverallWidth", None)
        height = getattr(window, "OverallHeight", None)
        name = window.Name or f"Window #{window.id()}"

        if width is None or height is None:
            status = "warning"
            actual = "No dimensions data"
            comment = "Window OverallWidth or OverallHeight is not set; cannot verify area compliance."
            warning_count += 1
        else:
            # Convert from model units to meters, then compute area in m²
            width_m = width * unit_scale
            height_m = height * unit_scale
            area_m2 = round(width_m * height_m, 3)

            if area_m2 >= min_area:
                status = "pass"
                actual = f"{area_m2} m²"
                comment = None
                pass_count += 1
            else:
                status = "fail"
                actual = f"{area_m2} m²"
                comment = f"Window area {area_m2} m² is below the minimum {min_area} m² required for natural light."
                fail_count += 1

        results.append({
            "element_id": window.GlobalId,
            "element_type": "IfcWindow",
            "element_name": name,
            "element_name_long": None,
            "check_status": status,
            "actual_value": actual,
            "required_value": f">= {min_area} m²",
            "comment": comment,
            "log": None,
        })

    # Summary entry
    total = len(windows)
    if total == 0:
        summary_status = "warning"
        summary_comment = "No IfcWindow elements found in the model."
    elif fail_count > 0:
        summary_status = "fail"
        summary_comment = f"{fail_count} of {total} window(s) fail the minimum glazing area requirement."
    elif warning_count > 0:
        summary_status = "warning"
        summary_comment = f"{warning_count} of {total} window(s) have no dimension data; compliance could not be verified."
    else:
        summary_status = "pass"
        summary_comment = f"All {total} window(s) meet the minimum glazing area of {min_area} m²."

    results.append({
        "element_id": None,
        "element_type": "Summary",
        "element_name": "Window Minimum Area Check",
        "element_name_long": None,
        "check_status": summary_status,
        "actual_value": f"{pass_count} pass / {fail_count} fail / {warning_count} warning",
        "required_value": f"All windows >= {min_area} m²",
        "comment": summary_comment,
        "log": None,
    })

    return results
