import os
from flask import request, jsonify, send_file
from utils.log_util import write_log
from werkzeug.utils import secure_filename

def list_dir():
    rel_path = request.args.get('path', '')
    abs_path = os.path.abspath(rel_path) if os.path.isabs(rel_path) else os.path.abspath(os.path.join('/', rel_path))
    if not os.path.exists(abs_path):
        return jsonify({'error': '路径不存在'}), 400
    files = []
    dirs = []
    for entry in os.scandir(abs_path):
        stat = entry.stat()
        if entry.is_dir():
            dirs.append({
                'name': entry.name,
                'type': 'dir',
                'size': stat.st_size,
                'mtime': stat.st_mtime
            })
        else:
            files.append({
                'name': entry.name,
                'type': 'file',
                'size': stat.st_size,
                'mtime': stat.st_mtime
            })
    return jsonify({'dirs': dirs, 'files': files, 'path': abs_path})

def download_file():
    rel_path = request.args.get('path')
    abs_path = os.path.abspath(rel_path) if os.path.isabs(rel_path) else os.path.abspath(os.path.join('/', rel_path))
    if not os.path.isfile(abs_path):
        return '文件不存在', 404
    write_log('DOWNLOAD', abs_path)
    return send_file(abs_path, as_attachment=True)

def upload_file():
    rel_path = request.args.get('path', '')
    abs_dir = os.path.abspath(rel_path) if os.path.isabs(rel_path) else os.path.abspath(os.path.join('/', rel_path))
    if not os.path.isdir(abs_dir):
        return jsonify({'error': '非法路径'}), 400
    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400
    file = request.files['file']
    filename = file.filename  # 保留原始文件名（含多级目录）
    save_path = os.path.join(abs_dir, filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)  # 自动创建多级目录
    if os.path.exists(save_path):
        return jsonify({'error': '文件已存在', 'exists': True}), 409
    file.save(save_path)
    write_log('UPLOAD', save_path)
    return jsonify({'success': True})

def delete_file():
    rel_path = request.args.get('path') or request.form.get('path')
    abs_path = os.path.abspath(rel_path) if os.path.isabs(rel_path) else os.path.abspath(os.path.join('/', rel_path))
    if not os.path.isfile(abs_path):
        return jsonify({'error': '只能删除文件，不能删除文件夹'}), 400
    try:
        os.remove(abs_path)
        write_log('DELETE', abs_path)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500 