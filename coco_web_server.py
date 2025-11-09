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

# Color BASIC token table
BASIC_TOKENS = {
    0x80: "FOR", 0x81: "GO", 0x82: "REM", 0x83: "'", 0x84: "ELSE",
    0x85: "IF", 0x86: "DATA", 0x87: "PRINT", 0x88: "ON", 0x89: "INPUT",
    0x8A: "END", 0x8B: "NEXT", 0x8C: "DIM", 0x8D: "READ", 0x8E: "RUN",
    0x8F: "RESTORE", 0x90: "RETURN", 0x91: "STOP", 0x92: "POKE", 0x93: "CONT",
    0x94: "LIST", 0x95: "CLEAR", 0x96: "NEW", 0x97: "CLOAD", 0x98: "CSAVE",
    0x99: "OPEN", 0x9A: "CLOSE", 0x9B: "LLIST", 0x9C: "SET", 0x9D: "RESET",
    0x9E: "CLS", 0x9F: "MOTOR", 0xA0: "SOUND", 0xA1: "AUDIO", 0xA2: "EXEC",
    0xA3: "SKIPF", 0xA4: "TAB(", 0xA5: "TO", 0xA6: "SUB", 0xA7: "THEN",
    0xA8: "NOT", 0xA9: "STEP", 0xAA: "OFF", 0xAB: "+", 0xAC: "-",
    0xAD: "*", 0xAE: "/", 0xAF: "^", 0xB0: "AND", 0xB1: "OR",
    0xB2: ">", 0xB3: "=", 0xB4: "<", 0xB5: "DEL", 0xB6: "EDIT",
    0xB7: "TRON", 0xB8: "TROFF", 0xB9: "DEF", 0xBA: "LET", 0xBB: "LINE",
    0xBC: "PCLS", 0xBD: "PSET", 0xBE: "PRESET", 0xBF: "SCREEN", 0xC0: "PCLEAR",
    0xC1: "COLOR", 0xC2: "CIRCLE", 0xC3: "PAINT", 0xC4: "GET", 0xC5: "PUT",
    0xC6: "DRAW", 0xC7: "PCOPY", 0xC8: "PMODE", 0xC9: "PLAY", 0xCA: "DLOAD",
    0xCB: "RENUM", 0xCC: "FN", 0xCD: "USING", 0xCE: "DIR", 0xCF: "DRIVE",
    0xD0: "FIELD", 0xD1: "FILES", 0xD2: "KILL", 0xD3: "LOAD", 0xD4: "LSET",
    0xD5: "MERGE", 0xD6: "RENAME", 0xD7: "RSET", 0xD8: "SAVE", 0xD9: "WRITE",
    0xDA: "VERIFY", 0xDB: "UNLOAD", 0xDC: "DSKINI", 0xDD: "BACKUP", 0xDE: "COPY",
    0xDF: "DSKI$", 0xE0: "DSKO$", 0xE1: "SGN", 0xE2: "INT", 0xE3: "ABS",
    0xE4: "USR", 0xE5: "RND", 0xE6: "SIN", 0xE7: "PEEK", 0xE8: "LEN",
    0xE9: "STR$", 0xEA: "VAL", 0xEB: "ASC", 0xEC: "CHR$", 0xED: "EOF",
    0xEE: "JOYSTK", 0xEF: "LEFT$", 0xF0: "RIGHT$", 0xF1: "MID$", 0xF2: "POINT",
    0xF3: "INKEY$", 0xF4: "MEM", 0xF5: "ATN", 0xF6: "COS", 0xF7: "TAN",
    0xF8: "EXP", 0xF9: "FIX", 0xFA: "LOG", 0xFB: "POS", 0xFC: "SQR",
    0xFD: "HEX$", 0xFE: "VARPTR", 0xFF: "INSTR"
}

def detokenize_basic(data):
    """Detokenize a Color BASIC program from binary to ASCII format"""
    output = []
    pos = 0

    try:
        while pos < len(data):
            # Check for end of program (0x00 0x00)
            if pos + 1 < len(data) and data[pos] == 0x00 and data[pos + 1] == 0x00:
                break

            # Get pointer to next line (2 bytes, big-endian)
            if pos + 2 > len(data):
                break
            next_line = (data[pos] << 8) | data[pos + 1]
            pos += 2

            if next_line == 0:
                break

            # Get line number (2 bytes, big-endian)
            if pos + 2 > len(data):
                break
            line_num = (data[pos] << 8) | data[pos + 1]
            pos += 2

            # Build line
            line = f"{line_num} "

            # Process tokens/characters until end of line (0x00)
            while pos < len(data) and data[pos] != 0x00:
                byte = data[pos]
                pos += 1

                if byte >= 0x80:  # Token
                    token = BASIC_TOKENS.get(byte, f"[{byte:02X}]")
                    # Add space before token if needed
                    if line and line[-1] not in (' ', '(', ','):
                        line += ' '
                    line += token
                    # Add space after token if it's a keyword
                    if byte < 0xAB or byte > 0xB4:  # Not an operator
                        line += ' '
                elif byte == 0x0D:  # Carriage return within line
                    line += '\n'
                elif byte == 0x22:  # Quote
                    line += chr(byte)
                    # Copy everything until next quote or end of line
                    while pos < len(data) and data[pos] != 0x22 and data[pos] != 0x00:
                        line += chr(data[pos])
                        pos += 1
                    if pos < len(data) and data[pos] == 0x22:
                        line += chr(data[pos])
                        pos += 1
                elif byte >= 0x20 and byte < 0x7F:  # Printable ASCII
                    line += chr(byte)
                else:  # Other control characters
                    line += f"[{byte:02X}]"

            # Skip the 0x00 end-of-line marker
            if pos < len(data) and data[pos] == 0x00:
                pos += 1

            output.append(line.rstrip() + '\r\n')

        return ''.join(output).encode('ascii', errors='replace')

    except Exception as e:
        # If detokenization fails, return original data
        return data

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
        # Get format parameter (binary or ascii)
        format_mode = request.args.get('format', 'binary')

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

        # Convert to ASCII if requested and file is BASIC binary
        if format_mode == 'ascii' and entry.file_type == 0x00 and entry.ascii_flag == 0x00:
            # Detokenize BASIC file
            file_data = detokenize_basic(file_data)
            # Change filename extension to .BAS for ASCII
            download_filename = filename
        else:
            download_filename = filename

        # Send as download
        return send_file(
            io.BytesIO(file_data),
            as_attachment=True,
            download_name=download_filename,
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
