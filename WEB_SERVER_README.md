# TRS-80 CoCo DSK Web Server

A web-based interface for managing TRS-80 Color Computer DSK/JVC disk images.

## Features

- **Mount DSK Images**: Upload and mount existing DSK/JVC files from your computer
- **Browse Files**: View directory listings of mounted disk images
- **Download Files**: Extract individual files from DSK images to your PC
- **Upload Files**: Add new files to mounted DSK images
- **Delete Files**: Remove files from DSK images
- **Format New Disks**: Create new blank DSK images with custom geometry
- **Download DSK**: Save modified DSK images back to your computer
- **Session Management**: Track changes and modifications

## Starting the Server

```bash
python3 coco_web_server.py
```

The server will start on **port 6809** (the Motorola 6809 CPU port - a tribute to the CoCo!)

Access the web interface at: **http://localhost:6809**

## Using the Web Interface

### Mounting a DSK Image

1. Click "SELECT DSK FILE" button
2. Choose a .dsk or .jvc file from your computer
3. The disk will be mounted and files will be displayed

### Creating a New DSK

1. Click "CREATE NEW DSK IMAGE" (or "FORMAT NEW DSK" when a disk is mounted)
2. Select the disk geometry:
   - **35 tracks**: 160KB (standard CoCo format)
   - **40 tracks**: 180KB
   - **80 tracks**: 360KB
3. Choose single or double-sided
4. Optionally add JVC header (for emulator compatibility)
5. Click "FORMAT"

### Downloading Files from DSK

- Click on any filename in the directory listing
- The file will be downloaded to your computer

### Uploading Files to DSK

1. Click "UPLOAD FILE TO DSK"
2. Select a file from your computer
3. Enter the DSK filename (8.3 format, e.g., HELLO.BAS)
4. Choose file type:
   - **ML** (Machine Language/Binary) - default
   - **BASIC** (Tokenized BASIC program)
   - **DATA** (BASIC data file)
   - **TEXT** (Text file)
5. Optionally check "ASCII MODE" for text files
6. Click "UPLOAD"

### Deleting Files

- Click the "DELETE" button next to any file in the listing
- Confirm the deletion

### Downloading the DSK Image

- Click "DOWNLOAD DSK IMAGE" to save the current disk image to your computer
- The modified badge indicates if changes have been made

### Unmounting

- Click "UNMOUNT DSK" to clear the current disk from memory
- You'll be prompted to download if changes were made

## API Endpoints

The server provides the following REST API endpoints:

- `GET /api/status` - Check if DSK is mounted
- `POST /api/mount` - Mount a DSK file
- `GET /api/list` - List files in mounted DSK
- `GET /api/download/<filename>` - Download file from DSK
- `POST /api/upload` - Upload file to DSK
- `DELETE /api/delete/<filename>` - Delete file from DSK
- `POST /api/format` - Format new DSK image
- `GET /api/download-dsk` - Download current DSK image
- `POST /api/unmount` - Unmount current DSK

## Requirements

- Python 3.x
- Flask 3.0.0
- Werkzeug 3.0.1

Install dependencies:
```bash
pip3 install -r requirements.txt
```

## Technical Details

- Maximum file upload size: 16MB
- Session-based DSK management (each browser session can mount its own DSK)
- Temporary files are stored in system temp directory
- Supports both DSK (raw) and JVC (with header) formats

## Port 6809

The server runs on port **6809** as a tribute to the Motorola 6809 processor that powered the TRS-80 Color Computer!

## Credits

Coded by ChipShift (Reyco2000@gmail.com) using Claude Code
Based on the dsktools library by mseminatore
(C) 2025
