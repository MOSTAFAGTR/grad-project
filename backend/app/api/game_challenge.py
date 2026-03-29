from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.database import get_db
from .. import models
from .projects import (
    EXTRACTED_PROJECTS_DIR,
    scan_project_for_vulnerabilities,
)
from ..scanner.scorer import calculate_risk
from .auth import get_current_user, require_role


router = APIRouter()

_ADVANCED_HINTS: dict[str, list[dict[str, Any]]] = {
    "sql-injection": [
        {"level": 1, "text": "Inspect how user input is included in SQL query construction.", "penalty": 0},
        {"level": 2, "text": "Look for quote-breaking payloads that alter WHERE conditions.", "penalty": 5},
        {"level": 3, "text": "Use OR-based tautology to bypass credential checks.", "penalty": 10},
    ],
    "xss": [
        {"level": 1, "text": "Find an HTML sink that renders untrusted input.", "penalty": 0},
        {"level": 2, "text": "Try a payload that executes in browser context.", "penalty": 5},
        {"level": 3, "text": "Test event-handler based payload if script tags are filtered.", "penalty": 10},
    ],
    "csrf": [
        {"level": 1, "text": "Look for state-changing endpoints lacking CSRF token validation.", "penalty": 0},
        {"level": 2, "text": "Use an auto-submitted form from attacker-controlled origin.", "penalty": 5},
        {"level": 3, "text": "Ensure victim cookies are sent implicitly by browser.", "penalty": 10},
    ],
    "command-injection": [
        {"level": 1, "text": "Find where user input reaches a shell command.", "penalty": 0},
        {"level": 2, "text": "Try shell separators such as ';' or '&&'.", "penalty": 5},
        {"level": 3, "text": "Inject a harmless marker command to confirm execution.", "penalty": 10},
    ],
    "security-misc": [
        {"level": 1, "text": "Explore undocumented API paths that may expose config.", "penalty": 0},
        {"level": 2, "text": "Probe internal/admin endpoints while authenticated.", "penalty": 5},
        {"level": 3, "text": "Inspect responses for leaked secrets or debug metadata.", "penalty": 10},
    ],
    "directory-traversal": [
        {"level": 1, "text": "Check how file path is composed from user input.", "penalty": 0},
        {"level": 2, "text": "Try using ../ to escape intended directories.", "penalty": 5},
        {"level": 3, "text": "Probe sensitive files such as /etc/passwd in vulnerable mode.", "penalty": 10},
    ],
    "xxe": [
        {"level": 1, "text": "Review how XML parser handles external entities.", "penalty": 0},
        {"level": 2, "text": "Use DOCTYPE with SYSTEM entity declarations.", "penalty": 5},
        {"level": 3, "text": "Inject an entity that references local file paths.", "penalty": 10},
    ],
    "insecure-storage": [
        {"level": 1, "text": "Inspect whether credentials are stored as plain text.", "penalty": 0},
        {"level": 2, "text": "Attempt a storage dump and inspect password values.", "penalty": 5},
        {"level": 3, "text": "Observe why plaintext storage enables credential compromise.", "penalty": 10},
    ],
    "broken-auth": [
        {"level": 1, "text": "Observe how login checks are implemented.", "penalty": 0},
        {"level": 2, "text": "Try manipulating auth input to alter decision logic.", "penalty": 5},
        {"level": 3, "text": "Pivot from bypass to privileged response verification.", "penalty": 10},
    ],
}


class AttackRequest(BaseModel):
    challenge_id: int
    vulnerability_id: int


class FixRequest(BaseModel):
    challenge_id: int
    vulnerability_id: int


class HintRequest(BaseModel):
    challenge_id: str
    time_spent_delta: int = 0


