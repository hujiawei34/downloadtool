import os
from datetime import datetime
from flask import request

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
LOG_FILE = os.path.join(LOG_DIR, 'operation.log')

def write_log(action, file_path):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {action} {file_path} from {request.remote_addr}\n") 