from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    send_file,
)
from flask_cors import CORS
import os

from utils.constants import FRONT_DIR,PROJECT_ROOT
from utils.log_util import default_logger as logger

from service.impl.local_file_service import LocalFileService
from service.impl.remote_file_service import RemoteFileService
logger.info("[app] Starting Flask application")
logger.info("FRONT_DIR: %s", FRONT_DIR)
logger.info("PROJECT_ROOT: %s", PROJECT_ROOT)
app = Flask(
    __name__,
    static_folder=str(FRONT_DIR / "static"),
    template_folder=str(FRONT_DIR / "templates"),
)
# 配置Flask应用
app.config['JSON_AS_ASCII'] = False  # 确保JSON响应中的非ASCII字符不会被转义
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # 禁用美化输出，减少响应大小
app.json.ensure_ascii = False  # 确保JSON不会将中文等字符转换为Unicode转义序列
CORS(app)

local_service = LocalFileService()
remote_service = RemoteFileService()

def get_service(mode: str):
    return remote_service if mode == "remote" else local_service

@app.route("/")
def index():
    logger.info("[app] index page requested")
    return render_template("index.html")

@app.route("/files")
def files():
    logger.info("[app] files page requested")
    return render_template("files.html")

@app.route("/api/list", methods=["GET"])
def api_list_dir():
    mode = request.args.get("mode")
    rel_path = request.args.get("path", "")
    service = get_service(mode)
    try:
        result = service.list_dir(mode, rel_path)
        logger.info(f"[app] /api/list result: {result}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"[app] /api/list error: {str(e)}")
        error_message = f"访问目录失败: {str(e)}"
        return jsonify({"error": error_message.encode('utf-8').decode('utf-8')}), 500

@app.route("/api/list_with_sizes", methods=["GET"])
def api_list_dir_with_sizes():
    mode = request.args.get("mode")
    rel_path = request.args.get("path", "")
    service = get_service(mode)
    
    try:
        # 获取文件列表
        result = service.list_dir(mode, rel_path)
        
        if "error" in result:
            return jsonify(result), 400
        
        # 计算当前目录总大小
        size_result = service.calculate_folder_size(mode, rel_path)
        
        if "success" in size_result and size_result["success"]:
            # 更新目录信息
            result["dir_info"] = {
                "total_size": size_result.get("total_size", 0),
                "file_count": size_result.get("file_count", 0),
                "is_complete": True
            }
            
            # 计算每个子目录大小
            for i, dir_entry in enumerate(result["dirs"]):
                # 构造子目录路径，适应不同模式
                current_path = result["path"]
                if current_path.endswith('/'):
                    dir_path = current_path + dir_entry["name"]
                else:
                    dir_path = current_path + '/' + dir_entry["name"]
                    
                try:
                    dir_size = service.calculate_folder_size(mode, dir_path)
                    if "success" in dir_size and dir_size["success"]:
                        result["dirs"][i]["size"] = dir_size.get("total_size", 0)
                except Exception as e:
                    logger.warning(f"[app] Failed to calculate size for directory: {dir_path}, error: {str(e)}")
                    # 子目录大小计算失败不影响整体结果
                    result["dirs"][i]["size"] = None
        
        logger.info(f"[app] /api/list_with_sizes completed for path: {rel_path}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"[app] /api/list_with_sizes error: {str(e)}")
        error_message = f"处理目录失败: {str(e)}"
        return jsonify({"error": error_message.encode('utf-8').decode('utf-8')}), 500

@app.route("/api/download", methods=["GET"])
def api_download_file():
    mode = request.args.get("mode")
    rel_path = request.args.get("path")
    if not rel_path:
        logger.warning("[app] /api/download missing path parameter")
        return jsonify({"error": "路径参数缺失".encode('utf-8').decode('utf-8')}), 400
    
    try:
        service = get_service(mode)
        file_path = service.download_file(mode, rel_path)
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"[app] /api/download file not found: {file_path}")
            return jsonify({"error": "文件不存在".encode('utf-8').decode('utf-8')}), 404
        
        filename = os.path.basename(rel_path)
        logger.info(f"[app] DOWNLOAD {file_path}")
        return send_file(file_path, as_attachment=True, download_name=filename)
    except Exception as e:
        logger.error(f"[app] /api/download error: {str(e)}")
        error_message = f"下载文件失败: {str(e)}"
        return jsonify({"error": error_message.encode('utf-8').decode('utf-8')}), 500

@app.route("/api/calculate_size", methods=["GET"])
def api_calculate_size():
    mode = request.args.get("mode")
    rel_path = request.args.get("path")
    if not rel_path:
        logger.warning("[app] /api/calculate_size missing path parameter")
        return jsonify({"error": "路径参数缺失".encode('utf-8').decode('utf-8')}), 400
    
    try:
        service = get_service(mode)
        result = service.calculate_folder_size(mode, rel_path)
        logger.info(f"[app] /api/calculate_size result: {result}")
        if "error" in result:
            # 确保错误信息编码正确
            if isinstance(result["error"], str):
                result["error"] = result["error"].encode('utf-8').decode('utf-8')
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        logger.error(f"[app] /api/calculate_size error: {str(e)}")
        error_message = f"计算文件夹大小失败: {str(e)}"
        return jsonify({"error": error_message.encode('utf-8').decode('utf-8')}), 500

@app.route("/api/upload", methods=["POST"])
def api_upload_file():
    mode = request.args.get("mode")
    rel_path = request.args.get("path", "")
    if not rel_path:
        logger.warning("[app] /api/upload missing path parameter")
        return jsonify({"error": "路径参数缺失"}), 400
    if "file" not in request.files:
        logger.warning("[app] /api/upload no file selected")
        return jsonify({"error": "未选择文件"}), 400
    file = request.files["file"]
    service = get_service(mode)
    result = service.upload_file(mode, rel_path, file)
    logger.info(f"[app] /api/upload result: {result}")
    return jsonify(result)

@app.route("/api/delete", methods=["POST"])
def api_delete_file():
    mode = request.args.get("mode")
    rel_path = request.args.get("path")
    if not rel_path:
        logger.warning("[app] /api/delete missing path parameter")
        return jsonify({"success": False, "error": "路径参数缺失"}), 400
    service = get_service(mode)
    result = service.delete_file(mode, rel_path)
    logger.info(f"[app] /api/delete result: {result}")
    return jsonify(result)

@app.route("/api/default_dir")
def get_default_dir():
    mode = request.args.get("mode")
    service = get_service(mode)
    result = service.get_default_dir(mode)
    logger.info(f"[app] /api/default_dir result: {result}")
    return jsonify(result)

@app.route("/api/remote_servers")
def get_remote_servers():
    result = remote_service.get_remote_servers()
    logger.info(f"[app] /api/remote_servers result: {result}")
    return jsonify({"remote_server_list": result})

@app.route("/api/test_server_connectivity", methods=["POST"])
def test_server_connectivity():
    ssh_info = request.json
    result = remote_service.test_server_connectivity(ssh_info)
    logger.info(f"[app] /api/test_server_connectivity result: {result}")
    return jsonify(result)

@app.route("/api/save_server_pwd", methods=["POST"])
def save_server_pwd():
    data = request.json
    server_name = data.get("server_name")
    user_pwd = data.get("user_pwd")
    result = remote_service.save_server_pwd(server_name, user_pwd)
    logger.info(f"[app] /api/save_server_pwd result: {result}")
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=18023, debug=True)
