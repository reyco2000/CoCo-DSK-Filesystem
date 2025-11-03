# CoCo Commander - User Guide

Norton Commander-style TUI for managing TRS-80 Color Computer DSK/JVC disk images.

## Versions

- **coco_commander.py**: Standard version - Full-featured dual-pane file manager
- **coco_commander_v1.py**: Enhanced version with BASIC detokenization support

## Quick Start

```bash
# Standard version
python3 coco_commander.py

# V1 with detokenization (requires coco_detokenizer.py in same directory)
python3 coco_commander_v1.py
```

## Interface Layout

```
┌─────────────────────────────┬─────────────────────────────┐
│ PC Files                    │ DSK Image: [None Loaded]    │
│ /current/path               │                             │
│                             │                             │
│  [..]                       │  No DSK image loaded        │
│  [Documents]                │                             │
│  [Downloads]                │                             │
│  readme.txt         1.5K    │                             │
│  program.bin       12.3K    │                             │
│  game.dsk         160.0K    │                             │
│                             │                             │
└─────────────────────────────┴─────────────────────────────┘
│ F2 Info | F3 View | F4 Edit | F5 Copy | F6 Move | F7 Format | F8 Delete | F10 Quit
│ TAB: Switch Panels | Active: PC Files
```

## Navigation

| Key | Action |
|-----|--------|
| **↑/↓** | Navigate file list up/down |
| **TAB** | Switch between PC files (left) and DSK image (right) panels |
| **ENTER** | Navigate into directory (PC) or load DSK file |
| **Q/F10** | Quit CoCo Commander |

## Function Keys

### F2 - Information
Shows detailed information about the selected file or disk:
- **PC Files**: File path, size, granules needed for DSK
- **DSK Files**: Type, mode, granule chain, file size
- **Disk Stats**: Total/used/free granules and space

### F3 - View File
Opens a hex/text viewer to inspect file contents:
- **Hex View**: Shows hexadecimal and ASCII representation
- **UP/DOWN**: Scroll through file
- **PAGE UP/DOWN**: Jump by page
- **Q/ESC**: Close viewer

### F4 - Edit (PC Files Only)
Simple text editor for PC files before uploading:
- **Arrow Keys**: Navigate cursor
- **HOME/END**: Jump to start/end of line
- **BACKSPACE/DELETE**: Edit text
- **ENTER**: New line
- **F9**: Save changes
- **F10/ESC**: Exit (prompts to discard if modified)

**Note**: Only works on text files. Binary files cannot be edited.

### F5 - Copy
Bidirectional file copy between PC and DSK:

**PC → DSK (Upload)**:
1. Select file in left panel (PC)
2. Press F5
3. Enter DSK filename (8.3 format)
4. Choose file type: BASIC, DATA, ML, or TEXT
5. Choose mode: Binary or ASCII
6. File is uploaded and DSK is saved

**DSK → PC (Download)**:
1. Select file in right panel (DSK)
2. Press F5
3. **[V1 Only]** If file is BASIC type, you'll be asked: "Detokenize to readable text?"
   - **Yes**: Converts tokenized BASIC to human-readable text (.txt)
   - **No**: Downloads raw tokenized binary format
4. Enter PC filename (auto-suggests .txt for detokenized files)
5. File is downloaded to current PC directory

**Note**: BASIC detokenization feature is only available in `coco_commander_v1.py`

### F6 - Rename (DSK Files Only)
Rename files within DSK image:
1. Select file in right panel (DSK)
2. Press F6
3. Enter new filename (8.3 format)
4. File is renamed and DSK is saved

**Note**: Only changes the filename, not the content or type.

### F7 - Format New DSK
Create a new blank DSK/JVC disk image:
1. Press F7
2. Enter new DSK filename
3. Choose number of tracks: 35 (160K), 40 (180K), or 80 (360K)
4. Choose sides: Single or Double-sided
5. Confirm to create the disk
6. DSK is created in current PC directory

### F8 - Delete
Delete files from PC or DSK:

**PC Files**:
- Deletes file from local filesystem
- Confirmation required

**DSK Files**:
- Deletes file from DSK image
- Frees granules for reuse
- DSK is automatically saved
- Confirmation required

## Typical Workflow

### 1. Browse and Load a DSK Image

