import * as React from 'react';
import { useNavigate } from 'react-router-dom';

const BrokenAuthTutorialPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="text-white max-w-4xl">
      <h1 className="text-4xl font-bold mb-2">Broken Authentication</h1>
      <p className="text-gray-400 mb-8">Understanding credential and session vulnerabilities</p>

      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-3 text-red-400">What is Broken Authentication?</h2>
        <p className="text-gray-300 leading-relaxed">
          Broken authentication occurs when an application fails to properly implement authentication mechanisms, allowing
          attackers to compromise passwords, keys, or session tokens, or exploit other implementation flaws to assume other
          users&apos; identities. It is ranked in the OWASP Top 10 because it is both common and severe.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-3 text-red-400">Common Vulnerable Patterns</h2>
        <p className="text-gray-400 text-sm mb-2">VULNERABLE — Plaintext password storage and comparison:</p>
        <pre className="bg-gray-900 border border-gray-700 rounded-lg p-4 text-sm text-green-300 overflow-x-auto mb-6 whitespace-pre-wrap">
{`# VULNERABLE: Storing and comparing plaintext passwords
users_db = {"admin": "secret123", "user": "password"}

def login(username, password):
    if users_db.get(username) == password:
        return create_session(username)
    return None
# If the database is breached, ALL passwords are immediately
# exposed with no protection whatsoever.`}
        </pre>
        <p className="text-gray-400 text-sm mb-2">VULNERABLE — Weak session token generation:</p>
        <pre className="bg-gray-900 border border-gray-700 rounded-lg p-4 text-sm text-green-300 overflow-x-auto whitespace-pre-wrap">
{`# VULNERABLE: Predictable session tokens
import random
def create_session(username):
    token = str(random.randint(1000, 9999))  # Only 9000 possibilities
    sessions[token] = username
    return token
# An attacker can brute-force all possible tokens in seconds.`}
        </pre>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-3 text-emerald-400">The Secure Approach</h2>
        <p className="text-gray-400 text-sm mb-2">SECURE — Bcrypt password hashing:</p>
        <pre className="bg-gray-900 border border-gray-700 rounded-lg p-4 text-sm text-green-300 overflow-x-auto mb-6 whitespace-pre-wrap">
{`from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def register(username, password):
    hashed = pwd_context.hash(password)
    db.save_user(username, hashed)

def login(username, password):
    user = db.get_user(username)
    if user and pwd_context.verify(password, user.hashed_password):
        return create_secure_session(username)
    return None
# Even if the DB is breached, bcrypt hashes cannot be reversed.`}
        </pre>
        <p className="text-gray-400 text-sm mb-2">SECURE — Cryptographically secure session tokens:</p>
        <pre className="bg-gray-900 border border-gray-700 rounded-lg p-4 text-sm text-green-300 overflow-x-auto whitespace-pre-wrap">
{`import secrets
def create_secure_session(username):
    token = secrets.token_urlsafe(32)  # 256 bits of randomness
    sessions[token] = username
    return token
# Impossible to brute-force: 2^256 possible values.`}
        </pre>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-3 text-blue-400">Why This Matters</h2>
        <p className="text-gray-300 leading-relaxed">
          Broken authentication is responsible for some of the largest data breaches in history. When credentials are stored
          as plaintext or with weak hashing (MD5, SHA1), a single database breach exposes every user&apos;s password
          immediately. Attackers then use credential stuffing — trying those same username/password combinations on banking,
          email, and social media sites. Modern password hashing with bcrypt, scrypt, or Argon2 means that even after a
          breach, attackers face years of computation to crack a single password.
        </p>
      </section>

      <section className="mb-10">
        <h2 className="text-2xl font-bold mb-3 text-purple-400">In This Challenge</h2>
        <p className="text-gray-300 leading-relaxed mb-6">
          The broken auth challenge exposes a login endpoint that compares passwords in plaintext against a hardcoded
          dictionary. Your goal is to identify this pattern and exploit it by supplying credentials that match a known
          plaintext value. In the fix phase, you will replace the plaintext comparison with proper bcrypt hashing using
          passlib.
        </p>
        <div className="w-full max-w-4xl mx-auto rounded-lg overflow-hidden border-2 border-gray-700 border-dashed mb-6 min-h-[120px] flex items-center justify-center text-gray-500 text-sm">
          Tutorial video placeholder — content planned for a future phase
        </div>
        <button
          type="button"
          onClick={() => navigate('/challenges/5/attack')}
          className="w-full max-w-md bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-4 rounded-lg"
        >
          Go to Attack
        </button>
      </section>
    </div>
  );
};

export default BrokenAuthTutorialPage;
