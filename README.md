# Download Tool

## 目录结构

```
tool/download-tool/
  src/python/         # 后端Flask服务
    app.py            # 主程序
    requirements.txt  # 依赖
  front/              # 前端页面
    templates/
      index.html      # 主页面
    static/
      main.js         # 前端JS
      style.css       # 样式
```

## 功能说明
- 列出服务器当前目录下的文件和文件夹，表格显示文件名、大小、修改日期，行明暗交错
- 点击文件名可直接下载文件
- 上传按钮支持上传文件/文件夹，若同名提示是否覆盖
- 浏览器标题显示当前路径
- 服务启动在18023端口

## 启动方法

### 1. 安装依赖
```bash
cd tool/download-tool/src/python
pip install -r requirements.txt
```

### 2. 启动后端服务
```bash
python app.py
```

### 3. 访问前端页面
浏览器访问：http://服务器IP:18023

## 备注
- 前端和后端已分离，便于维护和扩展
- 文件列表样式参考了 downloadweb.jpg 