import json
import subprocess


STACKS = {
    "apex-pacs-orthanc-1": "8042",
    "apex-pacs-rebuild-orthanc-1": "8043",
}


def main():
    for container, port in STACKS.items():
        result = subprocess.run(
            [
                "docker", "--context", "desktop-linux", "inspect",
                "--format", "{{json .}}", container,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise SystemExit(f"FAIL: {container}: {result.stderr.strip()}")

        details = json.loads(result.stdout)
        if not details["State"]["Running"]:
            raise SystemExit(f"FAIL: {container} is stopped")

        expected = {"8042/tcp": [{"HostIp": "127.0.0.1", "HostPort": port}]}
        actual = details["HostConfig"]["PortBindings"]
        if actual != expected:
            raise SystemExit(
                f"FAIL: {container}: expected {expected}, got {actual}"
            )

        print(f"PASS: {container} publishes only 127.0.0.1:{port}")


if __name__ == "__main__":
    main()
