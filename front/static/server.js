// 服务器选择与连接相关逻辑
export let selectedServer = null;
export let serverList = [];

export function loadServerList(autoConnect = false) {
    fetch('/api/remote_servers').then(res => res.json()).then(data => {
        serverList = data.remote_server_list || [];
        const select = document.getElementById('server-list');
        select.innerHTML = '';
        serverList.forEach((srv, idx) => {
            const option = document.createElement('option');
            option.value = idx;
            option.textContent = srv.server_name || (srv.config && srv.config.host_ip) || '未命名服务器';
            select.appendChild(option);
        });
        if (serverList.length > 0) {
            select.selectedIndex = 0;
            selectedServer = serverList[0];
            if (autoConnect) {
                // 自动连接第一个服务器
                const pwd = selectedServer.config.user_pwd || '';
                const config = Object.assign({}, selectedServer.config, {user_pwd: pwd});
                document.getElementById('connect-status').textContent = '自动连接中...';
                fetch('/api/test_server_connectivity', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(config)
                }).then(res => res.json()).then(data => {
                    if (data.success) {
                        fetch('/api/save_server_pwd', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({server_name: selectedServer.server_name, user_pwd: pwd})
                        });
                        document.getElementById('connect-status').textContent = '连接成功！';
                        document.getElementById('server-select-container').style.display = 'none';
                        document.getElementById('main-ui').style.display = '';
                        fetch('/api/default_dir?mode=remote')
                            .then(res => res.json())
                            .then(data => {
                                import('./file.js').then(module => {
                                    module.fetchFileList(null, true, true);
                                });
                            });
                    } else {
                        document.getElementById('connect-status').textContent = '自动连接失败: ' + (data.error || '未知错误');
                    }
                });
            }
        }
    }).catch(err => {
        console.error('加载服务器列表失败:', err);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    localStorage.removeItem('lastPath');
    loadServerList(true);
    document.getElementById('server-list').addEventListener('change', function() {
        selectedServer = serverList[this.value];
    });
    document.getElementById('test-connect-btn').addEventListener('click', function() {
        const pwd = document.getElementById('server-password').value;
        if (!selectedServer) return;
        const config = Object.assign({}, selectedServer.config, {user_pwd: pwd});
        document.getElementById('connect-status').textContent = '测试中...';
        fetch('/api/test_server_connectivity', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(config)
        }).then(res => res.json()).then(data => {
            if (data.success) {
                fetch('/api/save_server_pwd', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({server_name: selectedServer.server_name, user_pwd: pwd})
                });
                document.getElementById('connect-status').textContent = '连接成功！';
                document.getElementById('server-select-container').style.display = 'none';
                document.getElementById('main-ui').style.display = '';
                fetch('/api/default_dir?mode=remote')
                    .then(res => {
                        if (!res.ok) {
                            throw new Error('获取默认目录失败');
                        }
                        return res.json();
                    })
                    .then(data => {
                        if (data.error) {
                            console.warn('默认目录警告:', data.error);
                        }
                        import('./file.js').then(module => {
                            module.fetchFileList(null, true, true);
                        }).catch(err => {
                            console.error('加载file.js失败:', err);
                        });
                    })
                    .catch(err => {
                        console.error('获取默认目录失败:', err);
                        import('./file.js').then(module => {
                            module.fetchFileList('~', false, true);
                        }).catch(err => {
                            console.error('加载file.js失败:', err);
                        });
                    });
            } else {
                document.getElementById('connect-status').textContent = '连接失败: ' + (data.error || '未知错误');
            }
        }).catch(err => {
            document.getElementById('connect-status').textContent = '连接失败: ' + err.message;
        });
    });
    document.getElementById('disconnect-btn').addEventListener('click', function() {
        document.getElementById('main-ui').style.display = 'none';
        document.getElementById('server-select-container').style.display = '';
        document.getElementById('server-password').value = '';
        document.getElementById('connect-status').textContent = '';
        selectedServer = null;
        localStorage.removeItem('lastPath');
    });
}); 