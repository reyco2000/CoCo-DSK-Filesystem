# TRS-80 Color Computer DSK/JVC File System Tool

**Version 1.1** - Real CoCo DECB Behavior + Comprehensive Documentation!

A Python tool for managing TRS-80 Color Computer DSK/JVC disk images with authentic hardware behavior. This tool allows you to mount, inspect, and transfer files between Color Computer disk images and your PC, with a Norton Commander-style browser for easy navigation.



## Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/reyco2000/CoCo-DSK-Filesystem.git
   cd CoCo-DSK-Filesystem
   ```

2. **Install requirements (if needed):**

   **Linux / macOS / WSL:**
   ```bash
   # No installation needed! Works out of the box with Python 3.6+
   python3 coco_commander_v1.py
   ```

   **Windows (Native):**
   ```bash
   # Install curses support for Windows
   pip install -r requirements.txt

   # Then run
   python coco_commander_v1.py
   ```

3. **You're ready to go!**
   ```bash
   # Run CoCo Commander V1 (with detokenization)
   python3 coco_commander_v1.py

   # Or use command-line tool
   python3 coco_dsk.py mydisk.dsk -l
   ```

## Two Ways to Use

### 1. CoCo Commander V1 - Norton Commander-style TUI

**NEW in v1.0!** Enhanced text-based UI with integrated BASIC detokenization:

```bash
python3 coco_commander_v1.py
```

**Features:**
- ✨ **BASIC Detokenization** - Automatically convert tokenized BASIC programs to readable text
- 🎨 **Color-Coded Selection** - Green highlight for active panel, white for inactive
- 📝 **Smart Filename Entry** - Cursor starts at end for quick editing
- 🔄 **Enhanced Dialogs** - Improved Yes/No dialogs with button navigation
- 🎯 **Dual-Pane Interface** - PC files ↔ DSK image side-by-side
- 📁 **Function Keys** - F2: Info | F3: View | F4: Edit | F5: Copy | F6: Rename | F7: Format | F8: Delete
- ⌨️ **Intuitive Navigation** - Arrow keys and TAB for panel switching
- 👁️ **Built-in Viewers** - Hex/text viewer and text editor
- 🎨 **Norton Commander Style** - Familiar dual-pane file management

**Requirements:** `coco_detokenizer.py` must be in the same directory

See [COCO_COMMANDER_GUIDE.md](COCO_COMMANDER_GUIDE.md) for complete documentation.

### 2. Command-Line Tool - coco_dsk.py

Traditional command-line interface for scripting and automation.

## Features

- **Mount DSK/JVC disk images** - Parse and read Color Computer disk images
- **List directory contents** - View all files with their types and attributes
- **Extract files** - Copy files from DSK images to your PC
- **Upload files** - Add files from your PC to DSK images with flexible type/mode options
- **Delete files** - Remove files from DSK images and free up space
- **Format new disks** - Create blank DSK/JVC images with custom geometries
- **Free space calculation** - See available storage on disk images
- **JVC header support** - Handles both raw DSK and JVC formats

## What's New in Version 1.1

### 🔧 Real CoCo DECB Hardware Behavior

Version 1.1 implements **authentic TRS-80 Color Computer DECB behavior** based on real hardware observations:

- **Granule Allocation**: Files now start allocating from granule 32 (track 16), matching real CoCo DECB behavior
- **Directory Entry Formatting**: Active entries use `0x00` padding in reserved bytes (not `0xFF`)
- **Deletion Markers**: Deleted entries marked with first byte `0x00` only, rest may retain old data
- **Fresh Format Behavior**: Never-used entries filled with `0xFF` on fresh formatted disks
- **FAT Padding**: Uses `0x00` for FAT sector padding during file operations (bytes 68-255)
- **Default Format**: No JVC header by default (real CoCo standard); use `--add-jvc` for emulator compatibility

### 📚 Comprehensive Technical Documentation

Two new professional documentation files:

- **DSK_JVC_FORMAT_SPECIFICATION.md** - Complete 1,250+ line technical specification covering:
  - Physical disk structure and track/sector format
  - Sector interleaving and skip factors
  - Detailed FAT and directory structure
  - File storage algorithms with working examples
  - Common issues and troubleshooting

- **DSK_JVC_PROGRAMMER_GUIDE.md** - Concise programmer's reference with:
  - Quick reference diagrams
  - Implementation code examples
  - Real CoCo DECB behavior notes
  - Troubleshooting checklist

### 🎉 CoCo Commander V1 with BASIC Detokenization

Flagship feature with integrated BASIC detokenization:

- **Automatic BASIC Detection**: Recognizes tokenized BASIC files when copying from DSK
- **Interactive Choice**: Asks if you want to detokenize before saving to PC
- **Smart Naming**: Auto-suggests `.txt` extension for detokenized files
- **Readable Output**: Converts tokenized BASIC to human-readable source code
- **Full Token Support**: Handles Color BASIC, Extended Color BASIC, and CoCo 3 Super Extended BASIC
- **Fallback Protection**: If detokenization fails, raw file is still saved

### 🎨 Enhanced User Interface

- Color-coded selection bars (green for active panel)
- Improved dialog system with visual button navigation
- Better cursor positioning in input fields
- Tab behavior resets DSK panel to top

### 📦 What's Included

- `coco_commander_v1.py` - CoCo Commander with BASIC detokenization
- `coco_detokenizer.py` - Standalone BASIC detokenizer
- `coco_dsk.py` - Command-line DSK tool and Python API with real CoCo behavior
- `COCO_COMMANDER_GUIDE.md` - Complete user guide
- `DSK_JVC_FORMAT_SPECIFICATION.md` - Complete technical specification (1,250+ lines)
- `DSK_JVC_PROGRAMMER_GUIDE.md` - Concise programmer's reference

## Requirements

### System Requirements

- **Python**: 3.6 or higher (3.7+ recommended)
- **Operating System**: Linux, macOS, Windows, or WSL

### Dependencies

**Good news!** No external dependencies required on Linux/macOS/WSL - everything uses Python's standard library.

**Windows users:** One optional package for curses support:
```bash
pip install -r requirements.txt
```

This installs `windows-curses` which enables the text-based UI on Windows.

**What's included in requirements.txt:**
- `windows-curses>=2.3.0` (Windows only)
- All other dependencies are part of Python's standard library

### File Requirements

- For **CoCo Commander V1**: `coco_detokenizer.py` must be in the same directory
- For **Command-line tool**: `coco_dsk.py` is standalone

## Usage

### List Files in a DSK Image

```bash
python coco_dsk.py mydisk.dsk -l
```

Output shows filename, type, mode (ASCII/BIN), and starting granule for each file.

### Copy File from DSK to PC

```bash
# Copy with specified output name
python coco_dsk.py mydisk.dsk -g HELLO.BAS -o hello.bas

