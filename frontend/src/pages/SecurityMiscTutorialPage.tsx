import * as React from 'react';
import { useNavigate } from 'react-router-dom';

const SecurityMiscTutorialPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="text-white max-w-4xl">
      <h1 className="text-4xl font-bold mb-2">Security Misconfiguration</h1>
      <p className="text-gray-400 mb-8">When default or insecure settings expose your system</p>

      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-3 text-green-400">What is Security Misconfiguration?</h2>
        <p className="text-gray-300 leading-relaxed">
          Security misconfiguration is the most commonly seen issue in security audits. It occurs when security settings are
          defined, implemented, and maintained incorrectly. This can happen at any level of the application stack: network,
          platform, web server, application server, database, framework, or custom code. OWASP ranks it in the Top 10
          because it is pervasive and easy to exploit once discovered.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-3 text-amber-400">Common Vulnerable Patterns</h2>
        <p className="text-gray-400 text-sm mb-2">VULNERABLE — Debug mode in production:</p>
        <pre className="bg-gray-900 border border-gray-700 rounded-lg p-4 text-sm text-green-300 overflow-x-auto mb-6 whitespace-pre-wrap">
{`# VULNERABLE: Debug mode exposes stack traces and config
app = Flask(__name__)
app.run(debug=True)  # Never in production!
# Attackers can see full stack traces, source code paths,
# and sometimes execute arbitrary code via the debugger.`}
        </pre>
        <p className="text-gray-400 text-sm mb-2">VULNERABLE — Sensitive config exposed via endpoint:</p>
        <pre className="bg-gray-900 border border-gray-700 rounded-lg p-4 text-sm text-green-300 overflow-x-auto mb-6 whitespace-pre-wrap">
{`# VULNERABLE: Admin config endpoint with no authentication
@app.route('/api/admin/config')
def get_config():
    return {
        "db_url": os.getenv("DATABASE_URL"),
        "secret_key": os.getenv("SECRET_KEY"),
        "debug": True
    }
# Any unauthenticated user can retrieve database credentials
# and the JWT signing secret.`}
        </pre>
        <p className="text-gray-400 text-sm mb-2">VULNERABLE — Default credentials never changed:</p>
        <pre className="bg-gray-900 border border-gray-700 rounded-lg p-4 text-sm text-green-300 overflow-x-auto whitespace-pre-wrap">
{`# VULNERABLE: Hardcoded default admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"  # Default never changed
# The first thing attackers try when they find an admin panel.`}
        </pre>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-3 text-emerald-400">The Secure Approach</h2>
        <p className="text-gray-400 text-sm mb-2">SECURE — Require authentication on all sensitive endpoints:</p>
        <pre className="bg-gray-900 border border-gray-700 rounded-lg p-4 text-sm text-green-300 overflow-x-auto mb-6 whitespace-pre-wrap">
{`from functools import wraps

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not verify_admin_token(token):
            abort(403)
        return f(*args, **kwargs)
    return decorated

@app.route('/api/admin/config')
@require_admin
def get_config():
    # Only return non-sensitive operational status
    return {"status": "healthy", "version": "1.0.0"}`}
        </pre>
        <p className="text-gray-400 text-sm mb-2">SECURE — Environment-based configuration:</p>
        <pre className="bg-gray-900 border border-gray-700 rounded-lg p-4 text-sm text-green-300 overflow-x-auto whitespace-pre-wrap">
{`import os

# SECURE: Never expose secrets via endpoints
# All secrets live in environment variables only
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable required")`}
        </pre>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-3 text-blue-400">Why This Matters</h2>
        <p className="text-gray-300 leading-relaxed">
          Security misconfiguration is dangerous precisely because it is invisible to developers who focus on features rather
          than security posture. Debug endpoints left enabled, admin panels exposed without authentication, verbose error
          messages in production, and default credentials that were never rotated are all examples of misconfigurations that
          have caused major breaches. The 2017 Equifax breach, which exposed 147 million people&apos;s personal data, was
          caused partly by an unpatched, misconfigured Apache Struts server — not by sophisticated zero-day exploits.
        </p>
      </section>

      <section className="mb-10">
        <h2 className="text-2xl font-bold mb-3 text-purple-400">In This Challenge</h2>
        <p className="text-gray-300 leading-relaxed mb-6">
          The security misconfiguration challenge exposes an admin configuration endpoint that returns sensitive server data
          without any authentication check. Your goal is to discover this endpoint and retrieve the sensitive information it
          exposes. In the fix phase, you will add proper authentication checks and remove sensitive data from the response
          entirely.
        </p>
        <div className="w-full max-w-4xl mx-auto rounded-lg overflow-hidden border-2 border-gray-700 border-dashed mb-6 min-h-[120px] flex items-center justify-center text-gray-500 text-sm">
          Tutorial video placeholder — content planned for a future phase
        </div>
        <button
          type="button"
          onClick={() => navigate('/challenges/6/attack')}
          className="w-full max-w-md bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg"
        >
          Go to Attack
        </button>
      </section>
    </div>
  );
};

export default SecurityMiscTutorialPage;
