from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from ..db.database import get_db
from .. import models
from .auth import get_current_user

router = APIRouter()


@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return total unread messages for the current user."""
    count = (
        db.query(models.Message)
        .filter(
            models.Message.receiver_id == current_user.id,
            models.Message.is_read == False,  # noqa: E712
        )
        .count()
    )
    return {"unread": count}


@router.get("/with/{user_id}")
def get_conversation(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Fetch all messages between the current user and another user.
    Marks incoming unread messages as read.
    """
    other = db.query(models.User).filter(models.User.id == user_id).first()
    if not other:
        raise HTTPException(status_code=404, detail="User not found")

    messages: List[models.Message] = (
        db.query(models.Message)
        .filter(
            or_(
                and_(
                    models.Message.sender_id == current_user.id,
                    models.Message.receiver_id == user_id,
                ),
                and_(
                    models.Message.sender_id == user_id,
                    models.Message.receiver_id == current_user.id,
                ),
            )
        )
        .order_by(models.Message.created_at.asc())
        .all()
    )

    # Mark incoming messages as read
    for m in messages:
        if m.receiver_id == current_user.id and not m.is_read:
            m.is_read = True
    db.commit()

    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "receiver_id": m.receiver_id,
            "content": m.content,
            "created_at": m.created_at,
            "is_read": m.is_read,
        }
        for m in messages
    ]


@router.post("/send")
def send_message(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Send a message.
    Role rules:
    - Student (role='user'): can only send to instructors or admins.
    - Instructor/Admin: can send to any existing user.
    """
    receiver_id = payload.get("receiver_id")
    content = (payload.get("content") or "").strip()

    if not receiver_id or not content:
        raise HTTPException(status_code=400, detail="receiver_id and content are required")

    receiver = db.query(models.User).filter(models.User.id == receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    # Enforce role-based messaging rules
    if current_user.role == "user":
        # Students may only message instructors or admins
        if receiver.role not in ("instructor", "admin"):
            raise HTTPException(
                status_code=403,
                detail="Students may only message instructors or admins.",
            )

    # Prevent sending to self
    if receiver.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot send message to yourself")

    msg = models.Message(
        sender_id=current_user.id,
        receiver_id=receiver.id,
        content=content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return {
        "id": msg.id,
        "sender_id": msg.sender_id,
        "receiver_id": msg.receiver_id,
        "content": msg.content,
        "created_at": msg.created_at,
        "is_read": msg.is_read,
    }


@router.get("/contacts")
def list_contacts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    List available contacts based on role rules.
    - Student: instructors and admins.
    - Instructor/Admin: all users (except self).
    """
    q = db.query(models.User)
    if current_user.role == "user":
        q = q.filter(models.User.role.in_(["instructor", "admin"]))
    else:
        q = q.filter(models.User.id != current_user.id)

    users = q.order_by(models.User.email.asc()).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "role": u.role,
        }
        for u in users
    ]

