#!/usr/bin/env python3
"""
Color BASIC / Extended Color BASIC Detokenizer
Usage:
    python coco_detokenizer.py REVERSE.BAS
"""

import sys
from pathlib import Path

# --- Token tables ---
TOKENS = {
    128: 'FOR', 129: 'GO', 130: 'REM', 131: "'", 132: 'ELSE', 133: 'IF', 134: 'DATA', 135: 'PRINT',
    136: 'ON', 137: 'INPUT', 138: 'END', 139: 'NEXT', 140: 'DIM', 141: 'READ', 142: 'RUN',
    143: 'RESTORE', 144: 'RETURN', 145: 'STOP', 146: 'POKE', 147: 'CONT', 148: 'LIST', 149: 'CLEAR',
    150: 'NEW', 151: 'CLOAD', 152: 'CSAVE', 153: 'OPEN', 154: 'CLOSE', 155: 'LLIST', 156: 'SET',
    157: 'RESET', 158: 'CLS', 159: 'MOTOR', 160: 'SOUND', 161: 'AUDIO', 162: 'EXEC', 163: 'SKIPF',
    164: 'TAB(', 165: 'TO', 166: 'SUB', 167: 'THEN', 168: 'NOT', 169: 'STEP', 170: 'OFF',
    171: '+', 172: '-', 173: '*', 174: '/', 175: '^', 176: 'AND', 177: 'OR', 178: '>', 179: '=',
    180: '<', 181: 'DEL', 182: 'EDIT', 183: 'TRON', 184: 'TROFF', 185: 'DEF', 186: 'LET', 187: 'LINE',
    188: 'PCLS', 189: 'PSET', 190: 'PRESET', 191: 'SCREEN', 192: 'PCLEAR', 193: 'COLOR', 194: 'CIRCLE',
    195: 'PAINT', 196: 'GET', 197: 'PUT', 198: 'DRAW', 199: 'PCOPY', 200: 'PMODE', 201: 'PLAY',
    202: 'DLOAD', 203: 'RENUM', 204: 'FN', 205: 'USING', 206: 'DIR', 207: 'DRIVE', 208: 'FIELD',
    209: 'FILES', 210: 'KILL', 211: 'LOAD', 212: 'LSET', 213: 'MERGE', 214: 'RENAME', 215: 'RSET',
    216: 'SAVE', 217: 'WRITE', 218: 'VERIFY', 219: 'UNLOAD', 220: 'DSKINI', 221: 'BACKUP',
    222: 'COPY', 223: 'DSKI$', 224: 'DSKO$',
    # Super Extended BASIC / Disk Extended BASIC tokens (0xE1-0xFE)
    # CoCo 3 / Super Extended Color BASIC commands
    226: 'WIDTH',   # 0xE2 - Screen width (40/80 columns)
    227: 'PALETTE', # 0xE3 - Set color palette
    228: 'HSCREEN', # 0xE4 - Hi-res screen mode
    230: 'HCLS',    # 0xE6 - Hi-res clear screen
    231: 'HCOLOR',  # 0xE7 - Hi-res set color
    232: 'HPAINT',  # 0xE8 - Hi-res paint
    233: 'HCIRCLE', # 0xE9 - Hi-res circle
    234: 'HLINE',   # 0xEA - Hi-res line
    235: 'HGET',    # 0xEB - Hi-res get
    236: 'HPUT',    # 0xEC - Hi-res put
    237: 'HBUFF',   # 0xED - Hi-res buffer
    238: 'HPRINT',  # 0xEE - Hi-res print
    239: 'ERR',     # 0xEF - Error trap (ON ERR GOTO)
    240: 'BRK',     # 0xF0 - Break trap (ON BRK GOTO)
    243: 'HSET',    # 0xF3 - Hi-res set pixel
    244: 'HRESET',  # 0xF4 - Hi-res reset pixel
    245: 'HDRAW',   # 0xF5 - Hi-res draw
    246: 'CMP',     # 0xF6 - Compare/Complete graphics
    247: 'RGB',     # 0xF7 - RGB color function
    248: 'ATTR'     # 0xF8 - Attribute command
}

