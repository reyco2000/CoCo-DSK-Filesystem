#!/usr/bin/env python3
"""
TRS-80 Color Computer OS-9 RBF File System Tool

Coded by ChipShift Reyco2000@gmail.com Using Claude Code
(C) 2025

This script provides support for OS-9 Level 1/2 and NitrOS-9 disk images
using the RBF (Random Block File) filesystem.

OS-9 RBF Format Details:
- Hierarchical directory structure (supports subdirectories)
- Variable cluster size (1, 2, 4, 8... sectors per cluster)
- LSN 0: Identification sector (disk descriptor)
- LSN 1+: Allocation bitmap
- File descriptors contain segment lists for file data
- Supports timestamps, ownership, and permissions
"""

import struct
import os
import sys
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass
from datetime import datetime


@dataclass
class OS9DiskDescriptor:
    """OS-9 Identification Sector (LSN 0) structure"""
    dd_tot: int = 0          # Total number of sectors on disk (3 bytes)
    dd_tks: int = 0          # Number of tracks per side (1 byte)
    dd_map: int = 0          # Number of bytes in allocation map (2 bytes)
    dd_bit: int = 0          # Number of sectors per cluster (2 bytes)
    dd_dir: int = 0          # Starting LSN of root directory (3 bytes)
    dd_own: int = 0          # Owner's user number (2 bytes)
    dd_att: int = 0          # Disk attributes (1 byte)
    dd_dsk: int = 0          # Disk identification number (2 bytes)
    dd_fmt: int = 0          # Disk format (density, sides) (1 byte)
    dd_spt: int = 0          # Number of sectors per track (2 bytes)
    dd_res: int = 0          # Reserved bytes (2 bytes)
    dd_bt: int = 0           # System bootstrap LSN (3 bytes)
    dd_bsz: int = 0          # Size of bootstrap file in bytes (2 bytes)
    dd_dat: tuple = ()       # Creation date (YY, MM, DD, HH, MM) (5 bytes)
    dd_nam: str = ""         # Disk name (32 bytes ASCII)
    dd_opt: int = 0          # Additional options (1 byte)

    def __str__(self):
        date_str = f"{self.dd_dat[0]:02d}/{self.dd_dat[1]:02d}/{self.dd_dat[2]:02d}" if len(self.dd_dat) >= 3 else "N/A"
        return f"""OS-9 Disk Descriptor:
  Disk Name: {self.dd_nam}
  Total Sectors: {self.dd_tot}
  Tracks: {self.dd_tks}
  Sectors/Track: {self.dd_spt}
  Sectors/Cluster: {self.dd_bit}
  Cluster Size: {self.dd_bit * 256} bytes
  Allocation Map: {self.dd_map} bytes
  Root Directory LSN: {self.dd_dir}
  Format: 0x{self.dd_fmt:02X}
  Creation Date: {date_str}
  Disk ID: 0x{self.dd_dsk:04X}
"""


@dataclass
class OS9DirectoryEntry:
    """OS-9 Directory Entry structure (32 bytes)"""
    dir_nm: str              # Filename (28 bytes, last char has bit 7 set)
    dir_at: int              # File attributes (1 byte)
    dir_fd: int              # LSN of file descriptor sector (3 bytes)

    def __str__(self):
        # Attribute flags
        attr_flags = []
        if self.dir_at & 0x80:
            attr_flags.append("DIR")
        if self.dir_at & 0x40:
            attr_flags.append("SHARE")
        if self.dir_at & 0x20:
            attr_flags.append("PR")  # Public read
        if self.dir_at & 0x10:
            attr_flags.append("PW")  # Public write
        if self.dir_at & 0x08:
            attr_flags.append("PE")  # Public execute
        if self.dir_at & 0x02:
            attr_flags.append("W")   # Owner write
        if self.dir_at & 0x01:
            attr_flags.append("R")   # Owner read

        attr_str = " ".join(attr_flags) if attr_flags else "NONE"
        return f"{self.dir_nm:<28} FD@{self.dir_fd:<6} {attr_str}"


