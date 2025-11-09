#!/usr/bin/env python3
"""
CoCo Web Commander - Web interface for TRS-80 Color Computer DSK Files

Coded by ChipShift Reyco2000@gmail.com Using Claude Code
(C) 2025

A web-based dual-pane file manager for working with CoCo DSK/JVC disk images.
Runs on port 6809 (the 6809 CPU used in the CoCo!).
"""

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict
import base64
import tempfile
from werkzeug.utils import secure_filename

# Import CoCo DSK libraries
sys.path.insert(0, str(Path(__file__).parent))
from coco_dsk import DSKImage, DirectoryEntry

try:
    from coco_detokenizer import detokenize_file
    DETOKENIZER_AVAILABLE = True
except ImportError:
    DETOKENIZER_AVAILABLE = False

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Global state for currently loaded DSK
current_dsk: Optional[DSKImage] = None
current_dsk_path: Optional[Path] = None
current_pc_path: Path = Path.cwd()


@app.route('/')
def index():
    """Serve the main interface"""
    return render_template('index.html')


@app.route('/api/pc/browse', methods=['POST'])
def browse_pc():
    """Browse PC filesystem"""
    global current_pc_path

    data = request.json or {}
    path_str = data.get('path', str(current_pc_path))

    try:
        path = Path(path_str).resolve()

        # Security: prevent browsing outside allowed areas
        # You may want to restrict this further for production
        if not path.exists():
            return jsonify({'error': 'Path does not exist'}), 400

        current_pc_path = path

        items = []

        # Add parent directory if not at root
        if path.parent != path:
            items.append({
                'name': '..',
                'is_dir': True,
                'size': 0,
                'type': 'dir'
            })

        # List directories first, then files
        entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))

        for entry in entries:
            if entry.name.startswith('.'):
                continue

            is_dir = entry.is_dir()
            size = 0 if is_dir else entry.stat().st_size

            items.append({
                'name': entry.name,
                'is_dir': is_dir,
                'size': size,
                'type': 'dir' if is_dir else 'file'
            })

        return jsonify({
            'path': str(path),
            'items': items
        })

    except PermissionError:
        return jsonify({'error': 'Permission denied'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/pc/navigate', methods=['POST'])
def navigate_pc():
    """Navigate to a directory or return file info"""
    global current_pc_path

    data = request.json
    name = data.get('name')

    if not name:
        return jsonify({'error': 'No name provided'}), 400

    try:
        if name == '..':
            current_pc_path = current_pc_path.parent
        else:
            new_path = current_pc_path / name
            if new_path.is_dir():
                current_pc_path = new_path
            else:
                # Return file info
                return jsonify({
                    'type': 'file',
                    'path': str(new_path),
                    'name': name,
                    'size': new_path.stat().st_size,
                    'is_dsk': new_path.suffix.lower() in ('.dsk', '.jvc')
                })

        return jsonify({
            'type': 'dir',
            'path': str(current_pc_path)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dsk/load', methods=['POST'])
def load_dsk():
    """Load a DSK image"""
    global current_dsk, current_dsk_path

    data = request.json
    dsk_path_str = data.get('path')

    if not dsk_path_str:
        return jsonify({'error': 'No path provided'}), 400

    try:
        dsk_path = Path(dsk_path_str)

        if not dsk_path.exists():
            return jsonify({'error': 'DSK file not found'}), 404

        dsk = DSKImage(str(dsk_path))
        if dsk.mount():
            current_dsk = dsk
            current_dsk_path = dsk_path
            return jsonify({
                'success': True,
                'name': dsk_path.name,
                'path': str(dsk_path)
            })
        else:
            return jsonify({'error': 'Failed to mount DSK'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dsk/info', methods=['GET'])
def dsk_info():
    """Get info about currently loaded DSK"""
    global current_dsk, current_dsk_path

    if not current_dsk:
        return jsonify({'loaded': False})

    try:
        files = []
        for entry in current_dsk.directory:
            full_name = f"{entry.filename}.{entry.extension}" if entry.extension else entry.filename

            # Calculate file size from granule chain
            chain = current_dsk._get_granule_chain(entry.first_granule)
            size = 0
            for granule_num, sectors_used in chain:
                size += sectors_used * current_dsk.SECTOR_SIZE

            # Adjust for last sector bytes
            if entry.last_sector_bytes > 0 and size > 0:
                full_sectors = (size // current_dsk.SECTOR_SIZE) - 1
                size = (full_sectors * current_dsk.SECTOR_SIZE) + entry.last_sector_bytes

            type_names = {0x00: "BASIC", 0x01: "DATA", 0x02: "ML", 0x03: "TEXT"}

            files.append({
                'name': full_name,
                'filename': entry.filename,
                'extension': entry.extension,
                'type': entry.file_type,
                'type_name': type_names.get(entry.file_type, "UNK"),
                'ascii_flag': entry.ascii_flag,
                'mode': 'ASCII' if entry.ascii_flag == 0xFF else 'Binary',
                'size': size,
                'first_granule': entry.first_granule,
                'last_sector_bytes': entry.last_sector_bytes
            })

        free_granules = sum(1 for g in current_dsk.fat if g == 0xFF)
        free_kb = (free_granules * current_dsk.GRANULE_SIZE) / 1024

        return jsonify({
            'loaded': True,
            'name': current_dsk_path.name,
            'path': str(current_dsk_path),
            'files': files,
            'free_granules': free_granules,
            'free_kb': free_kb,
            'total_granules': 68
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dsk/format', methods=['POST'])
def format_dsk():
    """Format a new DSK image"""
    global current_pc_path

    data = request.json
    filename = data.get('filename', 'newdisk.dsk')
    tracks = data.get('tracks', 35)
    sides = data.get('sides', 1)
    add_jvc = data.get('add_jvc', False)

    try:
        dsk_path = current_pc_path / filename
        DSKImage.format_disk(str(dsk_path), tracks=tracks, sides=sides, add_jvc_header=add_jvc)

        total_kb = (tracks * sides * 18 * 256) // 1024

        return jsonify({
            'success': True,
            'path': str(dsk_path),
            'filename': filename,
            'size_kb': total_kb
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/file/view', methods=['POST'])
def view_file():
    """View file contents (PC or DSK)"""
    global current_dsk, current_pc_path

    data = request.json
    source = data.get('source')  # 'pc' or 'dsk'
    filename = data.get('filename')

    try:
        if source == 'pc':
            file_path = current_pc_path / filename
            with open(file_path, 'rb') as f:
                file_data = f.read(8192)  # Read first 8KB
        elif source == 'dsk':
            if not current_dsk:
                return jsonify({'error': 'No DSK loaded'}), 400

            # Find the entry
            entry = None
            for e in current_dsk.directory:
                full_name = f"{e.filename}.{e.extension}" if e.extension else e.filename
                if full_name == filename:
                    entry = e
                    break

            if not entry:
                return jsonify({'error': 'File not found in DSK'}), 404

            file_data = current_dsk.extract_file(entry)
        else:
            return jsonify({'error': 'Invalid source'}), 400

        # Convert to hex/ascii view
        lines = []
        bytes_per_line = 16
        for i in range(0, min(len(file_data), 8192), bytes_per_line):
            line_data = file_data[i:i + bytes_per_line]
            hex_str = ' '.join(f'{b:02X}' for b in line_data)
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in line_data)
            lines.append({
                'offset': i,
                'hex': hex_str,
                'ascii': ascii_str
            })

        return jsonify({
            'filename': filename,
            'size': len(file_data),
            'lines': lines,
            'data_base64': base64.b64encode(file_data[:8192]).decode('utf-8')
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/file/copy', methods=['POST'])
def copy_file():
    """Copy file between PC and DSK"""
    global current_dsk, current_pc_path

    data = request.json
    direction = data.get('direction')  # 'to_dsk' or 'to_pc'

    try:
        if direction == 'to_dsk':
            # Copy PC file to DSK
            if not current_dsk:
                return jsonify({'error': 'No DSK loaded'}), 400

            pc_filename = data.get('pc_filename')
            dsk_filename = data.get('dsk_filename')
            file_type = data.get('file_type', 2)  # Default ML
            ascii_flag = data.get('ascii_flag', 0x00)

            pc_path = current_pc_path / pc_filename

            if current_dsk.upload_from_pc(str(pc_path), dsk_filename, file_type, ascii_flag):
                current_dsk.save()
                return jsonify({'success': True, 'message': f'Uploaded {dsk_filename} to DSK'})
            else:
                return jsonify({'error': 'Upload failed'}), 500

        elif direction == 'to_pc':
            # Copy DSK file to PC
            if not current_dsk:
                return jsonify({'error': 'No DSK loaded'}), 400

            dsk_filename = data.get('dsk_filename')
            pc_filename = data.get('pc_filename')
            detokenize = data.get('detokenize', False)

            pc_path = current_pc_path / pc_filename

            if current_dsk.copy_to_pc(dsk_filename, str(pc_path)):
                # If detokenize was requested, process the file
                if detokenize and DETOKENIZER_AVAILABLE:
                    try:
                        detokenized = detokenize_file(str(pc_path))
                        Path(pc_path).write_text(detokenized, encoding='utf-8')
                        return jsonify({'success': True, 'message': f'Downloaded and detokenized {pc_filename}'})
                    except Exception as e:
                        return jsonify({'success': True, 'message': f'Downloaded but detokenization failed: {e}'})

                return jsonify({'success': True, 'message': f'Downloaded {pc_filename}'})
            else:
                return jsonify({'error': 'Download failed'}), 500
        else:
            return jsonify({'error': 'Invalid direction'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/file/delete', methods=['POST'])
def delete_file():
    """Delete a file (PC or DSK)"""
    global current_dsk, current_pc_path

    data = request.json
    source = data.get('source')  # 'pc' or 'dsk'
    filename = data.get('filename')

    try:
        if source == 'pc':
            file_path = current_pc_path / filename
            if file_path.is_file():
                file_path.unlink()
                return jsonify({'success': True, 'message': f'Deleted {filename}'})
            else:
                return jsonify({'error': 'Not a file or does not exist'}), 400

        elif source == 'dsk':
            if not current_dsk:
                return jsonify({'error': 'No DSK loaded'}), 400

            if current_dsk.delete_file(filename):
                current_dsk.save()
                return jsonify({'success': True, 'message': f'Deleted {filename} from DSK'})
            else:
                return jsonify({'error': 'Delete failed'}), 500
        else:
            return jsonify({'error': 'Invalid source'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/file/rename', methods=['POST'])
def rename_file():
    """Rename a file in DSK"""
    global current_dsk

    if not current_dsk:
        return jsonify({'error': 'No DSK loaded'}), 400

    data = request.json
    old_name = data.get('old_name')
    new_name = data.get('new_name')

    try:
        # Find the entry
        entry = None
        for e in current_dsk.directory:
            full_name = f"{e.filename}.{e.extension}" if e.extension else e.filename
            if full_name == old_name:
                entry = e
                break

        if not entry:
            return jsonify({'error': 'File not found'}), 404

        # Parse new name into filename and extension
        if '.' in new_name:
            new_filename, new_ext = new_name.rsplit('.', 1)
        else:
            new_filename, new_ext = new_name, ''

        new_filename = new_filename[:8].ljust(8).upper()
        new_ext = new_ext[:3].ljust(3).upper()

        # Update directory entry
        for sector_num in range(current_dsk.DIR_START_SECTOR, current_dsk.DIR_END_SECTOR + 1):
            sector_data = bytearray(current_dsk.read_sector(current_dsk.DIR_TRACK, sector_num))

            for i in range(8):
                offset = i * current_dsk.ENTRY_SIZE
                entry_data = sector_data[offset:offset + current_dsk.ENTRY_SIZE]

                if entry_data[0] not in (0x00, 0xFF):
                    parsed_entry = current_dsk._parse_directory_entry(entry_data)
                    if parsed_entry and parsed_entry.first_granule == entry.first_granule:
                        # Found the entry - update it
                        sector_data[offset:offset+8] = new_filename.encode('ascii')
                        sector_data[offset+8:offset+11] = new_ext.encode('ascii')

                        current_dsk.write_sector(current_dsk.DIR_TRACK, sector_num, bytes(sector_data))
                        current_dsk.save()

                        return jsonify({'success': True, 'message': f'Renamed {old_name} to {new_name}'})

        return jsonify({'error': 'Failed to find directory entry'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/file/upload', methods=['POST'])
def upload_file():
    """Upload a file to PC directory"""
    global current_pc_path

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        filename = secure_filename(file.filename)
        file_path = current_pc_path / filename
        file.save(str(file_path))

        return jsonify({
            'success': True,
            'filename': filename,
            'path': str(file_path)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/file/download/<path:filename>')
def download_file(filename):
    """Download a file from PC directory"""
    global current_pc_path

    try:
        return send_from_directory(str(current_pc_path), filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 404


@app.route('/api/system/info', methods=['GET'])
def system_info():
    """Get system information"""
    return jsonify({
        'detokenizer_available': DETOKENIZER_AVAILABLE,
        'current_pc_path': str(current_pc_path),
        'dsk_loaded': current_dsk is not None
    })


if __name__ == '__main__':
    print("=" * 60)
    print("CoCo Web Commander - Starting on port 6809")
    print("=" * 60)
    print(f"Current PC directory: {current_pc_path}")
    print(f"Detokenizer available: {DETOKENIZER_AVAILABLE}")
    print()
    print("WARNING: This server is for LOCAL USE ONLY!")
    print("For public server deployment, add authentication and security!")
    print()
    print("Access the interface at: http://localhost:6809")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    app.run(host='0.0.0.0', port=6809, debug=True)
