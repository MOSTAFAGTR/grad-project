import docker
import tempfile
import pathlib
import shutil
import uuid
import os
import traceback
import re
from requests.exceptions import ReadTimeout

ALLOWED_CHALLENGE_DIRS = {
    "challenge-sql-injection",
    "challenge-xss",
    "challenge-csrf",
    "challenge-command-injection",
    "challenge-redirect",
    "challenge-broken-auth",
    "challenge-security-misc",
    "challenge-directory-traversal",
    "challenge-xxe",
    "challenge-insecure-storage",
}
MAX_SUBMITTED_CODE_CHARS = int(os.getenv("SANDBOX_MAX_CODE_CHARS", "200000"))
SANDBOX_RUN_TIMEOUT = int(os.getenv("SANDBOX_RUN_TIMEOUT", "25"))


def run_in_sandbox(student_code: str, challenge_dir: str, event_logger=None):
    result = run_in_sandbox_detailed(student_code, challenge_dir, event_logger=event_logger)
    return bool(result.get("success")), str(result.get("logs") or "")


def _parse_test_summary(logs: str) -> dict:
    text = logs or ""
    failures = 0
    errors = 0
    tests_run = 0
    match_run = re.search(r"Ran\s+(\d+)\s+tests?", text)
    if match_run:
        tests_run = int(match_run.group(1))
    match_failed = re.search(r"FAILED\s+\(([^)]*)\)", text)
    if match_failed:
        details = match_failed.group(1)
        m_fail = re.search(r"failures=(\d+)", details)
        m_err = re.search(r"errors=(\d+)", details)
        failures = int(m_fail.group(1)) if m_fail else 0
        errors = int(m_err.group(1)) if m_err else 0
    return {
        "tests_run": tests_run,
        "failures": failures,
        "errors": errors,
    }