def _get_challenge_or_404(challenge_id: int, db: Session) -> models.GameChallenge:
    challenge = db.query(models.GameChallenge).filter(models.GameChallenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge


def _get_or_create_challenge_state(db: Session, user_id: int, challenge_id: str) -> models.ChallengeState:
    state = (
        db.query(models.ChallengeState)
        .filter(models.ChallengeState.user_id == user_id, models.ChallengeState.challenge_id == challenge_id)
        .first()
    )
    if state:
        return state
    state = models.ChallengeState(user_id=user_id, challenge_id=challenge_id, current_stage="started")
    db.add(state)
    db.commit()
    db.refresh(state)
    return state


@router.post("/start")
def start_challenge(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("instructor", "admin")),
):
    """
    Initialize a red vs blue challenge for a given project.

    We snapshot current vulnerabilities for this challenge so that:
    - red team can attempt exploits,
    - blue team can mark them as fixed without altering the underlying code.
    """
    project_dir = EXTRACTED_PROJECTS_DIR / project_id
    if not project_dir.is_dir():
        raise HTTPException(status_code=404, detail="Extracted project not found")

    # Create teams for this challenge.
    red_team = models.Team(name=f"Red Team {project_id}", type="red", created_at=datetime.utcnow())
    blue_team = models.Team(name=f"Blue Team {project_id}", type="blue", created_at=datetime.utcnow())
    db.add(red_team)
    db.add(blue_team)
    db.flush()

    challenge = models.GameChallenge(
        project_id=project_id,
        status="active",
        created_at=datetime.utcnow(),
        red_team_id=red_team.id,
        blue_team_id=blue_team.id,
        red_score=0,
        blue_score=0,
    )
    db.add(challenge)
    db.flush()

    # Snapshot vulnerabilities for this challenge.
    scan_result = scan_project_for_vulnerabilities(project_dir)
    for f in scan_result["findings"]:
        vuln = models.ChallengeVulnerability(
            challenge_id=challenge.id,
            file=f.get("file", ""),
            line=f.get("line"),
            vulnerability_type=f.get("vulnerability_type", ""),
            severity=f.get("severity", "Medium"),
            is_fixed=False,
        )
        db.add(vuln)

    db.commit()

    return {
        "challenge_id": challenge.id,
        "project_id": project_id,
        "red_team_id": red_team.id,
        "blue_team_id": blue_team.id,
        "initial_vulnerabilities": len(scan_result["findings"]),
    }


@router.post("/red/attack")
def red_team_attack(
    req: AttackRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("instructor", "admin")),
):
    challenge = _get_challenge_or_404(req.challenge_id, db)

    vuln = (
        db.query(models.ChallengeVulnerability)
        .filter(
            models.ChallengeVulnerability.id == req.vulnerability_id,
            models.ChallengeVulnerability.challenge_id == challenge.id,
        )
        .first()
    )

    if vuln and not vuln.is_fixed:
        success = True
        challenge.red_score += 10
    else:
        success = False
        challenge.red_score -= 2

    action = models.RedTeamAction(
        challenge_id=challenge.id,
        vulnerability_id=req.vulnerability_id,
        exploit_attempted=True,
        success=success,
    )
    db.add(action)
    db.commit()

    return {
        "challenge_id": challenge.id,
        "success": success,
        "red_team_score": challenge.red_score,
    }


@router.post("/blue/fix")
def blue_team_fix(
    req: FixRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("instructor", "admin")),
):
    challenge = _get_challenge_or_404(req.challenge_id, db)

    vuln = (
        db.query(models.ChallengeVulnerability)
        .filter(
            models.ChallengeVulnerability.id == req.vulnerability_id,
            models.ChallengeVulnerability.challenge_id == challenge.id,
        )
        .first()
    )
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found for this challenge")

    if not vuln.is_fixed:
        vuln.is_fixed = True

        # Score based on severity
        sev = (vuln.severity or "Medium").capitalize()
        if sev == "High":
            points = 12
        elif sev == "Low":
            points = 4
        else:
            points = 8
        challenge.blue_score += points

        fix = models.BlueTeamFix(
            challenge_id=challenge.id,
            vulnerability_id=vuln.id,
            fixed=True,
        )
        db.add(fix)

    # Recalculate live risk based on remaining (unfixed) vulnerabilities.
    remaining = (
        db.query(models.ChallengeVulnerability)
        .filter(
            models.ChallengeVulnerability.challenge_id == challenge.id,
            models.ChallengeVulnerability.is_fixed == False,  # noqa: E712
        )
        .all()
    )
    # Build a minimal finding-like list for risk scoring.
    remaining_findings = [
        {"severity": v.severity, "vulnerability_type": v.vulnerability_type}
        for v in remaining
    ]
    risk = calculate_risk(remaining_findings) if remaining_findings else {"total_score": 0, "risk_level": "Low", "breakdown": {}}

    db.commit()

    return {
        "challenge_id": challenge.id,
        "blue_team_score": challenge.blue_score,
        "current_risk": risk,
    }


