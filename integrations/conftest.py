import base64
import os

import pytest

docker = pytest.importorskip("docker")


@pytest.fixture(scope="session")
def tclsh(request):
    try:
        client = docker.from_env()
        image, _ = client.images.build(path=os.path.dirname(os.path.abspath(__file__)), rm=True)
    except Exception as e:
        pytest.skip(f"Docker not available: {e}")

    def run(code: str) -> str:
        script = f"puts -nonewline [eval {{{code}}}]"
        b64 = base64.b64encode(script.encode()).decode()
        output = client.containers.run(
            image,
            command=["sh", "-c", f"echo {b64} | base64 -d | tclsh"],
            remove=True,
        )
        return output.decode()

    return run
