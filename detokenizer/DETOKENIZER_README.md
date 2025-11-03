# TRS-80 Color Computer BASIC Detokenizer

**Complete Support for Color BASIC, Extended BASIC, Disk Extended BASIC, and Super Extended BASIC (CoCo 3)**

## Overview

This detokenizer converts binary tokenized .BAS files from the TRS-80 Color Computer (CoCo) to readable ASCII text. It supports all BASIC dialects including CoCo 3 Super Extended BASIC with its advanced hi-res graphics commands.

## What is Tokenization?

CoCo BASIC programs are stored in a compact binary format where keywords like `PRINT`, `FOR`, `GOTO`, `IF`, `THEN` are replaced with single-byte tokens:

- `0x80` = `FOR`
- `0x85` = `IF`
- `0x87` = `PRINT`
- `0x89` = `INPUT`
- `0xA7` = `THEN`
- And many more...

This saves memory and speeds up execution, but makes the files unreadable in a text editor.

## Features

- **Automatic Format Detection**: Detects tokenized BASIC files
- **ML Preamble Support**: Handles files with machine language preambles (0xFF header)
- **Link Pointer Format**: Properly reads CoCo's link-pointer format
- **Complete Token Table**: 159 BASIC tokens including:
  - **Color BASIC**: FOR, IF, PRINT, INPUT, DATA, DIM, READ, GOTO, GOSUB, etc.
  - **Extended BASIC**: PMODE, PCLS, PSET, SCREEN, DRAW, PLAY, SOUND, CIRCLE, etc.
  - **Disk Extended BASIC**: DIR, DRIVE, DLOAD, LOAD, SAVE, KILL, MERGE, BACKUP, etc.
  - **CoCo 3 Super Extended BASIC**: WIDTH, PALETTE, HSCREEN, HCOLOR, HPAINT, HCIRCLE, ERR, BRK, RGB, etc.
  - **Functions**: SGN, INT, ABS, SIN, COS, STR$, CHR$, PEEK, LPEEK, BUTTON, HPOINT, etc.
  - **Operators**: +, -, *, /, ^, AND, OR, >, =, <
- **String Handling**: Preserves quoted strings
- **Line Numbers**: Correctly reconstructs line numbers
- **Text Output**: Creates readable ASCII text files

## Usage


## File Format

CoCo BASIC files use this structure:

### Optional ML Preamble (5 bytes)
```
Byte 0: 0xFF (data block marker)
Bytes 1-2: Load address (big-endian)
Bytes 3-4: Length (big-endian)
```

### BASIC Program Structure
```
Each line:
  - Link pointer to next line (2 bytes, big-endian)
  - Line number (2 bytes, big-endian)
  - Tokenized line data
  - 0x00 line terminator

Program end: 0x00 0x00
```

## Example

### Before (Binary/Tokenized)
```
FF 10 F5 26 24 00 01 82 20 20 20 50 49 5A 5A 41
20 44 45 4C 49 56 45 52 59 20 47 41 4D 45 ...
```

### After (Detokenized ASCII)
```
1 REM    PIZZA DELIVERY GAME  12/83
2 REM
3 REM    PRACTICE IN USING GRIDS
...
100 REM INTIALIZE
105 CLS: CLEAR 1000: DIM H$(8,8)
110 FOR ROW = 1 TO 4
120 FOR COLUNM = 1 TO 4
130 READ H$(COLUNM,ROW)
140 NEXT COLUNM
150 NEXT ROW
```


## Complete Token Reference

### Standard Tokens (0x80-0xE0)

