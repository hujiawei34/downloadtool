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
The project includes a comprehensive unit test suite using pytest:

```bash
# Install testing dependencies
pip install -r src/python/requirements.txt

# Run all tests
cd src/python
python run_tests.py

# Run specific test file
python run_tests.py test_app.py
python run_tests.py test_local_file_service.py
python run_tests.py test_remote_file_service.py

# Run tests with pytest directly
python -m pytest tests/ -v
```

#### Test Coverage
- **API Endpoints**: All Flask routes (`/`, `/files`, `/api/*`)
- **LocalFileService**: File operations, directory listing, upload/download
- **RemoteFileService**: SFTP operations, connectivity, authentication
- **Error Handling**: Network errors, permission issues, invalid inputs
- **Edge Cases**: Empty directories, nested paths, missing files

#### Manual Testing
Additional manual testing can be done by:
1. Starting the Flask server on port 18023
2. Accessing the web interface at http://localhost:18023
3. Testing file operations (upload, download, delete, browse)

## Architecture

This is a Flask-based file management web application with the following structure:

### Backend (Python/Flask)
- **app.py**: Main Flask application with dual-mode file operations (local and remote SFTP)
- **service/**: Service layer with abstract interface and implementations
  - **file_service.py**: Abstract base class defining the file service interface
  - **impl/local_file_service.py**: Local filesystem operations implementation
  - **impl/remote_file_service.py**: Remote SFTP operations implementation
- **utils/**: Utility modules
  - **constants.py**: Project constants and path definitions
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
- **Service Layer Architecture**: Abstract interface with concrete implementations for local and remote operations
- **File Operations**: Browse, download, upload (files and folders), delete
- **SFTP Support**: Connects to remote servers via SSH/SFTP with password or key authentication
- **Configuration**: JSON-based configuration for server settings and default directories
- **Logging**: Operation logging to track file activities
- **Path Management**: Centralized path constants and utilities

### Configuration
The application uses `config.json` to define:
- Server port (default: 18023)
- Remote SFTP server configurations
- Default directories for local and remote operations

### Dependencies
- Flask: Web framework
- Flask-CORS: Cross-origin resource sharing
- paramiko: SSH/SFTP client for remote operations

### Code Structure Changes
The codebase has been refactored from a monolithic approach to a service-oriented architecture:

1. **Service Layer**: Introduced abstract `FileService` interface with concrete implementations
2. **Separation of Concerns**: Local and remote file operations are now in separate service classes
3. **Constants Management**: Centralized path and configuration constants in `utils/constants.py`
4. **Improved Logging**: Enhanced logging with service-specific log messages
5. **Removed Files**: `file_api.py` has been removed and its functionality integrated into the service layer