@dataclass
class OS9FileDescriptor:
    """OS-9 File Descriptor structure"""
    fd_att: int = 0          # File attributes (1 byte)
    fd_own: int = 0          # Owner's user number (2 bytes)
    fd_dat: tuple = ()       # Date last modified (YY, MM, DD, HH, MM) (5 bytes)
    fd_lnk: int = 0          # Link count (1 byte)
    fd_siz: int = 0          # File size in bytes (4 bytes)
    fd_dcr: tuple = ()       # Date created (YY, MM, DD) (3 bytes)
    fd_seg: List[Tuple[int, int]] = None  # Segment list: [(LSN, num_sectors), ...]

    def __post_init__(self):
        if self.fd_seg is None:
            self.fd_seg = []

    def __str__(self):
        mod_date = f"{self.fd_dat[0]:02d}/{self.fd_dat[1]:02d}/{self.fd_dat[2]:02d}" if len(self.fd_dat) >= 3 else "N/A"
        cr_date = f"{self.fd_dcr[0]:02d}/{self.fd_dcr[1]:02d}/{self.fd_dcr[2]:02d}" if len(self.fd_dcr) >= 3 else "N/A"
        is_dir = "DIR" if self.fd_att & 0x80 else "FILE"
        return f"""File Descriptor:
  Type: {is_dir}
  Size: {self.fd_siz} bytes
  Modified: {mod_date}
  Created: {cr_date}
  Owner: {self.fd_own}
  Links: {self.fd_lnk}
  Segments: {len(self.fd_seg)}
"""


