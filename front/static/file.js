import { renderFileList, renderCurrentPath } from './ui.js';
import { showErrorModal } from './modal.js';
// 文件操作相关逻辑
export let currentPath = null;
export let dirListCache = [];

// 处理错误信息，确保中文正常显示
function processErrorMessage(message) {
    if (!message) return '未知错误';
    
    try {
        // 尝试将Unicode转义序列转换为实际字符
        return decodeURIComponent(JSON.parse(`"${message.replace(/"/g, '\\"')}"`));
    } catch (e) {
        console.warn('错误消息解码失败', e);
        return message; // 返回原始消息
    }
}

export function fetchFileList(path = null, save = true) {
    const fileMode = localStorage.getItem('fileMode');
    const isRemote = fileMode === 'remote';
    
    if (path === null) {
        if (save && localStorage.getItem('lastPath')) {
            path = localStorage.getItem('lastPath');
        } else {
            // 如果没有指定路径，获取默认目录
            fetchDefaultDir().then(defaultDir => {
                fetchFileList(defaultDir, save);
            });
            return;
        }
    }
    
    // 显示加载状态
    const totalSizeDisplay = document.querySelector('.total-size-display');
    if (totalSizeDisplay) {
        totalSizeDisplay.textContent = '正在加载目录...';
        totalSizeDisplay.classList.add('calculating');
    }
    
    let url = '/api/list?path=' + encodeURIComponent(path);
    if (isRemote) {
        url += '&mode=remote';
    } else {
        url += '&mode=local';
    }
    
    fetch(url)
        .then(res => {
            // 检查HTTP状态
            if (!res.ok) {
                return res.text().then(text => {
                    try {
                        const jsonError = JSON.parse(text);
                        if (jsonError && jsonError.error) {
                            throw new Error(processErrorMessage(jsonError.error));
                        }
                    } catch (parseErr) {
                        // 如果JSON解析失败，使用原始错误文本
                    }
                    throw new Error(`服务器返回错误(${res.status}): ${text || res.statusText}`);
                });
            }
            return res.json();
        })
        .then(data => {
            if (totalSizeDisplay) {
                totalSizeDisplay.classList.remove('calculating');
            }
            
            if (data.error) {
                // 显示错误弹窗
                showErrorModal(processErrorMessage(data.error));
                return;
            }
            currentPath = data.path;
            window.currentPath = currentPath;
            if (save) localStorage.setItem('lastPath', currentPath);
            dirListCache = data.dirs.map(d => d.name);
            renderFileList(data);
            renderCurrentPath();
        })
        .catch(err => {
            console.error('加载目录失败:', err);
            if (totalSizeDisplay) {
                totalSizeDisplay.classList.remove('calculating');
                totalSizeDisplay.textContent = '加载失败';
            }
            
            // 显示错误弹窗
            showErrorModal(`无法加载目录: ${processErrorMessage(err.message) || '未知错误'}`);
        });
}

function fetchDefaultDir() {
    const fileMode = localStorage.getItem('fileMode');
    const isRemote = fileMode === 'remote';
    
    let url = '/api/default_dir';
    if (isRemote) url += '?mode=remote';
    else url += '?mode=local';
    
    return fetch(url)
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                console.warn('获取默认目录失败:', data.error);
                return isRemote ? '~' : '/';
            }
            return data.default_dir;
        })
        .catch(err => {
            console.error('获取默认目录失败:', err);
            return isRemote ? '~' : '/';
        });
}

// 计算文件夹大小
export function calculateFolderSize() {
    const path = currentPath || '/';
    const fileMode = localStorage.getItem('fileMode');
    const isRemote = fileMode === 'remote';
    
    // 显示正在计算的提示
    const totalSizeDisplay = document.querySelector('.total-size-display');
    if (totalSizeDisplay) {
        totalSizeDisplay.textContent = '正在计算文件夹大小，请稍候...';
        totalSizeDisplay.classList.add('calculating');
    }
    
    let url = `/api/calculate_size?path=${encodeURIComponent(path)}`;
    if (isRemote) {
        url += '&mode=remote';
    } else {
        url += '&mode=local';
    }
    
    fetch(url)
        .then(res => {
            // 检查HTTP状态
            if (!res.ok) {
                return res.text().then(text => {
                    try {
                        const jsonError = JSON.parse(text);
                        if (jsonError && jsonError.error) {
                            throw new Error(processErrorMessage(jsonError.error));
                        }
                    } catch (parseErr) {
                        // 如果JSON解析失败，使用原始错误文本
                    }
                    throw new Error(`服务器返回错误(${res.status}): ${text || res.statusText}`);
                });
            }
            return res.json();
        })
        .then(data => {
            if (data.error) {
                if (totalSizeDisplay) {
                    totalSizeDisplay.textContent = '计算失败';
                    totalSizeDisplay.classList.remove('calculating');
                }
                // 显示错误弹窗
                showErrorModal(processErrorMessage(data.error));
                return;
            }
            
            // 重新加载目录列表，以获取和显示子目录大小
            fetchFileListWithSizes(path);
        })
        .catch(err => {
            console.error('计算失败:', err);
            if (totalSizeDisplay) {
                totalSizeDisplay.textContent = '计算请求失败';
                totalSizeDisplay.classList.remove('calculating');
            }
            // 显示错误弹窗
            showErrorModal(`计算文件夹大小失败: ${processErrorMessage(err.message) || '未知错误'}`);
        });
}

