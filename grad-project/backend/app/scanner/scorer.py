from typing import List, Dict


def calculate_risk(findings: List[Dict]) -> Dict:
    """
    Compute a very simple, CVSS-inspired risk score from vulnerability findings.

    This does not replace real scoring frameworks, but:
    - gives students an intuitive numeric signal for how bad a project looks,
    - and provides a Low/Medium/High label that resembles enterprise tools.
    """
    severity_points = {
        "High": 5,
        "Medium": 3,
        "Low": 1,
    }

    breakdown = {
        "High": 0,
        "Medium": 0,
        "Low": 0,
    }

    total_score = 0

    for f in findings:
        sev = f.get("severity", "Medium")
        points = severity_points.get(sev, 3)
        total_score += points
        if sev in breakdown:
            breakdown[sev] += 1

    # Map total score to overall project risk level.
    if total_score <= 10:
        risk_level = "Low"
    elif total_score <= 20:
        risk_level = "Medium"
    else:
        risk_level = "High"

    return {
        "total_score": total_score,
        "risk_level": risk_level,
        "breakdown": breakdown,
    }

