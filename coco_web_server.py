#!/usr/bin/env python3
"""
TRS-80 Color Computer DSK Web Server
Coded by ChipShift Reyco2000@gmail.com Using Claude Code
(C) 2025

Web interface for managing DSK/JVC disk images on port 6809
"""

from flask import Flask, render_template, request, jsonify, send_file, session
import os
import tempfile
import secrets
from werkzeug.utils import secure_filename
from coco_dsk import DSKImage
import io

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Store mounted DSK images per session
UPLOAD_FOLDER = tempfile.gettempdir()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Session storage for DSK instances
mounted_dsks = {}


def get_session_dsk():
    """Get the DSKImage for current session"""
    session_id = session.get('dsk_id')
    if session_id and session_id in mounted_dsks:
        return mounted_dsks[session_id]
    return None


def set_session_dsk(dsk_image, filename):
    """Set the DSKImage for current session"""
    session_id = secrets.token_hex(16)
    session['dsk_id'] = session_id
    session['dsk_filename'] = filename
    session['dsk_modified'] = False
    mounted_dsks[session_id] = dsk_image


def clear_session_dsk():
    """Clear the DSKImage for current session"""
    session_id = session.get('dsk_id')
    if session_id and session_id in mounted_dsks:
        del mounted_dsks[session_id]
    session.pop('dsk_id', None)
    session.pop('dsk_filename', None)
    session.pop('dsk_modified', None)