| Hex  | Dec | Token    | Hex  | Dec | Token    | Hex  | Dec | Token    | Hex  | Dec | Token    |
|------|-----|----------|------|-----|----------|------|-----|----------|------|-----|----------|
| 0x80 | 128 | FOR      | 0x90 | 144 | RETURN   | 0xA0 | 160 | SOUND    | 0xB0 | 176 | AND      |
| 0x81 | 129 | GO       | 0x91 | 145 | STOP     | 0xA1 | 161 | AUDIO    | 0xB1 | 177 | OR       |
| 0x82 | 130 | REM      | 0x92 | 146 | POKE     | 0xA2 | 162 | EXEC     | 0xB2 | 178 | >        |
| 0x83 | 131 | '        | 0x93 | 147 | CONT     | 0xA3 | 163 | SKIPF    | 0xB3 | 179 | =        |
| 0x84 | 132 | ELSE     | 0x94 | 148 | LIST     | 0xA4 | 164 | TAB(     | 0xB4 | 180 | <        |
| 0x85 | 133 | IF       | 0x95 | 149 | CLEAR    | 0xA5 | 165 | TO       | 0xB5 | 181 | DEL      |
| 0x86 | 134 | DATA     | 0x96 | 150 | NEW      | 0xA6 | 166 | SUB      | 0xB6 | 182 | EDIT     |
| 0x87 | 135 | PRINT    | 0x97 | 151 | CLOAD    | 0xA7 | 167 | THEN     | 0xB7 | 183 | TRON     |
| 0x88 | 136 | ON       | 0x98 | 152 | CSAVE    | 0xA8 | 168 | NOT      | 0xB8 | 184 | TROFF    |
| 0x89 | 137 | INPUT    | 0x99 | 153 | OPEN     | 0xA9 | 169 | STEP     | 0xB9 | 185 | DEF      |
| 0x8A | 138 | END      | 0x9A | 154 | CLOSE    | 0xAA | 170 | OFF      | 0xBA | 186 | LET      |
| 0x8B | 139 | NEXT     | 0x9B | 155 | LLIST    | 0xAB | 171 | +        | 0xBB | 187 | LINE     |
| 0x8C | 140 | DIM      | 0x9C | 156 | SET      | 0xAC | 172 | -        | 0xBC | 188 | PCLS     |
| 0x8D | 141 | READ     | 0x9D | 157 | RESET    | 0xAD | 173 | *        | 0xBD | 189 | PSET     |
| 0x8E | 142 | RUN      | 0x9E | 158 | CLS      | 0xAE | 174 | /        | 0xBE | 190 | PRESET   |
| 0x8F | 143 | RESTORE  | 0x9F | 159 | MOTOR    | 0xAF | 175 | ^        | 0xBF | 191 | SCREEN   |

### Graphics & Extended BASIC Tokens (0xC0-0xE0)

| Hex  | Dec | Token    | Hex  | Dec | Token    | Hex  | Dec | Token    | Hex  | Dec | Token    |
|------|-----|----------|------|-----|----------|------|-----|----------|------|-----|----------|
| 0xC0 | 192 | PCLEAR   | 0xC8 | 200 | PMODE    | 0xD0 | 208 | FIELD    | 0xD8 | 216 | SAVE     |
| 0xC1 | 193 | COLOR    | 0xC9 | 201 | PLAY     | 0xD1 | 209 | FILES    | 0xD9 | 217 | WRITE    |
| 0xC2 | 194 | CIRCLE   | 0xCA | 202 | DLOAD    | 0xD2 | 210 | KILL     | 0xDA | 218 | VERIFY   |
| 0xC3 | 195 | PAINT    | 0xCB | 203 | RENUM    | 0xD3 | 211 | LOAD     | 0xDB | 219 | UNLOAD   |
| 0xC4 | 196 | GET      | 0xCC | 204 | FN       | 0xD4 | 212 | LSET     | 0xDC | 220 | DSKINI   |
| 0xC5 | 197 | PUT      | 0xCD | 205 | USING    | 0xD5 | 213 | MERGE    | 0xDD | 221 | BACKUP   |
| 0xC6 | 198 | DRAW     | 0xCE | 206 | DIR      | 0xD6 | 214 | RENAME   | 0xDE | 222 | COPY     |
| 0xC7 | 199 | PCOPY    | 0xCF | 207 | DRIVE    | 0xD7 | 215 | RSET     | 0xDF | 223 | DSKI$    |
|      |     |          |      |     |          |      |     |          | 0xE0 | 224 | DSKO$    |

### Super Extended BASIC / CoCo 3 Tokens (0xE2-0xF8)

| Hex  | Dec | Token    | Hex  | Dec | Token    | Hex  | Dec | Token    | Hex  | Dec | Token    |
|------|-----|----------|------|-----|----------|------|-----|----------|------|-----|----------|
| 0xE2 | 226 | WIDTH    | 0xE8 | 232 | HPAINT   | 0xEE | 238 | HPRINT   | 0xF4 | 244 | HRESET   |
| 0xE3 | 227 | PALETTE  | 0xE9 | 233 | HCIRCLE  | 0xEF | 239 | ERR      | 0xF5 | 245 | HDRAW    |
| 0xE4 | 228 | HSCREEN  | 0xEA | 234 | HLINE    | 0xF0 | 240 | BRK      | 0xF6 | 246 | CMP      |
| 0xE6 | 230 | HCLS     | 0xEB | 235 | HGET     | 0xF3 | 243 | HSET     | 0xF7 | 247 | RGB      |
| 0xE7 | 231 | HCOLOR   | 0xEC | 236 | HPUT     |      |     |          | 0xF8 | 248 | ATTR     |
|      |     |          | 0xED | 237 | HBUFF    |      |     |          |      |     |          |

### Function Tokens (Two-byte: 0xFF + second byte)

| Hex  | Dec | Function  | Hex  | Dec | Function  | Hex  | Dec | Function  | Hex  | Dec | Function  |
|------|-----|-----------|------|-----|-----------|------|-----|-----------|------|-----|-----------|
| 0x80 | 128 | SGN       | 0x88 | 136 | STR$      | 0x90 | 144 | MID$      | 0x98 | 152 | FIX       |
| 0x81 | 129 | INT       | 0x89 | 137 | VAL       | 0x91 | 145 | POINT     | 0x99 | 153 | LOG       |
| 0x82 | 130 | ABS       | 0x8A | 138 | ASC       | 0x92 | 146 | INKEY$    | 0x9A | 154 | POS       |
| 0x83 | 131 | USR       | 0x8B | 139 | CHR$      | 0x93 | 147 | MEM       | 0x9B | 155 | SQR       |
| 0x84 | 132 | RND       | 0x8C | 140 | EOF       | 0x94 | 148 | ATN       | 0x9C | 156 | HEX$      |
| 0x85 | 133 | SIN       | 0x8D | 141 | JOYSTK    | 0x95 | 149 | COS       | 0x9D | 157 | VARPTR    |
| 0x86 | 134 | PEEK      | 0x8E | 142 | LEFT$     | 0x96 | 150 | TAN       | 0x9E | 158 | INSTR     |
| 0x87 | 135 | LEN       | 0x8F | 143 | RIGHT$    | 0x97 | 151 | EXP       | 0x9F | 159 | TIMER     |

### Disk Extended BASIC Function Tokens (0xFF + 0xA0-0xA7)

| Hex  | Dec | Function  | Hex  | Dec | Function  |
|------|-----|-----------|------|-----|-----------|
| 0xA0 | 160 | PPOINT    | 0xA4 | 164 | LOC       |
| 0xA1 | 161 | STRING$   | 0xA5 | 165 | LOF       |
| 0xA2 | 162 | CVN       | 0xA6 | 166 | MKN$      |
| 0xA3 | 163 | FREE      | 0xA7 | 167 | AS        |

### Super Extended BASIC Function Tokens (0xFF + 0xA8-0xAC)

| Hex  | Dec | Function  | Description |
|------|-----|-----------|-------------|
| 0xA8 | 168 | LPEEK     | Long PEEK (extended memory access) |
| 0xA9 | 169 | BUTTON    | Button/mouse input |
| 0xAA | 170 | HPOINT    | Hi-res point function |
| 0xAB | 171 | ERNO      | Error number function |
| 0xAC | 172 | ERLIN     | Error line function |

## Special Token Notes

### Two-Byte Tokens

Some tokens require special handling:

- **GO Tokens**: `GOTO` and `GOSUB` are encoded as two-byte sequences starting with 0x81 (129):
  - `GOTO` = 0x81 0xA5 (129, 165)
  - `GOSUB` = 0x81 0xA6 (129, 166)

- **Function Tokens**: All function tokens are two-byte sequences starting with 0xFF (255), followed by the function code (0x80-0xA7)

- **REM Apostrophe**: The apostrophe form of REM (0x83/131) is often prefixed with a colon (0x3A) in some contexts

### Token Coverage

The current implementation includes:
- **97 Standard Tokens** (0x80-0xE0): Core Color BASIC, Extended Color BASIC, and Disk Extended BASIC commands
- **17 Super Extended BASIC Tokens** (0xE2-0xF8): CoCo 3 hi-res graphics and advanced features
- **40 Standard Function Tokens** (0xFF + 0x80-0xA7): Mathematical functions, string functions, and disk I/O functions
- **5 Super Extended Function Tokens** (0xFF + 0xA8-0xAC): CoCo 3 extended memory and error handling functions

**Total: 159 tokens supported**

All documented commands are included:
- **Color BASIC**: FOR, IF, PRINT, INPUT, GOTO, GOSUB, REM, DATA, READ, DIM, etc.
- **Extended Color BASIC**: PMODE, PCLS, PSET, SCREEN, DRAW, PLAY, SOUND, etc.
- **Disk Extended BASIC**: DIR, DRIVE, FIELD, FILES, KILL, LOAD, LSET, MERGE, RENAME, RSET, SAVE, WRITE, VERIFY, UNLOAD, DSKINI, BACKUP, COPY, DSKI$, DSKO$, DLOAD, OPEN, CLOSE
- **Super Extended BASIC (CoCo 3)**: WIDTH, PALETTE, HSCREEN, HCLS, HCOLOR, HPAINT, HCIRCLE, HLINE, HGET, HPUT, HBUFF, HPRINT, ERR, BRK, HSET, HRESET, HDRAW, CMP, RGB, ATTR
- **Disk Functions**: CVN, FREE, LOC, LOF, MKN$, AS, EOF
- **CoCo 3 Functions**: LPEEK, BUTTON, HPOINT, ERNO, ERLIN

## Known Limitations

1. **First Line Number**: The first line sometimes shows an incorrect number (e.g., 8224) due to reading the link pointer. This doesn't affect the rest of the program.

2. **Unknown Tokens**: Some extended/rare tokens may display as `{255-XX}` if not in the token table. These can be added as needed.

3. **Format Variations**: Some BASIC dialects or modified ROMs may use different token values.

4. **GOTO/GOSUB**: Currently treated as single-byte token (GO=0x81), not fully handling the two-byte sequence for GOTO/GOSUB.

## Technical Notes

### Detection Algorithm

The `is_tokenized_basic()` function checks:
- File size > 5 bytes
- Valid line number range (0-63999)
- Presence of token bytes (0x80+) in the file

### Detokenization Process

1. Skip ML preamble if present (0xFF marker)
2. Read link pointer (2 bytes)
3. Read line number (2 bytes)
4. Parse tokens and ASCII text until 0x00 terminator
5. Handle quoted strings (preserve contents)
6. Handle two-byte function tokens (0xFF prefix)
7. Repeat until 0x00 0x00 end marker

## Future Enhancements

Possible improvements:
- Better handling of first line number issue
- Option to re-tokenize ASCII back to binary (tokenizer)
- Support for other BASIC dialects (Dragon 32/64, MC-10, etc.)
- Detection and handling of custom/modified ROM token sets
- Preservation of original formatting and spacing

## Credits

- Based on CoCo BASIC token specifications
- Token table from Color BASIC documentation
- Tested with programs from CoCo community archives

### References and Sources

Token information and BASIC specifications compiled from:

- **Color BASIC Unravelled** by Spectral Associates
  - Available at: https://www.computerarcheology.com/CoCo/color-basic-unravelled.pdf
  - Available at: https://colorcomputerarchive.com/repo/Documents/Books/Unravelled%20Series/color-basic-unravelled.pdf

- **Extended BASIC Unravelled**
  - Available at: https://techheap.packetizer.com/computers/coco/unravelled_series/extended-basic-unravelled.pdf

- **Disk BASIC Unravelled II** by Spectral Associates (redone by Walter K. Zydhek, 1999)
  - Available at: http://os9projects.com/CD_Archive/TUTORIAL/COCO/UNRAVELLED/SuperExtendedBasic.pdf
  - Available at: https://bitchin100.com/files/coco/super-extended-basic-unravelled.pdf

- **BASIC Tokenization Examined** - Mimsy (Jerry Stratton)
  - https://www.hoboes.com/Mimsy/hacks/coco/tokenization/

- **Color Computer Disk BASIC Reference** - The Trailing Edge
  - http://www.trailingedge.com/trs80/CocoDiskRef.html

- **TRS-80 Color BASIC Tokenized File Format**
  - http://fileformats.archiveteam.org/wiki/TRS-80_Color_BASIC_tokenized_file

- **CoCopedia - Color Computer Wiki**
  - https://www.cocopedia.com/wiki/index.php/BASIC:BASIC

- **Color Computer Archive**
  - https://colorcomputerarchive.com/

- **Sub-Etha Software** - CoCo BASIC articles and research
  - https://subethasoftware.com/category/retro-computing/coco/

## See Also

- [coco_detokenizer.py](coco_detokenizer.py) - Detokenizer script
- Token tables based on Color Computer BASIC ROM specifications
