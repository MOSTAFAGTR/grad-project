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
        challenge_dir (str): The folder name (e.g., 'challenge-sql-injection').
    """
    run_id = str(uuid.uuid4())
    image_tag = f"scale-challenge-run-{run_id}"
    
    # We are inside the backend container at /app/app/
    # The challenge folders are mounted at /app/challenge-xxx
    base_path = pathlib.Path("/app").resolve()
    source_path = (base_path / challenge_dir).resolve()

    if not source_path.exists():
        return False, f"Configuration Error: Challenge directory not found at {source_path}"

    # Use a temporary directory that gets cleaned up automatically
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = pathlib.Path(temp_dir_str)
        print(f"[{run_id}] Created temporary directory: {temp_dir}")

        try:
            # 1. Copy the challenge files to the temp dir
            shutil.copytree(source_path, temp_dir, dirs_exist_ok=True)

            # 2. Overwrite app.py with the student's submitted code
            student_code_path = temp_dir / "app.py"
            student_code_path.write_text(student_code)
            
            # 3. Define the Dockerfile with WINDOWS FIX
            dockerfile_content = f"""
            FROM python:3.9-slim
            WORKDIR /app
            
            # Install dependencies
            COPY requirements.txt .
            RUN pip install --no-cache-dir -r requirements.txt
            
            # Copy challenge files
            COPY . .
            
            # --- CRITICAL FIX FOR WINDOWS USERS ---
            # Remove carriage returns (\\r) from the shell script before running it
            RUN sed -i 's/\\r$//' run_tests.sh
            
            # Run the tests
            CMD ["sh", "run_tests.sh"]
            """
            
            dockerfile_path = temp_dir / "Dockerfile"
            dockerfile_path.write_text(dockerfile_content)

            client = docker.from_env()
            print(f"[{run_id}] Building Docker image: {image_tag}...")
            
            # 4. Build the sandbox image
            client.images.build(path=str(temp_dir), tag=image_tag, rm=True)
            print(f"[{run_id}] Build complete.")

            print(f"[{run_id}] Running container...")
            
            # 5. Run the container
            # We connect to scale_net so it can talk to the database if needed
            logs = client.containers.run(
                image_tag,
                remove=True,
                network="scale_net" 
            )
            
            decoded_logs = logs.decode('utf-8')
            
            # 6. Check results
            # If the logs contain failure keywords, mark as failed
            if "FAILED" in decoded_logs or "Error" in decoded_logs or "Traceback" in decoded_logs:
                success = False
            else:
                success = True
            
            result = {"success": success, "logs": decoded_logs}

        except docker.errors.BuildError as e:
            # Capture build errors (like pip install failing)
            build_logs = "\n".join([line.get('stream', '').strip() for line in e.build_log])
            result = {"success": False, "logs": f"Build Error:\n{build_logs}"}
        except docker.errors.ContainerError as e:
            # Capture runtime errors
            result = {"success": False, "logs": f"Container Error:\n{e.stderr.decode('utf-8')}"}
        except Exception as e:
            result = {"success": False, "logs": f"An unexpected error occurred: {str(e)}"}
        finally:
            # Cleanup: Remove the image to save space
            if 'client' in locals() and client:
                try:
                    client.images.remove(image_tag, force=True)
                except:
                    pass

        return result['success'], result['logs']