"""
Instructor-led Red vs Blue lab games (SCALE challenges 1–10).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ..db.database import get_db
from .. import models
from ..security.security_logger import SecuritySeverity, log_security_event
from ..schemas import RedBlueAttackBody, RedBlueFixBody, RedBlueGameCreate
from .auth import get_current_user, require_role
from .challenges import _verify_fix_improvement

router = APIRouter()

LAB_CHALLENGE_SLUGS: dict[int, str] = {
    1: "sql-injection",
    2: "xss",
    3: "csrf",
    4: "command-injection",
    5: "broken-auth",
    6: "security-misc",
    7: "insecure-storage",
    8: "directory-traversal",
    9: "xxe",
    10: "redirect",
}

LAB_CHALLENGE_TITLES: dict[int, str] = {
    1: "SQL Injection",
    2: "XSS",
    3: "CSRF",
    4: "Command Injection",
    5: "Broken Authentication",
    6: "Security Misconfiguration",
    7: "Insecure Storage",
    8: "Directory Traversal",
    9: "XXE",
    10: "Unvalidated Redirect",
}


def _slug_for_lab(lab_id: int) -> str:
    return LAB_CHALLENGE_SLUGS.get(lab_id, "")


def _challenge_dir_for_lab(lab_id: int) -> Optional[str]:
    slug = _slug_for_lab(lab_id)
    if not slug:
        return None
    return f"/app/challenges/challenge-{slug}"


def _red_score_query(db: Session, game_id: int) -> int:
    q = (
        db.query(models.RedTeamAction)
        .filter(models.RedTeamAction.challenge_id == game_id)
        .filter(
            (models.RedTeamAction.status == "confirmed")
            | (models.RedTeamAction.status.is_(None))
        )
    )
    return q.count()


def _blue_score_query(db: Session, game_id: int) -> int:
    return (
        db.query(models.BlueTeamFix)
        .filter(models.BlueTeamFix.challenge_id == game_id, models.BlueTeamFix.fixed == True)  # noqa: E712
        .count()
    )


@router.post("/game/create")
def create_redblue_game(
    request: Request,
    body: RedBlueGameCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("instructor", "admin")),
):
    all_ids = list(set(body.red_member_ids + body.blue_member_ids))
    missing: list[int] = []
    for uid in all_ids:
        if not db.query(models.User).filter(models.User.id == uid).first():
            missing.append(uid)
    if missing:
        raise HTTPException(status_code=400, detail=f"Unknown user id(s): {sorted(missing)}")

    if body.challenge_id not in LAB_CHALLENGE_SLUGS:
        raise HTTPException(status_code=404, detail="Challenge not found.")

    overlap = set(body.red_member_ids) & set(body.blue_member_ids)
    if overlap:
        raise HTTPException(status_code=400, detail=f"Users cannot be on both teams: {sorted(overlap)}")

    # Deactivate prior active games for this lab challenge id
    existing = (
        db.query(models.GameChallenge)
        .filter(
            models.GameChallenge.lab_challenge_id == body.challenge_id,
            models.GameChallenge.status == "active",
        )
        .all()
    )
    for row in existing:
        row.status = "inactive"

    red_team = models.Team(
        name=body.red_team_name,
        type="red",
        created_at=datetime.utcnow(),
        created_by=current_user.id,
    )
    blue_team = models.Team(
        name=body.blue_team_name,
        type="blue",
        created_at=datetime.utcnow(),
        created_by=current_user.id,
    )
    db.add(red_team)
    db.add(blue_team)
    db.flush()

    for uid in body.red_member_ids:
        db.add(models.TeamMember(team_id=red_team.id, user_id=uid))
    for uid in body.blue_member_ids:
        db.add(models.TeamMember(team_id=blue_team.id, user_id=uid))

    project_id = f"redblue-{uuid.uuid4().hex[:16]}"
    game = models.GameChallenge(
        project_id=project_id,
        status="active",
        created_at=datetime.utcnow(),
        lab_challenge_id=body.challenge_id,
        started_at=datetime.utcnow(),
        red_team_id=red_team.id,
        blue_team_id=blue_team.id,
        red_score=0,
        blue_score=0,
    )
    db.add(game)
    db.commit()
    db.refresh(game)

    log_security_event(
        db=db,
        event_type="redblue_game_created",
        severity=SecuritySeverity.LOW,
        user_id=current_user.id,
        request=request,
        metadata={
            "challenge_id": body.challenge_id,
            "red_team": body.red_team_name,
            "blue_team": body.blue_team_name,
        },
        context_type="challenge",
    )

    return {
        "game_id": game.id,
        "red_team_id": red_team.id,
        "blue_team_id": blue_team.id,
        "status": "active",
    }


@router.get("/game/{game_id}")
def get_redblue_game(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    game = db.query(models.GameChallenge).filter(models.GameChallenge.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Not found")

    red_team = db.query(models.Team).filter(models.Team.id == game.red_team_id).first()
    blue_team = db.query(models.Team).filter(models.Team.id == game.blue_team_id).first()

    lab_id = game.lab_challenge_id or 0

    def members_for(team_id: int) -> list[dict[str, Any]]:
        rows = (
            db.query(models.TeamMember, models.User)
            .join(models.User, models.TeamMember.user_id == models.User.id)
            .filter(models.TeamMember.team_id == team_id)
            .all()
        )
        return [{"user_id": u.id, "email": u.email} for _, u in rows]

    red_actions = (
        db.query(models.RedTeamAction)
        .filter(models.RedTeamAction.challenge_id == game_id)
        .order_by(models.RedTeamAction.timestamp.desc())
        .all()
    )
    blue_fixes = (
        db.query(models.BlueTeamFix)
        .filter(models.BlueTeamFix.challenge_id == game_id)
        .order_by(models.BlueTeamFix.timestamp.desc())
        .all()
    )

    r_score = _red_score_query(db, game_id)
    b_score = _blue_score_query(db, game_id)

    return {
        "game_id": game.id,
        "challenge_id": lab_id,
        "status": game.status,
        "started_at": (game.started_at or game.created_at).isoformat() + "Z"
        if (game.started_at or game.created_at)
        else "",
        "red_team": {
            "id": red_team.id if red_team else 0,
            "name": red_team.name if red_team else "",
            "members": members_for(game.red_team_id) if game.red_team_id else [],
            "score": r_score,
        },
        "blue_team": {
            "id": blue_team.id if blue_team else 0,
            "name": blue_team.name if blue_team else "",
            "members": members_for(game.blue_team_id) if game.blue_team_id else [],
            "score": b_score,
        },
        "red_actions": [
            {
                "id": a.id,
                "challenge_id": lab_id,
                "payload_used": a.payload_used or "",
                "timestamp": a.timestamp.isoformat() + "Z" if a.timestamp else "",
                "impact_description": a.impact_description or "",
            }
            for a in red_actions
        ],
        "blue_fixes": [
            {
                "id": f.id,
                "challenge_id": lab_id,
                "fixed": bool(f.fixed),
                "timestamp": f.timestamp.isoformat() + "Z" if f.timestamp else "",
                "submitted_code": (f.submitted_code or "")[:50],
            }
            for f in blue_fixes
        ],
    }


@router.get("/game/{game_id}/attacks")
def poll_attacks(
    game_id: int,
    since_id: int = Query(0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    game = db.query(models.GameChallenge).filter(models.GameChallenge.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Not found")

    lab_id = game.lab_challenge_id or 0
    rows = (
        db.query(models.RedTeamAction)
        .filter(models.RedTeamAction.challenge_id == game_id, models.RedTeamAction.id > since_id)
        .order_by(models.RedTeamAction.id.asc())
        .all()
    )
    return {
        "attacks": [
            {
                "id": a.id,
                "challenge_id": lab_id,
                "payload_used": a.payload_used or "",
                "timestamp": a.timestamp.isoformat() + "Z" if a.timestamp else "",
                "impact_description": a.impact_description or "",
            }
            for a in rows
        ]
    }


@router.post("/game/{game_id}/attack")
def log_attack(
    request: Request,
    game_id: int,
    body: RedBlueAttackBody,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    game = db.query(models.GameChallenge).filter(models.GameChallenge.id == game_id).first()
    if not game or game.status != "active":
        raise HTTPException(status_code=400, detail="Game not active.")

    on_red = (
        db.query(models.TeamMember)
        .filter(
            models.TeamMember.team_id == game.red_team_id,
            models.TeamMember.user_id == current_user.id,
        )
        .first()
    )
    if not on_red:
        raise HTTPException(status_code=403, detail="You are not on the red team for this game.")

    action = models.RedTeamAction(
        challenge_id=game_id,
        vulnerability_id=None,
        exploit_attempted=True,
        success=True,
        timestamp=datetime.utcnow(),
        user_id=current_user.id,
        payload_used=body.payload_used,
        impact_description=body.impact_description,
        status="confirmed",
    )
    db.add(action)
    db.commit()
    db.refresh(action)

    log_security_event(
        db=db,
        event_type="redblue_attack_logged",
        severity=SecuritySeverity.MEDIUM,
        user_id=current_user.id,
        request=request,
        metadata={"game_id": game_id, "payload": (body.payload_used or "")[:200]},
        context_type="challenge",
    )

    return {"action_id": action.id, "message": "Attack logged."}


@router.post("/game/{game_id}/fix")
def submit_fix(
    request: Request,
    game_id: int,
    body: RedBlueFixBody,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    game = db.query(models.GameChallenge).filter(models.GameChallenge.id == game_id).first()
    if not game or game.status != "active":
        raise HTTPException(status_code=400, detail="Game not active.")

    on_blue = (
        db.query(models.TeamMember)
        .filter(
            models.TeamMember.team_id == game.blue_team_id,
            models.TeamMember.user_id == current_user.id,
        )
        .first()
    )
    if not on_blue:
        raise HTTPException(status_code=403, detail="You are not on the blue team for this game.")

    lab_id = game.lab_challenge_id
    if not lab_id:
        raise HTTPException(status_code=400, detail="Cannot resolve challenge directory.")

    challenge_dir = _challenge_dir_for_lab(lab_id)
    if not challenge_dir:
        raise HTTPException(status_code=400, detail="Cannot resolve challenge directory.")

    challenge_folder = challenge_dir.strip("/").split("/")[-1]
    result = _verify_fix_improvement(challenge_folder, body.submitted_code)
    fixed = bool(result.get("fixed", False))
    improvement_score = int(result.get("improvement_score") or 0)

    code_trim = (body.submitted_code or "")[:5000]
    fix = models.BlueTeamFix(
        challenge_id=game_id,
        vulnerability_id=None,
        fixed=fixed,
        timestamp=datetime.utcnow(),
        user_id=current_user.id,
        submitted_code=code_trim,
    )
    db.add(fix)
    db.commit()

    log_security_event(
        db=db,
        event_type="redblue_fix_submitted",
        severity=SecuritySeverity.LOW,
        user_id=current_user.id,
        request=request,
        metadata={"game_id": game_id, "fixed": fixed},
        context_type="challenge",
    )

    return {
        "fixed": fixed,
        "improvement_score": improvement_score,
        "message": "Fix accepted." if fixed else "Fix did not pass tests.",
    }


@router.get("/my-games")
def my_redblue_games(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Games the current user participates in (red or blue team).
    """
    challenge_names: dict[int, str] = {
        1: "SQL Injection",
        2: "XSS",
        3: "CSRF",
        4: "Command Injection",
        5: "Broken Authentication",
        6: "Security Misconfiguration",
        7: "Insecure Storage",
        8: "Directory Traversal",
        9: "XXE",
        10: "Redirect",
    }
    member_rows = (
        db.query(models.TeamMember)
        .filter(models.TeamMember.user_id == current_user.id)
        .all()
    )
    team_ids = [m.team_id for m in member_rows]
    if not team_ids:
        return {"games": []}

    games = (
        db.query(models.GameChallenge)
        .filter(
            (models.GameChallenge.red_team_id.in_(team_ids))
            | (models.GameChallenge.blue_team_id.in_(team_ids))
        )
        .all()
    )
    out: list[dict[str, Any]] = []
    for g in games:
        my_team: str | None = None
        if g.red_team_id in team_ids:
            my_team = "red"
        elif g.blue_team_id in team_ids:
            my_team = "blue"
        if not my_team:
            continue

        red_team = db.query(models.Team).filter(models.Team.id == g.red_team_id).first()
        blue_team = db.query(models.Team).filter(models.Team.id == g.blue_team_id).first()
        lab_id = g.lab_challenge_id or 0
        challenge_name = challenge_names.get(lab_id, str(lab_id))
        r_score = _red_score_query(db, g.id)
        b_score = _blue_score_query(db, g.id)
        status = (g.status or "").lower()
        my_team_name = red_team.name if my_team == "red" else (blue_team.name if blue_team else "")
        opponent_team_name = blue_team.name if my_team == "red" else (red_team.name if red_team else "")
        my_score = r_score if my_team == "red" else b_score
        opponent_score = b_score if my_team == "red" else r_score

        out.append(
            {
                "game_id": g.id,
                "challenge_id": lab_id,
                "challenge_name": challenge_name,
                "status": status,
                "started_at": (g.started_at or g.created_at).isoformat() + "Z"
                if (g.started_at or g.created_at)
                else "",
                "my_team": my_team,
                "my_team_name": my_team_name or "",
                "opponent_team_name": opponent_team_name or "",
                "my_score": my_score,
                "opponent_score": opponent_score,
                "red_score": r_score,
                "blue_score": b_score,
                "red_team_name": red_team.name if red_team else "",
                "blue_team_name": blue_team.name if blue_team else "",
            }
        )
    return {"games": out}


