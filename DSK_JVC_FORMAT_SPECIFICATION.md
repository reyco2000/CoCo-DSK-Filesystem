# DSK/JVC File Format Specification

## Complete Technical Documentation for TRS-80 Color Computer Disk Images

---

## Table of Contents

1. [Introduction](#introduction)
2. [Historical Context](#historical-context)
3. [Physical Disk Structure](#physical-disk-structure)
4. [Physical Track Format](#physical-track-format)
5. [Physical Sector Format](#physical-sector-format)
6. [Sector Interleaving and Skip Factor](#sector-interleaving-and-skip-factor)
7. [JVC Header Format](#jvc-header-format)
8. [Sector Organization](#sector-organization)
9. [The Granule System](#the-granule-system)
10. [File Allocation Table (FAT)](#file-allocation-table-fat)
11. [Directory Structure](#directory-structure)
12. [File Storage and Retrieval](#file-storage-and-retrieval)
13. [File Types](#file-types)
14. [Working Examples](#working-examples)
15. [Advanced Topics](#advanced-topics)
16. [Common Issues and Solutions](#common-issues-and-solutions)

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

## Physical Track Format

### Raw Track Structure

When the Color Computer formats a disk, it organizes each track with specific control bytes and data sectors. Each physical track contains approximately **6,250 bytes** total:

```
Byte Range    Contents
----------    --------
0-31          System control bytes (0x4E)
32-6115       Sector data (18 sectors × 338 bytes)
6116-6249*    System control bytes (0x4E)

*Note: The number of trailing control bytes may vary slightly
due to disk rotation speed variations.
```

### Track Layout Breakdown

| Component | Bytes | Description |
|-----------|-------|-------------|
| Pre-track gap | 32 | Gap bytes (0x4E) before first sector |
| Sector data | 6,084 | 18 sectors × 338 bytes each |
| Post-track gap | ~134 | Gap bytes (0x4E) after last sector |
| **Total** | **~6,250** | Approximate total per track |

### Gap Byte Purpose

The gap bytes (0x4E hexadecimal) serve several purposes:

- **Synchronization**: Allow the disk controller to synchronize with the data stream
- **Timing tolerance**: Compensate for slight speed variations in disk rotation
- **Error recovery**: Provide space between sectors for the controller to prepare
- **Write splicing**: Allow sectors to be rewritten without affecting adjacent sectors

### Important Notes

- DSK/JVC image files **do not store** these gap bytes - they only contain the 256 data bytes per sector
- The physical formatting is handled by the disk controller (WD1793/WD2793)
- Gap bytes are automatically regenerated when writing to real floppy disks
- Emulators typically don't need to simulate gap bytes

---

## Physical Sector Format

### Complete Sector Structure

Each physical sector on disk contains **338 bytes total**: 256 bytes of user data surrounded by control information for the disk controller.

```
Byte Range    Size    Contents
----------    ----    --------
0-55          56      Sector header and sync
56-311        256     User data (what's in DSK file)
312-337       26      CRC and post-sector gap
----------    ----    --------
Total:        338     Physical sector size
```

### Detailed Sector Header Format

The sector header identifies the sector and prepares the controller for reading:

| Byte Offset | Hex Value | Description |
|-------------|-----------|-------------|
| 0-7 | 0x00 | Pre-sync gap (8 bytes) |
| 8-10 | 0xF5 | Sync bytes (3 bytes)* |
| 11 | 0xFE | ID Address Mark |
| 12 | Track # | Current track number (0-34) |
| 13 | 0x00 | Side number (0=side 0, 1=side 1) |
| 14 | Sector # | Sector number (1-18) |
| 15 | 0x01 | Sector size code (1 = 256 bytes) |
| 16-17 | CRC | Cyclic Redundancy Check for header |
| 18-39 | 0x4E | Post-header gap (22 bytes) |
| 40-51 | 0x00 | Pre-data sync (12 bytes) |
| 52-54 | 0xF5 | Data sync bytes (3 bytes)* |
| 55 | 0xFB | Data Address Mark |
| **56-311** | **Data** | **256 bytes of user data** |
| 312-313 | CRC | Cyclic Redundancy Check for data |
| 314-337 | 0x4E | Post-data gap (24 bytes) |

*Note: 0xF5 sync bytes are actually written as 0xA1 with a missing clock bit - a special pattern the disk controller can recognize.

### Sector Size Codes

The sector size code (byte 15) determines the data area size:

| Code | Formula | Sector Size |
|------|---------|-------------|
| 0x00 | 128 << 0 | 128 bytes |
| 0x01 | 128 << 1 | 256 bytes (standard CoCo) |
| 0x02 | 128 << 2 | 512 bytes |
| 0x03 | 128 << 3 | 1024 bytes |

### CRC (Cyclic Redundancy Check)

Two CRC values protect sector integrity:

1. **Header CRC** (bytes 16-17): Protects track, side, sector, and size information
2. **Data CRC** (bytes 312-313): Protects the 256 bytes of user data

The WD1793/WD2793 controller automatically calculates and verifies CRCs. CRC errors indicate disk corruption or read errors.

### Address Marks

Special byte patterns that synchronize the controller:

- **0xFE**: ID Address Mark - Signals start of sector header
- **0xFB**: Data Address Mark - Signals start of data field
- **0xF5**: Written as 0xA1 with missing clock - Sync pattern
- **0xF8**: Deleted Data Mark - Marks deleted sectors (rarely used)

### What's in a DSK File?

DSK/JVC image files contain **only the 256 data bytes** from each sector (bytes 56-311). All header, sync, CRC, and gap bytes are omitted because:

- They're automatically regenerated by disk controllers
- They're not needed for emulation
- Including them would increase file size by 32% (338 vs 256 bytes/sector)

### Physical vs. Logical View

**Physical sector (on disk)**: 338 bytes with headers, CRCs, gaps
**Logical sector (in DSK)**: 256 bytes of pure data

When you access Track 0, Sector 1 in a DSK file, you're reading only the 256 data bytes, not the full 338-byte physical sector.

---

## Sector Interleaving and Skip Factor

### The Interleaving Problem

Floppy disks spin continuously at 300 RPM (5 revolutions per second). The CoCo reads or writes one sector at a time, but between sector operations, it must process the data in memory. This takes time.

**The challenge**: By the time the Computer finishes processing Sector 1, the disk has already spun past Sector 2!

### Skip Factor Solution

To solve this timing problem, the CoCo uses **sector interleaving** during formatting. Sectors are numbered on the disk in a non-sequential order, with a **skip factor** determining the spacing.

**Skip Factor 4** (standard): After reading a sector, skip 4 physical sectors before the next logical sector.

### Physical vs. Logical Sector Layout

With skip factor 4, the logical sector sequence is interleaved across the physical track:

```
Physical    Logical     Physical    Logical
Sector      Sector      Sector      Sector
--------    -------     --------    -------
   1           1           10          10
   2          12           11           3
   3           5           12          14
   4          16           13           7
   5           9           14          18
   6           2           15          11
   7          13           16           4
   8           6           17          15
   9          17           18           8
```

### How It Works

**Example: Reading sectors 1, 2, 3 sequentially**

1. **Read Logical Sector 1** (Physical Sector 1)
   - CoCo processes data (~4 sector times)
   - Disk spins past physical sectors 2, 3, 4, 5

2. **Read Logical Sector 2** (Physical Sector 6)
   - CoCo processes data (~4 sector times)
   - Disk spins past physical sectors 7, 8, 9, 10

3. **Read Logical Sector 3** (Physical Sector 11)
   - Process continues...

Without interleaving, the CoCo would have to wait a full rotation to catch each sector!

### Visual Representation

```
Track viewed as circular disk (Physical Layout):

         1(L1)
    18(L8)  2(L12)
  17(L15)     3(L5)
16(L4)          4(L16)
15(L11)         5(L9)
  14(L18)     6(L2)
    13(L7)  7(L13)
        8(L6)
         9(L17)
    10(L10)

L# = Logical sector number
```

### Calculating Physical Sector Number

Given a logical sector number (1-18) and skip factor (4):

```python
def logical_to_physical(logical_sector, skip_factor=4, sectors_per_track=18):
    """Convert logical sector to physical sector number."""
    physical = 1 + ((logical_sector - 1) * (skip_factor + 1)) % sectors_per_track
    return physical

# Examples:
# Logical 1 → Physical 1
# Logical 2 → Physical 6
# Logical 3 → Physical 11
```

### Reverse Calculation

```python
def physical_to_logical(physical_sector, skip_factor=4, sectors_per_track=18):
    """Convert physical sector to logical sector number."""
    # Build lookup table
    physical_to_logical_map = {}
    for logical in range(1, sectors_per_track + 1):
        physical = 1 + ((logical - 1) * (skip_factor + 1)) % sectors_per_track
        physical_to_logical_map[physical] = logical

    return physical_to_logical_map[physical_sector]
```

### Performance Implications

**Skip Factor 4** (standard for BASIC):
- Optimal for interpreted BASIC LOAD/SAVE operations
- Allows ~4 sector times for processing

**Skip Factor 3**:
- Faster for machine language operations
- Requires quicker processing: `DSKINI 0,3`

**Skip Factor 2**:
- Very fast, but only suitable for fast ML routines
- Risk of missing sectors if processing is slow

**Skip Factor 5 or higher**:
- Slower disk I/O
- Used for debugging or very slow processing

### Formatting with Different Skip Factors

The DSKINI command formats with a specific skip factor:

```basic
DSKINI 0, 4    ' Format drive 0 with skip factor 4 (standard)
DSKINI 0, 3    ' Format drive 0 with skip factor 3 (faster)
DSKINI 0, 5    ' Format drive 0 with skip factor 5 (slower)
```

**Warning**: Changing skip factor affects disk compatibility! A disk formatted with skip factor 3 may have read errors if the system expects skip factor 4.

### Skip Factor in DSK Files

**Important**: DSK/JVC image files store sectors in **logical order** (1, 2, 3, ... 18), not physical order. The skip factor interleaving is:

- **Not present** in the DSK file format
- **Only relevant** on physical floppy disks
- **Recreated** when writing DSK images to real floppies
- **Transparent** to emulators (they access sectors instantly)

### Interleaving Table Reference

Complete mapping for skip factor 4:

| Logical | Physical | Logical | Physical |
|---------|----------|---------|----------|
| 1 | 1 | 10 | 10 |
| 2 | 6 | 11 | 15 |
| 3 | 11 | 12 | 2 |
| 4 | 16 | 13 | 7 |
| 5 | 3 | 14 | 12 |
| 6 | 8 | 15 | 17 |
| 7 | 13 | 16 | 4 |
| 8 | 18 | 17 | 9 |
| 9 | 5 | 18 | 14 |

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

**Example 1: No Header (Pure DSK - Real CoCo Standard)**
```
File size: 161,280 bytes
161,280 % 256 = 0
Header size: 0 bytes
Format: Pure DSK, assumes defaults (18/1/256/1/0)
Note: This is the default format for real CoCo hardware
```

**Example 2: 5-byte JVC Header (For Emulators)**
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
Note: JVC headers are primarily for emulators; real CoCo uses no header
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
16     32, 33    ← Real CoCo DECB starts allocation here
17     (Reserved for directory)
18     34, 35
19     36, 37
...
34     66, 67
```

### Granule Allocation Strategy

**Real CoCo DECB behavior** (as implemented in coco_dsk.py):

Files are allocated starting from **granule 32** (track 16, just before the directory track).

**Allocation search order**:
1. Search granules 32-67 first (from track 16 forward)
2. If needed, wrap around to granules 0-31

This behavior matches real CoCo hardware and places new files near the directory track for faster access.

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
- **Special values**: First byte indicates entry status

**First Byte Status Codes**:

| First Byte | Status | Description |
|------------|--------|-------------|
| 0x00 | Deleted | File has been deleted, entry available for reuse |
| 0xFF | Never used | Entry has never been used (all following entries also unused) |
| 0x20-0x7E | Active | Valid filename character, entry is in use |

**Important**: When the first byte is 0xFF, it indicates that this entry **and all subsequent entries** in the directory have never been used. This allows the system to stop scanning the directory early.

**Examples**:
```
"HELLO   " (5 chars + 3 spaces) - Active file
"GAME1   " (5 chars + 3 spaces) - Active file
"PROGRAM " (7 chars + 1 space)  - Active file
"X       " (1 char + 7 spaces)  - Active file
0x00 followed by garbage         - Deleted file, can be reused
0xFF followed by garbage         - Never used, stop directory scan
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
0x10    00 00 00 00 00 00 00 00              Reserved (Real CoCo uses 0x00)
0x18    00 00 00 00 00 00 00 00              Reserved (Real CoCo uses 0x00)
```

### Empty and Deleted Directory Entries

Directory entries can be in three states:

**1. Active Entry (In Use)**
```
First byte: 0x20-0x7E (valid filename character)
Contains complete file information
Reserved bytes: 0x00 (Real CoCo DECB behavior)
```

**2. Deleted Entry (Available for Reuse)**
```
First byte: 0x00
Remaining bytes: May contain old file data (garbage)
Status: Available for new files
```

When a file is deleted:
- Only the first byte is set to 0x00 (Real CoCo DECB behavior)
- Other bytes may retain old data
- Entry can be reclaimed for new files

**3. Never Used Entry (Fresh Format)**
```
First byte: 0xFF
Remaining bytes: Typically all 0xFF
Status: Never been allocated
```

When first byte is 0xFF:
- This entry has **never been used**
- **All subsequent entries** are also unused
- Allows early termination of directory scan
- No need to check entries after the first 0xFF

**Real CoCo DECB Implementation Notes**:
- Fresh formatted disks: All directory entries filled with 0xFF
- Active entries: Reserved bytes (0x10-0x1F) use 0x00 padding
- Deleted entries: Only first byte set to 0x00, rest may retain old data
- This matches the behavior in coco_dsk.py

**Directory Scanning Logic**:

```python
for entry in directory_entries:
    first_byte = entry[0]

    if first_byte == 0xFF:
        # Never used - stop scanning
        break
    elif first_byte == 0x00:
        # Deleted - skip but continue scanning
        continue
    else:
        # Active file - process entry
        process_file(entry)
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
   Real CoCo DECB starts allocation from granule 32 (track 16)
   Search order: 32-67, then wrap to 0-31 if needed
   Found: Granules 32, 33, 35 are free
   ```

3. **Allocate granules** (update FAT)
   ```
   FAT[32] = 33    # Point to next granule
   FAT[33] = 35    # Point to next granule
   FAT[35] = 0xC6  # Last granule, 6 sectors used
   Note: Real CoCo uses 0x00 for FAT padding when writing
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
   - Granule 32 → Track 16, Sectors 1-9
   - Granule 33 → Track 16, Sectors 10-18
   - Granule 35 → Track 17+1, Sectors 10-11 (only 2 sectors, skip track 17)

6. **Create directory entry**
   ```
   Filename: "DATA.BIN"
   Type: 0x02 (ML)
   ASCII: 0x00 (Binary)
   First granule: 32
   Last sector bytes: 136
   Reserved bytes: 0x00 (Real CoCo behavior)
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
   0x10: 0x00...    # Reserved (Real CoCo uses 0x00, not 0xFF)
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
0010: 00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  |................|
0020: FF FF FF FF FF FF FF FF  FF FF FF FF FF FF FF FF  |................|
...
(Note: Real CoCo uses 0x00 for reserved bytes in active entries, 0xFF for unused entries)
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
0x0D: 0x20       # First granule = 32 (Real CoCo starts at 32)
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
   Bytes 68-255: 0xFF (padding for fresh format)
   Note: Real CoCo uses 0x00 padding when writing FAT during file operations
   ```

5. **Clear directory** (Track 17, Sectors 3-11)
   ```
   All bytes: 0xFF (fresh format - never-used entries)
   Note: Deleted entries marked with first byte = 0x00
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

**Created by**: reyco2000 (Reinaldo Torres) using Claude Code, based on dsktools and CoCo community resources

---

*End of DSK/JVC Format Specification*