# Copy with default name
python coco_dsk.py mydisk.dsk -g PROGRAM.BIN
```

### Upload File from PC to DSK

```bash
# Upload as machine code (default type)
python coco_dsk.py mydisk.dsk -p program.bin -n PROG.BIN

# Upload as BASIC program (using string type name)
python coco_dsk.py mydisk.dsk -p hello.bas -n HELLO.BAS -t basic

# Upload as text file in ASCII mode (long form)
python coco_dsk.py mydisk.dsk -p readme.txt -n README.TXT -t text --mode ascii

# Upload as text file in ASCII mode (short form)
python coco_dsk.py mydisk.dsk -p readme.txt -n README.TXT -t text -a

# Upload using numeric type code (backward compatible)
python coco_dsk.py mydisk.dsk -p data.dat -n DATA.DAT -t 1
```

### Delete File from DSK

```bash
# Delete a file (frees up space)
python coco_dsk.py mydisk.dsk -d HELLO.BAS

# Delete and save to a different file
python coco_dsk.py mydisk.dsk -d OLDFILE.BIN -s cleaned.dsk
```

### Format a New Blank DSK Image

```bash
# Create a standard 160K disk (35 tracks, single-sided, NO JVC header - real CoCo format)
python coco_dsk.py newdisk.dsk --format

