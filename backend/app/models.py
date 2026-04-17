from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime, Float, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .db.database import Base

# --- USER MODEL ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    role = Column(String(50), default='user')
    
    # Gatekeeping field:
    # Students/Admins = True
    # New Instructors = False (Pending)
    is_approved = Column(Boolean, default=True) 

    answers = relationship("UserAnswer", back_populates="user")
    progress = relationship("UserProgress", back_populates="user")
    quiz_attempts = relationship("QuizAttempt", back_populates="user")

# --- PROGRESS MODEL ---
class UserProgress(Base):  # <--- FIXED: Inherits from Base now
    __tablename__ = "user_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    challenge_id = Column(String(50))
    completed_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="progress")

# --- CHALLENGE MODELS ---
class XSSComment(Base):
    __tablename__ = "xss_comments"
    id = Column(Integer, primary_key=True, index=True)
    author = Column(String(255))
    content = Column(Text)

class Challenge(Base):
    __tablename__ = "challenges"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    description = Column(String(255))
    

# --- QUIZ BANK MODELS ---
class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    type = Column(String(20)) 
    topic = Column(String(50))
    difficulty = Column(String(20))
    skill_focus = Column(String(50))
    explanation = Column(Text)
    
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")
    answers = relationship("UserAnswer", back_populates="question")

class QuestionOption(Base):
    __tablename__ = "question_options"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    text = Column(String(255), nullable=False)
    is_correct = Column(Boolean, default=False)
    
    question = relationship("Question", back_populates="options")

class UserAnswer(Base):
    __tablename__ = "user_answers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    selected_option_id = Column(Integer, ForeignKey("question_options.id")) 
    is_correct = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="answers")
    question = relationship("Question", back_populates="answers")

class QuizAssignment(Base):
    __tablename__ = "quiz_assignments"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    instructor_id = Column(Integer, ForeignKey("users.id"))
    
    assigned_student_ids = Column(Text) 
    question_ids = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class QuizAssignmentStudent(Base):
    __tablename__ = "quiz_assignment_students"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("quiz_assignments.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)


class QuizAssignmentQuestion(Base):
    __tablename__ = "quiz_assignment_questions"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("quiz_assignments.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)


class QuizAttempt(Base):
    """Stores completed quiz attempts with score and time taken."""
    __tablename__ = "quiz_attempts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assignment_id = Column(Integer, ForeignKey("quiz_assignments.id"), nullable=True)
    title = Column(String(255))  # e.g. "Practice: SQL Injection" or assignment title
    score = Column(Integer)  # number correct
    total = Column(Integer)
    time_seconds = Column(Integer)  # elapsed time in seconds
    completed_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="quiz_attempts")


# --- CSRF CHALLENGE MODEL (NEW) ---
class CSRFAccount(Base):
    __tablename__ = "csrf_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    balance = Column(Integer, default=100)


# --- MESSAGING MODEL ---
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)


# --- PROJECT & SCAN HISTORY MODELS ---
class Project(Base):
    __tablename__ = "projects"

    # We re-use the existing project identifier (e.g. upload/extracted folder name)
    # so it is easy to correlate filesystem artifacts and DB entries.
    id = Column(String(100), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_scan_date = Column(DateTime, nullable=True)
    latest_risk_score = Column(Integer, nullable=True)
    latest_risk_level = Column(String(20), nullable=True)
    total_scans = Column(Integer, default=0)


class ScanHistory(Base):
    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(100), ForeignKey("projects.id"), nullable=False)
    scan_date = Column(DateTime, default=datetime.utcnow)
    total_vulnerabilities = Column(Integer, nullable=False)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String(20), nullable=False)
    # Store vulnerability type distribution as JSON-encoded text so we can
    # aggregate top vulnerability types for admin analytics.
    vuln_summary = Column(Text, nullable=True)


