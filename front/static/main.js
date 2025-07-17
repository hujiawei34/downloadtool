// main.js 入口文件
import './server.js';
import './file.js';
import './ui.js';
import './utils.js';
import { setupFileListClick } from './ui.js';
import { uploadFiles, uploadFolders } from './file.js';

// 设置事件监听
document.addEventListener('DOMContentLoaded', function() {
    setupFileListClick();
    
    // 添加上传按钮事件监听
    document.getElementById('upload-files-btn')?.addEventListener('click', uploadFiles);
    document.getElementById('upload-folders-btn')?.addEventListener('click', uploadFolders);
}); 