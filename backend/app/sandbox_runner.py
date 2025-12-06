import os
import docker
import tempfile
import pathlib
import shutil
import uuid
import os

def run_in_sandbox(student_code: str, challenge_dir: str):
    """
    Args:
        student_code (str): The code submitted by the student.
        challenge_dir (str): The folder name (e.g., 'challenge-sql-injection' or 'challenge-xss').
    """
    run_id = str(uuid.uuid4())
    image_tag = f"scale-challenge-run-{run_id}"
    
    # Resolve the path dynamically based on the directory passed
    # We assume the runner is in /app/app/, so we go up to /app/ then into the challenge dir
    base_path = pathlib.Path("/app").resolve()
    source_path = (base_path / challenge_dir).resolve()

    if not source_path.exists():
        return False, f"Configuration Error: Challenge directory not found at {source_path}"

    # Use a temporary directory that gets cleaned up automatically
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = pathlib.Path(temp_dir_str)
        print(f"[{run_id}] Created temporary directory: {temp_dir}")

        try:
            # Copy the entire challenge template into the temporary directory
            shutil.copytree(source_path, temp_dir, dirs_exist_ok=True)

            # Overwrite the template's app.py with the student's code
            student_code_path = temp_dir / "app.py"
            student_code_path.write_text(student_code)
            
            # Define the Dockerfile
            dockerfile_content = f"""
            FROM python:3.11-slim
            WORKDIR /app
            COPY requirements.txt .
            RUN pip install --no-cache-dir -r requirements.txt
            COPY . .
            CMD ["sh", "run_tests.sh"]
            """
            dockerfile_path = temp_dir / "Dockerfile"
            dockerfile_path.write_text(dockerfile_content)

            client = docker.from_env()
            print(f"[{run_id}] Building Docker image: {image_tag}...")
            
            # Build the sandbox image
            client.images.build(path=str(temp_dir), tag=image_tag, rm=True)
            print(f"[{run_id}] Build complete.")

            print(f"[{run_id}] Running container...")
            
            # Run the container
            # Note: We try to attach to the network, but if the network name differs 
            # (e.g. different folder name on host), we might need to adjust 'scale_application_scale_net'.
            # For XSS, the network isn't strictly required as it doesn't use an external DB, 
            # but we keep it for consistency.
            logs = client.containers.run(
                image_tag,
                remove=True,
                network="scale_application_scale_net" 
            )
            
            decoded_logs = logs.decode('utf-8')
            
            # Check the test output for failure keywords
            if "FAILED" in decoded_logs or "ERROR" in decoded_logs:
                success = False
            else:
                success = True
            
            result = {"success": success, "logs": decoded_logs}

        except docker.errors.BuildError as e:
            build_logs = "\n".join([line.get('stream', '').strip() for line in e.build_log])
            result = {"success": False, "logs": f"Build Error:\n{build_logs}"}
        except docker.errors.ContainerError as e:
            result = {"success": False, "logs": f"Container Error:\n{e.stderr.decode('utf-8')}"}
        except Exception as e:
            result = {"success": False, "logs": f"An unexpected error occurred: {str(e)}"}
        finally:
            # Cleanup image
            if 'client' in locals() and client:
                try:
                    client.images.remove(image_tag, force=True)
                except:
                    pass

        return result['success'], result['logs']