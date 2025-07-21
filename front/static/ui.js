// UI渲染相关逻辑
export function renderCurrentPath() {
    const container = document.getElementById('current-path-container');
    container.innerHTML = '';
    const currentPathSpan = document.createElement('span');
    currentPathSpan.id = 'current-path';
    currentPathSpan.textContent = window.currentPath;
    currentPathSpan.ondblclick = function() {
        showPathInput();
    };
    container.appendChild(currentPathSpan);
}

import { formatSize, formatDate } from './utils.js';
import { fetchFileList } from './file.js';

// 事件委托：监听文件夹点击和删除按钮点击
export function setupFileListClick() {
    const fileList = document.getElementById('file-list');
    if (!fileList) {
        console.warn('file-list element not found, skipping setupFileListClick');
        return;
    }
    fileList.addEventListener('click', function(e) {
        // 处理目录点击
        if (e.target.tagName === 'A' && e.target.dataset.dirpath) {
            e.preventDefault();
            import('./file.js').then(module => {
                module.fetchFileList(e.target.dataset.dirpath, true);
            }).catch(err => {
                console.error('加载file.js失败:', err);
            });
            return;
        }
        
        // 处理删除按钮点击
        if (e.target.classList.contains('delete-btn')) {
            const filePath = e.target.dataset.filepath;
            if (confirm('确定要删除该文件吗？')) {
                const fileMode = localStorage.getItem('fileMode');
                const isRemote = fileMode === 'remote';
                let url = `/api/delete?path=${encodeURIComponent(filePath)}`;
                if (isRemote) {
                    url += '&mode=remote';
                } else {
                    url += '&mode=local';
                }
                
                fetch(url, {
                    method: 'POST'
                }).then(res => res.json()).then(data => {
                    if (data.success) {
                        // 刷新文件列表
                        import('./file.js').then(module => {
                            module.fetchFileList(null, true);
                        });
                    } else {
                        alert(data.error || '删除失败');
                    }
                }).catch(err => {
                    console.error('删除请求失败:', err);
                    alert('删除请求失败');
                });
            }
        }
    });
}

export function renderFileList(data) {
    const fileList = document.getElementById('file-list');
    const pageTitle = document.getElementById('page-title');
    let path = data.path || '/';
    pageTitle.textContent = '文件浏览器 - ' + path;
    
    // 更新总大小显示
    const totalSizeDisplay = document.querySelector('.total-size-display');
    if (totalSizeDisplay && data.dir_info) {
        if (data.dir_info.is_complete) {
            totalSizeDisplay.textContent = `当前目录总大小: ${formatSize(data.dir_info.total_size)} (文件数: ${data.dir_info.file_count})`;
            totalSizeDisplay.style.color = '#ff6600';
        } else {
            totalSizeDisplay.textContent = `文件大小: ${formatSize(data.dir_info.total_size)} (仅当前目录文件，不含子目录)`;
            totalSizeDisplay.style.color = '#666666';
        }
    }
    
    let html = '';
    html += '<table class="file-table">';
    html += '<thead><tr><th>File Name</th><th>File Size</th><th>Date</th></tr></thead>';
    html += '<tbody>';
    if (path !== '/' && !isRootDrive(path)) {
        // 处理不同操作系统的上级目录路径计算
        let upPath;
        if (isWindowsPath(path)) {
            // Windows路径处理
            if (path.endsWith(':\\') || path.endsWith(':/')) {
                // 已经是盘符根目录，不显示上级目录
                upPath = null;
            } else {
                // 移除结尾的斜杠
                let cleanPath = path.replace(/[\/\\]+$/, '');
                // 获取上级目录
                upPath = cleanPath.substring(0, cleanPath.lastIndexOf('\\') + 1);
                // 如果上级路径为空，则设为盘符根目录
                if (!upPath) {
                    const driveMatch = path.match(/^([A-Za-z]:)[\/\\]/);
                    if (driveMatch) {
                        upPath = driveMatch[1] + '\\';
                    }
                }
            }
        } else {
            // Unix路径处理
            upPath = path.replace(/\/+$/, '').split('/').slice(0, -1).join('/') || '/';
        }
        
        // 只有在上级路径有效时才显示
        if (upPath) {
            html += `<tr class="row-alt"><td colspan="3"><a href="#" data-dirpath="${upPath}">../</a></td></tr>`;
        }
    }
    let rowIdx = 0;
    data.dirs.forEach(dir => {
        const dirPath = joinPath(path, dir.name);
        const sizeDisplay = dir.size === null ? '-' : formatSize(dir.size);
        html += `<tr class="${rowIdx % 2 === 0 ? '' : 'row-alt'}"><td><a href="#" data-dirpath="${dirPath}">${dir.name}/</a></td><td>${sizeDisplay}</td><td>${formatDate(dir.mtime)}</td></tr>`;
        rowIdx++;
    });
    data.files.forEach(file => {
        const filePath = joinPath(path, file.name);
        // 根据当前模式设置下载URL
        const fileMode = localStorage.getItem('fileMode');
        const isRemote = fileMode === 'remote';
        let downloadUrl = `/api/download?path=${encodeURIComponent(filePath)}`;
        if (isRemote) {
            downloadUrl += '&mode=remote';
        } else {
            downloadUrl += '&mode=local';
        }
        html += `<tr class="${rowIdx % 2 === 0 ? '' : 'row-alt'}">
            <td>
                <a href="${downloadUrl}">${file.name}</a>
                <button class="delete-btn" data-filepath="${filePath}">删除</button>
            </td>
            <td>${formatSize(file.size)}</td>
            <td>${formatDate(file.mtime)}</td>
        </tr>`;
        rowIdx++;
    });
    html += '</tbody></table>';
    fileList.innerHTML = html;
}

