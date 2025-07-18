import pytest
import json
import tempfile
from unittest.mock import patch, MagicMock, mock_open

from service.impl.remote_file_service import RemoteFileService

class TestRemoteFileService:
    """Test RemoteFileService functionality."""
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_list_dir_success_with_password(self, mock_json_load, mock_file, remote_service, mock_config):
        """Test successful directory listing with password authentication."""
        mock_json_load.return_value = mock_config
        
        # Mock paramiko components
        mock_transport = MagicMock()
        mock_sftp = MagicMock()
        mock_sftp.listdir_attr.return_value = [
            MagicMock(filename='test.txt', st_mode=33188, st_size=100, st_mtime=1234567890),
            MagicMock(filename='testdir', st_mode=16877, st_size=4096, st_mtime=1234567890)
        ]
        mock_sftp.normalize.return_value = '/home/testuser'
        
        with patch('paramiko.Transport', return_value=mock_transport), \
             patch('paramiko.SFTPClient.from_transport', return_value=mock_sftp), \
             patch('stat.S_ISDIR', side_effect=lambda x: x == 16877):
            
            result = remote_service.list_dir('remote', '/test/path')
            
            assert 'dirs' in result
            assert 'files' in result
            assert 'path' in result
            assert len(result['dirs']) == 1
            assert len(result['files']) == 1
            assert result['dirs'][0]['name'] == 'testdir'
            assert result['files'][0]['name'] == 'test.txt'
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_list_dir_success_with_ssh_key(self, mock_json_load, mock_file, remote_service, mock_config):
        """Test successful directory listing with SSH key authentication."""
        # Remove password to use SSH key
        mock_config['remote_server_list'][0]['config']['user_pwd'] = ''
        mock_json_load.return_value = mock_config
        
        mock_ssh = MagicMock()
        mock_sftp = MagicMock()
        mock_sftp.listdir_attr.return_value = []
        mock_sftp.normalize.return_value = '/home/testuser'
        
        with patch('paramiko.SSHClient', return_value=mock_ssh), \
             patch.object(mock_ssh, 'open_sftp', return_value=mock_sftp):
            
            result = remote_service.list_dir('remote', '/test/path')
            
            assert 'dirs' in result
            assert 'files' in result
            mock_ssh.connect.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_list_dir_tilde_path(self, mock_json_load, mock_file, remote_service, mock_config):
        """Test directory listing with tilde path."""
        mock_json_load.return_value = mock_config
        
        mock_transport = MagicMock()
        mock_sftp = MagicMock()
        mock_sftp.listdir_attr.return_value = []
        mock_sftp.normalize.return_value = '/home/testuser'
        
        with patch('paramiko.Transport', return_value=mock_transport), \
             patch('paramiko.SFTPClient.from_transport', return_value=mock_sftp):
            
            result = remote_service.list_dir('remote', '~/test')
            
            assert 'path' in result
            # Should expand ~ to home directory
            mock_sftp.listdir_attr.assert_called_once_with('/home/testuser/test')
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_list_dir_connection_error(self, mock_json_load, mock_file, remote_service, mock_config):
        """Test directory listing with connection error."""
        mock_json_load.return_value = mock_config
        
        with patch('paramiko.Transport', side_effect=Exception('Connection failed')):
            result = remote_service.list_dir('remote', '/test/path')
            
            assert 'error' in result
            assert 'Connection failed' in result['error']
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_download_file_success(self, mock_json_load, mock_file, remote_service, mock_config):
        """Test successful file download."""
        mock_json_load.return_value = mock_config
        
        mock_transport = MagicMock()
        mock_sftp = MagicMock()
        mock_sftp.normalize.return_value = '/home/testuser'
        
        with patch('paramiko.Transport', return_value=mock_transport), \
             patch('paramiko.SFTPClient.from_transport', return_value=mock_sftp), \
             patch('tempfile.NamedTemporaryFile') as mock_temp:
            
            mock_temp_file = MagicMock()
            mock_temp_file.name = '/tmp/test_file'
            mock_temp.return_value = mock_temp_file
            
            result = remote_service.download_file('remote', '/test/path/file.txt')
            
            assert result == '/tmp/test_file'
            mock_sftp.get.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_download_file_error(self, mock_json_load, mock_file, remote_service, mock_config):
        """Test file download with error."""
        mock_json_load.return_value = mock_config
        
        with patch('paramiko.Transport', side_effect=Exception('Download failed')):
            result = remote_service.download_file('remote', '/test/path/file.txt')
            
            assert result is None
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_upload_file_success(self, mock_json_load, mock_file, remote_service, mock_config, mock_file_obj):
        """Test successful file upload."""
        mock_json_load.return_value = mock_config
        
        mock_transport = MagicMock()
        mock_sftp = MagicMock()
        mock_sftp.normalize.return_value = '/home/testuser'
        mock_sftp.stat.side_effect = Exception('Directory not found')  # To test directory creation
        
        with patch('paramiko.Transport', return_value=mock_transport), \
             patch('paramiko.SFTPClient.from_transport', return_value=mock_sftp), \
             patch('tempfile.NamedTemporaryFile') as mock_temp:
            
            mock_temp_file = MagicMock()
            mock_temp_file.name = '/tmp/test_file'
            mock_temp.return_value = mock_temp_file
            
            result = remote_service.upload_file('remote', '/test/path', mock_file_obj)
            
            assert result['success'] is True
            assert 'path' in result
            mock_sftp.put.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_upload_file_no_filename(self, mock_json_load, mock_file, remote_service, mock_config):
        """Test upload with file object without filename."""
        mock_json_load.return_value = mock_config
        
        mock_file_obj = MagicMock()
        mock_file_obj.filename = None
        
        result = remote_service.upload_file('remote', '/test/path', mock_file_obj)
        
        assert result['success'] is False
        assert result['error'] == '文件名为空'
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_upload_file_with_subdirectory(self, mock_json_load, mock_file, remote_service, mock_config):
        """Test upload with subdirectory in filename."""
        mock_json_load.return_value = mock_config
        
        mock_file_obj = MagicMock()
        mock_file_obj.filename = 'subdir/test.txt'
        
        mock_transport = MagicMock()
        mock_sftp = MagicMock()
        mock_sftp.normalize.return_value = '/home/testuser'
        mock_sftp.stat.side_effect = Exception('Directory not found')  # To test directory creation
        
        with patch('paramiko.Transport', return_value=mock_transport), \
             patch('paramiko.SFTPClient.from_transport', return_value=mock_sftp), \
             patch('tempfile.NamedTemporaryFile') as mock_temp:
            
            mock_temp_file = MagicMock()
            mock_temp_file.name = '/tmp/test_file'
            mock_temp.return_value = mock_temp_file
            
            result = remote_service.upload_file('remote', '/test/path', mock_file_obj)
            
            assert result['success'] is True
            # Should create subdirectory
            mock_sftp.mkdir.assert_called()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_upload_file_connection_error(self, mock_json_load, mock_file, remote_service, mock_config, mock_file_obj):
        """Test upload with connection error."""
        mock_json_load.return_value = mock_config
        
        with patch('paramiko.Transport', side_effect=Exception('Connection failed')):
            result = remote_service.upload_file('remote', '/test/path', mock_file_obj)
            
            assert result['success'] is False
            assert 'Connection failed' in result['error']
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_delete_file_success(self, mock_json_load, mock_file, remote_service, mock_config):
        """Test successful file deletion."""
        mock_json_load.return_value = mock_config
        
        mock_transport = MagicMock()
        mock_sftp = MagicMock()
        mock_sftp.normalize.return_value = '/home/testuser'
        
        with patch('paramiko.Transport', return_value=mock_transport), \
             patch('paramiko.SFTPClient.from_transport', return_value=mock_sftp):
            
            result = remote_service.delete_file('remote', '/test/path/file.txt')
            
            assert result['success'] is True
            mock_sftp.remove.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_delete_file_error(self, mock_json_load, mock_file, remote_service, mock_config):
        """Test file deletion with error."""
        mock_json_load.return_value = mock_config
        
        mock_transport = MagicMock()
        mock_sftp = MagicMock()
        mock_sftp.normalize.return_value = '/home/testuser'
        mock_sftp.remove.side_effect = Exception('Delete failed')
        
        with patch('paramiko.Transport', return_value=mock_transport), \
             patch('paramiko.SFTPClient.from_transport', return_value=mock_sftp):
            
            result = remote_service.delete_file('remote', '/test/path/file.txt')
            
            assert result['success'] is False
            assert 'Delete failed' in result['error']
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_delete_file_connection_error(self, mock_json_load, mock_file, remote_service, mock_config):
        """Test file deletion with connection error."""
        mock_json_load.return_value = mock_config
        
        with patch('paramiko.Transport', side_effect=Exception('Connection failed')):
            result = remote_service.delete_file('remote', '/test/path/file.txt')
            
            assert result['success'] is False
            assert 'Connection failed' in result['error']
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_get_default_dir_success(self, mock_json_load, mock_file, remote_service, mock_config):
        """Test get default directory success."""
        mock_json_load.return_value = mock_config
        
        result = remote_service.get_default_dir('remote')
        
        assert result['default_dir'] == '~/test'
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_get_default_dir_no_config(self, mock_json_load, mock_file, remote_service):
        """Test get default directory with missing config."""
        mock_json_load.return_value = {'remote_server_list': [{'config': {}}]}
        
        result = remote_service.get_default_dir('remote')
        
        assert result['default_dir'] == '~'
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_get_default_dir_error(self, mock_json_load, mock_file, remote_service):
        """Test get default directory with error."""
        mock_json_load.side_effect = Exception('Config error')
        
        result = remote_service.get_default_dir('remote')
        
        assert 'error' in result
        assert 'Config error' in result['error']
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_get_remote_servers_success(self, mock_json_load, mock_file, remote_service, mock_config):
        """Test get remote servers success."""
        mock_json_load.return_value = mock_config
        
        result = remote_service.get_remote_servers()
        
        assert len(result) == 1
        assert result[0]['server_name'] == 'test_server'
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_get_remote_servers_error(self, mock_json_load, mock_file, remote_service):
        """Test get remote servers with error."""
        mock_json_load.side_effect = Exception('Config error')
        
        result = remote_service.get_remote_servers()
        
        assert result == []
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_test_server_connectivity_success(self, mock_json_load, mock_file, remote_service, mock_config):
        """Test server connectivity success."""
        mock_json_load.return_value = mock_config
        
        ssh_info = {
            'host_ip': '192.168.1.100',
            'user_name': 'testuser',
            'user_pwd': 'testpass'
        }
        
        mock_transport = MagicMock()
        
        with patch('paramiko.Transport', return_value=mock_transport):
            result = remote_service.test_server_connectivity(ssh_info)
            
            assert result['success'] is True
            mock_transport.connect.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_test_server_connectivity_ssh_key(self, mock_json_load, mock_file, remote_service, mock_config):
        """Test server connectivity with SSH key."""
        mock_json_load.return_value = mock_config
        
        ssh_info = {
            'host_ip': '192.168.1.100',
            'user_name': 'testuser',
            'user_pwd': ''  # No password, use SSH key
        }
        
        mock_ssh = MagicMock()
        
        with patch('paramiko.SSHClient', return_value=mock_ssh):
            result = remote_service.test_server_connectivity(ssh_info)
            
            assert result['success'] is True
            mock_ssh.connect.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_test_server_connectivity_error(self, mock_json_load, mock_file, remote_service, mock_config):
        """Test server connectivity with error."""
        mock_json_load.return_value = mock_config
        
        ssh_info = {
            'host_ip': '192.168.1.100',
            'user_name': 'testuser',
            'user_pwd': 'testpass'
        }
        
        with patch('paramiko.Transport', side_effect=Exception('Connection failed')):
            result = remote_service.test_server_connectivity(ssh_info)
            
            assert result['success'] is False
            assert 'Connection failed' in result['error']
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('json.dump')
    def test_save_server_pwd_success(self, mock_json_dump, mock_json_load, mock_file, remote_service, mock_config):
        """Test save server password success."""
        mock_json_load.return_value = mock_config
        
        result = remote_service.save_server_pwd('test_server', 'new_password')
        
        assert result['success'] is True
        mock_json_dump.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_save_server_pwd_error(self, mock_json_load, mock_file, remote_service):
        """Test save server password with error."""
        mock_json_load.side_effect = Exception('Config error')
        
        result = remote_service.save_server_pwd('test_server', 'new_password')
        
        assert result['success'] is False
        assert 'Config error' in result['error']

