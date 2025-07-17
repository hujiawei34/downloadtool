import { renderFileList, renderCurrentPath } from './ui.js';
// 文件操作相关逻辑
export let currentPath = null;
export let dirListCache = [];

export function fetchFileList(path = null, save = true, remote = false) {
    if (path === null) {
        if (remote && save && localStorage.getItem('lastPath')) {
            path = localStorage.getItem('lastPath');
        } else {
            path = currentPath || '/';
        }
    }
    let url = '/api/list?path=' + encodeURIComponent(path);
    if (remote) url += '&mode=remote';
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

// 上传文件
export function uploadFiles() {
    const input = document.getElementById('file-upload');
    const files = input.files;
    if (!files.length) {
        alert('请选择文件');
        return;
    }
    const path = currentPath || '/';
    for (let i = 0; i < files.length; i++) {
        const formData = new FormData();
        formData.append('file', files[i]);
        fetch(`/api/upload?path=${encodeURIComponent(path)}&mode=remote`, {
            method: 'POST',
            body: formData
        }).then(res => {
            if (res.status === 409) {
                return res.json().then(data => { alert('文件已存在: ' + files[i].name); });
            }
            return res.json();
        }).then(() => {
            fetchFileList(path, true, true);
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
    for (let i = 0; i < files.length; i++) {
        const formData = new FormData();
        formData.append('file', files[i], files[i].webkitRelativePath || files[i].name);
        fetch(`/api/upload?path=${encodeURIComponent(path)}&mode=remote`, {
            method: 'POST',
            body: formData
        }).then(res => {
            if (res.status === 409) {
                return res.json().then(data => { alert('文件已存在: ' + files[i].name); });
            }
            return res.json();
        }).then(() => {
            fetchFileList(path, true, true);
        }).catch(err => {
            console.error('上传失败:', err);
            alert('上传失败');
        });
    }
}

// 其余文件操作函数（如上传、删除）可继续拆分导出 