// 检查是否是Windows路径
function isWindowsPath(path) {
    return /^[A-Za-z]:[\\\/]/.test(path);
}

// 检查是否是根驱动器路径
function isRootDrive(path) {
    return /^[A-Za-z]:[\\\/]$/.test(path);
}

// 连接路径，处理不同系统分隔符
function joinPath(parentPath, childName) {
    // 处理Windows路径
    if (isWindowsPath(parentPath)) {
        // 移除末尾斜杠
        const cleanPath = parentPath.replace(/[\\\/]+$/, '');
        return cleanPath + '\\' + childName;
    } else {
        // Unix路径
        const cleanPath = parentPath.replace(/\/+$/, '');
        return (cleanPath === '/' ? '' : cleanPath) + '/' + childName;
    }
}

export function showPathInput() {
    const container = document.getElementById('current-path-container');
    const currentPath = window.currentPath || '/';
    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentPath;
    input.className = 'path-input';
    input.id = 'path-input';
    input.setAttribute('autocomplete', 'off');
    input.style.fontSize = '1.2em';
    input.style.fontFamily = 'inherit';
    input.style.width = '100%';
    input.style.boxSizing = 'border-box';
    input.style.padding = '4px 8px';

    // 下拉建议列表
    let suggestList = document.createElement('ul');
    suggestList.className = 'custom-suggest-list';
    suggestList.style.display = 'none';
    container.innerHTML = '';
    container.appendChild(input);
    container.appendChild(suggestList);
    input.focus();

    let filteredDirs = [];
    let activeIdx = -1;
    let dirListCache = window.dirListCache || [];

    function updateSuggest() {
        const val = input.value;
        let lastSlash = val.lastIndexOf('/');
        let prefix = lastSlash >= 0 ? val.slice(lastSlash + 1) : val;
        let base = lastSlash >= 0 ? val.slice(0, lastSlash) : '';
        filteredDirs = dirListCache.filter(name => name.startsWith(prefix));
        suggestList.innerHTML = '';
        if (filteredDirs.length > 0 && prefix.length > 0) {
            suggestList.style.display = '';
            filteredDirs.forEach((name, idx) => {
                const li = document.createElement('li');
                li.className = 'custom-suggest-item' + (idx === activeIdx ? ' active' : '');
                li.textContent = (base ? base : '') + '/' + name;
                li.onclick = () => {
                    input.value = (base ? base : '') + '/' + name;
                    suggestList.style.display = 'none';
                    fetchSubDirs(input.value);
                };
                li.onmouseenter = () => {
                    activeIdx = idx;
                    updateSuggest();
                };
                suggestList.appendChild(li);
            });
        } else {
            suggestList.style.display = 'none';
        }
    }

    function fetchSubDirs(path) {
        import('./file.js').then(module => {
            module.fetchFileList(path, false);
        });
    }

    input.addEventListener('input', function() {
        activeIdx = -1;
        updateSuggest();
    });
    input.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowDown') {
            if (filteredDirs.length > 0) {
                activeIdx = (activeIdx + 1) % filteredDirs.length;
                updateSuggest();
            }
        } else if (e.key === 'ArrowUp') {
            if (filteredDirs.length > 0) {
                activeIdx = (activeIdx - 1 + filteredDirs.length) % filteredDirs.length;
                updateSuggest();
            }
        } else if (e.key === 'Tab') {
            if (filteredDirs.length > 0) {
                e.preventDefault();
                let lastSlash = input.value.lastIndexOf('/');
                let base = lastSlash >= 0 ? input.value.slice(0, lastSlash) : '';
                input.value = (base ? base : '') + '/' + filteredDirs[activeIdx >= 0 ? activeIdx : 0];
                suggestList.style.display = 'none';
                fetchSubDirs(input.value);
            }
        } else if (e.key === 'Enter') {
            if (activeIdx >= 0 && filteredDirs.length > 0) {
                let lastSlash = input.value.lastIndexOf('/');
                let base = lastSlash >= 0 ? input.value.slice(0, lastSlash) : '';
                input.value = (base ? base : '') + '/' + filteredDirs[activeIdx];
                suggestList.style.display = 'none';
                fetchSubDirs(input.value);
            } else {
                import('./file.js').then(module => {
                    module.fetchFileList(input.value, true);
                });
            }
        } else if (e.key === 'Escape') {
            import('./ui.js').then(module => {
                module.renderCurrentPath();
            });
        } else {
            activeIdx = -1;
        }
    });
    setTimeout(() => {
        document.addEventListener('mousedown', onClickOutside);
    }, 0);
    function onClickOutside(e) {
        if (e.target !== input && !suggestList.contains(e.target)) {
            document.removeEventListener('mousedown', onClickOutside);
            import('./ui.js').then(module => {
                module.renderCurrentPath();
            });
        }
    }
    input.addEventListener('blur', function() {
        setTimeout(() => {
            import('./ui.js').then(module => {
                module.renderCurrentPath();
            });
        }, 100);
    });
    updateSuggest();
}

// 其余UI渲染函数可继续拆分导出 