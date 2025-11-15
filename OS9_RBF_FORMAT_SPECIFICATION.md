# OS-9 RBF File System Format Specification

## Complete Technical Documentation for TRS-80 Color Computer OS-9 Disk Images

---

## Table of Contents

1. [Introduction](#introduction)
2. [Historical Context](#historical-context)
3. [OS-9 vs DECB Comparison](#os-9-vs-decb-comparison)
4. [Physical Disk Structure](#physical-disk-structure)
5. [LSN 0: Identification Sector](#lsn-0-identification-sector)
6. [Allocation Bitmap](#allocation-bitmap)
7. [Directory Structure](#directory-structure)
8. [File Descriptors](#file-descriptors)
9. [Segment Lists](#segment-lists)
10. [File Storage and Retrieval](#file-storage-and-retrieval)
11. [File Attributes and Permissions](#file-attributes-and-permissions)
12. [Date and Time Format](#date-and-time-format)
13. [Subdirectories](#subdirectories)
14. [Working Examples](#working-examples)
15. [Advanced Topics](#advanced-topics)
16. [Common Issues and Solutions](#common-issues-and-solutions)
17. [Implementation Guide](#implementation-guide)

---

## Introduction

OS-9 is a real-time, multitasking operating system that was ported to the TRS-80 Color Computer in 1983. It uses the RBF (Random Block File) Manager for disk file organization, which is fundamentally different from DECB (Disk Extended Color BASIC).

### Key Characteristics

- **Hierarchical filesystem**: Supports directories and subdirectories
- **Dynamic allocation**: Cluster-based allocation with variable cluster sizes
- **Metadata rich**: Timestamps, ownership, permissions
- **Portable**: Same format used across different OS-9 platforms
- **Robust**: File descriptors with multiple segments support fragmentation

### Format Variations

1. **OS-9 Level 1**: Original version for 64K systems
2. **OS-9 Level 2**: Enhanced version supporting more memory
3. **NitrOS-9**: Modern community-maintained version with enhancements

---

## Historical Context

### OS-9 on the Color Computer

OS-9 was developed by Microware Systems Corporation and ported to the 6809-based Color Computer in 1983.

**Key Features**:
- Multi-user, multitasking operating system
- Written in C with 6809 assembly
- Modular kernel design
- UNIX-like command structure
- Real-time capabilities

### OS-9 Timeline

- **1980**: OS-9 created by Microware for 6809
- **1983**: OS-9 Level 1 released for CoCo
- **1987**: OS-9 Level 2 released for CoCo 3
- **2000s**: NitrOS-9 community project begins
- **Present**: Still actively maintained by community

### Why OS-9?

Unlike DECB which was a simple file manager for BASIC programs, OS-9 provided:
- Professional development environment
- Multitasking capabilities
- Hierarchical file organization
- Memory protection
- Device independence

---

## OS-9 vs DECB Comparison

| Feature | DECB | OS-9 RBF |
|---------|------|----------|
| **Filesystem** | Flat (no subdirectories) | Hierarchical (tree structure) |
| **Allocation Unit** | Granule (9 sectors = 2304 bytes) | Cluster (variable: 1, 2, 4, 8... sectors) |
| **Metadata Location** | Track 17 (fixed) | LSN 0 (identification sector) |
| **File Allocation** | FAT (File Allocation Table) | Allocation bitmap + segment lists |
| **Directory Location** | Track 17, Sectors 3-11 (fixed) | Variable LSN, expandable |
| **Max Files** | 72 files (fixed) | Limited by disk space |
| **File Size Limit** | ~156KB (68 granules) | Up to 2GB theoretical |
| **Timestamps** | None | Creation and modification dates |
| **Permissions** | None | Owner and public read/write/execute |
| **Subdirectories** | Not supported | Full hierarchical support |
| **Fragmentation** | Simple granule chain | Segment list (flexible) |

---

## Physical Disk Structure

### Logical Sector Numbering (LSN)

OS-9 uses **Logical Sector Numbers (LSN)** to address disk sectors sequentially:

```
LSN 0:    Identification Sector (Disk Descriptor)
LSN 1+:   Allocation Bitmap
LSN x:    Root Directory (LSN specified in DD.DIR)
LSN y+:   File data and other directories
```

### Standard Disk Geometries

#### 35-Track Single-Sided (160K)
```
Tracks: 35
Sectors/Track: 18
Total Sectors: 630
Total Size: 161,280 bytes
```

#### 40-Track Double-Sided (360K)
```
Tracks: 40
Sides: 2
Sectors/Track: 18
Total Sectors: 1440
Total Size: 368,640 bytes
```

#### 80-Track Double-Sided (720K)
```
Tracks: 80
Sides: 2
Sectors/Track: 18
Total Sectors: 2880
Total Size: 737,280 bytes
```

### Cluster Concept

A **cluster** is the allocation unit in OS-9 RBF:

- Cluster size is always a power of 2: 1, 2, 4, 8, 16, 32, or 64 sectors
- Common sizes:
  - **1 sector** (256 bytes) - fine granularity, larger bitmap
  - **2 sectors** (512 bytes) - good balance
  - **4 sectors** (1024 bytes) - larger files, less overhead
  - **8 sectors** (2048 bytes) - very large files

**Formula**: Cluster Size = `DD.BIT × 256 bytes`

---

## LSN 0: Identification Sector

The **Identification Sector** (also called Disk Descriptor) resides at LSN 0 and contains all critical disk parameters.

### Complete LSN 0 Structure (256 bytes)

```
Offset  Size  Field    Type      Description
------  ----  -------  --------  ----------------------------------
0x00    3     DD.TOT   3-byte    Total number of sectors on disk
0x03    1     DD.TKS   byte      Number of tracks per side
0x04    2     DD.MAP   word      Number of bytes in allocation map
0x06    2     DD.BIT   word      Number of sectors per cluster
0x08    3     DD.DIR   3-byte    Starting LSN of root directory
0x0B    2     DD.OWN   word      Owner's user number
0x0D    1     DD.ATT   byte      Disk attributes
0x0E    2     DD.DSK   word      Disk identification number
0x10    1     DD.FMT   byte      Disk format byte
0x11    2     DD.SPT   word      Number of sectors per track
0x13    2     DD.RES   word      Reserved for future use
0x15    3     DD.BT    3-byte    LSN of bootstrap file
0x18    2     DD.BSZ   word      Size of bootstrap file (bytes)
0x1A    5     DD.DAT   5-byte    Creation date (YY MM DD HH MM)
0x1F    32    DD.NAM   string    Disk name (ASCII, null-terminated)
0x3F    1     DD.OPT   byte      Additional options
0x40    192   --       --        Reserved/unused (typically 0x00)
```

### Field Details

#### DD.TOT (0x00, 3 bytes)
Total number of sectors on the disk.

**Example**: For a 160K disk (630 sectors):
```
Bytes: 0x00 0x02 0x76
Value: (0x00 << 16) | (0x02 << 8) | 0x76 = 630
```

#### DD.TKS (0x03, 1 byte)
Number of tracks per side.

**Values**: 35, 40, 80 (most common)

#### DD.MAP (0x04, 2 bytes)
Size of allocation bitmap in bytes.

**Formula**: `DD.MAP = ceiling((DD.TOT / DD.BIT) / 8)`

**Example**: 630 sectors, 2 sectors/cluster:
- Total clusters: 630 / 2 = 315
- Bits needed: 315
- Bytes needed: ceiling(315 / 8) = 40 bytes

#### DD.BIT (0x06, 2 bytes)
Sectors per cluster (allocation unit size).

**Valid values**: 1, 2, 4, 8, 16, 32, 64 (powers of 2)

**Trade-offs**:
- **Smaller clusters** (1-2): Less wasted space, larger bitmap
- **Larger clusters** (8-16): More wasted space, smaller bitmap

#### DD.DIR (0x08, 3 bytes)
Starting LSN of root directory file descriptor.

**Example**: Root directory at LSN 100:
```
Bytes: 0x00 0x00 0x64
Value: (0x00 << 16) | (0x00 << 8) | 0x64 = 100
```

#### DD.OWN (0x0B, 2 bytes)
Owner's user number (for multi-user systems).

**Typical**: 0x0000 for single-user disks

#### DD.ATT (0x0D, 1 byte)
Disk attributes flags.

**Bit flags**:
```
Bit 7: Reserved
Bit 6: Reserved
Bit 5: Public read
Bit 4: Public write
Bit 3: Public execute
Bit 2: Reserved
Bit 1: Owner write
Bit 0: Owner read
```

#### DD.DSK (0x0E, 2 bytes)
Disk identification number (arbitrary, user-defined).

#### DD.FMT (0x10, 1 byte)
Format descriptor byte.

**Bit layout**:
```
Bit 7-4: Reserved
Bit 3-2: Reserved
Bit 1:   Sides (0=single, 1=double)
Bit 0:   Density (0=single, 1=double)
```

**Examples**:
- 0x00: Single-density, single-sided
- 0x01: Double-density, single-sided
- 0x02: Single-density, double-sided
- 0x03: Double-density, double-sided

#### DD.SPT (0x11, 2 bytes)
Sectors per track.

**Common values**: 18 (standard CoCo), 9 (some formats)

#### DD.BT (0x15, 3 bytes)
LSN of system bootstrap file (typically OS9Boot).

**Note**: 0x000000 if no bootstrap

#### DD.BSZ (0x18, 2 bytes)
Size of bootstrap file in bytes.

#### DD.DAT (0x1A, 5 bytes)
Disk creation date and time.

**Format**: YY MM DD HH MM (5 bytes)

**Example**: January 15, 2025, 14:30
```
Bytes: 0x7D 0x01 0x0F 0x0E 0x1E
       125  1    15   14   30
Year: 1900 + 125 = 2025
```

#### DD.NAM (0x1F, 32 bytes)
Disk name (ASCII string, null-terminated).

**Example**: "NITROS9_BOOT"
```
Bytes: 4E 49 54 52 4F 53 39 5F 42 4F 4F 54 00 00 ...
```

#### DD.OPT (0x3F, 1 byte)
Additional options byte (format-specific).

---

## Allocation Bitmap

### Structure

The allocation bitmap starts at **LSN 1** (immediately after the identification sector).

**Size**: Specified by `DD.MAP` field (in bytes)

**Function**: Each bit represents one cluster:
- **Bit = 0**: Cluster is **free** (available for allocation)
- **Bit = 1**: Cluster is **allocated** (in use or defective)

### Bitmap Organization

Bits are organized with **MSB first** (bit 7 is cluster 0 of the byte).

```
Byte 0: [Cluster 0][1][2][3][4][5][6][7]
         Bit 7→0

Byte 1: [Cluster 8][9][10][11][12][13][14][15]
```

### Example

Given DD.MAP = 40 bytes (320 bits), you can manage 320 clusters.

If DD.BIT = 2 (sectors per cluster), the disk can have:
```
320 clusters × 2 sectors/cluster = 640 sectors
```

### Reading the Bitmap

To check if cluster N is allocated:

```python
byte_index = N // 8
bit_index = 7 - (N % 8)  # MSB first

is_allocated = (bitmap[byte_index] & (1 << bit_index)) != 0
```

**Example**: Check cluster 15
```python
byte_index = 15 // 8 = 1
bit_index = 7 - (15 % 8) = 7 - 7 = 0

# Check bit 0 of byte 1
is_allocated = (bitmap[1] & 0x01) != 0
```

### Bitmap Sectors

The bitmap may span multiple sectors if large.

**Example**: DD.MAP = 512 bytes requires 2 sectors (LSN 1-2).

---

## Directory Structure

### Directory Files

In OS-9, **directories are files** with a special attribute (bit 7 set in FD.ATT).

A directory file contains a list of 32-byte directory entries.

### Directory Entry Format (32 bytes)

```
Offset  Size  Field    Description
------  ----  -------  ----------------------------------
0x00    28    DIR.NM   Filename (ASCII, last char bit 7 set)
0x1C    1     DIR.AT   File attributes
0x1D    3     DIR.FD   LSN of file descriptor (3-byte)
```

### DIR.NM Field (28 bytes)

Filename is stored with the **last character having bit 7 set** as an end marker.

**Example**: Filename "STARTUP"
```
Bytes: 53 54 41 52 54 55 D0 00 00 ... (rest zeros)
       S  T  A  R  T  U  P|
                         ↑ bit 7 set (0x50 + 0x80 = 0xD0)
```

**Parsing**:
```python
filename = ""
for i in range(28):
    char = dir_entry[i]
    if char == 0:
        break
    if char & 0x80:
        filename += chr(char & 0x7F)
        break
    filename += chr(char)
```

### DIR.AT Field (1 byte)

File attribute flags.

**Bit layout**:
```
Bit 7: Directory (1=dir, 0=file)
Bit 6: Shared file
Bit 5: Public read
Bit 4: Public write
Bit 3: Public execute
Bit 2: Reserved
Bit 1: Owner write
Bit 0: Owner read
```

**Examples**:
- 0x83: Directory with owner read/write (0b10000011)
- 0x03: File with owner read/write (0b00000011)
- 0x2B: File with public read/execute, owner read/write/execute (0b00101011)

### DIR.FD Field (3 bytes)

LSN of the file's file descriptor sector.

**Example**: File descriptor at LSN 250
```
Bytes: 0x00 0x00 0xFA
Value: (0x00 << 16) | (0x00 << 8) | 0xFA = 250
```

### Special Directory Entries

Every directory contains at least two entries:

1. **"." (dot)**: Points to itself (current directory)
2. **".." (dot-dot)**: Points to parent directory (0 for root)

### Root Directory

- Location specified by `DD.DIR` in LSN 0
- Parent pointer (..) is 0x000000 (no parent)
- Contains initial files and subdirectories

---

## File Descriptors

Every file (including directories) has a **File Descriptor (FD)** sector that contains metadata and a segment list.

### File Descriptor Structure (256 bytes)

```
Offset  Size  Field    Description
------  ----  -------  ----------------------------------
0x00    1     FD.ATT   File attributes
0x01    2     FD.OWN   Owner's user number
0x03    5     FD.DAT   Date last modified (YY MM DD HH MM)
0x08    1     FD.LNK   Link count
0x09    4     FD.SIZ   File size in bytes (4-byte)
0x0D    3     FD.DCR   Date created (YY MM DD)
0x10    240   FD.SEG   Segment list (48 entries max)
```

### FD.ATT Field (1 byte)

Same format as DIR.AT:

```
Bit 7: Directory (1=dir, 0=file)
Bit 6: Shared file
Bit 5: Public read
Bit 4: Public write
Bit 3: Public execute
Bit 2: Reserved
Bit 1: Owner write
Bit 0: Owner read
```

### FD.OWN Field (2 bytes)

Owner's user ID (0x0000 for single-user systems).

### FD.DAT Field (5 bytes)

Date last modified: YY MM DD HH MM

**Example**: March 25, 2024, 09:45
```
Bytes: 0x7C 0x03 0x19 0x09 0x2D
       124  3    25   9    45
Year: 1900 + 124 = 2024
```

### FD.LNK Field (1 byte)

Link count (number of directory entries pointing to this FD).

- Normal files: 1
- Hard links: >1
- Directories: ≥2 (includes "." entry)

### FD.SIZ Field (4 bytes)

File size in bytes (32-bit big-endian).

**Example**: 10,240 bytes
```
Bytes: 0x00 0x00 0x28 0x00
Value: (0x00 << 24) | (0x00 << 16) | (0x28 << 8) | 0x00 = 10240
```

### FD.DCR Field (3 bytes)

Date created: YY MM DD

**Example**: January 1, 2025
```
Bytes: 0x7D 0x01 0x01
       125  1    1
Year: 1900 + 125 = 2025
```

### FD.SEG Field (240 bytes)

Segment list containing up to **48 segments** (5 bytes each).

See next section for details.

---

## Segment Lists

### Segment Structure

Each segment is **5 bytes**:

```
Bytes 0-2: Starting LSN (3-byte, big-endian)
Bytes 3-4: Sector count (2-byte, big-endian)
```

### Segment List Layout

The segment list starts at offset 0x10 in the file descriptor and can contain up to **48 segments**:

```
Offset  Segment
------  -------
0x10    Segment 0
0x15    Segment 1
0x1A    Segment 2
...
0xF5    Segment 47
0xFA-0xFF: Unused (6 bytes)
```

### End of List Marker

The segment list ends when a segment with **sector count = 0** is encountered.

### Example Segment List

File uses 3 segments:
1. LSN 100, 10 sectors
2. LSN 200, 5 sectors
3. LSN 350, 3 sectors

```
Offset 0x10: 00 00 64 00 0A  (LSN 100, 10 sectors)
Offset 0x15: 00 00 C8 00 05  (LSN 200, 5 sectors)
Offset 0x1A: 00 01 5E 00 03  (LSN 350, 3 sectors)
Offset 0x1F: 00 00 00 00 00  (End marker)
```

Total file data: (10 + 5 + 3) × 256 = 4,608 bytes maximum

Actual size determined by FD.SIZ field.

### Reading Segment List

```python
segments = []
offset = 0x10

while offset + 5 <= 256:
    lsn = (fd[offset] << 16) | (fd[offset+1] << 8) | fd[offset+2]
    count = (fd[offset+3] << 8) | fd[offset+4]

    if count == 0:
        break  # End of list

    segments.append((lsn, count))
    offset += 5

return segments
```

### Maximum File Size

With 48 segments and maximum sector count per segment:

```
Max sectors per segment: 65,535 (2-byte limit)
Max segments: 48
Theoretical max: 48 × 65,535 × 256 = 804,257,280 bytes (~804 MB)
Practical max: Limited by FD.SIZ (4 bytes) = 4,294,967,295 bytes (~4 GB)
```

---

## File Storage and Retrieval

### Writing a File

1. **Calculate clusters needed**
   ```
   file_size = 10,000 bytes
   cluster_size = 512 bytes (2 sectors)
   clusters_needed = ceiling(10,000 / 512) = 20 clusters
   ```

2. **Find free clusters** (scan allocation bitmap)

3. **Group into segments** (contiguous clusters)
   ```
   Found free: Clusters 10-15, 20-25, 30-35 (3 segments)
   ```

4. **Calculate LSNs**
   ```
   Cluster 10: LSN = 10 × 2 = 20
   Cluster 20: LSN = 20 × 2 = 40
   Cluster 30: LSN = 30 × 2 = 60
   ```

5. **Create segment list**
   ```
   Segment 1: LSN 20, 12 sectors (6 clusters)
   Segment 2: LSN 40, 12 sectors (6 clusters)
   Segment 3: LSN 60, 12 sectors (6 clusters)
   ```

6. **Write file data** to sectors

7. **Create file descriptor**
   - Set FD.SIZ = 10,000
   - Store segment list
   - Set timestamps
   - Set attributes and owner

8. **Create directory entry**
   - Set filename with bit 7 on last char
   - Set DIR.AT attributes
   - Set DIR.FD to FD sector LSN

9. **Update allocation bitmap** (mark clusters as allocated)

### Reading a File

1. **Find directory entry** (search directory file)

2. **Read file descriptor** (at LSN from DIR.FD)

3. **Extract segment list** from FD

4. **Read data from segments**
   ```python
   file_data = bytearray()
   for lsn, count in segments:
       for i in range(count):
           sector = read_lsn(lsn + i)
           file_data.extend(sector)
   ```

5. **Trim to actual size**
   ```python
   file_data = file_data[:fd_siz]
   ```

### File Fragmentation

OS-9 handles fragmentation elegantly via segment lists.

**Example**: 1000-byte file spread across 3 non-contiguous areas:
```
Segment 1: LSN 50, 2 sectors (512 bytes)
Segment 2: LSN 150, 2 sectors (512 bytes)
Segment 3: LSN 300, 1 sector (256 bytes, but only 232 used)

Total: 5 sectors = 1280 bytes
Actual file size (FD.SIZ): 1000 bytes
```

---

## File Attributes and Permissions

### Attribute Byte (FD.ATT / DIR.AT)

```
Bit 7: D (Directory)    - 1 = directory, 0 = file
Bit 6: S (Shared)       - Sharable file
Bit 5: PR (Public Read) - Public read permission
Bit 4: PW (Public Write)- Public write permission
Bit 3: PE (Public Exec) - Public execute permission
Bit 2: (Reserved)
Bit 1: W (Owner Write)  - Owner write permission
Bit 0: R (Owner Read)   - Owner read permission
```

### Common Attribute Values

| Value | Binary | Meaning |
|-------|--------|---------|
| 0x01 | 00000001 | Owner read only |
| 0x03 | 00000011 | Owner read/write |
| 0x07 | 00000111 | Owner read/write/execute |
| 0x2B | 00101011 | Owner RWE, Public RE |
| 0x3F | 00111111 | Owner RWE, Public RWE |
| 0x83 | 10000011 | Directory, owner RW |
| 0x87 | 10000111 | Directory, owner RWE |
| 0xAB | 10101011 | Directory, owner RWE, public RE |

### Permission Checking

**Read check**:
```python
def can_read(attr, user_id, owner_id):
    if user_id == owner_id:
        return (attr & 0x01) != 0  # Owner read
    else:
        return (attr & 0x20) != 0  # Public read
```

**Write check**:
```python
def can_write(attr, user_id, owner_id):
    if user_id == owner_id:
        return (attr & 0x02) != 0  # Owner write
    else:
        return (attr & 0x10) != 0  # Public write
```

---

## Date and Time Format

OS-9 uses a special date format.

### Date Fields

**Modified date** (FD.DAT): 5 bytes - YY MM DD HH MM
**Created date** (FD.DCR): 3 bytes - YY MM DD

### Year Encoding

Years are stored as **offset from 1900**.

```
Stored value: YY
Actual year: 1900 + YY
```

**Examples**:
- 0x00 = 1900
- 0x53 (83) = 1983
- 0x7D (125) = 2025
- 0xFF (255) = 2155

### Month, Day, Hour, Minute

Standard binary values (1-based for month/day):
- **Month**: 1-12
- **Day**: 1-31
- **Hour**: 0-23
- **Minute**: 0-59

### Example Parsing

```python
def parse_date_5(bytes):
    year = 1900 + bytes[0]
    month = bytes[1]
    day = bytes[2]
    hour = bytes[3]
    minute = bytes[4]
    return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"

# Example: 0x7D 0x03 0x0F 0x0E 0x1E
# Result: "2025-03-15 14:30"
```

---

## Subdirectories

### Creating Subdirectories

1. **Create directory file**
   - Set FD.ATT bit 7 (directory flag)
   - Initialize with "." and ".." entries

2. **Add entries**
   ```
   Entry 0: "." → points to itself
   Entry 1: ".." → points to parent directory
   ```

3. **Add to parent directory**
   - Create DIR entry pointing to directory's FD

### Traversing Directories

**Example path**: `/CMDS/BASIC/LIST`

1. Start at root directory (from DD.DIR)
2. Find "CMDS" entry → read its FD
3. Read CMDS directory data
4. Find "BASIC" entry → read its FD
5. Read BASIC directory data
6. Find "LIST" entry → read its FD
7. Read LIST file data

### Maximum Directory Depth

OS-9 has no hard limit on directory depth, but practical limits:
- Memory for pathname buffers
- Stack space for recursive operations
- Typically limited to ~32 levels

---

## Working Examples

### Example 1: Simple File

**File**: HELLO.TXT (150 bytes)
**Cluster size**: 2 sectors (512 bytes)
**Needs**: 1 cluster

**Allocation**:
- Cluster 10 allocated (LSN 20-21)

**File Descriptor** (LSN 100):
```
FD.ATT: 0x03 (owner read/write)
FD.OWN: 0x0000
FD.DAT: 0x7D 0x01 0x0F 0x0E 0x1E (2025-01-15 14:30)
FD.LNK: 0x01
FD.SIZ: 0x00 0x00 0x00 0x96 (150 bytes)
FD.DCR: 0x7D 0x01 0x0F (2025-01-15)
FD.SEG[0]: 00 00 14 00 02 (LSN 20, 2 sectors)
FD.SEG[1]: 00 00 00 00 00 (end marker)
```

**Directory Entry**:
```
DIR.NM: "HELLO.TX" + 0xD4 ('T' with bit 7) (0x54 | 0x80 = 0xD4)
DIR.AT: 0x03
DIR.FD: 0x00 0x00 0x64 (LSN 100)
```

**Data**:
- Sectors read: 2 (512 bytes)
- Actual data: 150 bytes
- Trailing: 362 bytes (ignored)

### Example 2: Fragmented File

**File**: DATA.BIN (5000 bytes)
**Cluster size**: 4 sectors (1024 bytes)
**Needs**: 5 clusters

**Allocation** (fragmented):
- Cluster 5-6 (LSN 20-27, 8 sectors)
- Cluster 10-12 (LSN 40-51, 12 sectors)

**File Descriptor** (LSN 200):
```
FD.SIZ: 0x00 0x00 0x13 0x88 (5000 bytes)
FD.SEG[0]: 00 00 14 00 08 (LSN 20, 8 sectors)
FD.SEG[1]: 00 00 28 00 0C (LSN 40, 12 sectors)
FD.SEG[2]: 00 00 00 00 00 (end marker)
```

**Data retrieval**:
```
Read LSN 20-27: 2048 bytes
Read LSN 40-51: 3072 bytes
Total: 5120 bytes
Trim to: 5000 bytes (FD.SIZ)
```

### Example 3: Directory with Files

**Directory**: GAMES (directory)

**Directory FD** (LSN 150):
```
FD.ATT: 0x87 (directory, owner read/write/execute)
FD.SIZ: 0x00 0x00 0x00 0xC0 (192 bytes = 6 entries)
FD.SEG[0]: 00 00 C8 00 01 (LSN 200, 1 sector)
```

**Directory data** (LSN 200):
```
Entry 0 (32 bytes):
  DIR.NM: "." + 0xAE (bit 7 on '.')
  DIR.AT: 0x87
  DIR.FD: 00 00 96 (LSN 150, points to itself)

Entry 1 (32 bytes):
  DIR.NM: ".." + 0xAE
  DIR.AT: 0x87
  DIR.FD: 00 00 0A (LSN 10, parent directory)

Entry 2 (32 bytes):
  DIR.NM: "PACMA" + 0xCE ('N' with bit 7)
  DIR.AT: 0x07 (owner read/write/execute)
  DIR.FD: 00 01 2C (LSN 300)

Entry 3 (32 bytes):
  DIR.NM: "TETRI" + 0xD3 ('S' with bit 7)
  DIR.AT: 0x07
  DIR.FD: 00 01 5E (LSN 350)

Entry 4-5: (unused, zeros or garbage)
```

---

## Advanced Topics

### Bootstrap Loading

**DD.BT field**: LSN of bootstrap file (OS9Boot)
**DD.BSZ field**: Size of bootstrap file

**Boot process**:
1. ROM reads LSN 0
2. Loads bootstrap file from DD.BT
3. Executes bootstrap code
4. Bootstrap loads OS-9 kernel
5. Kernel initializes system

### Hard Links

Multiple directory entries pointing to same FD.

**Example**:
```
/CMDS/DIR → FD at LSN 100 (FD.LNK = 2)
/CMDS/LS  → FD at LSN 100 (same FD)
```

Deleting one entry decrements FD.LNK. File is only freed when FD.LNK reaches 0.

### Sparse Files

OS-9 doesn't explicitly support sparse files, but segments can skip ranges.

**Theoretical sparse file**:
```
Segment 1: LSN 100, 1 sector  (bytes 0-255)
Segment 2: LSN 500, 1 sector  (bytes 1,000,000-1,000,255)
FD.SIZ: 1,000,256
```

Reading between segments would return garbage (not zeros).

### Symbolic Links

OS-9 Level 2 introduced symbolic links (separate from hard links).

Implementation varies by OS-9 version.

### Device Files

OS-9 supports device files in filesystem.

- Special file type (not regular or directory)
- Points to device driver module
- Allows unified file I/O interface

### File Locking

OS-9 supports file locking for multi-user access.

- Shared read locks
- Exclusive write locks
- Enforced by RBF manager

---

## Common Issues and Solutions

### Issue 1: Invalid LSN 0 Detection

**Problem**: Disk appears not to be OS-9 formatted.

**Causes**:
- Disk is DECB formatted
- Corrupted identification sector
- Wrong disk image offset

**Solution**:
```python
# Validate key fields
if dd_tot != expected_sectors:
    print("Total sectors mismatch")
if dd_spt not in [9, 18]:
    print("Invalid sectors per track")
if dd_bit not in [1, 2, 4, 8, 16]:
    print("Invalid cluster size")
```

### Issue 2: Allocation Bitmap Corruption

**Problem**: Free space calculation is wrong.

**Causes**:
- Bitmap not updated after file operations
- Disk not cleanly unmounted

**Solution**:
- Rebuild bitmap by scanning all file descriptors
- Mark all segments as allocated
- Remaining bits are free

### Issue 3: Segment List Overflow

**Problem**: File has more than 48 segments (highly fragmented).

**Causes**:
- Excessive fragmentation
- Many small allocations

**Solutions**:
- OS-9 uses **extension file descriptors** for files with >48 segments
- Last segment points to another FD with more segments
- Rarely encountered in practice

### Issue 4: Circular Directory References

**Problem**: Directory tree has a loop (A → B → C → A).

**Causes**:
- Filesystem corruption
- Improper hard links in directories

**Detection**:
```python
visited_fds = set()

def traverse(fd_lsn):
    if fd_lsn in visited_fds:
        raise Exception("Circular reference detected")
    visited_fds.add(fd_lsn)
    # ... continue traversal
```

### Issue 5: Date Overflow

**Problem**: Dates beyond year 2155.

**Cause**: 1-byte year field (0-255) + 1900 base.

**Solutions**:
- NitrOS-9 uses different epoch
- Extended formats may use 2-byte years
- Check OS-9 version documentation

### Issue 6: Filename End Marker Missing

**Problem**: Filenames appear corrupted or too long.

**Cause**: Last character doesn't have bit 7 set.

**Solution**:
```python
# Scan for first null or 28 bytes
for i in range(28):
    if data[i] & 0x80:
        name_end = i + 1
        break
    if data[i] == 0:
        name_end = i
        break
else:
    name_end = 28  # Use all 28 bytes
```

---

## Implementation Guide

### Minimal Read-Only Implementation

**1. Detect OS-9 Disk**
```python
def is_os9(disk_data):
    lsn0 = disk_data[0:256]
    dd_tot = parse_3byte(lsn0[0:3])
    dd_spt = parse_2byte(lsn0[0x11:0x13])
    dd_bit = parse_2byte(lsn0[0x06:0x08])

    # Validate
    if dd_spt not in [9, 18]:
        return False
    if dd_bit not in [1, 2, 4, 8, 16]:
        return False
    # ... more checks

    return True
```

**2. Parse LSN 0**
```python
def parse_lsn0(disk_data):
    lsn0 = disk_data[0:256]
    descriptor = {
        'dd_tot': parse_3byte(lsn0[0x00:0x03]),
        'dd_map': parse_2byte(lsn0[0x04:0x06]),
        'dd_bit': parse_2byte(lsn0[0x06:0x08]),
        'dd_dir': parse_3byte(lsn0[0x08:0x0B]),
        'dd_spt': parse_2byte(lsn0[0x11:0x13]),
        'dd_nam': lsn0[0x1F:0x3F].decode('ascii', errors='ignore').rstrip('\x00'),
        # ... other fields
    }
    return descriptor
```

**3. Read Allocation Bitmap**
```python
def read_allocation_map(disk_data, descriptor):
    map_bytes = descriptor['dd_map']
    lsn = 1
    bitmap = bytearray()

    while map_bytes > 0:
        sector = read_lsn(disk_data, lsn)
        bytes_to_copy = min(256, map_bytes)
        bitmap.extend(sector[:bytes_to_copy])
        map_bytes -= bytes_to_copy
        lsn += 1

    return bitmap
```

**4. Read Root Directory**
```python
def read_root_directory(disk_data, descriptor):
    root_fd_lsn = descriptor['dd_dir']
    root_fd = read_file_descriptor(disk_data, root_fd_lsn)

    # Read directory file data
    dir_data = read_file_data(disk_data, root_fd)

    # Parse directory entries
    entries = []
    for offset in range(0, len(dir_data), 32):
        entry_data = dir_data[offset:offset+32]
        entry = parse_directory_entry(entry_data)
        if entry:
            entries.append(entry)

    return entries
```

**5. Parse Directory Entry**
```python
def parse_directory_entry(data):
    if data[0] == 0:
        return None

    # Parse filename
    filename = ""
    for i in range(28):
        char = data[i]
        if char == 0:
            break
        if char & 0x80:
            filename += chr(char & 0x7F)
            break
        filename += chr(char)

    dir_at = data[28]
    dir_fd = parse_3byte(data[29:32])

    return {
        'name': filename,
        'attr': dir_at,
        'fd_lsn': dir_fd
    }
```

**6. Read File Descriptor**
```python
def read_file_descriptor(disk_data, fd_lsn):
    fd_sector = read_lsn(disk_data, fd_lsn)

    fd_att = fd_sector[0x00]
    fd_siz = parse_4byte(fd_sector[0x09:0x0D])

    # Parse segment list
    segments = []
    offset = 0x10
    while offset + 5 <= 256:
        lsn = parse_3byte(fd_sector[offset:offset+3])
        count = parse_2byte(fd_sector[offset+3:offset+5])
        if count == 0:
            break
        segments.append((lsn, count))
        offset += 5

    return {
        'attr': fd_att,
        'size': fd_siz,
        'segments': segments
    }
```

**7. Read File Data**
```python
def read_file_data(disk_data, fd):
    file_data = bytearray()

    for lsn, count in fd['segments']:
        for i in range(count):
            sector = read_lsn(disk_data, lsn + i)
            file_data.extend(sector)

    # Trim to actual size
    file_data = file_data[:fd['size']]
    return bytes(file_data)
```

**8. Helper Functions**
```python
def read_lsn(disk_data, lsn):
    offset = lsn * 256
    return disk_data[offset:offset+256]

def parse_2byte(data):
    return (data[0] << 8) | data[1]

def parse_3byte(data):
    return (data[0] << 16) | (data[1] << 8) | data[2]

def parse_4byte(data):
    return (data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]
```

### Full Implementation (Read/Write)

For a full implementation, add:

1. **Write file**
   - Find free clusters in bitmap
   - Create segment list
   - Write file data
   - Create file descriptor
   - Add directory entry
   - Update allocation bitmap

2. **Delete file**
   - Remove directory entry
   - Free clusters in bitmap
   - Decrement FD link count
   - Delete FD if link count = 0

3. **Create directory**
   - Allocate clusters
   - Create FD with directory flag
   - Initialize with "." and ".."
   - Add entry to parent

4. **Format disk**
   - Create LSN 0 with parameters
   - Initialize allocation bitmap
   - Create root directory
   - Mark system areas as allocated

---

## Testing and Validation

### Test Cases

1. **Detection**
   - Test with OS-9 disk → should return True
   - Test with DECB disk → should return False
   - Test with corrupted disk → should handle gracefully

2. **LSN 0 Parsing**
   - Validate all fields parse correctly
   - Check date conversion
   - Verify disk name extraction

3. **Directory Reading**
   - Read root directory
   - Handle empty directories
   - Handle "." and ".." entries
   - Parse filenames with bit 7 marker

4. **File Reading**
   - Read small files (1 sector)
   - Read large files (multiple segments)
   - Read fragmented files
   - Verify size trimming works

5. **Edge Cases**
   - Empty files (0 bytes)
   - Maximum size files
   - Files with 48 segments
   - Deeply nested directories

### Sample OS-9 Disks for Testing

- **OS-9 Level 1 boot disk**: Basic OS-9 system
- **NitrOS-9 boot disk**: Modern variant
- **CMDS disk**: OS-9 utilities
- **User data disk**: Various file types

---

## References

### Official Documentation

- **OS-9 Technical Manual** - Microware Systems Corporation
  - Available: http://www.icdia.co.uk/microware/tech/tech_7.pdf
  - Chapter 7: Disk File Organization

- **OS-9 System Programmer's Manual**
  - Available: https://www.roug.org/soren/6809/os9sysprog.pdf

- **NitrOS-9 Project**
  - Website: https://sourceforge.net/projects/nitros9/
  - Wiki: https://sourceforge.net/p/nitros9/wiki/

### Community Resources

- **Color Computer Archive**
  - https://colorcomputerarchive.com/

- **OS-9 Underground**
  - https://www.coco3.com/os9/

- **CoCo Disk BASIC vs OS-9 comparison**
  - https://subethasoftware.com/

### Tools

- **ToolShed** - OS-9 disk utilities
  - https://toolshed.sourceforge.net/

- **os9 tool** - Command-line RBF access
  - Part of ToolShed package

- **MAME** - Emulator with OS-9 support
  - https://www.mamedev.org/

---

## Appendix A: Quick Reference

### LSN 0 Field Offsets

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0x00 | 3 | DD.TOT | Total sectors |
| 0x03 | 1 | DD.TKS | Tracks per side |
| 0x04 | 2 | DD.MAP | Bitmap size (bytes) |
| 0x06 | 2 | DD.BIT | Sectors per cluster |
| 0x08 | 3 | DD.DIR | Root directory LSN |
| 0x0B | 2 | DD.OWN | Owner ID |
| 0x0D | 1 | DD.ATT | Disk attributes |
| 0x0E | 2 | DD.DSK | Disk ID |
| 0x10 | 1 | DD.FMT | Format byte |
| 0x11 | 2 | DD.SPT | Sectors per track |
| 0x15 | 3 | DD.BT | Bootstrap LSN |
| 0x18 | 2 | DD.BSZ | Bootstrap size |
| 0x1A | 5 | DD.DAT | Creation date |
| 0x1F | 32 | DD.NAM | Disk name |

### Directory Entry Structure (32 bytes)

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0x00 | 28 | DIR.NM | Filename (last char bit 7 set) |
| 0x1C | 1 | DIR.AT | Attributes |
| 0x1D | 3 | DIR.FD | File descriptor LSN |

### File Descriptor Structure

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0x00 | 1 | FD.ATT | File attributes |
| 0x01 | 2 | FD.OWN | Owner ID |
| 0x03 | 5 | FD.DAT | Modified date (YY MM DD HH MM) |
| 0x08 | 1 | FD.LNK | Link count |
| 0x09 | 4 | FD.SIZ | File size (bytes) |
| 0x0D | 3 | FD.DCR | Created date (YY MM DD) |
| 0x10 | 240 | FD.SEG | Segment list (48 × 5 bytes) |

### Attribute Bits

| Bit | Name | Description |
|-----|------|-------------|
| 7 | D | Directory flag |
| 6 | S | Shared file |
| 5 | PR | Public read |
| 4 | PW | Public write |
| 3 | PE | Public execute |
| 2 | - | Reserved |
| 1 | W | Owner write |
| 0 | R | Owner read |

### Common Cluster Sizes

| Sectors | Bytes | Use Case |
|---------|-------|----------|
| 1 | 256 | Very small files, more overhead |
| 2 | 512 | Good balance |
| 4 | 1024 | Standard for most disks |
| 8 | 2048 | Large files, less overhead |

---

## Revision History

- **Version 1.0** (2025) - Initial comprehensive documentation

---

## License and Credits

This document is provided for educational purposes to preserve and document the OS-9 RBF file system format.

**Based on**:
- OS-9 Technical Manual by Microware Systems Corporation
- NitrOS-9 Project documentation
- Community research and reverse engineering

**Created by**: reyco2000 (Reinaldo Torres) using Claude Code

---

*End of OS-9 RBF Format Specification*
