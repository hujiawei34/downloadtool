// main.js 入口文件
import './server.js';
import './file.js';
import './ui.js';
import './utils.js';
import { setupFileListClick } from './ui.js';
import { uploadFiles, uploadFolders, fetchFileList } from './file.js';

// 设置事件监听
document.addEventListener('DOMContentLoaded', function() {
    // 检查是否在files页面
    if (window.location.pathname === '/files') {
        // 初始化文件页面
        initFilesPage();
    } else if (window.location.pathname === '/') {
        // 初始化首页 - 服务器选择页面
        initIndexPage();
    }
    
    // 添加上传按钮事件监听 (仅在files页面存在)
    document.getElementById('upload-files-btn')?.addEventListener('click', uploadFiles);
    document.getElementById('upload-folders-btn')?.addEventListener('click', uploadFolders);
});

function initIndexPage() {
    // 首页初始化逻辑已在server.js中处理
    console.log('Index page initialized');
}

function initFilesPage() {
    // 检查是否有保存的模式
    const fileMode = localStorage.getItem('fileMode');
    if (!fileMode) {
        // 如果没有模式，重定向到首页
        window.location.href = '/';
        return;
    }
    
    // 显示模式指示器
    const modeIndicator = document.getElementById('mode-indicator');
    if (modeIndicator) {
        modeIndicator.textContent = fileMode === 'remote' ? '远程模式' : '本地模式';
    }
    
    // 设置返回按钮事件监听
    const backBtn = document.getElementById('back-to-server-btn');
    if (backBtn) {
        backBtn.addEventListener('click', function() {
            // 清除保存的模式和路径
            localStorage.removeItem('fileMode');
            localStorage.removeItem('selectedServer');
            localStorage.removeItem('lastPath');
            
            // 跳转回服务器选择页面
            window.location.href = '/';
        });
        console.log('Back button event listener attached');
    } else {
        console.error('Back button not found');
    }
    
    // 设置文件列表点击事件监听
    setupFileListClick();
    
    // 加载文件列表
    fetchFileList();
} 