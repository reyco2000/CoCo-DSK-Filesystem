# TRS-80 Color Computer DSK/JVC File System Tool

A Python tool for managing TRS-80 Color Computer DSK/JVC disk images. This tool allows you to mount, inspect, and transfer files between Color Computer disk images and your PC.


## Features

- **Mount DSK/JVC disk images** - Parse and read Color Computer disk images
- **List directory contents** - View all files with their types and attributes
- **Extract files** - Copy files from DSK images to your PC
- **Upload files** - Add files from your PC to DSK images
- **Free space calculation** - See available storage on disk images
- **JVC header support** - Handles both raw DSK and JVC formats

## Requirements

- Python 3.6 or higher
- No external dependencies required (uses standard library only)

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
# Upload as machine code (default)
python coco_dsk.py mydisk.dsk -p program.bin -n PROG.BIN

# Upload as BASIC program
python coco_dsk.py mydisk.dsk -p hello.bas -n HELLO.BAS -t 0

# Upload as ASCII text
python coco_dsk.py mydisk.dsk -p readme.txt -n README.TXT -t 3 -a
```

### Save Modified DSK to New File

```bash
python coco_dsk.py mydisk.dsk -p newfile.bin -s modified.dsk
```

## Command-Line Arguments

| Argument | Description |
|----------|-------------|
| `dsk_file` | DSK/JVC image file (required) |
| `-l, --list` | List files in DSK image |
| `-g, --get DSK_FILE` | Copy file from DSK to PC |
| `-o, --output PC_FILE` | Output filename for `-g` |
| `-p, --put PC_FILE` | Upload file from PC to DSK |
| `-n, --name DSK_NAME` | Name to use in DSK for `-p` |
| `-t, --type TYPE` | File type for `-p` (see below) |
| `-a, --ascii` | Mark file as ASCII for `-p` |
| `-s, --save OUTPUT_DSK` | Save modified DSK to new file |

## File Types

When uploading files with `-t`, use these type codes:

| Type | Code | Description |
|------|------|-------------|
| BASIC | 0 | Color BASIC program |
| DATA | 1 | BASIC data file |
| ML | 2 | Machine language/binary (default) |
| TEXT | 3 | Text/ASCII file |

## DSK Format Details

### Standard Format
- **Sector size:** 256 bytes
- **Default format:** 35 tracks, 18 sectors/track (160K)
- **Granule size:** 9 sectors (2,304 bytes)
- **Granules per disk:** 68

### Disk Structure
- **Directory track:** Track 17
- **FAT:** Track 17, Sector 2 (first 68 bytes)
- **Directory entries:** Track 17, Sectors 3-11
- **Entry size:** 32 bytes per directory entry
- **Max files:** 72 (9 sectors × 8 entries per sector)

### Directory Entry Format

Each 32-byte directory entry contains:
- Bytes 0-7: Filename (8 characters, space-padded)
- Bytes 8-10: Extension (3 characters, space-padded)
- Byte 11: File type (0=BASIC, 1=DATA, 2=ML, 3=TEXT)
- Byte 12: ASCII flag (0xFF=ASCII, 0x00=Binary)
- Byte 13: First granule number (0-67)
- Bytes 14-15: Last sector byte count (big-endian)
- Bytes 16-31: Reserved (0xFF)

## Examples

### Complete Workflow Example

```bash
# 1. List files on an existing DSK image
python coco_dsk.py games.dsk -l

# 2. Extract a BASIC program
python coco_dsk.py games.dsk -g SNAKE.BAS -o snake.bas

# 3. Upload a modified version back
python coco_dsk.py games.dsk -p snake_fixed.bas -n SNAKE2.BAS -t 0

# 4. Upload a machine language game
python coco_dsk.py games.dsk -p pacman.bin -n PACMAN.BIN -t 2

# 5. List files again to verify
python coco_dsk.py games.dsk -l
```

### Creating a Modified Disk

```bash
# Start with a blank or existing disk
python coco_dsk.py blank.dsk -l

# Add multiple files
python coco_dsk.py blank.dsk -p game1.bin -n GAME1.BIN -t 2
python coco_dsk.py blank.dsk -p game2.bin -n GAME2.BIN -t 2
python coco_dsk.py blank.dsk -p readme.txt -n README.TXT -t 3 -a

# Save as a new disk
python coco_dsk.py blank.dsk -s collection.dsk
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

# Mount a DSK image
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

    # Upload a file
    dsk.upload_from_pc('program.bin', 'PROG.BIN', file_type=2)

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
- Maximum 72 directory entries
- Filenames limited to 8.3 format (8 char name + 3 char extension)
- No subdirectory support (flat file system)
- Single-sided disk images only (default)

## Troubleshooting

### "File not found" Error
Make sure you're using the exact filename as shown in the directory listing (case-insensitive).

### "Not enough free space" Error
The disk is full. Check free space with `-l` option. You may need to use a larger disk image or remove files.

### "Directory is full" Error
Maximum 72 files per disk. You'll need to use a new disk image.

## References

- [dsktools GitHub Repository](https://github.com/mseminatore/dsktools/)
- [TRS-80 Color Computer Archive](https://colorcomputerarchive.com/)
- [Disk BASIC File Structure](https://www.lomont.org/software/misc/coco/Disk%20Basic%20Unravelled.pdf)
- [JVC Disk Image Format](http://www.tim-mann.org/trs80/dsk.html)



