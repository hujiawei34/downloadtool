import os
import json
import stat
import tempfile
from typing import List, Dict, Any, Optional
import paramiko
from utils.constants import CONFIG_FILE
from utils.log_util import default_logger as logger
from ..file_service import FileService

class RemoteFileService(FileService):
    def list_dir(self, mode: str, rel_path: str = "") -> Dict[str, Any]:
        logger.info(f"[RemoteFileService] list_dir: mode={mode}, rel_path={rel_path}")
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            remote = config["remote_server_list"][0]
            ssh_info = remote["config"]
            host = ssh_info["host_ip"]
            port = ssh_info.get("ssh_port", 22)
            username = ssh_info["user_name"]
            password = ssh_info.get("user_pwd", "")
            default_dir = ssh_info.get("default_dir", "~")
            path = rel_path or default_dir

            if password:
                transport = paramiko.Transport((host, port))
                transport.connect(username=username, password=password)
                sftp = paramiko.SFTPClient.from_transport(transport)
            else:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    host,
                    port=port,
                    username=username,
                    allow_agent=True,
                    look_for_keys=True,
                )
                sftp = ssh.open_sftp()
            if path == "~" or path.startswith("~/"):
                home = sftp.normalize(".")
                if path == "~":
                    path = home
                else:
                    path = home + path[1:]
            if not path.startswith("/"):
                path = "/" + path
            files = []
            dirs = []
            for entry in sftp.listdir_attr(path):
                if stat.S_ISDIR(entry.st_mode):
                    dirs.append(
                        {
                            "name": entry.filename,
                            "type": "dir",
                            "size": entry.st_size,
                            "mtime": entry.st_mtime,
                        }
                    )
                else:
                    files.append(
                        {
                            "name": entry.filename,
                            "type": "file",
                            "size": entry.st_size,
                            "mtime": entry.st_mtime,
                        }
                    )
            sftp.close()
            if not password:
                ssh.close()
            else:
                transport.close()
            logger.info(f"[RemoteFileService] list_dir result: dirs={dirs}, files={files}, path={path}")
            return {"dirs": dirs, "files": files, "path": path}
        except Exception as e:
            logger.error(
                f"远程SFTP访问失败 host={host} user={username} path={path} error={e}"
            )
            return {"error": str(e)}

    def download_file(self, mode: str, rel_path: str) -> Optional[str]:
        logger.info(f"[RemoteFileService] download_file: mode={mode}, rel_path={rel_path}")
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            remote = config["remote_server_list"][0]
            ssh_info = remote["config"]
            host = ssh_info["host_ip"]
            port = ssh_info.get("ssh_port", 22)
            username = ssh_info["user_name"]
            password = ssh_info.get("user_pwd", "")
            path = rel_path

            if password:
                transport = paramiko.Transport((host, port))
                transport.connect(username=username, password=password)
                sftp = paramiko.SFTPClient.from_transport(transport)
            else:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    host,
                    port=port,
                    username=username,
                    allow_agent=True,
                    look_for_keys=True,
                )
                sftp = ssh.open_sftp()
            if path == "~" or path.startswith("~/"):
                home = sftp.normalize(".")
                if path == "~":
                    path = home
                else:
                    path = home + path[1:]
            if not path.startswith("/"):
                path = "/" + path
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            sftp.get(path, tmp_file.name)
            sftp.close()
            if not password:
                ssh.close()
            else:
                transport.close()
            logger.info(f"[RemoteFileService] download_file success: tmp_file={tmp_file.name}")
            return tmp_file.name
        except Exception as e:
            logger.error(
                f"远程SFTP下载失败 host={host} user={username} path={path} error={e}"
            )
            return None

    def upload_file(self, mode: str, rel_path: str, file_obj) -> Dict[str, Any]:
        logger.info(f"[RemoteFileService] upload_file: mode={mode}, rel_path={rel_path}")
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            remote = config["remote_server_list"][0]
            ssh_info = remote["config"]
            host = ssh_info["host_ip"]
            port = ssh_info.get("ssh_port", 22)
            username = ssh_info["user_name"]
            password = ssh_info.get("user_pwd", "")
            path = rel_path

            if password:
                transport = paramiko.Transport((host, port))
                transport.connect(username=username, password=password)
                sftp = paramiko.SFTPClient.from_transport(transport)
            else:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    host,
                    port=port,
                    username=username,
                    allow_agent=True,
                    look_for_keys=True,
                )
                sftp = ssh.open_sftp()
            if path == "~" or path.startswith("~/"):
                home = sftp.normalize(".")
                if path == "~":
                    path = home
                else:
                    path = home + path[1:]
            if not path.startswith("/"):
                path = "/" + path
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            file_obj.save(tmp_file.name)
            sftp.put(tmp_file.name, path)
            sftp.close()
            if not password:
                ssh.close()
            else:
                transport.close()
            logger.info(f"[RemoteFileService] upload_file success: path={path}")
            return {"success": True, "path": path}
        except Exception as e:
            logger.error(
                f"远程SFTP上传失败 host={host} user={username} path={rel_path} error={e}"
            )
            return {"success": False, "error": str(e)}

    def delete_file(self, mode: str, rel_path: str) -> Dict[str, Any]:
        logger.info(f"[RemoteFileService] delete_file: mode={mode}, rel_path={rel_path}")
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            remote = config["remote_server_list"][0]
            ssh_info = remote["config"]
            host = ssh_info["host_ip"]
            port = ssh_info.get("ssh_port", 22)
            username = ssh_info["user_name"]
            password = ssh_info.get("user_pwd", "")
            path = rel_path

            if password:
                transport = paramiko.Transport((host, port))
                transport.connect(username=username, password=password)
                sftp = paramiko.SFTPClient.from_transport(transport)
            else:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    host,
                    port=port,
                    username=username,
                    allow_agent=True,
                    look_for_keys=True,
                )
                sftp = ssh.open_sftp()
            if path == "~" or path.startswith("~/"):
                home = sftp.normalize(".")
                if path == "~":
                    path = home
                else:
                    path = home + path[1:]
            if not path.startswith("/"):
                path = "/" + path
            try:
                sftp.remove(path)
                result = {"success": True}
                logger.info(f"[RemoteFileService] delete_file success: path={path}")
            except Exception as e:
                result = {"success": False, "error": str(e)}
                logger.error(f"[RemoteFileService] delete_file failed: path={path}, error={e}")
            sftp.close()
            if not password:
                ssh.close()
            else:
                transport.close()
            return result
        except Exception as e:
            logger.error(
                f"远程SFTP删除失败 host={host} user={username} path={rel_path} error={e}"
            )
            return {"success": False, "error": str(e)}

    def get_default_dir(self, mode: str) -> Dict[str, Any]:
        logger.info(f"[RemoteFileService] get_default_dir: mode={mode}")
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            remote = config["remote_server_list"][0]
            ssh_info = remote["config"]
            default_dir = ssh_info.get("default_dir", "~")
            logger.info(f"[RemoteFileService] get_default_dir result: {default_dir}")
            return {"default_dir": default_dir}
        except Exception as e:
            logger.error(f"[RemoteFileService] get_default_dir failed: error={e}")
            return {"error": str(e)}

    def get_remote_servers(self) -> List[Dict[str, Any]]:
        logger.info("[RemoteFileService] get_remote_servers called")
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            result = config.get("remote_server_list", [])
            logger.info(f"[RemoteFileService] get_remote_servers result: {result}")
            return result
        except Exception as e:
            logger.error(f"读取远程服务器列表失败 error={e}")
            return []

    def test_server_connectivity(self, ssh_info: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[RemoteFileService] test_server_connectivity: ssh_info={ssh_info}")
        host = ssh_info.get("host_ip")
        port = ssh_info.get("ssh_port", 22)
        username = ssh_info.get("user_name")
        password = ssh_info.get("user_pwd", "")
        try:
            if password:
                transport = paramiko.Transport((host, port))
                transport.connect(username=username, password=password)
                transport.close()
            else:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    host,
                    port=port,
                    username=username,
                    allow_agent=True,
                    look_for_keys=True,
                )
                ssh.close()
            logger.info(f"[RemoteFileService] test_server_connectivity success: host={host}")
            return {"success": True}
        except Exception as e:
            logger.error(f"远程服务器连通性测试失败 host={host} user={username} error={e}")
            return {"success": False, "error": str(e)}

    def save_server_pwd(self, server_name: str, user_pwd: str) -> Dict[str, Any]:
        logger.info(f"[RemoteFileService] save_server_pwd: server_name={server_name}")
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            for remote in config.get("remote_server_list", []):
                if remote.get("name") == server_name:
                    remote["config"]["user_pwd"] = user_pwd
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.info(f"[RemoteFileService] save_server_pwd success: server_name={server_name}")
            return {"success": True}
        except Exception as e:
            logger.error(f"保存远程服务器密码失败 server={server_name} error={e}")
            return {"success": False, "error": str(e)}