# Create with JVC header for emulators
python coco_dsk.py newdisk.dsk --format --add-jvc

# Create a 360K double-sided disk (40 tracks, 2 sides)
python coco_dsk.py bigdisk.dsk --format --tracks 40 --sides 2

# Create an 80-track 720K disk with JVC header
python coco_dsk.py huge.dsk --format --tracks 80 --sides 2 --add-jvc
```

### Save Modified DSK to New File

```bash
python coco_dsk.py mydisk.dsk -p newfile.bin -s modified.dsk
```

## Command-Line Arguments

### General Options
| Argument | Description |
|----------|-------------|
| `dsk_file` | DSK/JVC image file (required) |
| `-l, --list` | List files in DSK image |

### Extract (Get) Options
| Argument | Description |
|----------|-------------|
| `-g, --get DSK_FILE` | Copy file from DSK to PC |
| `-o, --output PC_FILE` | Output filename for `-g` (default: same as DSK filename) |

### Upload (Put) Options
| Argument | Description |
|----------|-------------|
| `-p, --put PC_FILE` | Upload file from PC to DSK |
| `-n, --name DSK_NAME` | Name to use in DSK for `-p` (default: PC filename in 8.3 format) |
| `-t, --type TYPE` | File type: `basic`, `data`, `ml`, `text` (or 0-3). Default: `ml` |
| `--mode MODE` | File mode: `binary` or `ascii` (default: `binary`) |
| `-a, --ascii` | Shorthand for `--mode ascii` |

### Delete Options
| Argument | Description |
|----------|-------------|
| `-d, --delete DSK_FILE` | Delete file from DSK image |

### Format Options
| Argument | Description |
|----------|-------------|
| `--format` | Format a new blank DSK image (no JVC header by default - real CoCo) |
| `--tracks TRACKS` | Number of tracks for `--format` (default: 35) |
| `--sides {1,2}` | Number of sides for `--format` (default: 1) |
| `--add-jvc` | Add JVC header when formatting (for emulators) |
| `--no-jvc` | Deprecated: no header is now the default |

### Save Options
| Argument | Description |
|----------|-------------|
| `-s, --save OUTPUT_DSK` | Save modified DSK to new file |

## File Types

When uploading files with `-t`, use these type names or codes:

| Type Name | Code | Description |
|-----------|------|-------------|
| `basic` | 0 | Color BASIC program (tokenized) |
| `data` | 1 | BASIC data file |
| `ml` | 2 | Machine language/binary (default) |
| `text` | 3 | Text/ASCII file |

## File Modes

When uploading files, specify the mode:

| Mode | Description |
|------|-------------|
| `binary` | Binary data, no translation (default) |
| `ascii` | ASCII text, CR/LF handling |

## DSK Format Details

### Standard Format
- **Sector size:** 256 bytes
- **Default format:** 35 tracks, 18 sectors/track (160K)
- **Granule size:** 9 sectors (2,304 bytes)
- **Granules per disk:** 68
- **Allocation start:** Granule 32 (track 16) - matches real CoCo DECB
- **Default header:** None (real CoCo standard); JVC headers optional for emulators

### Disk Structure
- **Directory track:** Track 17
- **FAT:** Track 17, Sector 2 (first 68 bytes)
- **Directory entries:** Track 17, Sectors 3-11
- **Entry size:** 32 bytes per directory entry
- **Max files:** 72 (9 sectors × 8 entries per sector)

### Directory Entry Format

Each 32-byte directory entry contains:
- Bytes 0-7: Filename (8 characters, space-padded)
  - First byte `0x00` = deleted entry
  - First byte `0xFF` = never used (all subsequent entries also unused)
  - First byte `0x20-0x7E` = active file
- Bytes 8-10: Extension (3 characters, space-padded)
- Byte 11: File type (0=BASIC, 1=DATA, 2=ML, 3=TEXT)
- Byte 12: ASCII flag (0xFF=ASCII, 0x00=Binary)
- Byte 13: First granule number (0-67)
- Bytes 14-15: Last sector byte count (big-endian)
- Bytes 16-31: Reserved (`0x00` for active entries, `0xFF` for fresh format)

### Real CoCo DECB Behavior

This tool implements authentic CoCo behavior:
- **Granule allocation**: Starts at granule 32, searches 32-67 then wraps to 0-31
- **Directory padding**: Active entries use `0x00` in reserved bytes
- **Deletion**: Only first byte set to `0x00`, rest retains old data
- **Fresh format**: All directory entries filled with `0xFF`
- **FAT padding**: Bytes 68-255 use `0x00` during file operations

For complete technical details, see [DSK_JVC_FORMAT_SPECIFICATION.md](DSK_JVC_FORMAT_SPECIFICATION.md)

## Examples

### Complete Workflow Example

```bash
# 1. List files on an existing DSK image
python coco_dsk.py games.dsk -l

