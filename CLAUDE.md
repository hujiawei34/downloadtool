# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Virtual Environment Setup
```bash
# Create virtual environment (if not exists)
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate.bat  # Windows

# Install dependencies
pip install -r src/python/requirements.txt
```

### Running the Application
```bash
# Start the Flask server
cd src/python
python app.py

# Or use the provided Windows batch file
./start.bat
```

### Testing
No formal test suite is configured. Manual testing is done by:
1. Starting the Flask server on port 18023
2. Accessing the web interface at http://localhost:18023
3. Testing file operations (upload, download, delete, browse)

## Architecture

This is a Flask-based file management web application with the following structure:

### Backend (Python/Flask)
- **app.py**: Main Flask application with dual-mode file operations (local and remote SFTP)
- **file_api.py**: Core file operations (list, download, upload, delete) for local files
- **log_util.py**: Logging utilities for operation tracking
- **config.json**: Configuration for server settings and remote SFTP connections

### Frontend (HTML/CSS/JavaScript)
- **templates/index.html**: Main web interface
- **static/**: JavaScript modules for different functionalities
  - **main.js**: Entry point and event setup
  - **server.js**: Server connection management
  - **file.js**: File operations handling
  - **ui.js**: User interface interactions
  - **utils.js**: Utility functions

### Key Features
- **Dual Mode Operation**: Supports both local filesystem and remote SFTP server file management
- **File Operations**: Browse, download, upload (files and folders), delete
- **SFTP Support**: Connects to remote servers via SSH/SFTP with password or key authentication
- **Configuration**: JSON-based configuration for server settings and default directories
- **Logging**: Operation logging to track file activities

### Configuration
The application uses `config.json` to define:
- Server port (default: 18023)
- Remote SFTP server configurations
- Default directories for local and remote operations

### Dependencies
- Flask: Web framework
- Flask-CORS: Cross-origin resource sharing
- paramiko: SSH/SFTP client for remote operations