import docker
import tempfile
import pathlib
import shutil
import uuid

# This path points to the challenge package inside the backend container's filesystem
CHALLENGE_BASE_PATH = pathlib.Path("./challenge-sql-injection").resolve()

def run_in_sandbox(student_code: str):
    run_id = str(uuid.uuid4())
    image_tag = f"scale-challenge-run-{run_id}"

    # Use a temporary directory that gets cleaned up automatically
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = pathlib.Path(temp_dir_str)
        print(f"[{run_id}] Created temporary directory: {temp_dir}")

        # Copy the entire challenge template into the temporary directory
        shutil.copytree(CHALLENGE_BASE_PATH, temp_dir, dirs_exist_ok=True)

        # Overwrite the template's app.py with the student's code
        student_code_path = temp_dir / "app.py"
        student_code_path.write_text(student_code)
        
        # Define the Dockerfile for building the isolated test environment
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

        client = None
        try:
            client = docker.from_env()
            print(f"[{run_id}] Building Docker image: {image_tag}...")
            
            # Build the sandbox image from the temporary directory
            client.images.build(path=str(temp_dir), tag=image_tag, rm=True)
            print(f"[{run_id}] Build complete.")

            print(f"[{run_id}] Running container on network 'scale_application_scale_net'...")
            
            # Run the container, connecting it to our shared network
            # This is what allows it to find the 'challenge_db_sqli' container by name
            logs = client.containers.run(
                image_tag,
                remove=True,
                network="scale_application_scale_net" # Project folder name + network name
            )
            print(f"[{run_id}] Container finished.")
            
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
            # Always try to clean up the Docker image
            if client:
                try:
                    client.images.remove(image_tag, force=True)
                    print(f"[{run_id}] Successfully removed image {image_tag}")
                except:
                    print(f"[{run_id}] Failed to remove image {image_tag}")
                    pass

        return result['success'], result['logs']