# --- RED/BLUE TEAM GAME MODELS ---
class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(10), nullable=False)  # 'red' or 'blue'
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    members = relationship("TeamMember", back_populates="team")


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    team = relationship("Team", back_populates="members")
    user = relationship("User")


class GameChallenge(Base):
    """
    Represents a red vs blue challenge for a given uploaded project.
    This is separate from the training 'challenges' table used by labs.
    """
    __tablename__ = "game_challenges"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(100), nullable=False)
    status = Column(String(20), default="active")  # active / inactive / completed
    created_at = Column(DateTime, default=datetime.utcnow)
    # SCALE lab challenge number (1–10) for instructor-led red vs blue sessions.
    lab_challenge_id = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)

    red_team_id = Column(Integer, ForeignKey("teams.id"))
    blue_team_id = Column(Integer, ForeignKey("teams.id"))

    red_score = Column(Integer, default=0)
    blue_score = Column(Integer, default=0)


class ChallengeVulnerability(Base):
    """
    Snapshot of a vulnerability for a specific challenge.
    We keep vulnerabilities even after they are 'fixed' by using is_fixed
    instead of deleting rows, so history and scoring remain intact.
    """
    __tablename__ = "challenge_vulnerabilities"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("game_challenges.id"), nullable=False)
    file = Column(String(500), nullable=False)
    line = Column(Integer)
    vulnerability_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    is_fixed = Column(Boolean, default=False)


class RedTeamAction(Base):
    __tablename__ = "red_team_actions"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("game_challenges.id"), nullable=False)
    vulnerability_id = Column(Integer, ForeignKey("challenge_vulnerabilities.id"), nullable=True)
    exploit_attempted = Column(Boolean, default=True)
    success = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    payload_used = Column(Text, nullable=True)
    impact_description = Column(Text, nullable=True)
    status = Column(String(20), nullable=True, default="confirmed")


class BlueTeamFix(Base):
    __tablename__ = "blue_team_fixes"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("game_challenges.id"), nullable=False)
    vulnerability_id = Column(Integer, ForeignKey("challenge_vulnerabilities.id"), nullable=True)
    fixed = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    submitted_code = Column(Text, nullable=True)


# --- PER-CHALLENGE STATE TRACKING ---
class ChallengeState(Base):
    """
    Tracks per-user state for each interactive challenge mini-game.
    Used for analytics, hint usage, and game-like progress.
    """
    __tablename__ = "challenge_state"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # e.g. 'csrf', 'broken-auth', 'security-misc', 'redirect', etc.
    challenge_id = Column(String(50), nullable=False)

    # Optional high-level stage label controlled by the challenge UIs
    current_stage = Column(String(100), default="started")
    attempt_count = Column(Integer, default=0)
    time_spent_seconds = Column(Integer, default=0)
    hints_used = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)


class SecurityLog(Base):
    __tablename__ = "security_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    event_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    payload = Column(Text, nullable=True)
    endpoint = Column(String(255), nullable=True)
    ip_address = Column(String(64), nullable=True)
    geo_bucket = Column(String(64), nullable=True)
    user_agent = Column(String(512), nullable=True)
    session_id = Column(String(128), nullable=True)
    correlation_id = Column(String(128), nullable=True)
    context_type = Column(String(50), default="real")
    meta_data = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User")

    __table_args__ = (
        Index("ix_security_logs_user_id", "user_id"),
        Index("ix_security_logs_event_type", "event_type"),
        Index("ix_security_logs_created_at", "created_at"),
    )


class UserLearningProgress(Base):
    __tablename__ = "user_learning_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    vulnerabilities_solved = Column(Integer, default=0)
    failed_attempts = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    avg_time = Column(Float, default=0.0)
    strongest_category = Column(String(100), default="N/A")
    weakest_category = Column(String(100), default="N/A")
    level = Column(String(30), default="Beginner")
    streak_days = Column(Integer, default=0)
    learning_speed = Column(Float, default=0.0)
    retention_score = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