@router.get("/leaderboard")
def challenge_leaderboard(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    challenge = _get_challenge_or_404(challenge_id, db)

    if challenge.red_score > challenge.blue_score:
        status = "Red Team Leading"
    elif challenge.blue_score > challenge.red_score:
        status = "Blue Team Leading"
    else:
        status = "Tied"

    return {
        "challenge_id": challenge.id,
        "red_team_score": challenge.red_score,
        "blue_team_score": challenge.blue_score,
        "status": status,
    }


@router.get("/status")
def challenge_status(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    challenge = _get_challenge_or_404(challenge_id, db)

    vulns = (
        db.query(models.ChallengeVulnerability)
        .filter(models.ChallengeVulnerability.challenge_id == challenge.id)
        .all()
    )
    remaining = [v for v in vulns if not v.is_fixed]
    fixed = [v for v in vulns if v.is_fixed]

    remaining_findings = [
        {"severity": v.severity, "vulnerability_type": v.vulnerability_type}
        for v in remaining
    ]
    risk = calculate_risk(remaining_findings) if remaining_findings else {"total_score": 0, "risk_level": "Low", "breakdown": {}}

    score_diff = challenge.red_score - challenge.blue_score

    return {
        "challenge_id": challenge.id,
        "remaining_vulnerabilities": len(remaining),
        "fixed_vulnerabilities": len(fixed),
        "red_team_score": challenge.red_score,
        "blue_team_score": challenge.blue_score,
        "score_difference": score_diff,
        "current_risk": risk,
    }


@router.post("/hint")
def get_next_hint(
    req: HintRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    hints = _ADVANCED_HINTS.get(req.challenge_id, [])
    if not hints:
        return {
            "challenge_id": req.challenge_id,
            "hint": None,
            "level": 0,
            "penalty": 0,
            "remaining_levels": 0,
            "recommendation": "No hints configured for this challenge.",
            "completed": True,
        }

    state = _get_or_create_challenge_state(db, current_user.id, req.challenge_id)
    next_index = min(state.hints_used or 0, len(hints) - 1)
    hint = hints[next_index]

    state.hints_used = min((state.hints_used or 0) + 1, len(hints))
    state.attempt_count = (state.attempt_count or 0) + 1
    if req.time_spent_delta:
        state.time_spent_seconds = (state.time_spent_seconds or 0) + req.time_spent_delta
    state.last_updated = datetime.utcnow()
    db.commit()

    recommendation = (
        "Try the suggested direction now before requesting another hint."
        if next_index < len(hints) - 1
        else "You reached the final hint. Focus on implementing the secure fix."
    )

    return {
        "challenge_id": req.challenge_id,
        "hint": hint["text"],
        "hint_text": hint["text"],
        "level": hint["level"],
        "penalty": hint["penalty"],
        "remaining_levels": max(0, len(hints) - (state.hints_used or 0)),
        "recommendation": recommendation,
        "next_recommendation": recommendation,
        "completed": state.hints_used >= len(hints),
        "hints_used": state.hints_used,
        "attempts": state.attempt_count,
        "time_spent": state.time_spent_seconds,
    }