# 2. Extract a BASIC program
python coco_dsk.py games.dsk -g SNAKE.BAS -o snake.bas

# 3. Upload a modified version back
python coco_dsk.py games.dsk -p snake_fixed.bas -n SNAKE2.BAS -t basic

# 4. Upload a machine language game
python coco_dsk.py games.dsk -p pacman.bin -n PACMAN.BIN -t ml

# 5. Delete the old version
python coco_dsk.py games.dsk -d SNAKE.BAS

# 6. List files again to verify
python coco_dsk.py games.dsk -l
```

### Creating a New Disk from Scratch

```bash
# 1. Format a new 160K disk
python coco_dsk.py collection.dsk --format

# 2. Add multiple files
python coco_dsk.py collection.dsk -p game1.bin -n GAME1.BIN -t ml
python coco_dsk.py collection.dsk -p game2.bin -n GAME2.BIN -t ml
python coco_dsk.py collection.dsk -p readme.txt -n README.TXT -t text -a

# 3. List to verify
python coco_dsk.py collection.dsk -l
```

### Working with Different Disk Sizes

```bash
# Create a large 720K disk for more storage
python coco_dsk.py bigdisk.dsk --format --tracks 80 --sides 2

# Create a 360K double-sided disk
python coco_dsk.py medium.dsk --format --tracks 40 --sides 2

# Verify the disk is empty
python coco_dsk.py bigdisk.dsk -l
```

## Technical Notes

### Granule Chain Following
The tool follows the File Allocation Table (FAT) chain to read multi-granule files:
- FAT entries 0-67: Point to next granule in chain
- FAT entries 0xC0-0xC9: Last granule (lower 4 bits = sectors used)
- FAT entry 0xFF: Free/unused granule

### Track 17 Handling
Track 17 is reserved for the directory and FAT. When calculating granule-to-track mappings:
- Granules 0-33 map to tracks 0-16
- Granules 34-67 map to tracks 18-34
- Track 17 is skipped in the mapping

### Granule Allocation Strategy
**Real CoCo DECB behavior**: Files allocate starting from granule 32 (track 16, just before directory track):
- Search order: 32→67 (toward end of disk)
- If needed, wraps to: 0→31 (toward beginning)
- This places new files near the directory track for faster access

### JVC Header Support
The tool automatically detects and parses JVC headers if present. JVC headers are optional and contain:
- Byte 0: Sectors per track
- Byte 1: Side count
- Byte 2: Sector size code
- Byte 3: First sector ID
- Byte 4: Sector attribute flags

## Python API Usage

You can also use this tool as a Python module:

```python
from coco_dsk import DSKImage

# Format a new disk
dsk = DSKImage.format_disk('newdisk.dsk', tracks=35, sides=1)

# Or mount an existing DSK image
dsk = DSKImage('mydisk.dsk')
if dsk.mount():
    # List files
    dsk.list_files()

    # Extract a file
    for entry in dsk.directory:
        if entry.filename == 'HELLO':
            data = dsk.extract_file(entry)
            with open('hello.bas', 'wb') as f:
                f.write(data)

    # Upload a file (file_type: 0=BASIC, 1=DATA, 2=ML, 3=TEXT)
    # ascii_flag: 0x00=binary, 0xFF=ASCII
    dsk.upload_from_pc('program.bin', 'PROG.BIN', file_type=0x02, ascii_flag=0x00)

    # Delete a file
    dsk.delete_file('OLDFILE.BAS')

    # Save changes
    dsk.save()

    # Or save to a new file
    dsk.save('modified.dsk')
