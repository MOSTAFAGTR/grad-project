from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from sqlalchemy import inspect, text
import time
import logging

# --- IMPORT ROUTERS ---
# We added 'stats', 'projects', 'game_challenge', and 'misconfig' to this import list
from .api import auth, quizzes, challenges, stats, messages, projects, game_challenge, misconfig, ai_mentor, attack_simulator, project_analyzer, security_logs, quiz_dynamic, instructor, report
from .db import database
from . import models 

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# --- CORS SETUP ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REGISTER ROUTES ---
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(quizzes.router, prefix="/api/quizzes", tags=["quizzes"])
app.include_router(challenges.router, prefix="/api/challenges", tags=["challenges"])
# NEW: Register the stats router so the Dashboards work
app.include_router(stats.router, prefix="/api/stats", tags=["statistics"])
# NEW: Messaging routes
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
# NEW: Project upload routes
app.include_router(projects.router, prefix="/api", tags=["projects"])
# NEW: Red vs Blue challenge routes (singular /challenge prefix)
app.include_router(game_challenge.router, prefix="/api/challenge", tags=["game_challenge"])
# NEW: Security misconfiguration mini-app routes
app.include_router(misconfig.router, prefix="/api", tags=["misconfig"])
# NEW: AI mentor analysis routes
app.include_router(ai_mentor.router, prefix="/api/ai", tags=["ai_mentor"])
# NEW: attack simulation lab routes
app.include_router(attack_simulator.router, prefix="/api/attack", tags=["attack_simulator"])
# NEW: project structure analyzer routes
app.include_router(project_analyzer.router, prefix="/api", tags=["project_analyzer"])
# NEW: centralized security logs routes
app.include_router(security_logs.router, prefix="/api/security", tags=["security_logs"])
# NEW: dynamic quiz generation from scan findings
app.include_router(quiz_dynamic.router, prefix="/api/quiz", tags=["quiz_dynamic"])
app.include_router(instructor.router, prefix="/api/instructor", tags=["instructor"])
app.include_router(report.router)


def _ensure_runtime_schema():
    """
    Lightweight runtime migration guard for environments without Alembic.
    Ensures newly introduced columns exist before write paths use them.
    """
    try:
        inspector = inspect(database.engine)
        with database.engine.begin() as conn:
            if "security_logs" in inspector.get_table_names():
                security_existing = {col["name"] for col in inspector.get_columns("security_logs")}
                security_required = {
                    "geo_bucket": "VARCHAR(50) NULL",
                    "session_id": "VARCHAR(100) NULL",
                    "correlation_id": "VARCHAR(100) NULL",
                    "context_type": "VARCHAR(50) NULL DEFAULT 'real'",
                }
                for column_name, ddl in security_required.items():
                    if column_name in security_existing:
                        continue
                    conn.execute(text(f"ALTER TABLE security_logs ADD COLUMN {column_name} {ddl}"))
                    logger.warning("Applied runtime schema patch: security_logs.%s", column_name)

            if "user_learning_progress" in inspector.get_table_names():
                learning_existing = {col["name"] for col in inspector.get_columns("user_learning_progress")}
                learning_required = {
                    "streak_days": "INT NULL DEFAULT 0",
                    "learning_speed": "FLOAT NULL DEFAULT 0",
                    "retention_score": "FLOAT NULL DEFAULT 0",
                }
                for column_name, ddl in learning_required.items():
                    if column_name in learning_existing:
                        continue
                    conn.execute(text(f"ALTER TABLE user_learning_progress ADD COLUMN {column_name} {ddl}"))
                    logger.warning("Applied runtime schema patch: user_learning_progress.%s", column_name)
    except Exception as exc:
        # Logging subsystem must not block API startup if migration is partially unsupported.
        logger.warning("Runtime schema self-heal skipped: %s", exc)

# --- DATABASE CONNECTION RETRY ---
@app.on_event("startup")
def startup_event():
    logger.info("Waiting for Database...")
    retries = 10
    while retries > 0:
        try:
            # Create tables if they don't exist
            models.Base.metadata.create_all(bind=database.engine)
            _ensure_runtime_schema()
            logger.info("Database connected and tables created!")
            break
        except OperationalError as e:
            retries -= 1
            logger.warning(f"DB not ready. Retrying... ({retries} left)")
            time.sleep(3)
            if retries == 0:
                logger.error("Could not connect to database.")
                raise e

@app.get("/")
def read_root():
    return {"message": "Welcome to the SCALE API"}