```
1. Navigate PC files (left panel) using ↑/↓
2. Press ENTER on a .dsk or .jvc file to load it
3. DSK contents appear in right panel
4. Press TAB to switch to DSK panel
```

### 2. Upload Files to DSK

```
1. In PC panel (left), select file to upload
2. Press F5 (Copy)
3. Enter DSK filename (e.g., "MYGAME.BIN")
4. Select file type (usually ML for binaries, BASIC for .BAS)
5. Select mode (Binary for most files, ASCII for text)
6. File is uploaded and saved
```

### 3. Download Files from DSK

```
1. In DSK panel (right), select file to download
2. Press F5 (Copy)
3. [V1 Only] If BASIC file, choose Yes/No for detokenization
4. Enter PC filename (e.g., "mygame.bin" or "program.txt")
5. File is saved to current PC directory
6. Press TAB to see it in PC panel
```

**V1 BASIC Detokenization Example**:
```
1. Select "GAME.BAS" in DSK panel
2. Press F5
3. Dialog: "Detokenize to readable text?" → Select Yes
4. Filename auto-suggests "game.txt"
5. Press ENTER to accept or edit filename
6. File saved as readable BASIC source code
```

### 4. Manage DSK Files

```
View File Info:  F2
View Contents:   F3
Rename File:     F6 (DSK panel only)
Delete File:     F8 (confirms before deletion)
```

### 5. Create New DSK

```
1. Press F7 (Format)
2. Enter filename: "newdisk.dsk"
3. Choose geometry (35T/1S for standard 160K)
4. Confirm creation
5. Press ENTER on newdisk.dsk to load it
6. Start uploading files with F5
```

## File Types

When uploading to DSK, choose the appropriate type:

| Type | Code | Description | Use For |
|------|------|-------------|---------|
| **BASIC** | 0 | Tokenized BASIC program | .BAS files from CoCo BASIC |
| **DATA** | 1 | BASIC data file | Data files accessed by BASIC |
| **ML** | 2 | Machine Language/Binary | Games, utilities, executables |
| **TEXT** | 3 | Text/ASCII file | README files, text documents |

## File Modes

| Mode | Description | When to Use |
|------|-------------|-------------|
| **Binary** | Raw data, no translation | Most files (games, ML programs, tokenized BASIC) |
| **ASCII** | Text with CR/LF handling | Plain text files, source code |

## Supported Disk Formats

### Standard Formats
- **35 tracks, 1 side**: 160KB (standard CoCo floppy)
- **40 tracks, 1 side**: 180KB
- **35 tracks, 2 sides**: 320KB
- **40 tracks, 2 sides**: 360KB
- **80 tracks, 2 sides**: 720KB

### File Types
- **.DSK**: Raw disk image
- **.JVC**: Disk image with JVC header (auto-detected)

## Tips

1. **Load DSK First**: Navigate to a .dsk file in the PC panel and press ENTER to load it
2. **8.3 Filenames**: DSK files must follow DOS 8.3 naming (8 char name + 3 char extension)
3. **Check Free Space**: Use F2 on DSK panel to see available granules before uploading
4. **Backup First**: Always keep backup copies of important DSK images
5. **ASCII Mode**: Use ASCII mode for text files you want to edit on the CoCo
6. **Binary Mode**: Use Binary mode for tokenized BASIC programs and ML programs
7. **[V1] Detokenize BASIC**: When downloading .BAS files, use detokenization to get readable source code
8. **[V1] Edit Before Re-upload**: Detokenize, edit with F4, then use a BASIC tokenizer to re-upload
9. **Cursor Position**: When entering filenames, cursor starts at the end for quick editing
10. **Color Coding**: Active panel shows green selection bar (V1), inactive shows white

## Keyboard Reference Card

