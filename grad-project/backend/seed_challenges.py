"""
Seed the 10 security challenges into the database
"""

import sys
import os
from pathlib import Path

# Add the backend app to the Python path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.env_bootstrap import load_env
load_env()

from app.db.database import SessionLocal
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHALLENGES = [
    {
        "id": 1,
        "title": "SQL Injection",
        "description": "Learn to identify and exploit SQL injection vulnerabilities"
    },
    {
        "id": 2,
        "title": "Cross-Site Scripting (XSS)",
        "description": "Master XSS attacks and defense techniques"
    },
    {
        "id": 3,
        "title": "Cross-Site Request Forgery (CSRF)",
        "description": "Understand CSRF attacks and how to prevent them"
    },
    {
        "id": 4,
        "title": "Command Injection",
        "description": "Learn about OS command injection vulnerabilities"
    },
    {
        "id": 5,
        "title": "Broken Authentication",
        "description": "Exploit weak authentication mechanisms"
    },
    {
        "id": 6,
        "title": "Directory Traversal",
        "description": "Learn path traversal attacks and defenses"
    },
    {
        "id": 7,
        "title": "Insecure Storage",
        "description": "Understand insecure data storage vulnerabilities"
    },
    {
        "id": 8,
        "title": "Security Misconfiguration",
        "description": "Identify and exploit common misconfigurations"
    },
    {
        "id": 9,
        "title": "Unvalidated Redirect",
        "description": "Learn about open redirect vulnerabilities"
    },
    {
        "id": 10,
        "title": "XML External Entity (XXE)",
        "description": "Master XXE attacks and prevention"
    }
]


def seed_challenges():
    """Insert all 10 challenges into the database"""
    db = SessionLocal()
    try:
        logger.info("Seeding challenges into database...")
        
        for challenge in CHALLENGES:
            # Check if challenge already exists
            result = db.execute(
                text("SELECT id FROM challenges WHERE id = :id"),
                {"id": challenge["id"]}
            )
            
            if result.fetchone():
                logger.info(f"✓ Challenge {challenge['id']} ({challenge['title']}) already exists")
            else:
                # Insert new challenge
                db.execute(
                    text("""
                        INSERT INTO challenges (id, title, description)
                        VALUES (:id, :title, :description)
                    """),
                    challenge
                )
                logger.info(f"✓ Added challenge {challenge['id']}: {challenge['title']}")
        
        db.commit()
        logger.info("\n✓ All challenges seeded successfully!")
        
    except Exception as e:
        logger.error(f"Error seeding challenges: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("SCALE Challenge Seeder")
    logger.info("=" * 60)
    seed_challenges()
    logger.info("=" * 60)
