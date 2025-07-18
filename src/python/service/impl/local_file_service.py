import os
from typing import List, Dict, Any, Optional
from utils.log_util import default_logger as logger
from ..file_service import FileService
import json
import os
from pathlib import Path
from utils.constants import PROJECT_ROOT

class LocalFileService(FileService):
    def list_dir(self, mode: str, rel_path: str = "") -> Dict[str, Any]:
        logger.info(f"[LocalFileService] list_dir: mode={mode}, rel_path={rel_path}")
        abs_path = (
            os.path.abspath(rel_path)
            if os.path.isabs(rel_path)
            else os.path.abspath(os.path.join("/", rel_path))
        )
        if not os.path.exists(abs_path):
            return {"error": "路径不存在"}
        files = []
        dirs = []
        for entry in os.scandir(abs_path):
            entry_stat = entry.stat()
            if entry.is_dir():
                dirs.append(
                    {
                        "name": entry.name,
                        "type": "dir",
                        "size": entry_stat.st_size,
                        "mtime": entry_stat.st_mtime,
                    }
                )
            else:
                files.append(
                    {
                        "name": entry.name,
                        "type": "file",
                        "size": entry_stat.st_size,
                        "mtime": entry_stat.st_mtime,
                    }
                )
        return {"dirs": dirs, "files": files, "path": abs_path}

    def download_file(self, mode: str, rel_path: str) -> Optional[str]:
        logger.info(f"[LocalFileService] download_file: mode={mode}, rel_path={rel_path}")
        abs_path = (
            os.path.abspath(rel_path)
            if os.path.isabs(rel_path)
            else os.path.abspath(os.path.join("/", rel_path))
        )
        if not os.path.exists(abs_path):
            return None
        return abs_path

    def upload_file(self, mode: str, rel_path: str, file_obj) -> Dict[str, Any]:
        logger.info(f"[LocalFileService] upload_file: mode={mode}, rel_path={rel_path}")
        # rel_path is the directory path, we need to combine it with the filename
        directory_path = (
            os.path.abspath(rel_path)
            if os.path.isabs(rel_path)
            else os.path.abspath(os.path.join("/", rel_path))
        )
        
        # Get the filename from the file object
        filename = file_obj.filename
        if not filename:
            return {"success": False, "error": "文件名为空"}
        
        # Combine directory path with filename
        abs_path = os.path.join(directory_path, filename)
        
        try:
            # Create directory structure if it doesn't exist
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            file_obj.save(abs_path)
            return {"success": True, "path": abs_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_file(self, mode: str, rel_path: str) -> Dict[str, Any]:
        logger.info(f"[LocalFileService] delete_file: mode={mode}, rel_path={rel_path}")
        abs_path = (
            os.path.abspath(rel_path)
            if os.path.isabs(rel_path)
            else os.path.abspath(os.path.join("/", rel_path))
        )
        try:
            if os.path.isdir(abs_path):
                os.rmdir(abs_path)
            else:
                os.remove(abs_path)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_default_dir(self, mode: str) -> Dict[str, Any]:
        logger.info(f"[LocalFileService] get_default_dir: mode={mode}")
        # 读取配置文件中的默认目录
        config_path = PROJECT_ROOT / "config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # 获取配置值，默认为"~"
        default_dir = config.get("local_default_dir", "~")
        
        # 解析家目录符号
        resolved_dir = os.path.expanduser(default_dir)
        
        return {"default_dir": resolved_dir}

    def get_remote_servers(self) -> List[Dict[str, Any]]:
        logger.info("[LocalFileService] get_remote_servers called")
        return []

    def test_server_connectivity(self, ssh_info: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[LocalFileService] test_server_connectivity: ssh_info={ssh_info}")
        return {"success": False, "error": "本地模式不支持"}

    def save_server_pwd(self, server_name: str, user_pwd: str) -> Dict[str, Any]:
        logger.info(f"[LocalFileService] save_server_pwd: server_name={server_name}")
        return {"success": False, "error": "本地模式不支持"}