// 获取包含目录大小的文件列表
export function fetchFileListWithSizes(path = null) {
    const fileMode = localStorage.getItem('fileMode');
    const isRemote = fileMode === 'remote';
    
    if (path === null) {
        path = currentPath || '/';
    }
    
    const totalSizeDisplay = document.querySelector('.total-size-display');
    if (totalSizeDisplay) {
        totalSizeDisplay.textContent = '正在计算所有目录大小，请稍候...';
        totalSizeDisplay.classList.add('calculating');
    }
    
    let url = `/api/list_with_sizes?path=${encodeURIComponent(path)}`;
    if (isRemote) {
        url += '&mode=remote';
    } else {
        url += '&mode=local';
    }
    
    fetch(url)
        .then(res => {
            // 检查HTTP状态
            if (!res.ok) {
                return res.text().then(text => {
                    try {
                        const jsonError = JSON.parse(text);
                        if (jsonError && jsonError.error) {
                            throw new Error(processErrorMessage(jsonError.error));
                        }
                    } catch (parseErr) {
                        // 如果JSON解析失败，使用原始错误文本
                    }
                    throw new Error(`服务器返回错误(${res.status}): ${text || res.statusText}`);
                });
            }
            return res.json();
        })
        .then(data => {
            if (data.error) {
                const totalSizeDisplay = document.querySelector('.total-size-display');
                if (totalSizeDisplay) {
                    totalSizeDisplay.textContent = '获取目录信息失败';
                    totalSizeDisplay.classList.remove('calculating');
                }
                // 显示错误弹窗
                showErrorModal(processErrorMessage(data.error));
                return;
            }
            currentPath = data.path;
            window.currentPath = currentPath;
            localStorage.setItem('lastPath', currentPath);
            dirListCache = data.dirs.map(d => d.name);
            
            // 移除计算中状态
            if (totalSizeDisplay) {
                totalSizeDisplay.classList.remove('calculating');
            }
            
            renderFileList(data);
            renderCurrentPath();
        })
        .catch(err => {
            console.error('获取目录列表失败:', err);
            const totalSizeDisplay = document.querySelector('.total-size-display');
            if (totalSizeDisplay) {
                totalSizeDisplay.textContent = '获取目录列表失败';
                totalSizeDisplay.classList.remove('calculating');
            }
            // 显示错误弹窗
            showErrorModal(`获取目录列表失败: ${processErrorMessage(err.message) || '未知错误'}`);
        });
}

// 上传文件
export function uploadFiles() {
    const input = document.getElementById('file-upload');
    const files = input.files;
    if (!files.length) {
        alert('请选择文件');
        return;
    }
    const path = currentPath || '/';
    const fileMode = localStorage.getItem('fileMode');
    const isRemote = fileMode === 'remote';
    
    for (let i = 0; i < files.length; i++) {
        const formData = new FormData();
        formData.append('file', files[i]);
        let url = `/api/upload?path=${encodeURIComponent(path)}`;
        if (isRemote) {
            url += '&mode=remote';
        } else {
            url += '&mode=local';
        }
        
        fetch(url, {
            method: 'POST',
            body: formData
        }).then(res => {
            if (res.status === 409) {
                return res.json().then(data => { alert('文件已存在: ' + files[i].name); });
            }
            return res.json();
        }).then(() => {
            fetchFileList(path, true);
        }).catch(err => {
            console.error('上传失败:', err);
            alert('上传失败');
        });
    }
}

// 上传文件夹
export function uploadFolders() {
    const input = document.getElementById('folder-upload');
    const files = input.files;
    if (!files.length) {
        alert('请选择文件夹');
        return;
    }
    const path = currentPath || '/';
    const fileMode = localStorage.getItem('fileMode');
    const isRemote = fileMode === 'remote';
    
    for (let i = 0; i < files.length; i++) {
        const formData = new FormData();
        formData.append('file', files[i], files[i].webkitRelativePath || files[i].name);
        let url = `/api/upload?path=${encodeURIComponent(path)}`;
        if (isRemote) {
            url += '&mode=remote';
        } else {
            url += '&mode=local';
        }
        
        fetch(url, {
            method: 'POST',
            body: formData
        }).then(res => {
            if (res.status === 409) {
                return res.json().then(data => { alert('文件已存在: ' + files[i].name); });
            }
            return res.json();
        }).then(() => {
            fetchFileList(path, true);
        }).catch(err => {
            console.error('上传失败:', err);
            alert('上传失败');
        });
    }
}

// 格式化文件大小
export function formatSize(size) {
    if (size === undefined || size === null) return '-';
    
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let i = 0;
    while (size >= 1024 && i < units.length - 1) {
        size /= 1024;
        i++;
    }
    
    return size.toFixed(2) + ' ' + units[i];
}

// 其余文件操作函数（如上传、删除）可继续拆分导出 