class TestRemoteFileServiceDirectoryCreation:
    """Test directory creation logic in remote file service."""
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_upload_file_directory_creation_nested(self, mock_json_load, mock_file, remote_service, mock_config):
        """Test upload with nested directory creation."""
        mock_json_load.return_value = mock_config
        
        mock_file_obj = MagicMock()
        mock_file_obj.filename = 'level1/level2/test.txt'
        
        mock_transport = MagicMock()
        mock_sftp = MagicMock()
        mock_sftp.normalize.return_value = '/home/testuser'
        
        # Mock stat to simulate directories don't exist
        mock_sftp.stat.side_effect = Exception('Directory not found')
        
        with patch('paramiko.Transport', return_value=mock_transport), \
             patch('paramiko.SFTPClient.from_transport', return_value=mock_sftp), \
             patch('tempfile.NamedTemporaryFile') as mock_temp:
            
            mock_temp_file = MagicMock()
            mock_temp_file.name = '/tmp/test_file'
            mock_temp.return_value = mock_temp_file
            
            result = remote_service.upload_file('remote', '/test/path', mock_file_obj)
            
            assert result['success'] is True
            # Should attempt to create directories
            assert mock_sftp.mkdir.call_count >= 1
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_upload_file_directory_exists(self, mock_json_load, mock_file, remote_service, mock_config):
        """Test upload when directory already exists."""
        mock_json_load.return_value = mock_config
        
        mock_file_obj = MagicMock()
        mock_file_obj.filename = 'existing_dir/test.txt'
        
        mock_transport = MagicMock()
        mock_sftp = MagicMock()
        mock_sftp.normalize.return_value = '/home/testuser'
        
        # Mock stat to simulate directory exists
        mock_sftp.stat.return_value = MagicMock()
        
        with patch('paramiko.Transport', return_value=mock_transport), \
             patch('paramiko.SFTPClient.from_transport', return_value=mock_sftp), \
             patch('tempfile.NamedTemporaryFile') as mock_temp:
            
            mock_temp_file = MagicMock()
            mock_temp_file.name = '/tmp/test_file'
            mock_temp.return_value = mock_temp_file
            
            result = remote_service.upload_file('remote', '/test/path', mock_file_obj)
            
            assert result['success'] is True
            # Should not attempt to create directory
            mock_sftp.mkdir.assert_not_called()