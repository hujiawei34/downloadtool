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
                        
                        // 保存模式和服务器信息到localStorage
                        localStorage.setItem('fileMode', 'remote');
                        localStorage.setItem('selectedServer', JSON.stringify(selectedServer));
                        
                        // 跳转到文件管理页面
                        window.location.href = '/files';
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
    // 加载远程服务器列表
    loadServerList();
    document.getElementById('server-list').addEventListener('change', function() {
        selectedServer = serverList[this.value];
    });
    document.getElementById('use-local-btn').addEventListener('click', function() {
        // 保存模式到localStorage
        localStorage.setItem('fileMode', 'local');
        
        // 跳转到文件管理页面
        window.location.href = '/files';
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
                
                // 保存模式和服务器信息到localStorage
                localStorage.setItem('fileMode', 'remote');
                localStorage.setItem('selectedServer', JSON.stringify(selectedServer));
                
                // 跳转到文件管理页面
                window.location.href = '/files';
            } else {
                document.getElementById('connect-status').textContent = '连接失败: ' + (data.error || '未知错误');
            }
        }).catch(err => {
            document.getElementById('connect-status').textContent = '连接失败: ' + err.message;
        });
    });
    // 在files.html页面中使用的返回按钮处理
    if (document.getElementById('back-to-server-btn')) {
        document.getElementById('back-to-server-btn').addEventListener('click', function() {
            // 清除保存的模式和路径
            localStorage.removeItem('fileMode');
            localStorage.removeItem('selectedServer');
            localStorage.removeItem('lastPath');
            
            // 跳转回服务器选择页面
            window.location.href = '/';
        });
    }
});