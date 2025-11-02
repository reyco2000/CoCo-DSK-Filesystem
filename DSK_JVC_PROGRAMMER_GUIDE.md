# DSK/JVC Programmer Guide

This guide distills `DSK_JVC_FORMAT_SPECIFICATION.md` into a programmer-friendly reference with diagrams that can be embedded in generated PDFs. Each figure is provided as Mermaid source so you can render vector diagrams during PDF export.

## 1. Disk Geometry at a Glance

- Standard CoCo disks ship with 35 tracks, 18 sectors per track, and 256-byte sectors (≈160 KB raw).
- Track 17 is reserved for metadata; data spans granules 0-67 (two granules per data track).
- Optional JVC headers encode non-default geometry in the low five bytes of the image.

| Parameter | Default | Notes |
|-----------|---------|-------|
| Tracks | 35 | Variants: 40, 80 |
| Sides | 1 | Set to 2 when header byte 0x01 == 2 |
| Sectors/Track | 18 | Byte 0x00 of header |
| Sector Size | 256 | `128 << header[0x02]` |
| Directory Track | 17 | Never stores user data |

![Figure 1. Logical layout of a 35-track disk](diagrams/figure1.svg)

Figure 1 highlights how user data spans tracks 0-16 and 18-34 while track 17 hosts FAT and directory metadata.

## 2. Parsing the Optional JVC Header

Use the modulus rule `header_size = file_size % 256` to detect header presence. When `header_size > 0`, parse the first five bytes:

```python
sectors_per_track = header[0]
side_count = header[1]
sector_size = 128 << header[2]
first_sector_id = header[3] or 1
sector_attribute = header[4]
```

![Figure 2. Header parsing flow](diagrams/figure2.svg)

Figure 2 shows the decision tree for detecting and decoding optional JVC header bytes before you manipulate sectors.

## 3. Granule Allocation Workflow

A granule maps to 9 contiguous sectors (2,304 bytes). The FAT (track 17, sector 2) exposes 68 entries that form linked lists per file.

![Figure 3. FAT chain traversal](diagrams/figure3.svg)

Figure 3 maps the sequence you follow when walking FAT entries from the directory’s starting granule to the terminating 0xC0-0xC9 marker.

Implementation notes:

- Values 0x00-0x43 reference the next granule index.
- 0xFF marks a free granule.
- 0xC0-0xC9 marks the final granule and encodes used sectors in the low nibble (0 == 9 sectors).

## 4. Directory Entry Cheatsheet

Each entry is 32 bytes located on Track 17, Sectors 3-11.

```
0x00-0x07  NAME (8 chars, space padded)
0x08-0x0A  EXT (3 chars, space padded)
0x0B       TYPE (0=BASIC,1=DATA,2=ML,3=TEXT)
0x0C       MODE (0xFF=ASCII, 0x00=Binary)
0x0D       FIRST GRANULE (0-67)
0x0E-0x0F  LAST SECTOR BYTE COUNT (big endian)
0x10-0x1F  RESERVED (0xFF)
```

Example entry for `HELLO.BAS` (BASIC, binary mode, starting granule 5, 147 trailing bytes):

```
48 45 4C 4C 4F 20 20 20 | 42 41 53 | 00 | 00 | 05 | 00 93 | FF..FF
```

## 5. Read/Write Reference Implementations

```python
def read_file(image, fat, entry):
    granule = entry.first_granule
    chain = []
    while granule <= 67:
        value = fat[granule]
        chain.append(granule)
        if value >= 0xC0:  # tail granule
            sectors = (value & 0x0F) or 9
            return chain, sectors
        granule = value
    raise ValueError("FAT chain corrupted")
```

```python
def write_file(fat, granules, tail_sectors):
    for index, granule in enumerate(granules):
        if index == len(granules) - 1:
            fat[granule] = 0xC0 | (tail_sectors % 10)
        else:
            fat[granule] = granules[index + 1]
```

## 6. Troubleshooting Checklist

- **Garbage filenames**: confirm directory bytes are uppercase ASCII and space padded.
- **Short reads**: compare expected granule count against traversed FAT chain.
- **Write failures**: snapshot the image, then diff FAT and directory sectors after the operation.
- **Cross-compatibility**: some emulators expect `first_sector_id == 0`; adjust header byte 3 when synthesizing disks.

## Rendering This Guide to PDF

1. Update the Mermaid sources in `diagrams/*.mmd` if you tweak a figure.
2. Regenerate the SVGs:
   ```bash
   for f in diagrams/*.mmd; do mmdc -i "$f" -o "${f%.mmd}.svg"; done
   ```
3. Render the Markdown to PDF (requires Node.js):
   ```bash
   npx md-to-pdf DSK_JVC_PROGRAMMER_GUIDE.md --launch-options '{"args":["--no-sandbox","--disable-setuid-sandbox"]}'
   ```
4. Verify that `DSK_JVC_PROGRAMMER_GUIDE.pdf` opens cleanly and that each figure caption matches the embedded SVG.
