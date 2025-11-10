#!/usr/bin/env python3
"""
Apple II Disk Image Web Manager
Coded by ChipShift Reyco2000@gmail.com Using Claude Code
(C) 2025

Web interface for managing Apple II disk images on port 6502
Uses diskii tool (https://github.com/zellyn/diskii)
"""

from flask import Flask, render_template, request, jsonify, send_file, session
import os
import tempfile
import secrets
import subprocess
import json
import re
from werkzeug.utils import secure_filename
import io

app = Flask(__name__, template_folder='apple_templates')
app.secret_key = secrets.token_hex(16)

# Store mounted disk images per session
UPLOAD_FOLDER = tempfile.gettempdir()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Session storage for disk image paths
mounted_disks = {}

# Path to diskii executable
DISKII_PATH = os.path.expanduser("~/go/bin/diskii")


def get_session_disk():
    """Get the disk image path for current session"""
    session_id = session.get('disk_id')
    if session_id and session_id in mounted_disks:
        return mounted_disks[session_id]
    return None


def set_session_disk(disk_path, filename):
    """Set the disk image for current session"""
    session_id = secrets.token_hex(16)
    session['disk_id'] = session_id
    session['disk_filename'] = filename
    session['disk_modified'] = False
    mounted_disks[session_id] = disk_path


def clear_session_disk():
    """Clear the disk image for current session"""
    session_id = session.get('disk_id')
    if session_id and session_id in mounted_disks:
        disk_path = mounted_disks[session_id]
        # Clean up temp file
        if os.path.exists(disk_path):
            try:
                os.remove(disk_path)
            except:
                pass
        del mounted_disks[session_id]
    session.pop('disk_id', None)
    session.pop('disk_filename', None)
    session.pop('disk_modified', None)


def run_diskii(args):
    """Run diskii command and return output"""
    cmd = [DISKII_PATH] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode


def parse_ls_output(output):
    """Parse diskii ls output into structured data"""
    files = []
    lines = output.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line or line.startswith('Warning'):
            continue

        # Parse the line - format varies by filesystem
        # DOS 3.3 format: * FILENAME    T.SSS
        # ProDOS format: FILENAME    TYPE  BLOCKS
        parts = line.split()
        if len(parts) >= 2:
            locked = parts[0] == '*'
            if locked:
                parts = parts[1:]

            if len(parts) >= 1:
                filename = parts[0]
                file_type = parts[1] if len(parts) > 1 else 'unknown'
                size_info = parts[2] if len(parts) > 2 else '0'

                files.append({
                    'name': filename,
                    'type': file_type,
                    'size': size_info,
                    'locked': locked
                })

    return files


@app.route('/')
def index():
    """Main page"""
    return render_template('apple_index.html')


@app.route('/api/mount', methods=['POST'])
def mount_disk():
    """Mount a disk image uploaded by user"""
    if 'disk_file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['disk_file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    try:
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f'apple_{secrets.token_hex(8)}_{filename}')
        file.save(temp_path)

        # Try to list files to verify it's a valid disk image
        output, error, returncode = run_diskii(['ls', temp_path])

        if returncode != 0:
            os.remove(temp_path)
            return jsonify({'success': False, 'error': f'Failed to mount disk image: {error}'}), 400

        files = parse_ls_output(output)

        # Store in session
        set_session_disk(temp_path, filename)

        return jsonify({
            'success': True,
            'filename': filename,
            'file_count': len(files)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/list', methods=['GET'])
def list_files():
    """List files in mounted disk"""
    disk_path = get_session_disk()
    if not disk_path:
        return jsonify({'success': False, 'error': 'No disk mounted'}), 400

    try:
        output, error, returncode = run_diskii(['ls', disk_path])

        if returncode != 0:
            return jsonify({'success': False, 'error': f'Failed to list files: {error}'}), 500

        files = parse_ls_output(output)

        # Calculate disk size
        disk_size = os.path.getsize(disk_path) if os.path.exists(disk_path) else 0

        return jsonify({
            'success': True,
            'files': files,
            'disk_size': disk_size,
            'disk_filename': session.get('disk_filename', 'unknown'),
            'modified': session.get('disk_modified', False)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download a file from the mounted disk"""
    disk_path = get_session_disk()
    if not disk_path:
        return jsonify({'success': False, 'error': 'No disk mounted'}), 400

    try:
        # Use diskii dump to extract file
        output, error, returncode = run_diskii(['dump', disk_path, filename])

        if returncode != 0:
            return jsonify({'success': False, 'error': f'Failed to extract file: {error}'}), 404

        # Send as download
        return send_file(
            io.BytesIO(output.encode('latin-1')),  # diskii outputs raw bytes
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/download-disk', methods=['GET'])
def download_disk():
    """Download the current disk image"""
    disk_path = get_session_disk()
    if not disk_path:
        return jsonify({'success': False, 'error': 'No disk mounted'}), 400

    try:
        filename = session.get('disk_filename', 'disk.dsk')

        # Send disk image
        return send_file(
            disk_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/unmount', methods=['POST'])
def unmount_disk():
    """Unmount the current disk"""
    disk_path = get_session_disk()
    if not disk_path:
        return jsonify({'success': False, 'error': 'No disk mounted'}), 400

    try:
        clear_session_disk()
        return jsonify({'success': True, 'message': 'Disk unmounted'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def status():
    """Get current mount status"""
    disk_path = get_session_disk()

    if disk_path:
        return jsonify({
            'mounted': True,
            'filename': session.get('disk_filename', 'unknown'),
            'modified': session.get('disk_modified', False)
        })
    else:
        return jsonify({
            'mounted': False
        })


if __name__ == '__main__':
    print("=" * 60)
    print("Apple II Disk Image Web Manager")
    print("=" * 60)
    print(f"Starting server on http://localhost:6502")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    app.run(host='0.0.0.0', port=6502, debug=True)
