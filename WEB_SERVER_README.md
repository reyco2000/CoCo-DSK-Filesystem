# CoCo Web Commander - Web Interface for DSK Management

A web-based interface for managing TRS-80 Color Computer DSK/JVC disk images, running on port 6809 (named after the 6809 CPU used in the CoCo!).

## Features

The web interface provides all the features of the TUI version:

- **Dual-Pane File Manager**: Browse PC files (left) and DSK image files (right)
- **DSK Operations**:
  - Load and mount DSK/JVC images
  - Format new DSK images (35/40/80 tracks, 1-2 sides)
  - View disk statistics and file information
- **File Operations**:
  - View files in hex/ASCII format
  - Copy files between PC and DSK
  - Delete files (PC or DSK)
  - Rename files in DSK
  - Upload files to PC directory
- **BASIC Support**:
  - Automatic BASIC file detection
  - Optional detokenization when copying from DSK to PC
  - Converts tokenized BASIC to readable text

## Installation

1. Install Python 3.7 or higher
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install Flask flask-cors
```

## Usage

### Local Development (Default)

For local use only:

```bash
python coco_web_server.py
```

Then open your browser to: http://localhost:6809

### Running on a Public Server

**⚠️ SECURITY WARNING**: The default configuration is NOT secure for public deployment!

Before deploying to a public server, you MUST:

1. **Add Authentication**: Implement user authentication and session management
2. **Configure Path Restrictions**: Limit filesystem access to specific directories
3. **Use HTTPS**: Deploy behind a reverse proxy with SSL/TLS (nginx, Apache, Caddy)
4. **Add Rate Limiting**: Prevent abuse and DoS attacks
5. **Set File Size Limits**: Already configured (16MB max), adjust as needed
6. **Disable Debug Mode**: Set `debug=False` in production
7. **Use a Production WSGI Server**: Replace Flask's dev server with gunicorn or uwsgi

### Example: Production Deployment with Gunicorn

1. Install gunicorn:
```bash
pip install gunicorn
```

2. Run with gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:6809 coco_web_server:app
```

3. Configure nginx as reverse proxy:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";

    location / {
        proxy_pass http://127.0.0.1:6809;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Security Considerations for Public Deployment

### Current Security Limitations

The default configuration has these security concerns:

1. **No Authentication**: Anyone can access the server
2. **Full Filesystem Access**: Users can browse the entire filesystem
3. **File Upload**: Unrestricted file uploads to current directory
4. **No Session Management**: No user sessions or access control
5. **Debug Mode**: Flask debug mode is enabled by default
6. **No HTTPS**: Unencrypted communication

### Recommended Security Enhancements

#### 1. Add Authentication

Add Flask-Login or similar:

```python
from flask_login import LoginManager, login_required

# Protect all routes with @login_required decorator
@app.route('/api/pc/browse', methods=['POST'])
@login_required
def browse_pc():
    # ... existing code
```

#### 2. Restrict Filesystem Access

Modify the path handling to restrict to a specific directory:

```python
import os

# Set allowed base directory
ALLOWED_BASE_DIR = Path('/home/coco/dsk_files').resolve()

def is_safe_path(path):
    """Check if path is within allowed directory"""
    resolved = Path(path).resolve()
    try:
        resolved.relative_to(ALLOWED_BASE_DIR)
        return True
    except ValueError:
        return False

@app.route('/api/pc/browse', methods=['POST'])
def browse_pc():
    path = Path(path_str).resolve()

    if not is_safe_path(path):
        return jsonify({'error': 'Access denied'}), 403

    # ... rest of code
```

#### 3. Add Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route('/api/file/upload', methods=['POST'])
@limiter.limit("10 per hour")
def upload_file():
    # ... existing code
```

#### 4. Input Validation

Add strict validation for all inputs:

```python
import re

def validate_filename(filename):
    """Validate DSK filename format"""
    # Only allow alphanumeric, dots, and hyphens
    if not re.match(r'^[a-zA-Z0-9._-]+$', filename):
        raise ValueError('Invalid filename')
    return filename

def validate_dsk_name(name):
    """Validate 8.3 format"""
    if '.' in name:
        base, ext = name.rsplit('.', 1)
        if len(base) > 8 or len(ext) > 3:
            raise ValueError('Invalid 8.3 format')
    elif len(name) > 8:
        raise ValueError('Filename too long')
    return name
```

#### 5. Content Security Policy

Add CSP headers:

```python
@app.after_request
def set_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

## API Endpoints

### PC Filesystem
- `POST /api/pc/browse` - Browse PC directory
- `POST /api/pc/navigate` - Navigate to directory or get file info

### DSK Operations
- `POST /api/dsk/load` - Load a DSK image
- `GET /api/dsk/info` - Get loaded DSK information
- `POST /api/dsk/format` - Format new DSK image

### File Operations
- `POST /api/file/view` - View file contents (hex/ASCII)
- `POST /api/file/copy` - Copy file between PC and DSK
- `POST /api/file/delete` - Delete a file
- `POST /api/file/rename` - Rename DSK file
- `POST /api/file/upload` - Upload file to PC directory
- `GET /api/file/download/<filename>` - Download file from PC

### System
- `GET /api/system/info` - Get system information

## Keyboard Shortcuts

- **TAB**: Switch between panels
- **↑/↓**: Navigate file list
- **ENTER**: Navigate directory or load DSK
- **F2**: Show file/disk information
- **F3**: View file contents
- **F5**: Copy file
- **F6**: Rename file (DSK only)
- **F7**: Format new DSK
- **F8**: Delete file
- **F9**: Upload file to PC

## Browser Compatibility

Tested and working on:
- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Troubleshooting

### Port 6809 already in use

Change the port in `coco_web_server.py`:

```python
app.run(host='0.0.0.0', port=8080, debug=True)  # Use port 8080 instead
```

### Cannot access from other devices

Make sure:
1. Firewall allows port 6809
2. Server is bound to `0.0.0.0` not `127.0.0.1`
3. For production, use proper reverse proxy with HTTPS

### File upload fails

Check:
1. File size under 16MB limit
2. Disk space available
3. Write permissions on target directory

## Development

To modify the interface:

1. Edit `templates/index.html` for frontend changes
2. Edit `coco_web_server.py` for backend/API changes
3. Restart the server to see changes (or use `debug=True` for auto-reload)

## License

(C) 2025 ChipShift - CoCoByte Club

## Credits

Created by ChipShift (Reyco2000@gmail.com) using Claude Code

Based on the CoCo Commander TUI and CoCo DSK library.

---

**Remember**: This is a powerful tool that provides filesystem access. Always run it in a controlled environment and implement proper security measures for public deployment!
