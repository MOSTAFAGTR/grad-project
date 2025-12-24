from app.db.database import SessionLocal, engine
from app import models
from sqlalchemy.orm import Session
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_data():
    db: Session = SessionLocal()
    try:
        # Check if questions already exist
        existing_question = db.query(models.Question).first()
        if existing_question:
            logger.info("Questions already exist. Skipping seeding.")
            return

        logger.info("Seeding database with initial questions...")
        
        questions_data = [
            # SQL Injection Questions
            {
                "text": "What is SQL Injection (SQLi)?",
                "type": "multiple_choice",
                "topic": "SQL Injection",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "SQL Injection is a code injection technique whereby an attacker executes malicious SQL statements that control a web application's database server.",
                "options": [
                    {"text": "A way to optimize SQL queries", "is_correct": False},
                    {"text": "A vulnerability allowing attackers to execute malicious SQL", "is_correct": True},
                    {"text": "A database backup technique", "is_correct": False},
                    {"text": "A method to encrypt database content", "is_correct": False},
                ]
            },
            {
                "text": "Which character is often used to start an SQL Injection attack by closing a string literal?",
                "type": "multiple_choice",
                "topic": "SQL Injection",
                "difficulty": "Easy",
                "skill_focus": "Exploitation",
                "explanation": "The single quote (') is commonly used to close a string literal in SQL queries.",
                "options": [
                    {"text": ";", "is_correct": False},
                    {"text": "*", "is_correct": False},
                    {"text": "'", "is_correct": True},
                    {"text": "!", "is_correct": False},
                ]
            },
            {
                "text": "What does the SQL comment sequence '--' do in an injection attack?",
                "type": "multiple_choice",
                "topic": "SQL Injection",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "In many SQL dialects, '--' starts a comment, causing the database to ignore the remainder of the query.",
                "options": [
                    {"text": "Starts a new query", "is_correct": False},
                    {"text": "Ignores the rest of the query", "is_correct": True},
                    {"text": "Deletes the table", "is_correct": False},
                    {"text": "Executes the query immediately", "is_correct": False},
                ]
            },
            {
                "text": "Which of the following is an example of a Tautology based SQL injection?",
                "type": "multiple_choice",
                "topic": "SQL Injection",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "' OR 1=1 is a tautology (always true) often used to bypass authentication.",
                "options": [
                    {"text": "SELECT * FROM users", "is_correct": False},
                    {"text": "' OR 1=1 --", "is_correct": True},
                    {"text": "DROP TABLE users", "is_correct": False},
                    {"text": "UNION SELECT 1,2", "is_correct": False},
                ]
            },
            {
                "text": "What is a 'Blind' SQL Injection?",
                "type": "multiple_choice",
                "topic": "SQL Injection",
                "difficulty": "Hard",
                "skill_focus": "Knowledge",
                "explanation": "In Blind SQLi, the application doesn't return data directly, so attackers infer information based on behavior or timing.",
                "options": [
                    {"text": "The attacker cannot see the keyboard", "is_correct": False},
                    {"text": "The database is encrypted", "is_correct": False},
                    {"text": "No data is returned, only true/false behavior or timing differences", "is_correct": True},
                    {"text": "The injection happens automatically", "is_correct": False},
                ]
            },
            {
                "text": "Which SQL statement is commonly used in Union-based SQL injection to combine results?",
                "type": "multiple_choice",
                "topic": "SQL Injection",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "The UNION operator is used to combine the result-set of two or more SELECT statements.",
                "options": [
                    {"text": "JOIN", "is_correct": False},
                    {"text": "MERGE", "is_correct": False},
                    {"text": "UNION", "is_correct": True},
                    {"text": "COMBINE", "is_correct": False},
                ]
            },
            {
                "text": "What is the most effective defense against SQL Injection?",
                "type": "multiple_choice",
                "topic": "SQL Injection",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "Prepared statements (or parameterized queries) ensure that the database treats user input as data, not executable code.",
                "options": [
                    {"text": "Input validation", "is_correct": False},
                    {"text": "Prepared Statements (Parameterized Queries)", "is_correct": True},
                    {"text": "Using a firewall", "is_correct": False},
                    {"text": "Encrypting the database", "is_correct": False},
                ]
            },

            # XSS Questions
            {
                "text": "What does XSS stand for?",
                "type": "multiple_choice",
                "topic": "XSS",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "XSS stands for Cross-Site Scripting.",
                "options": [
                    {"text": "External Site Styling", "is_correct": False},
                    {"text": "Cross-Site Scripting", "is_correct": True},
                    {"text": "XML Site Scripting", "is_correct": False},
                    {"text": "X-Ray Site Security", "is_correct": False},
                ]
            },
            {
                "text": "Which programming language is primarily targeted/executed in an XSS attack?",
                "type": "multiple_choice",
                "topic": "XSS",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "XSS attacks execute malicious JavaScript in the victim's browser.",
                "options": [
                    {"text": "Python", "is_correct": False},
                    {"text": "C++", "is_correct": False},
                    {"text": "JavaScript", "is_correct": True},
                    {"text": "SQL", "is_correct": False},
                ]
            },
            {
                "text": "What is Stored (Persistent) XSS?",
                "type": "multiple_choice",
                "topic": "XSS",
                "difficulty": "Medium",
                "skill_focus": "Knowledge",
                "explanation": "Stored XSS occurs when the malicious script is permanently stored on the target server (e.g., in a comment or database).",
                "options": [
                    {"text": "The script is reflected off the web server immediately", "is_correct": False},
                    {"text": "The script is saved in the database and served to other users", "is_correct": True},
                    {"text": "The script is only in the DOM", "is_correct": False},
                    {"text": "The script targets the server's OS", "is_correct": False},
                ]
            },
            {
                "text": "What is Reflected XSS?",
                "type": "multiple_choice",
                "topic": "XSS",
                "difficulty": "Medium",
                "skill_focus": "Knowledge",
                "explanation": "Reflected XSS occurs when code injected in a request is immediately returned (reflected) in the response.",
                "options": [
                    {"text": "The payload is stored in the database", "is_correct": False},
                    {"text": "The payload is reflected in the web application's response", "is_correct": True},
                    {"text": "The payload modifies the DOM directly", "is_correct": False},
                    {"text": "The payload is encrypted", "is_correct": False},
                ]
            },
            {
                "text": "Which HTML tag is most commonly used to test for XSS vulnerabilities?",
                "type": "multiple_choice",
                "topic": "XSS",
                "difficulty": "Easy",
                "skill_focus": "Exploitation",
                "explanation": "The <script> tag is the classic way to execute JavaScript.",
                "options": [
                    {"text": "<div>", "is_correct": False},
                    {"text": "<h1>", "is_correct": False},
                    {"text": "<script>", "is_correct": True},
                    {"text": "<span>", "is_correct": False},
                ]
            },
            {
                "text": "What is DOM-based XSS?",
                "type": "multiple_choice",
                "topic": "XSS",
                "difficulty": "Hard",
                "skill_focus": "Knowledge",
                "explanation": "DOM-based XSS vulnerability exists in client-side code rather than server-side code.",
                "options": [
                    {"text": "Attack acts on the server database", "is_correct": False},
                    {"text": "Attack payload is executed as a result of modifying the DOM environment", "is_correct": True},
                    {"text": "Attack uses a domain controller", "is_correct": False},
                    {"text": "Attack targets the DNS server", "is_correct": False},
                ]
            },
            {
                "text": "Which of the following is a common defense against XSS?",
                "type": "multiple_choice",
                "topic": "XSS",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "Content Security Policy (CSP) restricts the sources from which content can be loaded.",
                "options": [
                    {"text": "Disabling cookies", "is_correct": False},
                    {"text": "Content Security Policy (CSP)", "is_correct": True},
                    {"text": "Using SSL/HTTPS", "is_correct": False},
                    {"text": "Strong passwords", "is_correct": False},
                ]
            },
            {
                "text": "Why is 'alert(1)' often used in XSS proof-of-concepts?",
                "type": "multiple_choice",
                "topic": "XSS",
                "difficulty": "Easy",
                "skill_focus": "Exploitation",
                "explanation": "It creates a visible popup proving that JavaScript execution was possible.",
                "options": [
                    {"text": "It destroys the database", "is_correct": False},
                    {"text": "It provides a visual confirmation that code executed", "is_correct": True},
                    {"text": "It steals the user's password", "is_correct": False},
                    {"text": "It crashes the browser", "is_correct": False},
                ]
            }
        ]

        for q_data in questions_data:
            options_data = q_data.pop("options")
            question = models.Question(**q_data)
            db.add(question)
            db.commit()
            db.refresh(question)
            
            for opt_data in options_data:
                option = models.QuestionOption(**opt_data, question_id=question.id)
                db.add(option)
            db.commit()
            
        logger.info("Successfully seeded 15 questions.")
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Create tables if they don't exist (though main.py usually does this, seed might run first)
    models.Base.metadata.create_all(bind=engine)
    seed_data()
