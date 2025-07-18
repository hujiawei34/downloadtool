import pytest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from service.impl.local_file_service import LocalFileService

class TestLocalFileService:
    """Test LocalFileService functionality."""
    
    def test_list_dir_success(self, local_service, temp_dir, sample_files):
        """Test successful directory listing."""
        result = local_service.list_dir('local', temp_dir)
        
        assert 'dirs' in result
        assert 'files' in result
        assert 'path' in result
        assert result['path'] == temp_dir
        
        # Check if subdir is in dirs
        dir_names = [d['name'] for d in result['dirs']]
        assert 'subdir' in dir_names
        
        # Check if files are in files
        file_names = [f['name'] for f in result['files']]
        assert 'test.txt' in file_names
        assert 'image.png' in file_names
    
    def test_list_dir_nonexistent_path(self, local_service):
        """Test listing non-existent directory."""
        result = local_service.list_dir('local', '/nonexistent/path')
        
        assert 'error' in result
        assert result['error'] == '路径不存在'
    
    def test_list_dir_relative_path(self, local_service, temp_dir):
        """Test listing with relative path."""
        # Use relative path that doesn't exist (should return error)
        result = local_service.list_dir('local', 'test_relative')
        
        # Should return error for non-existent path
        assert 'error' in result
        assert '路径不存在' in result['error']
    
    def test_download_file_success(self, local_service, temp_dir, sample_files):
        """Test successful file download."""
        test_file = os.path.join(temp_dir, 'test.txt')
        
        result = local_service.download_file('local', test_file)
        
        assert result == test_file
        assert os.path.exists(result)
    
    def test_download_file_nonexistent(self, local_service):
        """Test download of non-existent file."""
        result = local_service.download_file('local', '/nonexistent/file.txt')
        
        assert result is None
    
    def test_download_file_relative_path(self, local_service):
        """Test download with relative path."""
        result = local_service.download_file('local', 'relative/path.txt')
        
        # Should return None for non-existent relative path
        assert result is None
    
    def test_upload_file_success(self, local_service, temp_dir, mock_file_obj):
        """Test successful file upload."""
        result = local_service.upload_file('local', temp_dir, mock_file_obj)
        
        assert result['success'] is True
        assert 'path' in result
        mock_file_obj.save.assert_called_once()
    
    def test_upload_file_no_filename(self, local_service, temp_dir):
        """Test upload with file object without filename."""
        mock_file_obj = MagicMock()
        mock_file_obj.filename = None
        
        result = local_service.upload_file('local', temp_dir, mock_file_obj)
        
        assert result['success'] is False
        assert result['error'] == '文件名为空'
    
    def test_upload_file_with_subdirectory(self, local_service, temp_dir):
        """Test upload with subdirectory in filename."""
        mock_file_obj = MagicMock()
        mock_file_obj.filename = 'subdir/test.txt'
        
        result = local_service.upload_file('local', temp_dir, mock_file_obj)
        
        assert result['success'] is True
        # Should create subdirectory
        expected_path = os.path.join(temp_dir, 'subdir', 'test.txt')
        assert result['path'] == expected_path
        mock_file_obj.save.assert_called_once_with(expected_path)
    
    def test_upload_file_save_error(self, local_service, temp_dir):
        """Test upload with save error."""
        mock_file_obj = MagicMock()
        mock_file_obj.filename = 'test.txt'
        mock_file_obj.save.side_effect = Exception('Permission denied')
        
        result = local_service.upload_file('local', temp_dir, mock_file_obj)
        
        assert result['success'] is False
        assert 'Permission denied' in result['error']
    
    def test_delete_file_success(self, local_service, temp_dir, sample_files):
        """Test successful file deletion."""
        test_file = os.path.join(temp_dir, 'test.txt')
        
        result = local_service.delete_file('local', test_file)
        
        assert result['success'] is True
        assert not os.path.exists(test_file)
    
    def test_delete_directory_success(self, local_service, temp_dir, sample_files):
        """Test successful directory deletion."""
        test_dir = os.path.join(temp_dir, 'empty_dir')
        os.makedirs(test_dir)
        
        result = local_service.delete_file('local', test_dir)
        
        assert result['success'] is True
        assert not os.path.exists(test_dir)
    
    def test_delete_nonexistent_file(self, local_service):
        """Test deletion of non-existent file."""
        result = local_service.delete_file('local', '/nonexistent/file.txt')
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_delete_non_empty_directory(self, local_service, temp_dir, sample_files):
        """Test deletion of non-empty directory."""
        test_dir = os.path.join(temp_dir, 'subdir')
        
        result = local_service.delete_file('local', test_dir)
        
        assert result['success'] is False
        assert 'error' in result
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"local_default_dir": "/custom/path"}')
    @patch('os.path.expanduser')
    def test_get_default_dir_custom(self, mock_expanduser, mock_file, local_service):
        """Test get default directory with custom path."""
        mock_expanduser.return_value = '/custom/path'
        
        result = local_service.get_default_dir('local')
        
        assert result['default_dir'] == '/custom/path'
        mock_expanduser.assert_called_once_with('/custom/path')
    
    @patch('builtins.open', new_callable=mock_open, read_data='{}')
    @patch('os.path.expanduser')
    def test_get_default_dir_default(self, mock_expanduser, mock_file, local_service):
        """Test get default directory with default path."""
        mock_expanduser.return_value = '/home/user'
        
        result = local_service.get_default_dir('local')
        
        assert result['default_dir'] == '/home/user'
        mock_expanduser.assert_called_once_with('~')
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"local_default_dir": "~/custom"}')
    @patch('os.path.expanduser')
    def test_get_default_dir_tilde_expansion(self, mock_expanduser, mock_file, local_service):
        """Test get default directory with tilde expansion."""
        mock_expanduser.return_value = '/home/user/custom'
        
        result = local_service.get_default_dir('local')
        
        assert result['default_dir'] == '/home/user/custom'
        mock_expanduser.assert_called_once_with('~/custom')
    
    def test_get_remote_servers(self, local_service):
        """Test get remote servers (should return empty list)."""
        result = local_service.get_remote_servers()
        
        assert result == []
    
    def test_test_server_connectivity(self, local_service):
        """Test server connectivity (should return not supported)."""
        result = local_service.test_server_connectivity({'host': 'test'})
        
        assert result['success'] is False
        assert result['error'] == '本地模式不支持'
    
    def test_save_server_pwd(self, local_service):
        """Test save server password (should return not supported)."""
        result = local_service.save_server_pwd('test_server', 'password')
        
        assert result['success'] is False
        assert result['error'] == '本地模式不支持'

class TestLocalFileServiceEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_list_dir_empty_directory(self, local_service, temp_dir):
        """Test listing empty directory."""
        empty_dir = os.path.join(temp_dir, 'empty')
        os.makedirs(empty_dir)
        
        result = local_service.list_dir('local', empty_dir)
        
        assert result['dirs'] == []
        assert result['files'] == []
        assert result['path'] == empty_dir
    
    def test_upload_file_absolute_path(self, local_service, mock_file_obj):
        """Test upload with absolute path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = local_service.upload_file('local', temp_dir, mock_file_obj)
            
            assert result['success'] is True
            expected_path = os.path.join(temp_dir, 'test.txt')
            assert result['path'] == expected_path
    
    def test_upload_file_relative_path(self, local_service, mock_file_obj, temp_dir):
        """Test upload with relative path."""
        # Use temp_dir as base to ensure the directory structure can be created
        relative_upload_dir = os.path.join(temp_dir, 'relative', 'path')
        result = local_service.upload_file('local', relative_upload_dir, mock_file_obj)
        
        assert result['success'] is True
        expected_path = os.path.join(relative_upload_dir, 'test.txt')
        assert result['path'] == expected_path
    
    def test_delete_file_permission_error(self, local_service, temp_dir):
        """Test delete file with permission error."""
        test_file = os.path.join(temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        
        with patch('os.remove', side_effect=PermissionError('Permission denied')):
            result = local_service.delete_file('local', test_file)
            
            assert result['success'] is False
            assert 'Permission denied' in result['error']