class OS9Image:
    """Handler for OS-9 RBF disk images"""

    SECTOR_SIZE = 256

    def __init__(self, filename: str):
        self.filename = filename
        self.data = b''
        self.descriptor = OS9DiskDescriptor()
        self.allocation_map = bytearray()
        self.root_dir_entries = []

    def mount(self) -> bool:
        """Mount (open and parse) an OS-9 disk image file"""
        try:
            with open(self.filename, 'rb') as f:
                self.data = f.read()

            # Parse LSN 0 (identification sector)
            if not self._parse_disk_descriptor():
                return False

            # Read allocation bitmap
            self._read_allocation_map()

            # Read root directory
            self._read_root_directory()

            return True
        except Exception as e:
            print(f"Error mounting OS-9 disk image: {e}")
            import traceback
            traceback.print_exc()
            return False

    def is_os9_disk(self) -> bool:
        """
        Detect if this is an OS-9 formatted disk.
        Validates disk descriptor fields for consistency.
        """
        if len(self.data) < self.SECTOR_SIZE:
            return False

        try:
            # Read LSN 0
            lsn0 = self.data[0:self.SECTOR_SIZE]

            # Extract key fields
            dd_tot = (lsn0[0x00] << 16) | (lsn0[0x01] << 8) | lsn0[0x02]
            dd_map = (lsn0[0x04] << 8) | lsn0[0x05]
            dd_bit = (lsn0[0x06] << 8) | lsn0[0x07]
            dd_dir = (lsn0[0x08] << 16) | (lsn0[0x09] << 8) | lsn0[0x0A]
            dd_spt = (lsn0[0x11] << 8) | lsn0[0x12]

            # Validate total sectors matches file size
            expected_sectors = len(self.data) // self.SECTOR_SIZE
            if dd_tot != expected_sectors:
                # Allow some tolerance for header variations
                if abs(dd_tot - expected_sectors) > 10:
                    return False

            # Check sectors per track is reasonable (typically 18 for CoCo)
            if dd_spt < 1 or dd_spt > 255:
                return False

            # Check sectors per cluster is power of 2 and reasonable
            if dd_bit not in [1, 2, 4, 8, 16, 32, 64]:
                return False

            # Check allocation map size is reasonable
            # Maximum 4096 clusters, each bit is 1 cluster, so max 512 bytes
            if dd_map < 1 or dd_map > 2048:
                return False

            # Check root directory LSN is valid
            if dd_dir < 1 or dd_dir >= dd_tot:
                return False

            # Check disk name contains printable ASCII or nulls
            disk_name = lsn0[0x1F:0x3F]
            for byte in disk_name:
                if byte != 0 and (byte < 0x20 or byte > 0x7E):
                    return False

            return True

        except Exception:
            return False

    def _parse_disk_descriptor(self) -> bool:
        """Parse LSN 0 (Identification Sector)"""
        if len(self.data) < self.SECTOR_SIZE:
            print("Error: Disk image too small")
            return False

        lsn0 = self.data[0:self.SECTOR_SIZE]

        # Parse disk descriptor fields
        self.descriptor.dd_tot = (lsn0[0x00] << 16) | (lsn0[0x01] << 8) | lsn0[0x02]
        self.descriptor.dd_tks = lsn0[0x03]
        self.descriptor.dd_map = (lsn0[0x04] << 8) | lsn0[0x05]
        self.descriptor.dd_bit = (lsn0[0x06] << 8) | lsn0[0x07]
        self.descriptor.dd_dir = (lsn0[0x08] << 16) | (lsn0[0x09] << 8) | lsn0[0x0A]
        self.descriptor.dd_own = (lsn0[0x0B] << 8) | lsn0[0x0C]
        self.descriptor.dd_att = lsn0[0x0D]
        self.descriptor.dd_dsk = (lsn0[0x0E] << 8) | lsn0[0x0F]
        self.descriptor.dd_fmt = lsn0[0x10]
        self.descriptor.dd_spt = (lsn0[0x11] << 8) | lsn0[0x12]
        self.descriptor.dd_res = (lsn0[0x13] << 8) | lsn0[0x14]
        self.descriptor.dd_bt = (lsn0[0x15] << 16) | (lsn0[0x16] << 8) | lsn0[0x17]
        self.descriptor.dd_bsz = (lsn0[0x18] << 8) | lsn0[0x19]

        # Parse creation date (5 bytes: YY MM DD HH MM)
        self.descriptor.dd_dat = tuple(lsn0[0x1A:0x1F])

        # Parse disk name (32 bytes)
        disk_name_bytes = lsn0[0x1F:0x3F]
        self.descriptor.dd_nam = disk_name_bytes.decode('ascii', errors='ignore').rstrip('\x00')

        # Options byte
        if len(lsn0) > 0x3F:
            self.descriptor.dd_opt = lsn0[0x3F]

        return True

    def _read_lsn(self, lsn: int) -> bytes:
        """Read a logical sector by LSN number"""
        if lsn < 0 or lsn >= self.descriptor.dd_tot:
            raise ValueError(f"LSN {lsn} out of range (0-{self.descriptor.dd_tot-1})")

        offset = lsn * self.SECTOR_SIZE
        return self.data[offset:offset + self.SECTOR_SIZE]

    def _read_allocation_map(self):
        """Read allocation bitmap starting at LSN 1"""
        self.allocation_map = bytearray()

        # Allocation map starts at LSN 1
        map_bytes_needed = self.descriptor.dd_map
        lsn = 1

        while map_bytes_needed > 0:
            sector = self._read_lsn(lsn)
            bytes_to_copy = min(self.SECTOR_SIZE, map_bytes_needed)
            self.allocation_map.extend(sector[:bytes_to_copy])
            map_bytes_needed -= bytes_to_copy
            lsn += 1

    def _is_cluster_allocated(self, cluster_num: int) -> bool:
        """Check if a cluster is allocated (bit = 1) or free (bit = 0)"""
        byte_index = cluster_num // 8
        bit_index = 7 - (cluster_num % 8)  # MSB first

        if byte_index >= len(self.allocation_map):
            return True  # Assume allocated if beyond map

        return (self.allocation_map[byte_index] & (1 << bit_index)) != 0

    def _get_free_cluster_count(self) -> int:
        """Count free clusters in allocation map"""
        total_clusters = self.descriptor.dd_tot // self.descriptor.dd_bit
        free_count = 0

        for cluster in range(total_clusters):
            if not self._is_cluster_allocated(cluster):
                free_count += 1

        return free_count

    def _read_root_directory(self):
        """Read root directory entries"""
        self.root_dir_entries = []

        # Read root directory file descriptor first
        root_fd = self._read_file_descriptor(self.descriptor.dd_dir)
        if not root_fd:
            print("Warning: Could not read root directory file descriptor")
            return

        # Read directory data via segment list
        dir_data = self._read_file_data(root_fd)

        # Parse directory entries (32 bytes each)
        offset = 0
        while offset + 32 <= len(dir_data):
            entry_data = dir_data[offset:offset + 32]
            entry = self._parse_directory_entry(entry_data)
            if entry:
                self.root_dir_entries.append(entry)
            offset += 32

    def _parse_directory_entry(self, data: bytes) -> Optional[OS9DirectoryEntry]:
        """Parse a 32-byte directory entry"""
        if len(data) != 32:
            return None

        # Check if entry is empty (all zeros or starts with 0x00)
        if data[0] == 0x00:
            return None

        # Parse filename (28 bytes, last char has bit 7 set)
        filename_bytes = bytearray(data[0:28])

        # Find the end marker (byte with bit 7 set)
        name_end = -1
        for i in range(28):
            if filename_bytes[i] & 0x80:
                filename_bytes[i] &= 0x7F  # Clear bit 7
                name_end = i + 1
                break

        if name_end == -1:
            # If no end marker found, use full 28 bytes
            name_end = 28

        # Decode filename
        filename = filename_bytes[:name_end].decode('ascii', errors='ignore').rstrip('\x00')

        # Skip "." and ".." entries for cleaner output (optional)
        if filename in [".", ".."]:
            return None

        # Parse attributes (1 byte at offset 28)
        dir_at = data[28]

        # Parse file descriptor LSN (3 bytes at offset 29-31, big-endian)
        dir_fd = (data[29] << 16) | (data[30] << 8) | data[31]

        return OS9DirectoryEntry(
            dir_nm=filename,
            dir_at=dir_at,
            dir_fd=dir_fd
        )

    def _read_file_descriptor(self, fd_lsn: int) -> Optional[OS9FileDescriptor]:
        """Read and parse a file descriptor sector"""
        try:
            fd_sector = self._read_lsn(fd_lsn)

            # Parse file descriptor fields
            fd_att = fd_sector[0x00]
            fd_own = (fd_sector[0x01] << 8) | fd_sector[0x02]
            fd_dat = tuple(fd_sector[0x03:0x08])  # 5 bytes: YY MM DD HH MM
            fd_lnk = fd_sector[0x08]
            fd_siz = (fd_sector[0x09] << 24) | (fd_sector[0x0A] << 16) | \
                     (fd_sector[0x0B] << 8) | fd_sector[0x0C]
            fd_dcr = tuple(fd_sector[0x0D:0x10])  # 3 bytes: YY MM DD

            # Parse segment list (starts at offset 0x10)
            # Each segment is 5 bytes: 3 bytes LSN + 2 bytes sector count
            # Continue until we find an entry with 0 sectors
            fd_seg = []
            offset = 0x10

            while offset + 5 <= self.SECTOR_SIZE:
                seg_lsn = (fd_sector[offset] << 16) | (fd_sector[offset+1] << 8) | fd_sector[offset+2]
                seg_count = (fd_sector[offset+3] << 8) | fd_sector[offset+4]

                if seg_count == 0:
                    break

                fd_seg.append((seg_lsn, seg_count))
                offset += 5

            return OS9FileDescriptor(
                fd_att=fd_att,
                fd_own=fd_own,
                fd_dat=fd_dat,
                fd_lnk=fd_lnk,
                fd_siz=fd_siz,
                fd_dcr=fd_dcr,
                fd_seg=fd_seg
            )

        except Exception as e:
            print(f"Error reading file descriptor at LSN {fd_lsn}: {e}")
            return None

    def _read_file_data(self, fd: OS9FileDescriptor) -> bytes:
        """Read file data using the segment list in the file descriptor"""
        file_data = bytearray()

        for seg_lsn, seg_count in fd.fd_seg:
            # Read all sectors in this segment
            for i in range(seg_count):
                sector = self._read_lsn(seg_lsn + i)
                file_data.extend(sector)

        # Trim to actual file size
        if fd.fd_siz > 0:
            file_data = file_data[:fd.fd_siz]

        return bytes(file_data)

    def list_files(self, show_details: bool = False):
        """Display directory listing"""
        if not self.root_dir_entries:
            print("No files found in root directory.")
            return

        print(f"\nDirectory of {self.filename}")
        print(f"Disk: {self.descriptor.dd_nam}")
        print("=" * 80)

        if show_details:
            print(f"{'Filename':<28} {'Type':<5} {'Size':<10} {'Modified':<10} {'Attrs'}")
            print("-" * 80)

            for entry in self.root_dir_entries:
                # Read file descriptor to get size and date
                fd = self._read_file_descriptor(entry.dir_fd)
                if fd:
                    file_type = "DIR" if fd.fd_att & 0x80 else "FILE"
                    size_str = f"{fd.fd_siz}" if fd.fd_siz > 0 else ""
                    date_str = f"{fd.fd_dat[0]:02d}/{fd.fd_dat[1]:02d}/{fd.fd_dat[2]:02d}" if len(fd.fd_dat) >= 3 else ""

                    # Build attribute string
                    attrs = []
                    if entry.dir_at & 0x02:
                        attrs.append("W")
                    if entry.dir_at & 0x01:
                        attrs.append("R")
                    if entry.dir_at & 0x08:
                        attrs.append("PE")
                    attr_str = "".join(attrs)

                    print(f"{entry.dir_nm:<28} {file_type:<5} {size_str:<10} {date_str:<10} {attr_str}")
                else:
                    print(f"{entry.dir_nm:<28} ???   (FD read error)")
        else:
            print(f"{'Filename':<28} {'FD LSN':<8} {'Attributes'}")
            print("-" * 80)
            for entry in self.root_dir_entries:
                print(entry)

        print("-" * 80)
        print(f"Total files: {len(self.root_dir_entries)}")

        # Show free space
        total_clusters = self.descriptor.dd_tot // self.descriptor.dd_bit
        free_clusters = self._get_free_cluster_count()
        cluster_size = self.descriptor.dd_bit * self.SECTOR_SIZE
        free_bytes = free_clusters * cluster_size

        print(f"Free clusters: {free_clusters}/{total_clusters} ({free_bytes} bytes free)")

    def extract_file(self, filename: str, output_path: str) -> bool:
        """Extract a file from the OS-9 disk to PC"""
        # Find file in directory
        entry = None
        for e in self.root_dir_entries:
            if e.dir_nm.upper() == filename.upper():
                entry = e
                break

        if not entry:
            print(f"File '{filename}' not found")
            return False

        try:
            # Read file descriptor
            fd = self._read_file_descriptor(entry.dir_fd)
            if not fd:
                print(f"Could not read file descriptor for '{filename}'")
                return False

            # Check if it's a directory
            if fd.fd_att & 0x80:
                print(f"'{filename}' is a directory, cannot extract")
                return False

            # Read file data
            file_data = self._read_file_data(fd)

            # Write to PC file
            with open(output_path, 'wb') as f:
                f.write(file_data)

            print(f"Extracted '{filename}' to '{output_path}' ({len(file_data)} bytes)")
            return True

        except Exception as e:
            print(f"Error extracting file: {e}")
            import traceback
            traceback.print_exc()
            return False

    def show_disk_info(self):
        """Display detailed disk information"""
        print(self.descriptor)

        # Show format details
        fmt = self.descriptor.dd_fmt
        density = "Single" if (fmt & 0x01) == 0 else "Double"
        sides = 1 if (fmt & 0x02) == 0 else 2

        print(f"  Density: {density}")
        print(f"  Sides: {sides}")

        # Calculate disk capacity
        total_bytes = self.descriptor.dd_tot * self.SECTOR_SIZE
        total_kb = total_bytes // 1024
        print(f"  Total Capacity: {total_kb}KB ({total_bytes} bytes)")

        # Show cluster information
        total_clusters = self.descriptor.dd_tot // self.descriptor.dd_bit
        free_clusters = self._get_free_cluster_count()
        used_clusters = total_clusters - free_clusters
        cluster_size = self.descriptor.dd_bit * self.SECTOR_SIZE

        print(f"\nCluster Information:")
        print(f"  Total Clusters: {total_clusters}")
        print(f"  Used Clusters: {used_clusters}")
        print(f"  Free Clusters: {free_clusters}")
        print(f"  Cluster Size: {cluster_size} bytes")


