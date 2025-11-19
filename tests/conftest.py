import pytest
import subprocess
import time
import os


@pytest.fixture(scope="session")
def flask_app():
    """Start Flask app before tests (minimal fixture).

    This fixture starts the Flask app as a subprocess for integration tests.
    It no longer depends on Playwright.
    """
    os.environ['FLASK_ENV'] = 'testing'
    process = subprocess.Popen(
        ['python', 'app.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(2)
    yield process
    process.terminate()
    process.wait()


@pytest.fixture(scope="session")
def base_url():
    return "http://127.0.0.1:5001"
