import os
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

            # Determine network to use
            env_net = os.environ.get("SANDBOX_NETWORK")
            available_network = None

            if env_net:
                # If user supplied a network via env var, prefer it (but verify it exists)
                try:
                    nets = client.networks.list(names=[env_net])
                    if nets:
                        available_network = env_net
                    else:
                        print(f"[{run_id}] SANDBOX_NETWORK '{env_net}' not found; will probe other networks.")
                except Exception as e:
                    print(f"[{run_id}] Error while checking SANDBOX_NETWORK '{env_net}': {e}")

            if not available_network:
                # Common candidate names (project-based or explicit)
                candidate_networks = [
                    "grad-project_scale_net",
                    "scale_application_scale_net",
                    "scale_net",
                ]
                try:
                    networks = client.networks.list()
                    existing_names = {n.name for n in networks}
                    # pick first exact candidate match
                    for cand in candidate_networks:
                        if cand in existing_names:
                            available_network = cand
                            break
                    # if none matched, pick any network that contains 'scale_net' as fallback
                    if not available_network:
                        for name in existing_names:
                            if "scale_net" in name or name.endswith("scale_net"):
                                available_network = name
                                break
                except Exception as e:
                    print(f"[{run_id}] Failed to list docker networks: {e}")
                    available_network = None

            # Run the container, connecting it to the selected network if available
            if available_network:
                print(f"[{run_id}] Running container on network '{available_network}'...")
                logs = client.containers.run(
                    image_tag,
                    remove=True,
                    network=available_network
                )
            else:
                print(f"[{run_id}] No suitable network found; running container without specifying a network.")
                logs = client.containers.run(
                    image_tag,
                    remove=True
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
                except Exception:
                    print(f"[{run_id}] Failed to remove image {image_tag}")
                    pass

        return result['success'], result['logs']