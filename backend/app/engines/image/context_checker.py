from typing import Dict, Any, List


def evaluate_image_context(
    metadata: Dict[str, Any],
    ai_results: Dict[str, Any],
    manipulation_results: Dict[str, Any],
    user_context: str = ""
) -> Dict[str, Any]:
    """
    Evaluates whether an authentic image may still be presented in a misleading or inaccurate context.
    """
    findings = []
    is_misleading = False

    date_time = metadata.get("date_time")
    if date_time:
        findings.append(f"Image creation timestamp recorded: {date_time}")
        if user_context and any(recent in user_context.lower() for recent in ["breaking", "just now", "today", "yesterday"]):
            # If the image timestamp is from years ago but claimed as breaking
            year = date_time[:4]
            if year.isdigit() and int(year) < 2024:
                is_misleading = True
                findings.append(f"Potential out-of-context recycling: metadata indicates capture year {year}, but claimed as recent event.")

    camera_make = metadata.get("camera_make")
    camera_model = metadata.get("camera_model")
    if camera_make or camera_model:
        findings.append(f"Physical camera device identified: {camera_make or ''} {camera_model or ''}".strip())

    return {
        "context_verdict": "MISLEADING_CONTEXT" if is_misleading else "ACCURATE_CONTEXT",
        "findings": findings
    }