def mark_modified():
    """Mark current DSK as modified"""
    session['dsk_modified'] = True


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/mount', methods=['POST'])
def mount_dsk():
    """Mount a DSK file uploaded by user"""
    if 'dsk_file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['dsk_file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    try:
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f'dsk_{secrets.token_hex(8)}_{filename}')
        file.save(temp_path)

        # Mount the DSK
        dsk = DSKImage(temp_path)
        if not dsk.mount():
            os.remove(temp_path)
            return jsonify({'success': False, 'error': 'Failed to mount DSK image'}), 400

        # Store in session
        set_session_dsk(dsk, filename)

        return jsonify({
            'success': True,
            'filename': filename,
            'file_count': len(dsk.directory)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/list', methods=['GET'])
def list_files():
    """List files in mounted DSK"""
    dsk = get_session_dsk()
    if not dsk:
        return jsonify({'success': False, 'error': 'No DSK mounted'}), 400

    try:
        files = []
        for entry in dsk.directory:
            file_type_names = {
                0x00: "BASIC",
                0x01: "DATA",
                0x02: "ML",
                0x03: "TEXT"
            }
            type_name = file_type_names.get(entry.file_type, f"UNK({entry.file_type:02X})")
            ascii_str = "ASCII" if entry.ascii_flag == 0xFF else "BIN"
            full_name = f"{entry.filename}.{entry.extension}" if entry.extension else entry.filename

            # Calculate file size
            chain = dsk._get_granule_chain(entry.first_granule)
            total_sectors = sum(sectors for _, sectors in chain)
            file_size = (total_sectors - 1) * dsk.SECTOR_SIZE + entry.last_sector_bytes if entry.last_sector_bytes > 0 else total_sectors * dsk.SECTOR_SIZE

            files.append({
                'name': full_name,
                'type': type_name,
                'mode': ascii_str,
                'granule': entry.first_granule,
                'size': file_size
            })

        # Calculate free space
        free_granules = sum(1 for g in dsk.fat if g == 0xFF)
        free_bytes = free_granules * dsk.GRANULE_SIZE

        return jsonify({
            'success': True,
            'files': files,
            'free_granules': free_granules,
            'free_bytes': free_bytes,
            'dsk_filename': session.get('dsk_filename', 'unknown'),
            'modified': session.get('dsk_modified', False)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download a file from the mounted DSK"""
    dsk = get_session_dsk()
    if not dsk:
        return jsonify({'success': False, 'error': 'No DSK mounted'}), 400

    try:
        # Find the file
        entry = None
        for e in dsk.directory:
            full_name = f"{e.filename}.{e.extension}" if e.extension else e.filename
            if full_name == filename:
                entry = e
                break

        if not entry:
            return jsonify({'success': False, 'error': f'File {filename} not found'}), 404

        # Extract file data
        file_data = dsk.extract_file(entry)

        # Send as download
        return send_file(
            io.BytesIO(file_data),
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload a file to the mounted DSK"""
    dsk = get_session_dsk()
    if not dsk:
        return jsonify({'success': False, 'error': 'No DSK mounted'}), 400

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    try:
        # Get parameters
        dsk_name = request.form.get('dsk_name', '').upper()
        if not dsk_name:
            dsk_name = secure_filename(file.filename).upper()

        file_type_map = {
            'basic': 0x00,
            'data': 0x01,
            'ml': 0x02,
            'text': 0x03
        }
        file_type = file_type_map.get(request.form.get('file_type', 'ml').lower(), 0x02)
        ascii_flag = 0xFF if request.form.get('ascii_mode') == 'true' else 0x00

        # Save file temporarily
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f'upload_{secrets.token_hex(8)}_{secure_filename(file.filename)}')
        file.save(temp_path)

        # Upload to DSK
        success = dsk.upload_from_pc(temp_path, dsk_name, file_type, ascii_flag)

        # Clean up temp file
        os.remove(temp_path)

        if success:
            mark_modified()
            return jsonify({'success': True, 'message': f'File uploaded as {dsk_name}'})
        else:
            return jsonify({'success': False, 'error': 'Failed to upload file to DSK'}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a file from the mounted DSK"""
    dsk = get_session_dsk()
    if not dsk:
        return jsonify({'success': False, 'error': 'No DSK mounted'}), 400

    try:
        if dsk.delete_file(filename):
            mark_modified()
            return jsonify({'success': True, 'message': f'File {filename} deleted'})
        else:
            return jsonify({'success': False, 'error': 'Failed to delete file'}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/format', methods=['POST'])
def format_dsk():
    """Format a new DSK image"""
    try:
        data = request.get_json()
        tracks = int(data.get('tracks', 35))
        sides = int(data.get('sides', 1))
        add_jvc = data.get('add_jvc', False)

        # Create temp file for new DSK
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f'formatted_{secrets.token_hex(8)}.dsk')

        # Format the disk
        dsk = DSKImage.format_disk(temp_path, tracks=tracks, sectors_per_track=18, sides=sides, add_jvc_header=add_jvc)

        # Mount the new disk
        dsk.mount()

        # Store in session
        filename = f'formatted_{tracks}t_{sides}s.dsk'
        set_session_dsk(dsk, filename)
        mark_modified()

        return jsonify({
            'success': True,
            'message': f'Created new {tracks}T/{sides}S DSK image',
            'filename': filename
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/download-dsk', methods=['GET'])
def download_dsk():
    """Download the current DSK image"""
    dsk = get_session_dsk()
    if not dsk:
        return jsonify({'success': False, 'error': 'No DSK mounted'}), 400

    try:
        filename = session.get('dsk_filename', 'disk.dsk')

        # Send DSK data
        return send_file(
            io.BytesIO(dsk.data),
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/unmount', methods=['POST'])
def unmount_dsk():
    """Unmount the current DSK"""
    dsk = get_session_dsk()
    if not dsk:
        return jsonify({'success': False, 'error': 'No DSK mounted'}), 400

    try:
        # Clean up temp file if it exists
        if os.path.exists(dsk.filename):
            try:
                os.remove(dsk.filename)
            except:
                pass  # Ignore errors on cleanup

        clear_session_dsk()

        return jsonify({'success': True, 'message': 'DSK unmounted'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def status():
    """Get current mount status"""
    dsk = get_session_dsk()

    if dsk:
        return jsonify({
            'mounted': True,
            'filename': session.get('dsk_filename', 'unknown'),
            'modified': session.get('dsk_modified', False),
            'file_count': len(dsk.directory)
        })
    else:
        return jsonify({
            'mounted': False
        })


if __name__ == '__main__':
    print("=" * 60)
    print("TRS-80 Color Computer DSK Web Server")
    print("=" * 60)
    print(f"Starting server on http://localhost:6809")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    app.run(host='0.0.0.0', port=6809, debug=True)
