from flask import Flask, send_from_directory, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from flask import send_file
import json
from datetime import datetime
import log_util
from file_api import list_dir, download_file, upload_file, delete_file
import logging
from paramiko import SSHClient, AutoAddPolicy
from flask import session
import paramiko
import stat
import tempfile

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FRONT_DIR = os.path.abspath(os.path.join(BASE_DIR, '../../front'))
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
LOG_FILE = os.path.join(LOG_DIR, 'operation.log')

app = Flask(
    __name__,
    static_folder=os.path.join(FRONT_DIR, 'static'),
    template_folder=os.path.join(FRONT_DIR, 'templates')
)
CORS(app)

write_log = log_util.write_log

log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs/flask.log'))
logging.basicConfig(filename=log_path, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', encoding='utf-8')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/list', methods=['GET'])
def list_dir():
    mode = request.args.get('mode')
    rel_path = request.args.get('path', '')
    if mode == 'remote':
        config_path = os.path.join(os.path.dirname(__file__), '../../config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        remote = config['remote_server_list'][0]
        ssh_info = remote['config']
        host = ssh_info['host_ip']
        port = ssh_info.get('ssh_port', 22)
        username = ssh_info['user_name']
        password = ssh_info.get('user_pwd', '')
        default_dir = ssh_info.get('default_dir', '~')
        path = rel_path or default_dir
        try:
            if password:
                transport = paramiko.Transport((host, port))
                transport.connect(username=username, password=password)
                sftp = paramiko.SFTPClient.from_transport(transport)
            else:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(host, port=port, username=username, allow_agent=True, look_for_keys=True)
                sftp = ssh.open_sftp()
            # 统一展开~为远程home目录
            if path == '~' or path.startswith('~/'):
                home = sftp.normalize('.')
                if path == '~':
                    path = home
                else:
                    path = home + path[1:]
            # 保证 path 以 / 开头
            if not path.startswith('/'):
                path = '/' + path
            files = []
            dirs = []
            for entry in sftp.listdir_attr(path):
                if stat.S_ISDIR(entry.st_mode):
                    dirs.append({'name': entry.filename, 'type': 'dir', 'size': entry.st_size, 'mtime': entry.st_mtime})
                else:
                    files.append({'name': entry.filename, 'type': 'file', 'size': entry.st_size, 'mtime': entry.st_mtime})
            sftp.close()
            if not password:
                ssh.close()
            else:
                transport.close()
            return jsonify({'dirs': dirs, 'files': files, 'path': path})
        except Exception as e:
            logging.error(f"远程SFTP访问失败 host={host} user={username} path={path} error={e}")
            return jsonify({'error': str(e)}), 400
    else:
        abs_path = os.path.abspath(rel_path) if os.path.isabs(rel_path) else os.path.abspath(os.path.join('/', rel_path))
        if not os.path.exists(abs_path):
            return jsonify({'error': '路径不存在'}), 400
        files = []
        dirs = []
        for entry in os.scandir(abs_path):
            entry_stat = entry.stat()
            if entry.is_dir():
                dirs.append({
                    'name': entry.name,
                    'type': 'dir',
                    'size': entry_stat.st_size,
                    'mtime': entry_stat.st_mtime
                })
            else:
                files.append({
                    'name': entry.name,
                    'type': 'file',
                    'size': entry_stat.st_size,
                    'mtime': entry_stat.st_mtime
                })
        return jsonify({'dirs': dirs, 'files': files, 'path': abs_path})

@app.route('/api/download', methods=['GET'])
def download_file():
    mode = request.args.get('mode')
    rel_path = request.args.get('path')
    
    # 确保rel_path不为None
    if not rel_path:
        return '路径参数缺失', 400
    
    if mode == 'remote':
        # 从远程SFTP下载文件
        config_path = os.path.join(os.path.dirname(__file__), '../../config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        remote = config['remote_server_list'][0]
        ssh_info = remote['config']
        host = ssh_info['host_ip']
        port = ssh_info.get('ssh_port', 22)
        username = ssh_info['user_name']
        password = ssh_info.get('user_pwd', '')
        
        try:
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            # 连接SFTP
            if password:
                transport = paramiko.Transport((host, port))
                transport.connect(username=username, password=password)
                sftp = paramiko.SFTPClient.from_transport(transport)
            else:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(host, port=port, username=username, allow_agent=True, look_for_keys=True)
                sftp = ssh.open_sftp()
            
            # 下载文件
            sftp.get(rel_path, temp_path)
            sftp.close()
            if password:
                transport.close()
            else:
                ssh.close()
            
            # 发送文件
            filename = os.path.basename(rel_path)
            write_log('DOWNLOAD', f'Remote: {rel_path}')
            return send_file(temp_path, as_attachment=True, download_name=filename)
        except Exception as e:
            logging.error(f"远程文件下载失败 host={host} user={username} path={rel_path} error={e}")
            return f'远程文件下载失败: {str(e)}', 404
    else:
        # 本地文件下载，保持原有逻辑
        abs_path = os.path.abspath(rel_path) if os.path.isabs(rel_path) else os.path.abspath(os.path.join('/', rel_path))
        if not os.path.isfile(abs_path):
            return '文件不存在', 404
        write_log('DOWNLOAD', abs_path)
        return send_file(abs_path, as_attachment=True)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    mode = request.args.get('mode')
    rel_path = request.args.get('path', '')
    
    if not rel_path:
        return jsonify({'error': '路径参数缺失'}), 400
    
    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400
    
    file = request.files['file']
    filename = file.filename  # 保留原始文件名（含多级目录）
    
    if mode == 'remote':
        # 远程SFTP上传
        config_path = os.path.join(os.path.dirname(__file__), '../../config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        remote = config['remote_server_list'][0]
        ssh_info = remote['config']
        host = ssh_info['host_ip']
        port = ssh_info.get('ssh_port', 22)
        username = ssh_info['user_name']
        password = ssh_info.get('user_pwd', '')
        
        try:
            # 保存到临时文件
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_path = temp_file.name
            temp_file.close()
            file.save(temp_path)
            
            # 连接SFTP
            if password:
                transport = paramiko.Transport((host, port))
                transport.connect(username=username, password=password)
                sftp = paramiko.SFTPClient.from_transport(transport)
            else:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(host, port=port, username=username, allow_agent=True, look_for_keys=True)
                sftp = ssh.open_sftp()
            
            # 确保远程路径存在
            remote_path = rel_path
            if not remote_path.startswith('/'):
                remote_path = '/' + remote_path
                
            # 上传文件
            remote_file_path = os.path.join(remote_path, filename).replace('\\', '/')
            
            # 检查文件是否存在
            try:
                sftp.stat(remote_file_path)
                sftp.close()
                if password:
                    transport.close()
                else:
                    ssh.close()
                os.unlink(temp_path)  # 删除临时文件
                return jsonify({'error': '文件已存在', 'exists': True}), 409
            except:
                # 文件不存在，可以上传
                pass
                
            # 创建目录（如果需要）
            remote_dir = os.path.dirname(remote_file_path)
            try:
                sftp.stat(remote_dir)
            except:
                # 目录不存在，创建
                try:
                    # 创建多级目录
                    current_dir = ''
                    for part in remote_dir.split('/'):
                        if not part:
                            continue
                        current_dir = current_dir + '/' + part
                        try:
                            sftp.stat(current_dir)
                        except:
                            sftp.mkdir(current_dir)
                except Exception as e:
                    logging.error(f"创建远程目录失败: {remote_dir}, error: {str(e)}")
                    return jsonify({'error': f'创建远程目录失败: {str(e)}'}), 400
            
            # 上传文件
            sftp.put(temp_path, remote_file_path)
            sftp.close()
            if password:
                transport.close()
            else:
                ssh.close()
            os.unlink(temp_path)  # 删除临时文件
            
            write_log('UPLOAD', f'Remote: {remote_file_path}')
            return jsonify({'success': True})
        except Exception as e:
            logging.error(f"远程文件上传失败: {str(e)}")
            return jsonify({'error': f'上传失败: {str(e)}'}), 400
    else:
        # 本地文件上传，保持原有逻辑
        abs_dir = os.path.abspath(rel_path) if os.path.isabs(rel_path) else os.path.abspath(os.path.join('/', rel_path))
        if not os.path.isdir(abs_dir):
            return jsonify({'error': '非法路径'}), 400
        
        save_path = os.path.join(abs_dir, filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)  # 自动创建多级目录
        if os.path.exists(save_path):
            return jsonify({'error': '文件已存在', 'exists': True}), 409
        file.save(save_path)
        write_log('UPLOAD', save_path)
        return jsonify({'success': True})

@app.route('/api/default_dir')
def get_default_dir():
    mode = request.args.get('mode')
    try:
        config_path = os.path.join(os.path.dirname(__file__), '../../config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        if mode == 'remote':
            if not config.get('remote_server_list'):
                logging.warning("远程服务器列表为空")
                return jsonify({'default_dir': '~', 'error': 'No remote servers configured'})
            remote = config['remote_server_list'][0]
            default_dir = remote['config'].get('default_dir', '~')
            return jsonify({'default_dir': default_dir})
        else:
            default_dir = config.get('local_default_dir', '/')
            default_dir = os.path.expanduser(default_dir)
            return jsonify({'default_dir': default_dir})
    except Exception as e:
        logging.error(f"获取default_dir失败: {str(e)}")
        return jsonify({'default_dir': '~', 'error': str(e)})

@app.route('/api/remote_servers')
def get_remote_servers():
    config_path = os.path.join(os.path.dirname(__file__), '../../config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    return jsonify({'remote_server_list': config.get('remote_server_list', [])})

@app.route('/api/test_server_connectivity', methods=['POST'])
def test_server_connectivity():
    data = request.json
    host = data.get('host_ip')
    port = data.get('ssh_port', 22)
    username = data.get('user_name')
    password = data.get('user_pwd', '')
    try:
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        if password:
            ssh.connect(host, port=port, username=username, password=password, timeout=5)
        else:
            ssh.connect(host, port=port, username=username, timeout=5, allow_agent=True, look_for_keys=True)
        ssh.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save_server_pwd', methods=['POST'])
def save_server_pwd():
    data = request.json
    server_name = data.get('server_name')
    user_pwd = data.get('user_pwd')
    config_path = os.path.join(os.path.dirname(__file__), '../../config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    for srv in config['remote_server_list']:
        if srv['server_name'] == server_name:
            srv['config']['user_pwd'] = user_pwd
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)
    return jsonify({'success': True})

@app.route('/api/delete', methods=['POST'])
def delete_file():
    mode = request.args.get('mode')
    rel_path = request.args.get('path')
    
    # 确保rel_path不为None
    if not rel_path:
        return jsonify({'success': False, 'error': '路径参数缺失'}), 400
    
    if mode == 'remote':
        # 从远程SFTP删除文件
        config_path = os.path.join(os.path.dirname(__file__), '../../config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        remote = config['remote_server_list'][0]
        ssh_info = remote['config']
        host = ssh_info['host_ip']
        port = ssh_info.get('ssh_port', 22)
        username = ssh_info['user_name']
        password = ssh_info.get('user_pwd', '')
        
        try:
            # 连接SFTP
            if password:
                transport = paramiko.Transport((host, port))
                transport.connect(username=username, password=password)
                sftp = paramiko.SFTPClient.from_transport(transport)
            else:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(host, port=port, username=username, allow_agent=True, look_for_keys=True)
                sftp = ssh.open_sftp()
            
            # 删除文件
            sftp.remove(rel_path)
            sftp.close()
            if password:
                transport.close()
            else:
                ssh.close()
            
            write_log('DELETE', f'Remote: {rel_path}')
            return jsonify({'success': True})
        except Exception as e:
            logging.error(f"远程文件删除失败 host={host} user={username} path={rel_path} error={e}")
            return jsonify({'success': False, 'error': str(e)}), 400
    else:
        # 本地文件删除，保持原有逻辑
        abs_path = os.path.abspath(rel_path) if os.path.isabs(rel_path) else os.path.abspath(os.path.join('/', rel_path))
        if not os.path.isfile(abs_path):
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        try:
            os.remove(abs_path)
            write_log('DELETE', abs_path)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400

app.add_url_rule('/api/list', view_func=list_dir, methods=['GET'])
app.add_url_rule('/api/download', view_func=download_file, methods=['GET'])
app.add_url_rule('/api/upload', view_func=upload_file, methods=['POST'])
app.add_url_rule('/api/delete', view_func=delete_file, methods=['POST'])

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=18023, debug=True) 