def run_in_sandbox_detailed(student_code: str, challenge_dir: str, event_logger=None):
    """
    Args:
        student_code (str): The code submitted by the student.
        challenge_dir (str): The folder name (e.g., 'challenge-sql-injection').
    """
    run_id = str(uuid.uuid4())
    image_tag = f"scale-challenge-run-{run_id}"

    if challenge_dir not in ALLOWED_CHALLENGE_DIRS:
        if event_logger:
            event_logger({"status": "invalid_challenge_dir", "challenge_dir": challenge_dir})
        return {"success": False, "logs": "Invalid challenge directory", "tests_run": 0, "failures": 0, "errors": 1}
    if not isinstance(student_code, str) or len(student_code) > MAX_SUBMITTED_CODE_CHARS:
        if event_logger:
            event_logger({"status": "submission_too_large", "challenge_dir": challenge_dir})
        return {"success": False, "logs": "Submission is too large", "tests_run": 0, "failures": 0, "errors": 1}
    
    base_path = pathlib.Path("/app/challenges").resolve()
    source_path = (base_path / challenge_dir).resolve()
    print(f"[{run_id}] Running sandbox at: {source_path}")

    if not source_path.exists():
        return {"success": False, "logs": f"Configuration Error: Challenge directory not found at {source_path}", "tests_run": 0, "failures": 0, "errors": 1}

    # Use a temporary directory that gets cleaned up automatically
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = pathlib.Path(temp_dir_str)
        print(f"[{run_id}] Created temporary directory: {temp_dir}")

        client = None
        container = None
        try:
            # 1. Copy the challenge files to the temp dir
            shutil.copytree(source_path, temp_dir, dirs_exist_ok=True)

            # 2. Overwrite app.py with the student's submitted code
            student_code_path = temp_dir / "app.py"
            student_code_path.write_text(student_code)
            
            # 3. Define the Dockerfile with WINDOWS FIX
            # Command-injection challenge needs 'ping' (not in python:3.9-slim)
            ping_install = ""
            if challenge_dir == "challenge-command-injection":
                ping_install = "RUN apt-get update && apt-get install -y --no-install-recommends iputils-ping && rm -rf /var/lib/apt/lists/*\n            "

            dockerfile_content = f"""
            FROM python:3.9-slim
            WORKDIR /app
            RUN apt-get update && apt-get install -y --no-install-recommends bash && rm -rf /var/lib/apt/lists/*

            {ping_install}
            # Install dependencies
            COPY requirements.txt .
            RUN pip install --no-cache-dir -r requirements.txt

            # Copy challenge files
            COPY . .

            # --- CRITICAL FIX FOR WINDOWS USERS ---
            RUN sed -i 's/\\r$//' run_tests.sh

            # Run the tests
            CMD ["bash", "run_tests.sh"]
            """
            
            dockerfile_path = temp_dir / "Dockerfile"
            dockerfile_path.write_text(dockerfile_content)

            client = docker.from_env()
            print(f"[{run_id}] Building Docker image: {image_tag}...")
            
            # 4. Build the sandbox image
            client.images.build(path=str(temp_dir), tag=image_tag, rm=True)
            print(f"[{run_id}] Build complete.")

            print(f"[{run_id}] Running container...")

            # 5. Create and run the container, then wait with timeout.
            # NOTE: docker.sock access is powerful. Keep this sandbox constrained.
            container = client.containers.run(
                image_tag,
                detach=True,
                remove=False,
                network="scale_net",
                mem_limit="256m",
                cpu_quota=50000,  # ~0.5 CPU
                pids_limit=128,
                environment={"PYTHONDONTWRITEBYTECODE": "1"},
            )

            timed_out = False
            exit_code = 1
            try:
                wait_result = container.wait(timeout=SANDBOX_RUN_TIMEOUT)
                exit_code = int(wait_result.get("StatusCode", 1))
            except ReadTimeout:
                timed_out = True
                try:
                    container.kill()
                except Exception:
                    pass

            decoded_logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="ignore")
            if timed_out:
                decoded_logs = (
                    f"Execution timed out after {SANDBOX_RUN_TIMEOUT}s.\n"
                    + decoded_logs
                )
                summary = _parse_test_summary(decoded_logs)
                result = {"success": False, "logs": decoded_logs, **summary}
            else:
                summary = _parse_test_summary(decoded_logs)
                success = exit_code == 0 and summary["failures"] == 0 and summary["errors"] == 0
                result = {"success": success, "logs": decoded_logs, **summary}

        except docker.errors.BuildError as e:
            # Capture build errors (like pip install failing)
            build_logs = "\n".join([line.get('stream', '').strip() for line in e.build_log])
            result = {"success": False, "logs": f"Build Error:\n{build_logs}", "tests_run": 0, "failures": 0, "errors": 1}
        except docker.errors.ContainerError as e:
            # Capture runtime errors
            stderr = (e.stderr or b"").decode("utf-8", errors="ignore")
            stdout = (e.stdout or b"").decode("utf-8", errors="ignore")
            result = {"success": False, "logs": f"Container Error:\n{stdout}\n{stderr}".strip(), "tests_run": 0, "failures": 0, "errors": 1}
        except docker.errors.APIError as e:
            result = {"success": False, "logs": f"Docker API Error: {e.explanation or str(e)}", "tests_run": 0, "failures": 0, "errors": 1}
        except Exception as e:
            result = {
                "success": False,
                "logs": f"Sandbox Unexpected Error: {str(e)}\n{traceback.format_exc()}",
                "tests_run": 0,
                "failures": 0,
                "errors": 1,
            }
        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
            # Cleanup: Remove the image to save space
            if client:
                try:
                    client.images.remove(image_tag, force=True)
                except Exception:
                    pass

        if event_logger:
            event_logger(
                {
                    "status": "completed",
                    "challenge_dir": challenge_dir,
                    "success": bool(result.get("success")),
                    "logs_preview": (result.get("logs") or "")[:500],
                }
            )
        return result