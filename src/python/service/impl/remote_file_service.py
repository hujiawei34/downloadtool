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
    def __init__(self):
        self.current_server = None  # Track the currently connected server
    def list_dir(self, mode: str, rel_path: str = "") -> Dict[str, Any]:
        logger.info(f"[RemoteFileService] list_dir: mode={mode}, rel_path={rel_path}")
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # Use the current server if available, otherwise use the first one
            if self.current_server:
                remote = self.current_server
                logger.info(f"[RemoteFileService] Using current server: {remote.get('server_name')}")
            else:
                remote = config["remote_server_list"][0]
                logger.info(f"[RemoteFileService] Using first server: {remote.get('server_name')}")
            
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
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(host, port=port, username=username, password=password)
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
            
            total_size = 0
            file_count = 0
            
            for entry in sftp.listdir_attr(path):
                if stat.S_ISDIR(entry.st_mode):
                    dirs.append(
                        {
                            "name": entry.filename,
                            "type": "dir",
                            "size": None,  # 不计算目录大小，显示为未知
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
                    total_size += entry.st_size
                    file_count += 1
                    
            # 只统计当前目录中的文件大小总和，不包含子目录
            current_dir_info = {
                "total_size": total_size,
                "file_count": file_count,
                "is_complete": False  # 标记未完全计算
            }
            
            sftp.close()
            ssh.close()
            if password:
                transport.close()
            
            logger.info(f"[RemoteFileService] list_dir result: dirs={dirs}, files={files}, path={path}")
            return {"dirs": dirs, "files": files, "path": path, "dir_info": current_dir_info}
        except Exception as e:
            logger.error(
                f"远程SFTP访问失败 host={host} user={username} path={path} error={e}"
            )
            return {"error": str(e)}
    
    def _get_remote_dir_size(self, ssh, dir_path: str) -> int:
        """计算远程目录大小"""
        try:
            # 使用du命令计算目录大小
            du_command = f'du -sb "{dir_path}" 2>/dev/null || echo 0'
            stdin, stdout, stderr = ssh.exec_command(du_command)
            du_output = stdout.read().decode('utf-8').strip()
            if du_output and du_output != "0":
                size_parts = du_output.split()
                if size_parts:
                    return int(size_parts[0])
            return 0
        except Exception as e:
            logger.error(f"计算远程目录大小失败: {str(e)}")
            return 0

    def download_file(self, mode: str, rel_path: str) -> Optional[str]:
        logger.info(f"[RemoteFileService] download_file: mode={mode}, rel_path={rel_path}")
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # Use the current server if available, otherwise use the first one
            if self.current_server:
                remote = self.current_server
                logger.info(f"[RemoteFileService] download_file using current server: {remote.get('server_name')}")
            else:
                remote = config["remote_server_list"][0]
                logger.info(f"[RemoteFileService] download_file using first server: {remote.get('server_name')}")
            
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
            
            # Use the current server if available, otherwise use the first one
            if self.current_server:
                remote = self.current_server
                logger.info(f"[RemoteFileService] upload_file using current server: {remote.get('server_name')}")
            else:
                remote = config["remote_server_list"][0]
                logger.info(f"[RemoteFileService] upload_file using first server: {remote.get('server_name')}")
            
            ssh_info = remote["config"]
            host = ssh_info["host_ip"]
            port = ssh_info.get("ssh_port", 22)
            username = ssh_info["user_name"]
            password = ssh_info.get("user_pwd", "")
            
            # rel_path is the directory path, we need to combine it with the filename
            directory_path = rel_path
            filename = file_obj.filename
            if not filename:
                return {"success": False, "error": "文件名为空"}
            
            # Combine directory path with filename
            if directory_path.endswith('/'):
                path = directory_path + filename
            else:
                path = directory_path + '/' + filename

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
            
            # Create directory structure if it doesn't exist
            remote_dir = path.rsplit('/', 1)[0] if '/' in path else ''
            if remote_dir:
                try:
                    # Create directories recursively
                    dirs_to_create = []
                    current_dir = remote_dir
                    while current_dir and current_dir != '/':
                        try:
                            sftp.stat(current_dir)
                            break  # Directory exists
                        except Exception:
                            dirs_to_create.append(current_dir)
                            current_dir = current_dir.rsplit('/', 1)[0] if '/' in current_dir else ''
                    
                    # Create directories from parent to child
                    for dir_path in reversed(dirs_to_create):
                        try:
                            sftp.mkdir(dir_path)
                        except Exception:
                            # Directory might already exist, ignore error
                            pass
                except Exception:
                    # If directory creation fails, continue anyway
                    pass
            
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
            
            # Use the current server if available, otherwise use the first one
            if self.current_server:
                remote = self.current_server
                logger.info(f"[RemoteFileService] delete_file using current server: {remote.get('server_name')}")
            else:
                remote = config["remote_server_list"][0]
                logger.info(f"[RemoteFileService] delete_file using first server: {remote.get('server_name')}")
            
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
            
            # Use the current server if available, otherwise use the first one
            if self.current_server:
                remote = self.current_server
                logger.info(f"[RemoteFileService] get_default_dir using current server: {remote.get('server_name')}")
            else:
                remote = config["remote_server_list"][0]
                logger.info(f"[RemoteFileService] get_default_dir using first server: {remote.get('server_name')}")
            
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
            # Find and set the current server based on the host
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                for remote in config.get("remote_server_list", []):
                    if remote["config"]["host_ip"] == host:
                        self.current_server = remote
                        logger.info(f"[RemoteFileService] Set current server to: {remote.get('server_name')}")
                        break
            except Exception as e:
                logger.error(f"Failed to set current server: {e}")
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
                if remote.get("server_name") == server_name:
                    remote["config"]["user_pwd"] = user_pwd
                    # Update the current server to this one
                    self.current_server = remote
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.info(f"[RemoteFileService] save_server_pwd success: server_name={server_name}")
            return {"success": True}
        except Exception as e:
            logger.error(f"保存远程服务器密码失败 server={server_name} error={e}")
            return {"success": False, "error": str(e)}

    def calculate_folder_size(self, mode: str, rel_path: str) -> Dict[str, Any]:
        logger.info(f"[RemoteFileService] calculate_folder_size: mode={mode}, rel_path={rel_path}")
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # Use the current server if available, otherwise use the first one
            if self.current_server:
                remote = self.current_server
                logger.info(f"[RemoteFileService] Using current server: {remote.get('server_name')}")
            else:
                remote = config["remote_server_list"][0]
                logger.info(f"[RemoteFileService] Using first server: {remote.get('server_name')}")
            
            ssh_info = remote["config"]
            host = ssh_info["host_ip"]
            port = ssh_info.get("ssh_port", 22)
            username = ssh_info["user_name"]
            password = ssh_info.get("user_pwd", "")
            path = rel_path
            
            # 创建SSH连接
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if password:
                ssh.connect(host, port=port, username=username, password=password)
            else:
                ssh.connect(host, port=port, username=username, allow_agent=True, look_for_keys=True)
            
            # 处理路径
            if path == "~" or path.startswith("~/"):
                sftp = ssh.open_sftp()
                home = sftp.normalize(".")
                sftp.close()
                if path == "~":
                    path = home
                else:
                    path = home + path[1:]
            
            if not path.startswith("/"):
                path = "/" + path
            
            # 使用du命令获取文件夹大小和find命令获取文件数量
            du_command = f'du -sb "{path}"'
            find_command = f'find "{path}" -type f | wc -l'
            
            # 执行命令
            stdin, stdout, stderr = ssh.exec_command(du_command)
            du_error = stderr.read().decode('utf-8').strip()
            if du_error:
                ssh.close()
                return {"error": du_error}
            
            # 解析du命令的输出
            du_output = stdout.read().decode('utf-8').strip()
            total_size = int(du_output.split()[0])
            
            # 执行find命令获取文件数量
            stdin, stdout, stderr = ssh.exec_command(find_command)
            find_error = stderr.read().decode('utf-8').strip()
            if find_error:
                ssh.close()
                return {"error": find_error}
            
            # 解析find命令的输出
            file_count = int(stdout.read().decode('utf-8').strip())
            
            ssh.close()
            
            return {
                "success": True,
                "total_size": total_size,
                "file_count": file_count,
                "path": path,
                "is_complete": True  # 标记为完整计算
            }
        except Exception as e:
            logger.error(f"远程计算文件夹大小失败: {str(e)}")
            return {"success": False, "error": str(e)}