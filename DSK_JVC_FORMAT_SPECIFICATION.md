# DSK/JVC File Format Specification

## Complete Technical Documentation for TRS-80 Color Computer Disk Images

---

## Table of Contents

1. [Introduction](#introduction)
2. [Historical Context](#historical-context)
3. [Physical Disk Structure](#physical-disk-structure)
4. [JVC Header Format](#jvc-header-format)
5. [Sector Organization](#sector-organization)
6. [The Granule System](#the-granule-system)
7. [File Allocation Table (FAT)](#file-allocation-table-fat)
8. [Directory Structure](#directory-structure)
9. [File Storage and Retrieval](#file-storage-and-retrieval)
10. [File Types](#file-types)
11. [Working Examples](#working-examples)
12. [Advanced Topics](#advanced-topics)
13. [Common Issues and Solutions](#common-issues-and-solutions)

---

## Introduction

The DSK file format is a virtual disk image format used to store and preserve TRS-80 Color Computer (CoCo) floppy disk contents. The JVC format is an enhanced version that includes an optional header with disk geometry information.

### Key Characteristics

- **Sector-based storage**: Direct sector-by-sector copy of physical disk
- **DECB file system**: Uses Disk Extended Color Basic file system
- **Simple structure**: No compression, direct binary representation
- **Emulator compatible**: Supported by most CoCo emulators

### Format Variations

1. **Pure DSK**: Raw sector data, no header
2. **JVC Format**: Optional variable-length header + sector data
3. **VDK Format**: Fixed 12-byte header (not covered here)

---

## Historical Context

### The TRS-80 Color Computer

The Tandy/Radio Shack TRS-80 Color Computer (CoCo) was a home computer series produced from 1980-1991. It used:

- **Motorola 6809 CPU**: 8-bit microprocessor
- **Color BASIC**: Microsoft BASIC in ROM
- **Disk Extended BASIC**: Enhanced BASIC with disk support

### Original Floppy Drives

The original 1981 CoCo floppy drive specifications:

```
Drive: Tandy FD-501/502
Capacity: 160KB (single-sided)
Tracks: 35
Sectors per track: 18
Sector size: 256 bytes
RPM: 300
Interface: WD1793/WD2793 controller
```

**Calculation**: 35 tracks × 18 sectors × 256 bytes = 161,280 bytes (160KB)

### Evolution

- **1981**: 35-track, single-sided (160KB)
- **1983**: 40-track, single-sided (180KB)
- **1985**: 40-track, double-sided (360KB)
- **Late 1980s**: 80-track, double-sided (720KB)

---

## Physical Disk Structure

### Track and Sector Layout

A disk is organized as concentric circles (tracks) divided into sectors:

```
Track 0  [Sector 1][Sector 2][Sector 3]...[Sector 18]
Track 1  [Sector 1][Sector 2][Sector 3]...[Sector 18]
Track 2  [Sector 1][Sector 2][Sector 3]...[Sector 18]
...
Track 17 [Sector 1][Sector 2][Sector 3]...[Sector 18]  <- DIRECTORY TRACK
Track 18 [Sector 1][Sector 2][Sector 3]...[Sector 18]
...
Track 34 [Sector 1][Sector 2][Sector 3]...[Sector 18]
```

### Standard Disk Geometry (35-track)

| Parameter | Value |
|-----------|-------|
| Total tracks | 35 |
| Sectors per track | 18 |
| Bytes per sector | 256 |
| Total sectors | 630 |
| Total capacity | 161,280 bytes |
| Directory track | 17 |
| Data tracks | 34 (track 17 excluded) |

### Sector Numbering

**Important**: Sectors are numbered starting from **1**, not 0!

- Track 0: Sectors 1-18
- Track 1: Sectors 1-18
- ...
- Track 34: Sectors 1-18

### Linear Sector Addressing

In a DSK file, sectors are stored sequentially:

```
File Offset = Header_Size + ((Track × Sectors_Per_Track) + (Sector - 1)) × Sector_Size

Example for Track 17, Sector 2:
Offset = 0 + ((17 × 18) + (2 - 1)) × 256
       = 0 + (306 + 1) × 256
       = 0 + 307 × 256
       = 78,592 bytes
```

---

## JVC Header Format

### Header Detection

The JVC header is **optional** and **variable-length**. Its size is determined by:

```
Header_Size = File_Size % 256
```

If the file size is evenly divisible by 256, there is **no header** (pure DSK format).

### Header Structure

The header can be 0 to 255 bytes long. Each byte has a specific meaning:

| Offset | Size | Name | Default | Description |
|--------|------|------|---------|-------------|
| 0x00 | 1 | Sectors per track | 18 | Number of sectors on each track |
| 0x01 | 1 | Side count | 1 | Number of disk sides (1 or 2) |
| 0x02 | 1 | Sector size code | 1 | Sector size = 128 × 2^n |
| 0x03 | 1 | First sector ID | 1 | ID of first sector (usually 1) |
| 0x04 | 1 | Sector attribute | 0 | Additional flags |
| 0x05+ | ... | Reserved | - | Future expansion |

### Sector Size Code

The sector size is calculated as: **Sector_Size = 128 << n**

| Code | Calculation | Sector Size |
|------|-------------|-------------|
| 0 | 128 << 0 | 128 bytes |
| 1 | 128 << 1 | 256 bytes (standard) |
| 2 | 128 << 2 | 512 bytes |
| 3 | 128 << 3 | 1024 bytes |

### Header Examples

**Example 1: No Header (Pure DSK)**
```
File size: 161,280 bytes
161,280 % 256 = 0
Header size: 0 bytes
Format: Pure DSK, assumes defaults (18/1/256/1/0)
```

**Example 2: 5-byte JVC Header**
```
File size: 161,285 bytes
161,285 % 256 = 5
Header size: 5 bytes

Header bytes:
0x00: 12 (18 decimal) - 18 sectors per track
0x01: 01           - Single-sided
0x02: 01           - 256-byte sectors
0x03: 01           - First sector is #1
0x04: 00           - No special attributes
```

**Example 3: Extended Geometry**
```
Header for 40-track, double-sided disk:
0x00: 12 (18 decimal) - 18 sectors per track
0x01: 02           - Double-sided (2 heads)
0x02: 01           - 256-byte sectors
0x03: 01           - First sector is #1
0x04: 00           - No attributes

Total capacity: 40 tracks × 2 sides × 18 sectors × 256 bytes = 368,640 bytes
File size: 368,640 + 5 = 368,645 bytes
```

---

## Sector Organization

### Memory Map Overview

```
Track  Sectors  Purpose
-----  -------  -----------------------------------------------
0-16   1-18     User data (34 granules = 77,824 bytes)
17     1-2      Reserved/Boot sector
17     2        File Allocation Table (FAT)
17     3-11     Directory entries (72 max files)
17     12-18    Reserved/Additional directory space
18-34  1-18     User data (34 granules = 77,824 bytes)
```

### Track 17: The Directory Track

Track 17 is the heart of the DECB file system:

```
Sector 1:  Boot/Reserved (256 bytes)
Sector 2:  File Allocation Table - FAT (256 bytes)
Sector 3:  Directory entries 1-8 (32 bytes each)
Sector 4:  Directory entries 9-16
Sector 5:  Directory entries 17-24
Sector 6:  Directory entries 25-32
Sector 7:  Directory entries 33-40
Sector 8:  Directory entries 41-48
Sector 9:  Directory entries 49-56
Sector 10: Directory entries 57-64
Sector 11: Directory entries 65-72
Sectors 12-18: Reserved
```

**Maximum files**: 9 sectors × 8 entries per sector = 72 files

---

## The Granule System

### What is a Granule?

A **granule** is the smallest unit of disk space allocation in DECB. It consists of:

- **9 consecutive sectors**
- **2,304 bytes** (9 × 256)
- **2 granules per track**

### Why Granules?

Using granules simplifies file allocation:
- Reduces FAT size (68 bytes vs. 630 bytes for sector-level allocation)
- Minimizes fragmentation
- Aligns with track boundaries

### Granule Numbering

On a 35-track disk:
- **Total tracks**: 35
- **Directory track**: 17 (excluded from data storage)
- **Data tracks**: 34
- **Total granules**: 34 × 2 = 68 granules

```
Track  Granules
-----  --------
0      0, 1
1      2, 3
2      4, 5
...
16     32, 33
17     (Reserved for directory)
18     34, 35
19     36, 37
...
34     66, 67
```

### Granule to Track/Sector Mapping

To convert granule number to track and starting sector:

```python
def granule_to_track_sector(granule_num):
    if granule_num < 34:  # Before directory track
        track = granule_num // 2
    else:  # After directory track (skip track 17)
        track = (granule_num // 2) + 1

    granule_on_track = granule_num % 2
    start_sector = (granule_on_track * 9) + 1

    return track, start_sector
```

**Examples**:

| Granule | Track | Sectors |
|---------|-------|---------|
| 0 | 0 | 1-9 |
| 1 | 0 | 10-18 |
| 2 | 1 | 1-9 |
| 33 | 16 | 10-18 |
| 34 | 18 | 1-9 (skip track 17) |
| 35 | 18 | 10-18 |
| 67 | 34 | 10-18 |

### Available Storage

```
Total granules: 68
Granule size: 2,304 bytes
Total storage: 68 × 2,304 = 156,672 bytes (153KB)

(161,280 total - 4,608 directory track = 156,672 bytes)
```

---

## File Allocation Table (FAT)

### FAT Location and Size

- **Location**: Track 17, Sector 2
- **Size**: First 68 bytes of the sector
- **Remaining**: 188 bytes unused (typically 0xFF)

### FAT Structure

The FAT is a simple array where each byte represents one granule:

```
Offset  Granule  Value
------  -------  -----
0x00    0        FAT entry for granule 0
0x01    1        FAT entry for granule 1
0x02    2        FAT entry for granule 2
...
0x43    67       FAT entry for granule 67
0x44-0xFF        Unused (filled with 0xFF)
```

### FAT Entry Values

Each FAT byte has a specific meaning:

| Value Range | Meaning |
|-------------|---------|
| 0xFF | Granule is **free** (available) |
| 0x00 - 0x43 | Points to **next granule** in chain (0-67) |
| 0xC0 - 0xC9 | **Last granule** in file chain |

### Last Granule Encoding

When a FAT entry is 0xC0-0xC9, it indicates:
- This is the **final granule** in the file
- Lower 4 bits (0-9) indicate **sectors used**

```
Value = 0xC0 | sectors_used

Examples:
0xC1 = Last granule, 1 sector used
0xC5 = Last granule, 5 sectors used
0xC9 = Last granule, 9 sectors used (full granule)
0xC0 = Last granule, 0 sectors used (treated as 9)
```

### FAT Example: Simple File

A file using 3 granules (5, 8, 12) with 7 sectors in the last granule:

```
Offset  Granule  Value   Meaning
------  -------  -----   -------
0x05    5        0x08    Points to granule 8
0x08    8        0x0C    Points to granule 12
0x0C    12       0xC7    Last granule, 7 sectors used
```

### FAT Example: Complete Disk

```
Offset  Value   Description
------  -----   -----------
0x00    0xFF    Granule 0: Free
0x01    0xFF    Granule 1: Free
0x02    0x03    Granule 2: Points to granule 3 (file 1)
0x03    0xC5    Granule 3: Last, 5 sectors (file 1)
0x04    0xFF    Granule 4: Free
0x05    0x06    Granule 5: Points to granule 6 (file 2)
0x06    0x07    Granule 6: Points to granule 7 (file 2)
0x07    0xC9    Granule 7: Last, 9 sectors (file 2)
0x08    0xC3    Granule 8: Standalone file, 3 sectors (file 3)
0x09-   0xFF    Granules 9-67: All free
0x43
```

This represents:
- **File 1**: Granules 2→3 (2 granules, ~4.5KB)
- **File 2**: Granules 5→6→7 (3 granules, ~6.75KB)
- **File 3**: Granule 8 only (3 sectors, 768 bytes)
- **Free**: 65 granules available

---

## Directory Structure

### Directory Location

- **Track**: 17
- **Sectors**: 3-11 (9 sectors)
- **Total entries**: 72 maximum (9 × 8)
- **Entry size**: 32 bytes

### Directory Entry Format

Each 32-byte entry has this structure:

```
Offset  Size  Field Name           Description
------  ----  -------------------  ------------------------------------
0x00    8     Filename             Padded with spaces (0x20)
0x08    3     Extension            Padded with spaces (0x20)
0x0B    1     File Type            0=BASIC, 1=DATA, 2=ML, 3=TEXT
0x0C    1     ASCII Flag           0=Binary, 0xFF=ASCII
0x0D    1     First Granule        Starting granule number (0-67)
0x0E    2     Last Sector Bytes    Bytes used in final sector (big-endian)
0x10    16    Reserved/Unused      Typically filled with 0xFF
```

### Field Details

#### Filename (0x00-0x07)

- **Length**: 8 bytes
- **Format**: ASCII, uppercase
- **Padding**: Space (0x20) on the right
- **Invalid**: First byte 0x00 or 0xFF indicates unused entry

**Examples**:
```
"HELLO   " (5 chars + 3 spaces)
"GAME1   " (5 chars + 3 spaces)
"PROGRAM " (7 chars + 1 space)
"X       " (1 char + 7 spaces)
```

#### Extension (0x08-0x0A)

- **Length**: 3 bytes
- **Format**: ASCII, uppercase
- **Padding**: Space (0x20) on the right
- **Common**: BAS, DAT, BIN, TXT, CMD

**Examples**:
```
"BAS" - BASIC program
"BIN" - Binary file
"DAT" - Data file
"TXT" - Text file
"   " - No extension (3 spaces)
```

#### File Type (0x0B)

| Value | Type | Description |
|-------|------|-------------|
| 0x00 | BASIC | Tokenized BASIC program |
| 0x01 | DATA | BASIC data file |
| 0x02 | ML | Machine language/binary |
| 0x03 | TEXT | ASCII text file |

#### ASCII Flag (0x0C)

| Value | Mode | Description |
|-------|------|-------------|
| 0x00 | Binary | Binary data, no translation |
| 0xFF | ASCII | Text file, CR/LF handling |

#### First Granule (0x0D)

- **Range**: 0-67
- **Purpose**: Starting point for FAT chain
- **Invalid**: Values > 67 indicate corrupted entry

#### Last Sector Bytes (0x0E-0x0F)

- **Format**: 16-bit big-endian integer
- **Range**: 0-256
- **Purpose**: Exact file size calculation
- **Special**: 0 often means 256 (full sector)

**Example**:
```
Bytes: 0x01 0x2A
Value: (0x01 << 8) | 0x2A = 298
Meaning: Last sector contains 298 bytes (invalid, should be ≤256)

Bytes: 0x00 0x80
Value: 128
Meaning: Last sector contains 128 bytes
```

### Directory Entry Example

A BASIC program "HELLO.BAS" starting at granule 5, with 147 bytes in last sector:

```
Offset  Hex Value                            ASCII/Description
------  -----------------------------------  -----------------
0x00    48 45 4C 4C 4F 20 20 20              "HELLO   "
0x08    42 41 53                             "BAS"
0x0B    00                                   File type: BASIC
0x0C    00                                   Binary mode
0x0D    05                                   First granule: 5
0x0E    00 93                                Last sector: 147 bytes
0x10    FF FF FF FF FF FF FF FF              Reserved
0x18    FF FF FF FF FF FF FF FF              Reserved
```

### Empty Directory Entry

Unused entries are marked:

```
0x00    00 or FF ...  (first byte is 0x00 or 0xFF)
```

or

```
0x00-   All zeros or all 0xFF
0x1F
```

---

## File Storage and Retrieval

### Writing a File to Disk

**Step-by-step process**:

1. **Calculate space needed**
   ```
   file_size = 5000 bytes
   granules_needed = ceil(5000 / 2304) = 3 granules
   ```

2. **Find free granules** (scan FAT for 0xFF entries)
   ```
   Found: Granules 10, 11, 15 are free
   ```

3. **Allocate granules** (update FAT)
   ```
   FAT[10] = 11    # Point to next granule
   FAT[11] = 15    # Point to next granule
   FAT[15] = 0xC6  # Last granule, 6 sectors used
   ```

4. **Calculate last sector size**
   ```
   full_granules = 2 × 2304 = 4608 bytes
   remaining = 5000 - 4608 = 392 bytes
   sectors_in_last = ceil(392 / 256) = 2 sectors
   last_sector_bytes = 392 % 256 = 136 bytes
   ```
   Wait, let me recalculate:
   ```
   Granule 1: 2304 bytes (sectors 1-9)
   Granule 2: 2304 bytes (sectors 1-9)
   Granule 3: 5000 - 4608 = 392 bytes

   Sectors needed in granule 3: ceil(392 / 256) = 2 sectors
   Last sector bytes: 392 - 256 = 136 bytes

   Actually, if granule 3 uses 2 sectors:
   - Sector 1: 256 bytes
   - Sector 2: 136 bytes
   Total in granule 3: 392 bytes ✓
   ```

5. **Write file data**
   - Granule 10 → Track 5, Sectors 1-9
   - Granule 11 → Track 5, Sectors 10-18
   - Granule 15 → Track 7, Sectors 10-11 (only 2 sectors)

6. **Create directory entry**
   ```
   Filename: "DATA.BIN"
   Type: 0x02 (ML)
   ASCII: 0x00 (Binary)
   First granule: 10
   Last sector bytes: 136
   ```

7. **Find free directory slot** (scan sectors 3-11)
   - Found at Sector 3, Entry 4 (offset 96)

8. **Write directory entry** to Track 17, Sector 3, offset 96

### Reading a File from Disk

**Step-by-step process**:

1. **Scan directory** (Track 17, Sectors 3-11)
   - Find entry with matching filename

2. **Extract file info**
   ```
   Filename: "DATA.BIN"
   First granule: 10
   Last sector bytes: 136
   ```

3. **Follow FAT chain**
   ```
   Start: Granule 10
   FAT[10] = 11 → Next granule is 11
   FAT[11] = 15 → Next granule is 15
   FAT[15] = 0xC2 → Last granule, 2 sectors used

   Chain: [10, 11, 15]
   Sectors: [9, 9, 2]
   ```

4. **Calculate file size**
   ```
   Full granules: 2 × 2304 = 4608 bytes
   Last granule: 2 sectors, 136 bytes in last = 256 + 136 = 392 bytes
   Total: 4608 + 392 = 5000 bytes
   ```

5. **Read sectors**
   - Granule 10: Read Track 5, Sectors 1-9 (2304 bytes)
   - Granule 11: Read Track 5, Sectors 10-18 (2304 bytes)
   - Granule 15: Read Track 7, Sectors 10-11 (512 bytes)

6. **Trim to actual size**
   ```
   Buffer: 5120 bytes read
   Trim to: 5000 bytes (using last_sector_bytes calculation)
   ```

### File Size Calculation

To determine exact file size:

```python
def calculate_file_size(fat_chain, last_sector_bytes):
    total_bytes = 0

    for i, (granule, sectors_used) in enumerate(fat_chain):
        if i < len(fat_chain) - 1:
            # Full granule
            total_bytes += sectors_used * 256
        else:
            # Last granule
            full_sectors = sectors_used - 1
            total_bytes += full_sectors * 256
            total_bytes += last_sector_bytes

    return total_bytes
```

---

## File Types

### BASIC Programs (Type 0x00)

Tokenized BASIC programs stored in internal format.

**Structure**:
- Line number (2 bytes, big-endian)
- Line length (1 byte)
- Tokenized BASIC code
- 0x00 terminator

**Example**:
```
10 PRINT "HELLO"
20 GOTO 10
```

Tokenized format:
```
00 0A    # Line number 10
0A       # Line length
87       # PRINT token
20       # Space
22       # Quote
48 45 4C 4C 4F  # "HELLO"
22       # Quote
00       # End of line

00 14    # Line number 20
07       # Line length
89       # GOTO token
20       # Space
31 30    # "10"
00       # End of line
00       # End of program
```

### Data Files (Type 0x01)

BASIC data files created with OPEN/WRITE commands.

**Structure**: Variable, depends on BASIC program

### Machine Language (Type 0x02)

Binary executable code or data.

**Common format**: Binary with preamble
```
0x00      # Preamble type
0x1234    # Load address (big-endian)
0x0100    # Length (big-endian)
[data]    # Binary data
0xFF      # Postamble
```

### Text Files (Type 0x03)

Plain ASCII text files.

**Format**:
- ASCII characters
- Line endings: CR (0x0D) or LF (0x0A)
- No special formatting

---

## Working Examples

### Example 1: Creating a Simple Disk

Let's create a disk with one file: "HELLO.TXT" containing "HELLO WORLD".

**File content**:
```
"HELLO WORLD" = 11 bytes + newline = 12 bytes
```

**Steps**:

1. **Create blank disk** (161,280 bytes)
   - Fill all sectors with 0x00 or 0xFF

2. **Initialize FAT** (Track 17, Sector 2)
   ```
   Offset 0x00-0x43: All 0xFF (all granules free)
   ```

3. **Allocate granule for file**
   - Use granule 0
   - 12 bytes = 1 sector needed
   ```
   FAT[0] = 0xC1  # Last granule, 1 sector used
   ```

4. **Write file data** (Track 0, Sector 1)
   ```
   Offset 0x0000: 48 45 4C 4C 4F 20 57 4F 52 4C 44 0A  # "HELLO WORLD\n"
   ```

5. **Create directory entry** (Track 17, Sector 3, offset 0)
   ```
   0x00: "HELLO   " # Filename
   0x08: "TXT"      # Extension
   0x0B: 0x03       # TEXT type
   0x0C: 0xFF       # ASCII mode
   0x0D: 0x00       # First granule = 0
   0x0E: 0x00 0x0C  # Last sector = 12 bytes
   0x10: 0xFF...    # Reserved
   ```

**Hex dump of Track 17, Sector 2 (FAT)**:
```
0000: C1 FF FF FF FF FF FF FF  FF FF FF FF FF FF FF FF  |................|
0010: FF FF FF FF FF FF FF FF  FF FF FF FF FF FF FF FF  |................|
...
0040: FF FF FF FF                                       |....|
```

**Hex dump of Track 17, Sector 3 (Directory)**:
```
0000: 48 45 4C 4C 4F 20 20 20  54 58 54 03 FF 00 00 0C  |HELLO   TXT.....|
0010: FF FF FF FF FF FF FF FF  FF FF FF FF FF FF FF FF  |................|
0020: FF FF FF FF FF FF FF FF  FF FF FF FF FF FF FF FF  |................|
...
```

### Example 2: Multi-Granule File

A 5,000-byte file "DATA.BIN":

**Granules needed**: ceil(5000 / 2304) = 3 granules

**FAT allocation** (use granules 5, 8, 12):
```
FAT[5] = 0x08   # Points to granule 8
FAT[8] = 0x0C   # Points to granule 12
FAT[12] = 0xC2  # Last, 2 sectors used
```

**Size calculation**:
```
Granule 5: 9 sectors × 256 = 2304 bytes
Granule 8: 9 sectors × 256 = 2304 bytes
Granule 12: 2 sectors × 256 = 512 bytes
Total read: 5120 bytes

Last sector bytes: 5000 - (2304 + 2304 + 256) = 136 bytes
Actual file: 4864 + 136 = 5000 bytes
```

**Directory entry**:
```
0x00: "DATA    BIN"
0x0B: 0x02       # ML type
0x0C: 0x00       # Binary
0x0D: 0x05       # First granule = 5
0x0E: 0x00 0x88  # Last sector bytes = 136
```

### Example 3: Fragmented File

A file allocated to non-sequential granules: 3 → 7 → 15 → 20

**FAT**:
```
FAT[3] = 0x07
FAT[7] = 0x0F
FAT[15] = 0x14
FAT[20] = 0xC9  # Last, all 9 sectors used
```

**Data locations**:
- Granule 3: Track 1, Sectors 10-18
- Granule 7: Track 3, Sectors 10-18
- Granule 15: Track 7, Sectors 10-18
- Granule 20: Track 10, Sectors 1-9

**Total**: 4 granules = 36 sectors = 9,216 bytes

---

## Advanced Topics

### Disk Formatting

To create a new blank disk:

1. **Calculate total size**
   ```
   Size = Tracks × Sides × Sectors_per_track × Sector_size
   160K disk: 35 × 1 × 18 × 256 = 161,280 bytes
   ```

2. **Add JVC header** (optional)
   ```
   Header: [18, 1, 1, 1, 0] = 5 bytes
   Total: 161,280 + 5 = 161,285 bytes
   ```

3. **Initialize sectors**
   - Fill data area with 0x00 or 0xFF
   - Some systems prefer 0xFF for unused areas

4. **Create FAT** (Track 17, Sector 2)
   ```
   Bytes 0-67: 0xFF (all free)
   Bytes 68-255: 0xFF (unused)
   ```

5. **Clear directory** (Track 17, Sectors 3-11)
   ```
   All bytes: 0xFF or 0x00
   ```

### Defragmentation

To defragment a disk:

1. **Read all files** into memory
2. **Sort files** by desired order
3. **Re-initialize disk** (clear FAT and directory)
4. **Write files sequentially** starting from granule 0

This ensures files use consecutive granules.

### Bad Granule Handling

Some disks mark bad granules in the FAT:

```
FAT[10] = 0xDD  # Bad granule marker (not standard DECB)
```

Standard DECB doesn't support bad granule marking. Use granule linking to skip bad areas.

### Double-Sided Disks

For double-sided disks:

**Interleaved layout**:
```
Track 0, Side 0
Track 0, Side 1
Track 1, Side 0
Track 1, Side 1
...
```

**Side-by-side layout**:
```
Track 0-34, Side 0
Track 0-34, Side 1
```

The JVC header `side_count` field (byte 1) indicates single (1) or double (2) sided.

### Write Protection

The disk image format has no write protection flag. Protection is handled by:
- Emulator settings
- File system permissions
- External metadata

### Timestamps

DECB format has **no timestamp support**. Directory entries don't store:
- Creation date/time
- Modification date/time
- Access date/time

Later DOS systems (OS-9, NitrOS-9) added timestamp support in reserved bytes.

### Long Filenames

DECB is limited to 8.3 filenames. Workarounds:
- Use numeric sequences: PROG01, PROG02...
- Abbreviations: MYPRGRAM (8 chars max)
- External documentation

### File Attributes

No attribute system like DOS (hidden, system, read-only). The only flags are:
- File type (4 values)
- ASCII flag (binary/ASCII)

### Subdirectories

DECB has **no subdirectory support**. The file system is completely flat.

Advanced DOS systems (OS-9) use different directory structures for hierarchy.

---

## Common Issues and Solutions

### Issue 1: File Size Mismatch

**Problem**: Calculated file size doesn't match expected size.

**Causes**:
- Incorrect `last_sector_bytes` value
- Corrupted FAT chain
- Missing terminator granule

**Solution**:
```python
# Validate last_sector_bytes
if last_sector_bytes > 256 or last_sector_bytes == 0:
    last_sector_bytes = 256  # Assume full sector
```

### Issue 2: Circular FAT Chain

**Problem**: FAT chain loops back on itself.

**Example**:
```
FAT[5] = 8
FAT[8] = 5  # Points back to 5!
```

**Detection**:
```python
def detect_circular_chain(fat, start_granule):
    visited = set()
    current = start_granule

    while current != 0xFF and current < 0xC0:
        if current in visited:
            return True  # Circular!
        visited.add(current)
        current = fat[current]

    return False
```

**Solution**: Manual FAT repair required.

### Issue 3: Lost Granules

**Problem**: FAT shows granules as allocated but no directory entry references them.

**Detection**:
```python
# Build list of granules used by files
used_by_files = set()
for entry in directory:
    chain = follow_fat_chain(entry.first_granule)
    used_by_files.update(chain)

# Find allocated but unreferenced granules
for i, fat_value in enumerate(fat):
    if fat_value != 0xFF and i not in used_by_files:
        print(f"Lost granule: {i}")
```

**Solution**: Mark as free (0xFF) or investigate.

### Issue 4: Cross-Linked Files

**Problem**: Two files share the same granule.

**Example**:
```
File 1: Granules 5 → 8 → 10
File 2: Granules 7 → 10 → 12
```
Granule 10 is shared!

**Detection**: Track all granule references.

**Solution**:
- Copy data from shared granule
- Allocate new granule for one file
- Update FAT

### Issue 5: Invalid Granule Numbers

**Problem**: FAT or directory references granule > 67.

**Example**:
```
FAT[5] = 0x80  # Invalid! (not a valid pointer or terminator)
```

**Solution**:
- Corruption: Restore from backup
- Mark file as damaged
- Attempt data recovery

### Issue 6: Directory Corruption

**Problem**: Directory entries have invalid data.

**Signs**:
- First granule > 67
- File type > 3
- Invalid characters in filename

**Recovery**:
```python
def validate_directory_entry(entry_data):
    # Check first granule
    if entry_data[0x0D] > 67:
        return False

    # Check file type
    if entry_data[0x0B] > 3:
        return False

    # Check filename has valid ASCII
    for byte in entry_data[0:8]:
        if byte < 0x20 or byte > 0x7E:
            if byte != 0xFF:  # 0xFF is valid unused marker
                return False

    return True
```

### Issue 7: JVC Header Confusion

**Problem**: Misidentifying header presence/size.

**Common mistake**:
```python
# Wrong!
if file_size % 256 == 0:
    header_size = 0
else:
    header_size = 5  # Assumes fixed 5-byte header
```

**Correct**:
```python
header_size = file_size % 256  # Variable length!
```

### Issue 8: Sector Number Off-By-One

**Problem**: Forgetting sectors start at 1, not 0.

**Wrong**:
```python
sector_offset = track * sectors_per_track + sector  # Treats sector as 0-based
```

**Correct**:
```python
sector_offset = track * sectors_per_track + (sector - 1)  # Sectors start at 1
```

---

## Appendix A: Quick Reference

### Standard Disk Sizes

| Type | Tracks | Sides | Sect/Trk | Size |
|------|--------|-------|----------|------|
| 35SS | 35 | 1 | 18 | 160KB |
| 40SS | 40 | 1 | 18 | 180KB |
| 40DS | 40 | 2 | 18 | 360KB |
| 80DS | 80 | 2 | 18 | 720KB |

### FAT Value Summary

| Value | Meaning |
|-------|---------|
| 0xFF | Free granule |
| 0x00-0x43 | Next granule in chain (0-67) |
| 0xC0-0xC9 | Last granule (bits 0-3 = sectors used) |

### File Type Codes

| Code | Type | Description |
|------|------|-------------|
| 0x00 | BASIC | Tokenized BASIC program |
| 0x01 | DATA | BASIC data file |
| 0x02 | ML | Machine language/binary |
| 0x03 | TEXT | ASCII text file |

### Important Constants

```
SECTOR_SIZE = 256
GRANULE_SECTORS = 9
GRANULE_SIZE = 2304
DIR_TRACK = 17
FAT_SECTOR = 2
DIR_START_SECTOR = 3
DIR_END_SECTOR = 11
MAX_FILES = 72
MAX_GRANULES = 68
```

---

## Appendix B: Formulas

### File Offset Calculation

```
offset = header_size + (track * sectors_per_track + (sector - 1)) * sector_size
```

### Granules Needed

```
granules_needed = ceiling(file_size / granule_size)
```

### File Size from Chain

```
file_size = (full_granules * granule_size) +
            ((last_granule_sectors - 1) * sector_size) +
            last_sector_bytes
```

### Free Space

```
free_granules = count(FAT[i] == 0xFF for i in 0..67)
free_bytes = free_granules * granule_size
```

---

## Appendix C: Tools and Resources

### Emulators Supporting DSK/JVC

- **MAME** (Multi-Arcade Machine Emulator) - CoCo support
- **VCC** (Virtual Color Computer) - Windows
- **XRoar** - Cross-platform
- **CoCoPi** - Raspberry Pi

### Disk Image Tools

- **dsktools** (C library) - mseminatore/dsktools
- **ToolShed** - OS-9/NitrOS-9 tools
- **CoCo SDC** utilities
- **This Python script** - coco_dsk.py

### Documentation Resources

- Sub-Etha Software - CoCo disk structure articles
- Color Computer Archive - Technical documentation
- TRS-80.com - Historical information
- Tim Mann's page - Disk format specifications

---

## Revision History

- **Version 1.0** (2025) - Initial comprehensive documentation

---

## License and Credits

This document is provided for educational purposes to preserve and document the TRS-80 Color Computer disk image format.

**Based on**:
- Original DECB specifications by Microsoft/Tandy
- dsktools library documentation by Mark Seminatore
- Community documentation and reverse engineering

**Created by**: Reyco2000@gmail.com using Claude Code. 

---

*End of DSK/JVC Format Specification*
