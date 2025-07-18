import { renderFileList, renderCurrentPath } from './ui.js';
// 文件操作相关逻辑
export let currentPath = null;
export let dirListCache = [];

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
    
    let url = '/api/list?path=' + encodeURIComponent(path);
    if (isRemote) {
        url += '&mode=remote';
    } else {
        url += '&mode=local';
    }
    
    fetch(url)
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            currentPath = data.path;
            window.currentPath = currentPath;
            if (save) localStorage.setItem('lastPath', currentPath);
            dirListCache = data.dirs.map(d => d.name);
            renderFileList(data);
            renderCurrentPath();
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

// 其余文件操作函数（如上传、删除）可继续拆分导出 