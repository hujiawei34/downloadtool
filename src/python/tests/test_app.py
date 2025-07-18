import pytest
import json
import os
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import FileStorage
import io

class TestAppRoutes:
    """Test Flask application routes."""
    
    def test_index_route(self, client):
        """Test the index route."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'<!DOCTYPE html>' in response.data
    
    def test_files_route(self, client):
        """Test the files route."""
        response = client.get('/files')
        assert response.status_code == 200
        assert b'<!DOCTYPE html>' in response.data

class TestAPIEndpoints:
    """Test API endpoints."""
    
    @patch('app.get_service')
    def test_api_list_local(self, mock_get_service, client):
        """Test /api/list endpoint for local mode."""
        mock_service = MagicMock()
        mock_service.list_dir.return_value = {
            'dirs': [{'name': 'testdir', 'type': 'dir', 'size': 4096, 'mtime': 1234567890}],
            'files': [{'name': 'test.txt', 'type': 'file', 'size': 100, 'mtime': 1234567890}],
            'path': '/test/path'
        }
        mock_get_service.return_value = mock_service
        
        response = client.get('/api/list?mode=local&path=/test/path')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'dirs' in data
        assert 'files' in data
        assert data['path'] == '/test/path'
        mock_service.list_dir.assert_called_once_with('local', '/test/path')
    
    @patch('app.get_service')
    def test_api_list_remote(self, mock_get_service, client):
        """Test /api/list endpoint for remote mode."""
        mock_service = MagicMock()
        mock_service.list_dir.return_value = {
            'dirs': [],
            'files': [],
            'path': '/remote/path'
        }
        mock_get_service.return_value = mock_service
        
        response = client.get('/api/list?mode=remote&path=/remote/path')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['path'] == '/remote/path'
        mock_service.list_dir.assert_called_once_with('remote', '/remote/path')
    
    @patch('app.get_service')
    def test_api_upload_success(self, mock_get_service, client):
        """Test successful file upload."""
        mock_service = MagicMock()
        mock_service.upload_file.return_value = {
            'success': True,
            'path': '/test/path/test.txt'
        }
        mock_get_service.return_value = mock_service
        
        # Create a test file
        file_data = b'test file content'
        file_obj = FileStorage(
            stream=io.BytesIO(file_data),
            filename='test.txt',
            content_type='text/plain'
        )
        
        response = client.post('/api/upload?mode=local&path=/test/path', 
                             data={'file': file_obj})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['path'] == '/test/path/test.txt'
    
    @patch('app.get_service')
    def test_api_upload_missing_file(self, mock_get_service, client):
        """Test upload with missing file."""
        response = client.post('/api/upload?mode=local&path=/test/path')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert '未选择文件' in data['error']
    
    @patch('app.get_service')
    def test_api_upload_missing_path(self, mock_get_service, client):
        """Test upload with missing path."""
        file_obj = FileStorage(
            stream=io.BytesIO(b'test'),
            filename='test.txt'
        )
        
        response = client.post('/api/upload?mode=local', 
                             data={'file': file_obj})
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert '路径参数缺失' in data['error']
    
    @patch('app.get_service')
    @patch('app.send_file')
    def test_api_download_success(self, mock_send_file, mock_get_service, client):
        """Test successful file download."""
        mock_service = MagicMock()
        mock_service.download_file.return_value = '/test/path/test.txt'
        mock_get_service.return_value = mock_service
        
        mock_send_file.return_value = 'file_content'
        
        with patch('os.path.exists', return_value=True):
            response = client.get('/api/download?mode=local&path=/test/path/test.txt')
            assert response.status_code == 200
            mock_service.download_file.assert_called_once_with('local', '/test/path/test.txt')
    
    @patch('app.get_service')
    def test_api_download_missing_path(self, mock_get_service, client):
        """Test download with missing path."""
        response = client.get('/api/download?mode=local')
        assert response.status_code == 400
        assert '路径参数缺失'.encode('utf-8') in response.data
    
    @patch('app.get_service')
    def test_api_download_file_not_found(self, mock_get_service, client):
        """Test download with non-existent file."""
        mock_service = MagicMock()
        mock_service.download_file.return_value = None
        mock_get_service.return_value = mock_service
        
        response = client.get('/api/download?mode=local&path=/nonexistent/file.txt')
        assert response.status_code == 404
        assert '文件不存在'.encode('utf-8') in response.data
    
    @patch('app.get_service')
    def test_api_delete_success(self, mock_get_service, client):
        """Test successful file deletion."""
        mock_service = MagicMock()
        mock_service.delete_file.return_value = {'success': True}
        mock_get_service.return_value = mock_service
        
        response = client.post('/api/delete?mode=local&path=/test/path/test.txt')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        mock_service.delete_file.assert_called_once_with('local', '/test/path/test.txt')
    
    @patch('app.get_service')
    def test_api_delete_missing_path(self, mock_get_service, client):
        """Test delete with missing path."""
        response = client.post('/api/delete?mode=local')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert '路径参数缺失' in data['error']
    
    @patch('app.get_service')
    def test_api_default_dir_local(self, mock_get_service, client):
        """Test get default directory for local mode."""
        mock_service = MagicMock()
        mock_service.get_default_dir.return_value = {'default_dir': '/home/user'}
        mock_get_service.return_value = mock_service
        
        response = client.get('/api/default_dir?mode=local')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['default_dir'] == '/home/user'
        mock_service.get_default_dir.assert_called_once_with('local')
    
    @patch('app.get_service')
    def test_api_default_dir_remote(self, mock_get_service, client):
        """Test get default directory for remote mode."""
        mock_service = MagicMock()
        mock_service.get_default_dir.return_value = {'default_dir': '~/remote'}
        mock_get_service.return_value = mock_service
        
        response = client.get('/api/default_dir?mode=remote')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['default_dir'] == '~/remote'
        mock_service.get_default_dir.assert_called_once_with('remote')
    
    @patch('app.remote_service')
    def test_api_remote_servers(self, mock_remote_service, client):
        """Test get remote servers list."""
        mock_remote_service.get_remote_servers.return_value = [
            {'server_name': 'test1', 'config': {'host_ip': '192.168.1.100'}},
            {'server_name': 'test2', 'config': {'host_ip': '192.168.1.200'}}
        ]
        
        response = client.get('/api/remote_servers')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'remote_server_list' in data
        assert len(data['remote_server_list']) == 2
        assert data['remote_server_list'][0]['server_name'] == 'test1'
    
    @patch('app.remote_service')
    def test_api_test_server_connectivity(self, mock_remote_service, client):
        """Test server connectivity check."""
        mock_remote_service.test_server_connectivity.return_value = {
            'success': True
        }
        
        ssh_info = {
            'host_ip': '192.168.1.100',
            'user_name': 'testuser',
            'user_pwd': 'testpass'
        }
        
        response = client.post('/api/test_server_connectivity',
                             json=ssh_info,
                             content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
    
    @patch('app.remote_service')
    def test_api_save_server_pwd(self, mock_remote_service, client):
        """Test save server password."""
        mock_remote_service.save_server_pwd.return_value = {
            'success': True
        }
        
        request_data = {
            'server_name': 'test_server',
            'user_pwd': 'new_password'
        }
        
        response = client.post('/api/save_server_pwd',
                             json=request_data,
                             content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        mock_remote_service.save_server_pwd.assert_called_once_with('test_server', 'new_password')

class TestErrorHandling:
    """Test error handling scenarios."""
    
    @patch('app.get_service')
    def test_api_list_with_error(self, mock_get_service, client):
        """Test API list endpoint with service error."""
        mock_service = MagicMock()
        mock_service.list_dir.return_value = {'error': 'Permission denied'}
        mock_get_service.return_value = mock_service
        
        response = client.get('/api/list?mode=local&path=/forbidden')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'Permission denied'
    
    @patch('app.get_service')
    def test_api_upload_with_error(self, mock_get_service, client):
        """Test API upload endpoint with service error."""
        mock_service = MagicMock()
        mock_service.upload_file.return_value = {
            'success': False,
            'error': 'Disk full'
        }
        mock_get_service.return_value = mock_service
        
        file_obj = FileStorage(
            stream=io.BytesIO(b'test'),
            filename='test.txt'
        )
        
        response = client.post('/api/upload?mode=local&path=/test/path',
                             data={'file': file_obj})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'Disk full'