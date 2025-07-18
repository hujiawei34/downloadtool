import pytest
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app
from service.impl.local_file_service import LocalFileService
from service.impl.remote_file_service import RemoteFileService

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_files(temp_dir):
    """Create sample files for testing."""
    files = {
        'test.txt': 'Hello World',
        'subdir/nested.txt': 'Nested content',
        'image.png': b'fake image data'
    }
    
    for file_path, content in files.items():
        full_path = os.path.join(temp_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        mode = 'wb' if isinstance(content, bytes) else 'w'
        with open(full_path, mode) as f:
            f.write(content)
    
    return files

@pytest.fixture
def local_service():
    """Create a LocalFileService instance."""
    return LocalFileService()

@pytest.fixture
def remote_service():
    """Create a RemoteFileService instance."""
    return RemoteFileService()

@pytest.fixture
def mock_config():
    """Mock configuration data."""
    return {
        "local_default_dir": "/tmp/test",
        "remote_server_list": [
            {
                "server_name": "test_server",
                "config": {
                    "host_ip": "192.168.1.100",
                    "user_name": "testuser",
                    "user_pwd": "testpass",
                    "ssh_port": 22,
                    "default_dir": "~/test"
                }
            }
        ]
    }

@pytest.fixture
def mock_sftp():
    """Mock SFTP client."""
    sftp = MagicMock()
    sftp.listdir_attr.return_value = []
    sftp.stat.side_effect = Exception("File not found")
    sftp.normalize.return_value = "/home/testuser"
    return sftp

@pytest.fixture
def mock_file_obj():
    """Mock file object for upload tests."""
    file_obj = MagicMock()
    file_obj.filename = "test.txt"
    file_obj.save = MagicMock()
    return file_obj