TOKENS_EXT = {
    128: 'SGN', 129: 'INT', 130: 'ABS', 131: 'USR', 132: 'RND', 133: 'SIN', 134: 'PEEK',
    135: 'LEN', 136: 'STR$', 137: 'VAL', 138: 'ASC', 139: 'CHR$', 140: 'EOF', 141: 'JOYSTK',
    142: 'LEFT$', 143: 'RIGHT$', 144: 'MID$', 145: 'POINT', 146: 'INKEY$', 147: 'MEM',
    148: 'ATN', 149: 'COS', 150: 'TAN', 151: 'EXP', 152: 'FIX', 153: 'LOG', 154: 'POS',
    155: 'SQR', 156: 'HEX$', 157: 'VARPTR', 158: 'INSTR', 159: 'TIMER', 160: 'PPOINT',
    161: 'STRING$', 162: 'CVN', 163: 'FREE', 164: 'LOC', 165: 'LOF', 166: 'MKN$', 167: 'AS',
    # CoCo 3 Super Extended BASIC functions (0xFF + second byte)
    168: 'LPEEK',  # 0xA8 - Long PEEK (access extended memory)
    169: 'BUTTON', # 0xA9 - Button/mouse input
    170: 'HPOINT', # 0xAA - Hi-res point function
    171: 'ERNO',   # 0xAB - Error number function
    172: 'ERLIN'   # 0xAC - Error line function
}

# --- Helper functions ---
def read_word(data, offset):
    """Read a 16-bit word in little-endian format"""
    return data[offset] + (data[offset + 1] << 8)

def read_word_be(data, offset):
    """Read a 16-bit word in big-endian format"""
    return (data[offset] << 8) + data[offset + 1]

def detokenize_line(line_bytes):
    output = []
    in_string = False
    i = 0
    while i < len(line_bytes):
        b = line_bytes[i]
        if b == 0:
            break
        if not in_string and b == 255:
            i += 1
            if i < len(line_bytes):
                token = TOKENS_EXT.get(line_bytes[i], f"{{255-{line_bytes[i]}}}")
                output.append(token)
        elif not in_string and b in TOKENS:
            token = TOKENS[b]
            output.append(token)
            if token in ('REM', "'"):
                output.append(line_bytes[i+1:].decode('latin1', errors='replace'))
                break
        elif 32 <= b <= 126:
            ch = chr(b)
            output.append(ch)
            if ch == '"':
                in_string = not in_string
        else:
            output.append('¿')
        i += 1
    return ''.join(output)

def detokenize_file(path):
    data = Path(path).read_bytes()
    offset = 0
    if data[0] == 0xFF:
        offset = 5

    result = []
    first_line = True
    while True:
        if offset + 2 > len(data):
            break

        # First line after ML preamble has no link pointer
        if first_line:
            line_number = read_word_be(data, offset)
            start = offset + 2
            first_line = False
        else:
            if offset + 4 > len(data):
                break
            next_line = read_word_be(data, offset)
            line_number = read_word_be(data, offset + 2)
            if next_line == 0:
                break
            start = offset + 4

        if line_number == 0:
            break

        try:
            zero_pos = data.index(0, start)
        except ValueError:
            zero_pos = len(data)
        line_bytes = data[start:zero_pos]
        result.append(f"{line_number} {detokenize_line(line_bytes)}")
        offset = zero_pos + 1
    return "\n".join(result)

# --- Main ---
def main():
    if len(sys.argv) < 2:
        print("Usage: python coco_detokenizer.py <file.BAS>")
        sys.exit(1)

    infile = Path(sys.argv[1])
    if not infile.exists():
        print(f"❌ File not found: {infile}")
        sys.exit(1)

    print(f"📂 Detokenizing: {infile}")
    output = detokenize_file(infile)

    out_path = infile.with_suffix(".txt")
    out_path.write_text(output, encoding="utf-8")
    print(f"✅ Done! Saved detokenized output to {out_path}")

if __name__ == "__main__":
    main()
