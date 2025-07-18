"""
this file is a interface with abstract methods
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class FileService(ABC):
    @abstractmethod
    def list_dir(self, mode: str, rel_path: str = "") -> Dict[str, Any]:
        """列出目录内容"""
        pass

    @abstractmethod
    def download_file(self, mode: str, rel_path: str) -> Optional[str]:
        """下载文件，返回本地临时文件路径或绝对路径"""
        pass

    @abstractmethod
    def upload_file(self, mode: str, rel_path: str, file_obj) -> Dict[str, Any]:
        """上传文件，file_obj为文件对象"""
        pass

    @abstractmethod
    def delete_file(self, mode: str, rel_path: str) -> Dict[str, Any]:
        """删除文件"""
        pass

    @abstractmethod
    def get_default_dir(self, mode: str) -> Dict[str, Any]:
        """获取默认目录"""
        pass

    @abstractmethod
    def get_remote_servers(self) -> List[Dict[str, Any]]:
        """获取远程服务器列表"""
        pass

    @abstractmethod
    def test_server_connectivity(self, ssh_info: Dict[str, Any]) -> Dict[str, Any]:
        """测试远程服务器连通性"""
        pass

    @abstractmethod
    def save_server_pwd(self, server_name: str, user_pwd: str) -> Dict[str, Any]:
        """保存远程服务器密码"""
        pass