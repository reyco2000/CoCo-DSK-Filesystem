# TRS-80 Color Computer BASIC Tokenization

## Complete Technical Reference Guide

---

## Table of Contents

1. [Introduction to Tokenization](#introduction-to-tokenization)
2. [Why Tokenization?](#why-tokenization)
3. [Binary File Structure](#binary-file-structure)
4. [Complete Token Tables](#complete-token-tables)
5. [Tokenization Process](#tokenization-process)
6. [Detokenization Process](#detokenization-process)
7. [Special Cases and Edge Cases](#special-cases-and-edge-cases)
8. [Working Examples](#working-examples)
9. [Implementation Guide for AI](#implementation-guide-for-ai)
10. [Common Pitfalls](#common-pitfalls)

---

## Introduction to Tokenization

**Tokenization** is the process of converting human-readable BASIC source code into a compact binary representation. In the TRS-80 Color Computer (CoCo), Microsoft Extended Color BASIC uses tokenization to:

1. **Save memory**: Each keyword becomes a single byte instead of multiple ASCII characters
2. **Speed up execution**: The interpreter doesn't need to parse text keywords
3. **Protect code**: Binary format is less human-readable

### Example

**ASCII Source Code** (13 bytes):
```
PRINT "HELLO"
```

**Tokenized Binary** (9 bytes):
```
87 20 22 48 45 4C 4C 4F 22
```

Where `0x87` is the token for `PRINT`, `0x20` is space, `0x22` is quote, and `48 45 4C 4C 4F` is "HELLO" in ASCII.

---

## Why Tokenization?

### Historical Context

The TRS-80 Color Computer (1980-1991) had:
- **Limited RAM**: 4KB-128KB depending on model
- **Slow CPU**: Motorola 6809 at 0.89 MHz
- **Cassette/Floppy Storage**: Slow I/O speeds

### Benefits

| Aspect | ASCII BASIC | Tokenized BASIC | Savings |
|--------|-------------|-----------------|---------|
| "PRINT" | 5 bytes | 1 byte | 80% |
| "GOTO 100" | 8 bytes | 4 bytes | 50% |
| "FOR I=1 TO 10" | 14 bytes | 9 bytes | 36% |
| Execution Speed | Parse each time | Direct execution | 3-10x faster |

---

## Binary File Structure

### Overall File Format

CoCo BASIC files stored on disk follow this structure:

```
┌─────────────────────────────────────────────────┐
│ ML Preamble (Optional, 5 bytes)                 │
├─────────────────────────────────────────────────┤
│ Line 1:                                         │
│   ├─ Link Pointer (2 bytes, big-endian)        │
│   ├─ Line Number (2 bytes, big-endian)         │
│   ├─ Tokenized Content (variable)              │
│   └─ Null Terminator (0x00)                    │
├─────────────────────────────────────────────────┤
│ Line 2:                                         │
│   ├─ Link Pointer (2 bytes, big-endian)        │
│   ├─ Line Number (2 bytes, big-endian)         │
│   ├─ Tokenized Content (variable)              │
│   └─ Null Terminator (0x00)                    │
├─────────────────────────────────────────────────┤
│ ... (more lines)                                │
├─────────────────────────────────────────────────┤
│ End Marker: 0x00 0x00                           │
└─────────────────────────────────────────────────┘
```

### ML Preamble (Machine Language Header)

When saved with `CSAVE` or `CSAVEM`, files may have a 5-byte preamble:

| Offset | Size | Description | Example |
|--------|------|-------------|---------|
| 0x00 | 1 | Type Byte (0xFF = data block) | `0xFF` |
| 0x01 | 2 | Load Address (big-endian) | `0x1E 0x00` = 7680 |
| 0x03 | 2 | Length (big-endian) | `0x10 0x00` = 4096 |

**Note**: Not all BASIC files have this preamble. Files created in memory or with SAVE may start directly with the program data.

### Line Structure

Each line in memory has this format:

```
┌──────────────────────────────────────────────────────────┐
│ Offset │ Size │ Field Name      │ Description            │
├────────┼──────┼─────────────────┼────────────────────────┤
│ +0     │ 2    │ Link Pointer    │ Address of next line   │
│ +2     │ 2    │ Line Number     │ 0-63999                │
│ +4     │ var  │ Tokenized Data  │ Tokens + ASCII         │
│ +n     │ 1    │ Terminator      │ 0x00                   │
└──────────────────────────────────────────────────────────┘
```

#### Link Pointer Details

- **Format**: 16-bit big-endian address
- **Purpose**: Points to the start of the next line in memory
- **Special**: `0x00 0x00` indicates end of program
- **On Disk**: Calculated when loading into memory

#### Line Number Format

- **Format**: 16-bit big-endian integer (0-63999)
- **Range**: Typically 1-63999 (0 is special, rarely used)
- **Example**: `0x00 0x0A` = line 10, `0x03 0xE8` = line 1000

---

## Complete Token Tables

### Primary Token Table (0x80-0xFF)

Tokens in the range 0x80-0xFF represent BASIC keywords and operators.

#### Control Flow & Program Structure (0x80-0x8F)

| Token | Hex | Keyword | Description |
|-------|-----|---------|-------------|
| 128 | 0x80 | FOR | FOR loop start |
| 129 | 0x81 | GO | GO (used with TO/SUB) |
| 130 | 0x82 | REM | Remark/comment |
| 131 | 0x83 | ' | Shorthand REM |
| 132 | 0x84 | ELSE | ELSE clause |
| 133 | 0x85 | IF | IF condition |
| 134 | 0x86 | DATA | DATA statement |
| 135 | 0x87 | PRINT | PRINT statement |
| 136 | 0x88 | ON | ON...GOTO/GOSUB |
| 137 | 0x89 | INPUT | INPUT statement |
| 138 | 0x8A | END | END program |
| 139 | 0x8B | NEXT | NEXT in FOR loop |
| 140 | 0x8C | DIM | DIMension arrays |
| 141 | 0x8D | READ | READ from DATA |
| 142 | 0x8E | RUN | RUN program |
| 143 | 0x8F | RESTORE | RESTORE DATA pointer |

#### Program Control (0x90-0x9F)

| Token | Hex | Keyword | Description |
|-------|-----|---------|-------------|
| 144 | 0x90 | RETURN | RETURN from GOSUB |
| 145 | 0x91 | STOP | STOP execution |
| 146 | 0x92 | POKE | POKE memory |
| 147 | 0x93 | CONT | CONTinue after STOP |
| 148 | 0x94 | LIST | LIST program |
| 149 | 0x95 | CLEAR | CLEAR variables |
| 150 | 0x96 | NEW | NEW program |
| 151 | 0x97 | CLOAD | Cassette LOAD |
| 152 | 0x98 | CSAVE | Cassette SAVE |
| 153 | 0x99 | OPEN | OPEN file |
| 154 | 0x9A | CLOSE | CLOSE file |
| 155 | 0x9B | LLIST | LIST to printer |
| 156 | 0x9C | SET | SET graphics pixel |
| 157 | 0x9D | RESET | RESET graphics pixel |
| 158 | 0x9E | CLS | CLear Screen |
| 159 | 0x9F | MOTOR | Cassette MOTOR |

#### I/O and Utility (0xA0-0xAF)

| Token | Hex | Keyword | Description |
|-------|-----|---------|-------------|
| 160 | 0xA0 | SOUND | SOUND command |
| 161 | 0xA1 | AUDIO | AUDIO on/off |
| 162 | 0xA2 | EXEC | EXEC machine code |
| 163 | 0xA3 | SKIPF | SKIP File (tape) |
| 164 | 0xA4 | TAB( | TAB function |
| 165 | 0xA5 | TO | TO (in FOR) |
| 166 | 0xA6 | SUB | SUB (in GOSUB) |
| 167 | 0xA7 | THEN | THEN (in IF) |
| 168 | 0xA8 | NOT | NOT operator |
| 169 | 0xA9 | STEP | STEP in FOR |
| 170 | 0xAA | OFF | OFF |
| 171 | 0xAB | + | Plus operator |
| 172 | 0xAC | - | Minus operator |
| 173 | 0xAD | * | Multiply operator |
| 174 | 0xAE | / | Divide operator |
| 175 | 0xAF | ^ | Exponent operator |

#### Logical & Comparison (0xB0-0xBF)

| Token | Hex | Keyword | Description |
|-------|-----|---------|-------------|
| 176 | 0xB0 | AND | AND operator |
| 177 | 0xB1 | OR | OR operator |
| 178 | 0xB2 | > | Greater than |
| 179 | 0xB3 | = | Equals |
| 180 | 0xB4 | < | Less than |
| 181 | 0xB5 | DEL | DELete line |
| 182 | 0xB6 | EDIT | EDIT line |
| 183 | 0xB7 | TRON | TRace ON |
| 184 | 0xB8 | TROFF | TRace OFF |
| 185 | 0xB9 | DEF | DEFine function |
| 186 | 0xBA | LET | LET assignment |
| 187 | 0xBB | LINE | LINE graphics |
| 188 | 0xBC | PCLS | PCLS graphics |
| 189 | 0xBD | PSET | PSET pixel |
| 190 | 0xBE | PRESET | PRESET pixel |
| 191 | 0xBF | SCREEN | SCREEN mode |

#### Extended Graphics (0xC0-0xCF)

| Token | Hex | Keyword | Description |
|-------|-----|---------|-------------|
| 192 | 0xC0 | PCLEAR | PCLEAR graphics |
| 193 | 0xC1 | COLOR | COLOR command |
| 194 | 0xC2 | CIRCLE | CIRCLE graphics |
| 195 | 0xC3 | PAINT | PAINT fill |
| 196 | 0xC4 | GET | GET graphics |
| 197 | 0xC5 | PUT | PUT graphics |
| 198 | 0xC6 | DRAW | DRAW graphics |
| 199 | 0xC7 | PCOPY | PCOPY screen |
| 200 | 0xC8 | PMODE | PMODE graphics |
| 201 | 0xC9 | PLAY | PLAY music |
| 202 | 0xCA | DLOAD | Disk LOAD |
| 203 | 0xCB | RENUM | RENUMber lines |
| 204 | 0xCC | FN | FuNction call |
| 205 | 0xCD | USING | USING format |
| 206 | 0xCE | DIR | DIRectory |
| 207 | 0xCF | DRIVE | DRIVE select |

#### Disk Commands (0xD0-0xDF)

| Token | Hex | Keyword | Description |
|-------|-----|---------|-------------|
| 208 | 0xD0 | FIELD | FIELD file |
| 209 | 0xD1 | FILES | FILES list |
| 210 | 0xD2 | KILL | KILL file |
| 211 | 0xD3 | LOAD | LOAD program |
| 212 | 0xD4 | LSET | LSET string |
| 213 | 0xD5 | MERGE | MERGE programs |
| 214 | 0xD6 | RENAME | RENAME file |
| 215 | 0xD7 | RSET | RSET string |
| 216 | 0xD8 | SAVE | SAVE program |
| 217 | 0xD9 | WRITE | WRITE file |
| 218 | 0xDA | VERIFY | VERIFY tape |
| 219 | 0xDB | UNLOAD | UNLOAD |
| 220 | 0xDC | DSKINI | Disk INItialize |
| 221 | 0xDD | BACKUP | BACKUP disk |
| 222 | 0xDE | COPY | COPY file |
| 223 | 0xDF | DSKI$ | Disk Input string |
| 224 | 0xE0 | DSKO$ | Disk Output string |

#### Super Extended BASIC / CoCo 3 Commands (0xE2-0xF8)

| Token | Hex | Keyword | Description |
|-------|-----|---------|-------------|
| 226 | 0xE2 | WIDTH | Screen width (40/80 columns) |
| 227 | 0xE3 | PALETTE | Set color palette |
| 228 | 0xE4 | HSCREEN | Hi-res screen mode |
| 230 | 0xE6 | HCLS | Hi-res clear screen |
| 231 | 0xE7 | HCOLOR | Hi-res set color |
| 232 | 0xE8 | HPAINT | Hi-res paint |
| 233 | 0xE9 | HCIRCLE | Hi-res circle |
| 234 | 0xEA | HLINE | Hi-res line |
| 235 | 0xEB | HGET | Hi-res get |
| 236 | 0xEC | HPUT | Hi-res put |
| 237 | 0xED | HBUFF | Hi-res buffer |
| 238 | 0xEE | HPRINT | Hi-res print |
| 239 | 0xEF | ERR | Error trap (ON ERR GOTO) |
| 240 | 0xF0 | BRK | Break trap (ON BRK GOTO) |
| 243 | 0xF3 | HSET | Hi-res set pixel |
| 244 | 0xF4 | HRESET | Hi-res reset pixel |
| 245 | 0xF5 | HDRAW | Hi-res draw |
| 246 | 0xF6 | CMP | Compare/Complete graphics |
| 247 | 0xF7 | RGB | RGB color function |
| 248 | 0xF8 | ATTR | Attribute command |

### Function Tokens (Two-Byte: 0xFF + Second Byte)

Functions use a two-byte sequence: `0xFF` followed by a second token byte.

#### Mathematical Functions (0xFF 0x80-0x8F)

| Token | Hex | Function | Description |
|-------|-----|----------|-------------|
| - | FF 80 | SGN | Sign of number |
| - | FF 81 | INT | Integer part |
| - | FF 82 | ABS | Absolute value |
| - | FF 83 | USR | User routine |
| - | FF 84 | RND | Random number |
| - | FF 85 | SIN | Sine |
| - | FF 86 | PEEK | PEEK memory |
| - | FF 87 | LEN | Length of string |
| - | FF 88 | STR$ | String from number |
| - | FF 89 | VAL | Value from string |
| - | FF 8A | ASC | ASCII code |
| - | FF 8B | CHR$ | Character from code |
| - | FF 8C | EOF | End Of File |
| - | FF 8D | JOYSTK | Joystick |
| - | FF 8E | LEFT$ | Left substring |
| - | FF 8F | RIGHT$ | Right substring |

#### String & Math Functions (0xFF 0x90-0x9F)

| Token | Hex | Function | Description |
|-------|-----|----------|-------------|
| - | FF 90 | MID$ | Middle substring |
| - | FF 91 | POINT | POINT pixel test |
| - | FF 92 | INKEY$ | Input key |
| - | FF 93 | MEM | Free MEMory |
| - | FF 94 | ATN | Arctangent |
| - | FF 95 | COS | Cosine |
| - | FF 96 | TAN | Tangent |
| - | FF 97 | EXP | Exponential |
| - | FF 98 | FIX | Fix decimal |
| - | FF 99 | LOG | Logarithm |
| - | FF 9A | POS | Cursor POSition |
| - | FF 9B | SQR | Square root |
| - | FF 9C | HEX$ | Hexadecimal string |
| - | FF 9D | VARPTR | Variable pointer |
| - | FF 9E | INSTR | IN STRing search |
| - | FF 9F | TIMER | Timer value |

#### Graphics & System Functions (0xFF 0xA0-0xAF)

| Token | Hex | Function | Description |
|-------|-----|----------|-------------|
| - | FF A0 | PPOINT | Pixel POINT |
| - | FF A1 | STRING$ | STRING repeat |
| - | FF A2 | CVN | Convert to number |
| - | FF A3 | FREE | FREE memory |
| - | FF A4 | LOC | File LOCation |
| - | FF A5 | LOF | Length Of File |
| - | FF A6 | MKN$ | Make number string |
| - | FF A7 | AS | AS (file mode) |
| - | FF A8 | LPEEK | Long PEEK (extended memory) |
| - | FF A9 | BUTTON | Button/mouse input |
| - | FF AA | HPOINT | Hi-res point function |
| - | FF AB | ERNO | Error number function |
| - | FF AC | ERLIN | Error line function |

---

## Tokenization Process

### Step-by-Step: ASCII to Binary

Let's tokenize: `10 PRINT "HELLO":GOTO 20`

#### Step 1: Parse Line Number
```
Input:  "10 PRINT "HELLO":GOTO 20"
Action: Extract line number: 10
Binary: 0x00 0x0A (big-endian)
```

#### Step 2: Scan for Keywords
```
Text:   "PRINT "HELLO":GOTO 20"
Match:  "PRINT" -> 0x87
Result: 0x87
```

#### Step 3: Preserve Strings
```
Text:   " "HELLO""
Action: Keep space (0x20), quotes, and string content
Result: 0x20 0x22 0x48 0x45 0x4C 0x4C 0x4F 0x22
```

#### Step 4: Handle Statement Separator
```
Text:   ":"
Action: Colon remains as ASCII
Result: 0x3A
```

#### Step 5: Continue Tokenizing
```
Text:   "GOTO 20"
Match:  "GOTO" = "GO" + "TO" -> 0x81 0xA5
Result: 0x81 0xA5 0x20 0x32 0x30
```

#### Step 6: Add Terminator
```
Action: Add null byte at end of line
Result: 0x00
```

### Complete Binary Result

```
Line structure in memory:
┌────────────────────────────────────────────────────┐
│ Link Ptr │ Line # │ Tokenized Data        │ Term  │
│ xx xx    │ 00 0A  │ 87 20 22 48 45 4C 4C  │ 00    │
│          │        │ 4F 22 3A 81 A5 20 32  │       │
│          │        │ 30                     │       │
└────────────────────────────────────────────────────┘
```

**Breakdown**:
- `00 0A` = Line 10
- `87` = PRINT
- `20` = Space
- `22 48 45 4C 4C 4F 22` = "HELLO"
- `3A` = Colon
- `81 A5` = GO TO
- `20 32 30` = " 20"
- `00` = End of line

---

## Detokenization Process

### Step-by-Step: Binary to ASCII

Given binary: `00 0A 87 20 22 48 45 4C 4C 4F 22 3A 81 A5 20 32 30 00`

#### Step 1: Read Line Number
```
Bytes:  00 0A
Value:  (0x00 << 8) | 0x0A = 10
Output: "10 "
```

#### Step 2: Process Tokens
```
Position: After line number
State:    Not in string
```

#### Step 3: Token 0x87
```
Byte:   87
Lookup: Token table -> "PRINT"
Output: "10 PRINT"
```

#### Step 4: Space & String
```
Byte:   20 (space)
Output: "10 PRINT "

Byte:   22 (quote)
State:  Enter string mode
Output: "10 PRINT ""

Bytes:  48 45 4C 4C 4F (HELLO)
Output: "10 PRINT "HELLO"

Byte:   22 (quote)
State:  Exit string mode
Output: "10 PRINT "HELLO""
```

#### Step 5: Statement Separator
```
Byte:   3A (colon)
Output: "10 PRINT "HELLO":"
```

#### Step 6: Multi-byte Keyword
```
Bytes:  81 A5
Lookup: 81=GO, A5=TO
Output: "10 PRINT "HELLO":GOTO"
```

#### Step 7: Line Number Argument
```
Bytes:  20 32 30 (space, "2", "0")
Output: "10 PRINT "HELLO":GOTO 20"
```

#### Step 8: Terminator
```
Byte:   00
Action: End of line, move to next
```

### Final ASCII Result

```
10 PRINT "HELLO":GOTO 20
```

---

## Special Cases and Edge Cases

### Case 1: REM Statement

**Special Rule**: Everything after REM is treated as a comment and NOT tokenized.

```
BASIC:  100 REM PRINT IS NOT A KEYWORD HERE
Binary: 00 64 82 20 50 52 49 4E 54 20 49 53 ... 00
             ^^ = REM token
                ^^ onwards = raw ASCII
```

**Important**: "PRINT" after REM remains as ASCII: `50 52 49 4E 54`

### Case 2: DATA Statement

**Special Rule**: DATA content is generally NOT tokenized to preserve exact values.

```
BASIC:  200 DATA PRINT,100,HELLO
Binary: 00 C8 86 20 50 52 49 4E 54 2C 31 30 30 2C ... 00
             ^^ = DATA token
                All following content preserved as ASCII
```

### Case 3: Quoted Strings

**Rule**: Content inside quotes is NEVER tokenized.

```
BASIC:  300 PRINT "GOTO 500"
Binary: 00 012C 87 20 22 47 4F 54 4F 20 35 30 30 22 00
                         ^^^^^^^^^^^^^^^^^^^^^^
                         "GOTO 500" as ASCII, not tokenized
```

### Case 4: Variable Names

**Rule**: Variable names remain as ASCII, even if they contain keywords.

```
BASIC:  400 PRINTER=5
Binary: 00 90 01 BA 20 50 52 49 4E 54 45 52 B3 35 00
                      ^^^^^^^^^^^^^^^^ = "PRINTER" (ASCII)
                                   ^^ = equals token
```

Variable `PRINTER` contains "PRINT" but is NOT split into tokens.

### Case 5: Numbers in Different Formats

**Decimal Numbers**: Remain as ASCII digits
```
BASIC:  500 X=123
Binary: 58 20 B3 20 31 32 33
              ^^ = equals
                 ^^^^^^^^ = "123" as ASCII
```

**Hexadecimal Numbers**: `&H` prefix + hex digits
```
BASIC:  600 POKE &HFF00,0
Binary: 92 20 26 48 46 46 30 30 2C 30
        ^^ = POKE
           ^^^^^^^^^^^ = "&HFF00"
```

### Case 6: Function Calls with 0xFF Prefix

**Two-byte sequence**:

```
BASIC:  700 X=INT(3.14)
Binary: 58 B3 FF 81 28 33 2E 31 34 29
           ^^^^^ = INT function
           0xFF then 0x81
```

### Case 7: Line Continuation (No Native Support)

CoCo BASIC doesn't have true line continuation. Long lines are just long:

```
BASIC:  800 IF X>10 THEN PRINT "BIG":GOTO 900 ELSE PRINT "SMALL"
Binary: [Single long tokenized line, no continuation marker]
```

### Case 8: Multiple Statements per Line

**Colon separator** (0x3A) allows multiple statements:

```
BASIC:  900 CLS:PRINT "HI":END
Binary: 00 03 84 9E 3A 87 20 22 48 49 22 3A 8A 00
              ^^^^^ = CLS
                  ^^ = colon
                     ^^ = PRINT
                           ^^^^^^^^^^^ = "HI"
                                    ^^ = colon
                                       ^^ = END
```

### Case 9: Empty Lines

**Not stored**: Empty lines are skipped during tokenization. LINE 100 followed by LINE 200 has no entry for non-existent LINE 150.

### Case 10: Maximum Line Length

**Limit**: Approximately 250 characters per line (varies by implementation).
**Behavior**: Lines exceeding limit may be truncated or cause errors.

---

## Working Examples

### Example 1: Simple Program

**ASCII Source**:
```basic
10 PRINT "HELLO WORLD"
20 END
```

**Tokenized Binary** (with link pointers for illustration):

```
Line 10:
  Link: 00 20 (points to line 20)
  Line: 00 0A (10)
  Data: 87 20 22 48 45 4C 4C 4F 20 57 4F 52 4C 44 22
        ^^ = PRINT
           ^^ = space
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ = "HELLO WORLD"
  Term: 00

Line 20:
  Link: 00 00 (end of program)
  Line: 00 14 (20)
  Data: 8A
        ^^ = END
  Term: 00

End:
  00 00 (program terminator)
```

**Hex Dump**:
```
0000: 00 20 00 0A 87 20 22 48 45 4C 4C 4F 20 57 4F 52
0010: 4C 44 22 00 00 00 00 14 8A 00 00 00
```

### Example 2: FOR Loop

**ASCII Source**:
```basic
100 FOR I=1 TO 10
110 PRINT I
120 NEXT I
130 END
```

**Tokenized Analysis**:

Line 100: `FOR I=1 TO 10`
```
00 64 80 20 49 B3 31 20 A5 20 31 30 00
      ^^ = FOR
         ^^ = space
            ^^ = "I"
               ^^ = equals (=)
                  ^^ = "1"
                     ^^ = space
                        ^^ = TO
                           ^^^^^^ = " 10"
                                 ^^ = terminator
```

Line 110: `PRINT I`
```
00 6E 87 20 49 00
      ^^ = PRINT
         ^^^^ = " I"
               ^^ = terminator
```

Line 120: `NEXT I`
```
00 78 8B 20 49 00
      ^^ = NEXT
         ^^^^ = " I"
               ^^ = terminator
```

Line 130: `END`
```
00 82 8A 00
      ^^ = END
         ^^ = terminator
```

### Example 3: IF-THEN-ELSE

**ASCII Source**:
```basic
200 INPUT X
210 IF X>10 THEN PRINT "BIG" ELSE PRINT "SMALL"
```

**Line 210 Tokenized**:
```
00 D2 85 20 58 B2 31 30 20 A7 20 87 20 22 42 49 47 22 20 84 20 87 20 22 53 4D 41 4C 4C 22 00
      ^^ = IF
         ^^ = space
            ^^ = "X"
               ^^ = > (greater than)
                  ^^^^^ = "10"
                        ^^ = space
                           ^^ = THEN
                              ^^ = space
                                 ^^ = PRINT
                                       ^^^^^^^^^^^ = "BIG"
                                                   ^^ = space
                                                      ^^ = ELSE
                                                         ^^ = space
                                                            ^^ = PRINT
                                                                  ^^^^^^^^^^^^^^^^ = "SMALL"
```

### Example 4: Function Usage

**ASCII Source**:
```basic
300 X=INT(RND(1)*100)
```

**Tokenized**:
```
00 01 2C 58 B3 FF 81 28 FF 84 28 31 29 AD 31 30 30 29 00
          ^^ = "X"
             ^^ = = (equals)
                ^^^^^ = INT (0xFF 0x81)
                      ^^ = (
                         ^^^^^ = RND (0xFF 0x84)
                               ^^ = (
                                  ^^ = "1"
                                     ^^ = )
                                        ^^ = * (multiply)
                                           ^^^^^^ = "100"
                                                 ^^ = )
                                                    ^^ = terminator
```

---

## Implementation Guide for AI

### Pseudocode for Detokenization

```python
def detokenize_coco_basic(binary_data):
    """
    Detokenize CoCo BASIC binary file to ASCII text.

    Args:
        binary_data: bytes object containing tokenized BASIC

    Returns:
        String containing ASCII BASIC source code
    """

    # Initialize
    pos = 0
    output_lines = []

    # Skip ML preamble if present
    if binary_data[0] == 0xFF:
        pos = 5  # Skip 5-byte preamble

    # Skip leading zeros
    while pos < len(binary_data) and binary_data[pos] == 0x00:
        pos += 1

    # Process each line
    while pos < len(binary_data):
        # Check for end of program
        if (pos + 1 < len(binary_data) and
            binary_data[pos] == 0x00 and
            binary_data[pos + 1] == 0x00):
            break

        # Read link pointer (skip it for file processing)
        link_ptr = (binary_data[pos] << 8) | binary_data[pos + 1]
        pos += 2

        if link_ptr == 0:
            break

        # Read line number
        line_num = (binary_data[pos] << 8) | binary_data[pos + 1]
        pos += 2

        # Build line text
        line_text = f"{line_num} "
        in_string = False
        in_remark = False

        # Process tokens until terminator
        while pos < len(binary_data) and binary_data[pos] != 0x00:
            byte = binary_data[pos]

            # Handle strings
            if byte == 0x22:  # Quote
                in_string = not in_string
                line_text += chr(byte)
                pos += 1
                continue

            # Inside string - preserve as-is
            if in_string:
                line_text += chr(byte) if 0x20 <= byte <= 0x7E else f'\\x{byte:02x}'
                pos += 1
                continue

            # After REM - preserve as-is
            if in_remark:
                line_text += chr(byte) if 0x20 <= byte <= 0x7E else f'\\x{byte:02x}'
                pos += 1
                continue

            # Token processing
            if byte >= 0x80:
                # Check for two-byte function token
                if byte == 0xFF and pos + 1 < len(binary_data):
                    next_byte = binary_data[pos + 1]
                    token_key = (next_byte << 8) | 0xFF
                    keyword = FUNCTION_TOKEN_TABLE.get(token_key, f'<??{byte:02X}{next_byte:02X}>')
                    line_text += keyword
                    pos += 2
                else:
                    # Single-byte token
                    keyword = TOKEN_TABLE.get(byte, f'<??{byte:02X}>')

                    # Add spacing
                    if line_text and line_text[-1] not in (' ', '(', ','):
                        line_text += ' '

                    line_text += keyword

                    # Check for REM
                    if byte == 0x82:  # REM token
                        in_remark = True

                    # Add spacing after
                    if keyword not in ('(', "'"):
                        line_text += ' '

                    pos += 1
            else:
                # ASCII character
                char = chr(byte)

                # Handle special characters
                if byte == 0x3A:  # Colon
                    line_text = line_text.rstrip() + ':'
                    in_remark = False
                elif byte == 0x20:  # Space
                    if not line_text or line_text[-1] != ' ':
                        line_text += char
                else:
                    line_text += char

                pos += 1

        # Skip terminator
        if pos < len(binary_data) and binary_data[pos] == 0x00:
            pos += 1

        # Add line to output
        output_lines.append(line_text.rstrip())

    return '\n'.join(output_lines)
```

### Key Implementation Notes for AI

1. **Token Table Storage**: Create two dictionaries:
   ```python
   TOKEN_TABLE = {0x80: 'FOR', 0x81: 'GO', ...}
   FUNCTION_TABLE = {0x80FF: 'INT', 0x81FF: 'ABS', ...}
   ```

2. **State Tracking**: Maintain flags for:
   - `in_string`: Inside quoted string
   - `in_remark`: After REM/apostrophe
   - `in_data`: After DATA statement

3. **Spacing Rules**:
   - Add space BEFORE tokens (except after `(`, `,`)
   - Add space AFTER tokens (except `(`, `'`)
   - Preserve spaces in strings
   - Remove extra spaces around colons

4. **Error Handling**:
   - Unknown tokens: Display as `<??XX>` with hex value
   - Truncated file: Report position and error
   - Invalid line numbers: Skip or report

5. **Testing Strategy**:
   - Test with simple programs first
   - Verify REM handling
   - Check string preservation
   - Test nested functions
   - Validate line numbers

---

## Common Pitfalls

### Pitfall 1: Ignoring Link Pointers

**Problem**: Reading line numbers directly without accounting for link pointers.

**Wrong**:
```python
line_num = (data[0] << 8) | data[1]  # Reads link pointer, not line number!
```

**Correct**:
```python
link_ptr = (data[0] << 8) | data[1]  # Read and skip link pointer
line_num = (data[2] << 8) | data[3]  # Now read line number
```

### Pitfall 2: Tokenizing Inside Strings

**Problem**: Converting keywords inside quotes to tokens.

**Wrong**:
```
"PRINT" -> 0x87  # NO! Should stay as ASCII in quotes
```

**Correct**:
```
State check: if in_string: preserve_as_ascii()
```

### Pitfall 3: Tokenizing After REM

**Problem**: Tokenizing text in comments.

**Wrong**:
```
REM GOTO 100 -> 0x82 0x81 0xA5 0x31 0x30 0x30  # NO!
```

**Correct**:
```
REM GOTO 100 -> 0x82 0x20 0x47 0x4F 0x54 0x4F 0x20 0x31 0x30 0x30
```

### Pitfall 4: Endianness Confusion

**Problem**: Using little-endian for line numbers.

**Wrong**:
```python
line_num = data[0] | (data[1] << 8)  # Little-endian
```

**Correct**:
```python
line_num = (data[0] << 8) | data[1]  # Big-endian
```

### Pitfall 5: Missing Two-Byte Functions

**Problem**: Not recognizing 0xFF prefix for functions.

**Wrong**:
```
0xFF 0x81 -> keyword for 0xFF, then keyword for 0x81  # NO!
```

**Correct**:
```
0xFF 0x81 -> Combined token for INT function
```

### Pitfall 6: Assuming Fixed Line Length

**Problem**: Reading fixed-size chunks instead of using terminators.

**Wrong**:
```python
line_data = data[4:36]  # Assumes 32-byte lines
```

**Correct**:
```python
# Read until 0x00 terminator
while data[pos] != 0x00:
    # process byte
    pos += 1
```

### Pitfall 7: Not Preserving Variable Names

**Problem**: Treating variable names as keywords.

**Wrong**:
```
PRINTER -> PRINT + ER (trying to tokenize)  # NO!
```

**Correct**:
```
PRINTER -> 0x50 0x52 0x49 0x4E 0x54 0x45 0x52 (all ASCII)
```

### Pitfall 8: Improper Spacing

**Problem**: Missing or extra spaces around tokens.

**Wrong Output**:
```
10PRINT"HELLO"  # No spaces
10  PRINT  "HELLO"  # Extra spaces
```

**Correct Output**:
```
10 PRINT "HELLO"  # Proper spacing
```

### Pitfall 9: Forgetting Colon Handling

**Problem**: Not recognizing colon as statement separator.

**Wrong**:
```
CLS:PRINT -> CLS : PRINT  # Extra spaces around colon
```

**Correct**:
```
CLS:PRINT -> CLS:PRINT  # No spaces around colon
```

### Pitfall 10: Incomplete Token Tables

**Problem**: Missing extended or rare tokens.

**Solution**: Implement unknown token handler:
```python
keyword = TOKEN_TABLE.get(byte, f'<UNKNOWN:0x{byte:02X}>')
```

---

## Conclusion

This document provides a complete reference for understanding and implementing TRS-80 Color Computer BASIC tokenization. The token tables, examples, and implementation guidelines should enable any AI system to:

1. Parse tokenized BASIC files
2. Convert between binary and ASCII formats
3. Handle special cases correctly
4. Implement robust error handling
5. Generate production-quality code

### Quick Reference Summary

- **Token Range**: 0x80-0xFF (single-byte), 0xFF + 0x80-0xFF (two-byte functions)
- **File Structure**: [Optional ML Preamble][Lines with link pointers][0x00 0x00 end]
- **Line Format**: [Link(2)][LineNum(2)][Tokens+ASCII][0x00]
- **Special Cases**: REM, DATA, strings, variable names NOT tokenized
- **Endianness**: Big-endian for all 16-bit values

### For AI Implementation

Use the provided token tables, follow the pseudocode, avoid the common pitfalls, and test with real CoCo BASIC files. The format is well-defined and deterministic, making it suitable for automated processing.

---

*This document is designed to be comprehensive enough for AI systems to implement complete tokenization/detokenization without additional references.*