def main():
    """Command-line interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description='TRS-80 Color Computer OS-9 RBF File System Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Check if disk is OS-9 format
  python coco_dsk_os9.py os9disk.dsk --detect

  # Show disk information
  python coco_dsk_os9.py os9disk.dsk --info

  # List files in OS-9 disk
  python coco_dsk_os9.py os9disk.dsk -l

  # List files with details (size, date)
  python coco_dsk_os9.py os9disk.dsk -l --details

  # Extract file from OS-9 disk to PC
  python coco_dsk_os9.py os9disk.dsk -g STARTUP -o startup.txt

OS-9 RBF Filesystem:
  - Hierarchical directory structure
  - Variable cluster sizes (power of 2)
  - File descriptors with segment lists
  - Supports timestamps and permissions
  - Compatible with OS-9 Level 1/2 and NitrOS-9
        '''
    )

    parser.add_argument('dsk_file', help='OS-9 disk image file')
    parser.add_argument('-l', '--list', action='store_true', help='List files in root directory')
    parser.add_argument('--details', action='store_true', help='Show detailed file information (with -l)')
    parser.add_argument('--info', action='store_true', help='Show disk information')
    parser.add_argument('--detect', action='store_true', help='Detect if disk is OS-9 formatted')

    # Extract options
    parser.add_argument('-g', '--get', metavar='FILENAME', help='Extract file from OS-9 disk')
    parser.add_argument('-o', '--output', metavar='OUTPUT', help='Output filename for -g')

    args = parser.parse_args()

    # Check if file exists
    if not os.path.exists(args.dsk_file):
        print(f"Error: File '{args.dsk_file}' not found")
        return 1

    # Create OS-9 disk object
    disk = OS9Image(args.dsk_file)

    # Detect OS-9 format
    if args.detect:
        # Read file first
        with open(args.dsk_file, 'rb') as f:
            disk.data = f.read()

        if disk.is_os9_disk():
            print(f"'{args.dsk_file}' is an OS-9 RBF formatted disk")
            return 0
        else:
            print(f"'{args.dsk_file}' is NOT an OS-9 RBF formatted disk")
            return 1

    # Mount disk
    if not disk.mount():
        print(f"Failed to mount '{args.dsk_file}' as OS-9 disk")
        return 1

    # Execute commands
    if args.info:
        disk.show_disk_info()

    if args.list:
        disk.list_files(show_details=args.details)

    if args.get:
        output = args.output or args.get
        if not disk.extract_file(args.get, output):
            return 1

    # Default action if no options specified
    if not any([args.info, args.list, args.get]):
        disk.show_disk_info()
        print()
        disk.list_files(show_details=True)

    return 0


if __name__ == '__main__':
    sys.exit(main())