```

## Error Handling

The tool validates:
- File existence before mounting
- Granule numbers (must be 0-67)
- Free space before uploads
- Directory slot availability
- Sector and track bounds

## Limitations

- Only supports DECB (Disk Extended Color Basic) format
- Maximum 72 directory entries per disk
- Filenames limited to 8.3 format (8 char name + 3 char extension)
- No subdirectory support (flat file system)
- No timestamp support in DECB format

## Troubleshooting

### "File not found" Error
Make sure you're using the exact filename as shown in the directory listing (case-insensitive).

### "Not enough free space" Error
The disk is full. Check free space with `-l` option. You may need to use a larger disk image or remove files.

### "Directory is full" Error
Maximum 72 files per disk. You'll need to use a new disk image.

## Documentation

### Included Documentation Files

- **[DSK_JVC_FORMAT_SPECIFICATION.md](DSK_JVC_FORMAT_SPECIFICATION.md)** - Complete 1,250+ line technical specification
  - Physical disk structure with track/sector format
  - Sector interleaving and skip factors
  - Detailed FAT and directory structure
  - File storage algorithms with examples
  - Common issues and troubleshooting
  - Comprehensive reference for developers

- **[DSK_JVC_PROGRAMMER_GUIDE.md](DSK_JVC_PROGRAMMER_GUIDE.md)** - Concise programmer's reference
  - Quick reference cheatsheets
  - Code implementation examples
  - Real CoCo DECB behavior notes
  - Troubleshooting checklist
  - Ideal for quick lookups

- **[COCO_COMMANDER_GUIDE.md](COCO_COMMANDER_GUIDE.md)** - CoCo Commander V1 user guide
  - Complete UI reference
  - Keyboard shortcuts
  - BASIC detokenization guide
  - Usage examples

## External References

- [dsktools GitHub Repository](https://github.com/mseminatore/dsktools/) - Original C implementation
- [TRS-80 Color Computer Archive](https://colorcomputerarchive.com/) - Historical preservation
- [Disk BASIC File Structure](https://www.lomont.org/software/misc/coco/Disk%20Basic%20Unravelled.pdf) - Official documentation
- [JVC Disk Image Format](http://www.tim-mann.org/trs80/dsk.html) - Format specification

## License

Based on dsktools by mseminatore. This tool is provided for educational and preservation purposes.

## Version History

### Version 1.1 (January 2025)
- 🔧 **Real CoCo DECB behavior** - Granule allocation from granule 32, authentic padding
- 📚 **Comprehensive documentation** - 1,250+ line technical specification
- 📖 **Programmer's guide** - Concise reference with code examples
- 🎯 **Default format change** - No JVC header by default (real CoCo standard)
- ✅ **FAT/Directory behavior** - Matches real hardware (0x00 padding, deletion markers)
- 📝 **Enhanced docs** - Physical track/sector format, interleaving details

### Version 1.0 (2025)
- ✨ Released CoCo Commander V1 with integrated BASIC detokenization support
- 🎨 Enhanced UI with color-coded panels and improved dialogs
- 📝 Standalone BASIC detokenizer module included
- 📚 Comprehensive user guide and technical documentation
- 🔧 Improved filename input with cursor positioning
- 🎯 Tab behavior enhancements for better navigation
- 🧹 Simplified to single CoCo Commander version (V1 only)

### Previous Versions
- Initial release: Command-line DSK tool and prototype CoCo Commander

## Authoring

Made with ❤️ by Reinaldo Torres — a proud CoCo enthusiast 📧 reyco2000@gmail.com

🟢 Proud member and co-creator of the CoCoByte Club https://cocobyte.co/

🔗 See more on @ChipShift https://github.com/reyco2000/

**Coded with Claude Code** - Developed using Anthropic's Claude AI assistant

## Contributing

For issues or improvements related to the underlying disk format handling, please refer to the original [dsktools repository](https://github.com/mseminatore/dsktools/).