```
┌─────────────────────────────────────────────────────────┐
│                   CoCo Commander Keys                   │
├─────────────────────────────────────────────────────────┤
│ Navigation                                              │
│   ↑/↓ ........... Scroll file list                     │
│   TAB ........... Switch panels (PC ↔ DSK)             │
│   ENTER ......... Open folder / Load DSK               │
│                                                         │
│ Function Keys                                           │
│   F2 ............ Show file/disk information           │
│   F3 ............ View file (hex/text)                 │
│   F4 ............ Edit text file (PC only)             │
│   F5 ............ Copy (PC ↔ DSK)                      │
│   F6 ............ Rename (DSK only)                    │
│   F7 ............ Format new DSK                       │
│   F8 ............ Delete file                          │
│   F10/Q ......... Quit                                 │
│                                                         │
│ In Editor (F4)                                          │
│   Arrow Keys .... Move cursor                          │
│   HOME/END ...... Start/end of line                    │
│   Backspace ..... Delete character                     │
│   Enter ......... New line                             │
│   F9 ............ Save file                            │
│   F10/ESC ....... Exit editor                          │
│                                                         │
│ In Viewer (F3)                                          │
│   ↑/↓ ........... Scroll                               │
│   PgUp/PgDn ..... Page up/down                         │
│   Q/ESC ......... Close viewer                         │
└─────────────────────────────────────────────────────────┘
```

## Troubleshooting

### "File is not a text file. Cannot edit binary files."
- F4 editor only works on text files
- Use F3 to view binary files in hex mode instead

### "Not enough free space" when uploading
- DSK is full
- Check free granules with F2
- Delete unused files with F8, or use a larger DSK

### "Directory is full"
- Maximum 72 files per DSK
- Create a new DSK with F7 for additional files

### DSK won't load
- Verify the file is a valid .DSK or .JVC format
- Check file is not corrupted
- Try viewing with F3 first

### Terminal too small
- Minimum recommended terminal size: 80x24 characters
- Resize terminal window for better experience

### "Downloaded but detokenization failed" (V1)
- File was copied but couldn't be detokenized
- Raw tokenized file is still saved to PC
- File may be corrupted or not a valid BASIC file
- Try downloading without detokenization (select "No")

### Detokenizer not available (V1)
- Ensure `coco_detokenizer.py` is in the same directory as `coco_commander_v1.py`
- Check Python can import the module
- Standard version doesn't include this feature

## Requirements

- Python 3.6 or higher
- curses library (included in standard Python on Linux/Mac)
- coco_dsk.py module in the same directory
- **[V1 Only]** coco_detokenizer.py in the same directory for BASIC detokenization

## Platform Notes

### Linux/WSL
Works out of the box with standard Python installation.

### macOS
Works with standard Python installation.

### Windows
- **Recommended**: Use WSL (Windows Subsystem for Linux)
- **Alternative**: Install windows-curses: `pip install windows-curses`

## What's New in V1

### BASIC Detokenization
The V1 version includes integrated BASIC detokenization support:

- **Automatic Detection**: Recognizes BASIC files (type 0x00) when copying from DSK
- **User Choice**: Interactive dialog asks if you want to detokenize
- **Smart Naming**: Auto-suggests .txt extension for detokenized files
- **Readable Output**: Converts tokenized BASIC to human-readable source code
- **Fallback Support**: If detokenization fails, keeps the raw file

### Enhanced UI
- **Color-Coded Selection**: Active panel uses green highlight, inactive uses white
- **Better Dialogs**: Improved Yes/No dialogs with button navigation
- **Cursor Position**: Filename input starts with cursor at end for easy editing
- **Tab Behavior**: Switching to DSK panel resets selection to top

### File Distribution
To use V1 with detokenization, ensure both files are in the same directory:
- `coco_commander_v1.py`
- `coco_detokenizer.py`

## Detokenization Workflow Example

```
Traditional workflow (without V1):
1. Download GAME.BAS from DSK (tokenized binary)
2. Use separate detokenizer tool
3. Get readable text
4. Edit in external editor
5. Use separate tokenizer
6. Upload back to DSK

V1 Integrated workflow:
1. Press F5 on GAME.BAS in DSK panel
2. Select "Yes" to detokenize → Readable text saved
3. Press F4 to edit directly in CoCo Commander
4. [Use external tokenizer if needed]
5. Upload back to DSK
```

## License

Based on dsktools by mseminatore.
Coded by ChipShift Reyco2000@gmail.com using Claude Code.
(C) 2025

## Links

- GitHub: https://github.com/reyco2000/CoCo-DSK-Filesystem
- CoCoByte Club: https://cocobyte.co/
- Original dsktools: https://github.com/mseminatore/dsktools/