@router.get("/games")
def list_games(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("instructor", "admin")),
):
    rows = db.query(models.GameChallenge).order_by(models.GameChallenge.created_at.desc()).all()
    out: list[dict[str, Any]] = []
    for g in rows:
        red = db.query(models.Team).filter(models.Team.id == g.red_team_id).first()
        blue = db.query(models.Team).filter(models.Team.id == g.blue_team_id).first()
        lab = g.lab_challenge_id or 0
        out.append(
            {
                "game_id": g.id,
                "challenge_id": lab,
                "status": g.status,
                "started_at": (g.started_at or g.created_at).isoformat() + "Z"
                if (g.started_at or g.created_at)
                else "",
                "red_team_name": red.name if red else "",
                "blue_team_name": blue.name if blue else "",
                "red_score": _red_score_query(db, g.id),
                "blue_score": _blue_score_query(db, g.id),
            }
        )
    return {"games": out}


@router.post("/game/{game_id}/end")
def end_game(
    request: Request,
    game_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("instructor", "admin")),
):
    game = db.query(models.GameChallenge).filter(models.GameChallenge.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Not found")

    game.status = "completed"
    db.commit()

    fr = _red_score_query(db, game_id)
    fb = _blue_score_query(db, game_id)

    log_security_event(
        db=db,
        event_type="redblue_game_ended",
        severity=SecuritySeverity.LOW,
        user_id=current_user.id,
        request=request,
        metadata={"game_id": game_id, "final_red_score": fr, "final_blue_score": fb},
        context_type="challenge",
    )

    return {"message": "Game ended.", "final_red_score": fr, "final_blue_score": fb}
