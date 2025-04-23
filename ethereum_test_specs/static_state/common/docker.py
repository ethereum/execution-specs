"""Manage lllc docker container."""

import subprocess
import threading

# Global variable to store the container id once instantiated.
container_id = None

# A global lock to control concurrent access.
container_lock = threading.Lock()


def get_lllc_container_id():
    """
    Return the container ID. If the container is not yet instantiated,
    it acquires the lock and runs the Docker command to instantiate the container.
    """
    global container_id
    # Acquire the lock so that only one thread can instantiate the container.
    with container_lock:
        if container_id is None:
            try:
                # Run the docker command using subprocess. The command is equivalent to:
                # docker run -d --entrypoint tail -v /tmp:/tests -w /tests lllc -f /dev/null
                result = subprocess.run(
                    [
                        "docker",
                        "run",
                        "-d",
                        "--entrypoint",
                        "tail",
                        "-v",
                        "/tmp:/tests",
                        "-w",
                        "/tests",
                        "lllc",
                        "-f",
                        "/dev/null",
                    ],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                # The container id is expected to be printed to stdout.
                container_id = result.stdout.strip()
                print(f"Container instantiated with id: {container_id}")
            except subprocess.CalledProcessError as e:
                # In case of error, print the error message and raise the exception.
                raise Exception("Error instantiating container:", e.stderr) from e
    return container_id


def stop_lllc_containers():
    """Stop all running Docker containers that were started from the 'lllc' image."""
    try:
        # Retrieve container IDs for all running containers with the image 'lllc'
        result = subprocess.check_output(
            ["docker", "ps", "-q", "--filter", "ancestor=lllc"], text=True
        )
        container_ids = result.strip().splitlines()

        if not container_ids:
            print("No running containers for image 'lllc' found.")
            return

        # Iterate over each container ID and stop it.
        for cid in container_ids:
            subprocess.run(["docker", "stop", cid], check=True)

    except subprocess.CalledProcessError as e:
        raise Exception("Error while stopping containers:", e.stderr) from e
