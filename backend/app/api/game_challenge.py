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


router = APIRouter()


class AttackRequest(BaseModel):
    challenge_id: int
    vulnerability_id: int


class FixRequest(BaseModel):
    challenge_id: int
    vulnerability_id: int


def _get_challenge_or_404(challenge_id: int, db: Session) -> models.GameChallenge:
    challenge = db.query(models.GameChallenge).filter(models.GameChallenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge


@router.post("/start")
def start_challenge(project_id: str, db: Session = Depends(get_db)):
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
def red_team_attack(req: AttackRequest, db: Session = Depends(get_db)):
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
def blue_team_fix(req: FixRequest, db: Session = Depends(get_db)):
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
def challenge_leaderboard(challenge_id: int, db: Session = Depends(get_db)):
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
def challenge_status(challenge_id: int, db: Session = Depends(get_db)):
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

