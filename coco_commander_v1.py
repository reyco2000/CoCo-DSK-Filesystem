#!/usr/bin/env python3
"""
CoCo Commander V1 - Norton Commander-style TUI for TRS-80 Color Computer DSK Files

Coded by ChipShift Reyco2000@gmail.com Using Claude Code
(C) 2025

A dual-pane file manager for working with CoCo DSK/JVC disk images.
Includes BASIC detokenization support.
"""

import curses
import os
import sys
from pathlib import Path
from typing import Optional, List, Tuple
from coco_dsk import DSKImage, DirectoryEntry

# Import detokenizer from same directory
sys.path.insert(0, str(Path(__file__).parent))
try:
    from coco_detokenizer import detokenize_file
    DETOKENIZER_AVAILABLE = True
except ImportError:
    DETOKENIZER_AVAILABLE = False


class FilePanel:
    """Base class for file browser panels"""

    def __init__(self, window, title: str):
        self.window = window
        self.title = title
        self.selected_index = 0
        self.scroll_offset = 0
        self.items = []

    def get_visible_height(self) -> int:
        """Get the number of visible lines for file listing"""
        height, _ = self.window.getmaxyx()
        return height - 4  # Reserve space for border and title

    def draw_border(self, is_active: bool):
        """Draw panel border with title"""
        self.window.box()
        height, width = self.window.getmaxyx()

        # Draw title
        attr = curses.A_BOLD if is_active else curses.A_NORMAL
        title_str = f" {self.title} "
        self.window.addstr(0, 2, title_str, attr)

    def scroll_up(self):
        """Scroll selection up"""
        if self.selected_index > 0:
            self.selected_index -= 1
            if self.selected_index < self.scroll_offset:
                self.scroll_offset = self.selected_index

    def scroll_down(self):
        """Scroll selection down"""
        if self.selected_index < len(self.items) - 1:
            self.selected_index += 1
            visible_height = self.get_visible_height()
            if self.selected_index >= self.scroll_offset + visible_height:
                self.scroll_offset = self.selected_index - visible_height + 1

    def get_selected_item(self):
        """Get currently selected item"""
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None


class PCPanel(FilePanel):
    """Left panel - PC file browser"""

    def __init__(self, window):
        super().__init__(window, "PC Files")
        self.current_path = Path.cwd()
        self.refresh()

    def refresh(self):
        """Refresh file listing"""
        self.items = []

        # Add parent directory if not at root
        if self.current_path.parent != self.current_path:
            self.items.append(("..", True, 0))

        try:
            # List directories first, then files
            entries = sorted(self.current_path.iterdir(),
                           key=lambda x: (not x.is_dir(), x.name.lower()))

            for entry in entries:
                if entry.name.startswith('.'):
                    continue
                is_dir = entry.is_dir()
                size = 0 if is_dir else entry.stat().st_size
                self.items.append((entry.name, is_dir, size))
        except PermissionError:
            self.items.append(("Permission denied", False, 0))

    def draw(self, is_active: bool):
        """Draw panel contents"""
        self.window.erase()
        self.draw_border(is_active)

        height, width = self.window.getmaxyx()

        # Draw current path
        path_str = str(self.current_path)
        if len(path_str) > width - 4:
            path_str = "..." + path_str[-(width-7):]
        self.window.addstr(1, 2, path_str[:width-4], curses.A_BOLD)

        # Draw file listing
        visible_height = self.get_visible_height()
        for i in range(visible_height):
            list_index = self.scroll_offset + i
            if list_index >= len(self.items):
                break

            name, is_dir, size = self.items[list_index]
            y_pos = i + 3

            # Format line
            if is_dir:
                line = f"[{name}]"
            else:
                # Show size in KB
                size_kb = size / 1024
                if size_kb < 1:
                    size_str = f"{size}B"
                else:
                    size_str = f"{size_kb:.1f}K"
                line = f" {name:<{width-15}} {size_str:>8}"

            # Truncate if too long
            if len(line) > width - 4:
                line = line[:width-7] + "..."

            # Highlight selected item
            if list_index == self.selected_index:
                # Use colored highlight for active panel
                attr = curses.A_REVERSE
                if is_active:
                    attr |= curses.color_pair(2)  # Green for active selection
            else:
                attr = curses.A_NORMAL

            if is_dir:
                attr |= curses.A_BOLD

            try:
                self.window.addstr(y_pos, 2, line[:width-4], attr)
            except curses.error:
                pass

        self.window.refresh()

    def navigate_into(self):
        """Navigate into selected directory or return selected file"""
        item = self.get_selected_item()
        if not item:
            return None

        name, is_dir, _ = item

        if is_dir:
            if name == "..":
                self.current_path = self.current_path.parent
            else:
                self.current_path = self.current_path / name
            self.selected_index = 0
            self.scroll_offset = 0
            self.refresh()
            return None
        else:
            return self.current_path / name


class DSKPanel(FilePanel):
    """Right panel - DSK file browser"""

    def __init__(self, window):
        super().__init__(window, "DSK Image: [None Loaded]")
        self.dsk: Optional[DSKImage] = None
        self.dsk_path: Optional[Path] = None

    def load_dsk(self, dsk_path: Path) -> bool:
        """Load a DSK image"""
        try:
            self.dsk = DSKImage(str(dsk_path))
            if self.dsk.mount():
                self.dsk_path = dsk_path
                self.title = f"DSK Image: {dsk_path.name}"
                self.refresh()
                return True
        except Exception:
            pass
        return False

    def refresh(self):
        """Refresh DSK file listing"""
        self.items = []

        if self.dsk:
            for entry in self.dsk.directory:
                full_name = f"{entry.filename}.{entry.extension}" if entry.extension else entry.filename

                # Calculate file size from granule chain
                chain = self.dsk._get_granule_chain(entry.first_granule)
                size = 0
                for granule_num, sectors_used in chain:
                    size += sectors_used * self.dsk.SECTOR_SIZE

                # Adjust for last sector bytes
                if entry.last_sector_bytes > 0 and size > 0:
                    full_sectors = (size // self.dsk.SECTOR_SIZE) - 1
                    size = (full_sectors * self.dsk.SECTOR_SIZE) + entry.last_sector_bytes

                self.items.append((full_name, entry, size))

    def draw(self, is_active: bool):
        """Draw panel contents"""
        self.window.erase()
        self.draw_border(is_active)

        height, width = self.window.getmaxyx()

        # Draw disk info
        if self.dsk:
            free_granules = sum(1 for g in self.dsk.fat if g == 0xFF)
            free_kb = (free_granules * self.dsk.GRANULE_SIZE) / 1024
            info_str = f"Files: {len(self.items)} | Free: {free_kb:.1f}KB"
            self.window.addstr(1, 2, info_str[:width-4], curses.A_BOLD)
        else:
            self.window.addstr(1, 2, "No DSK image loaded", curses.A_DIM)

        # Draw file listing
        if not self.dsk:
            self.window.refresh()
            return

        visible_height = self.get_visible_height()
        for i in range(visible_height):
            list_index = self.scroll_offset + i
            if list_index >= len(self.items):
                break

            name, entry, size = self.items[list_index]
            y_pos = i + 3

            # Format line with type and size
            type_names = {0x00: "BAS", 0x01: "DAT", 0x02: "ML", 0x03: "TXT"}
            type_str = type_names.get(entry.file_type, "???")
            mode_str = "A" if entry.ascii_flag == 0xFF else "B"

            size_kb = size / 1024
            if size_kb < 1:
                size_str = f"{size}B"
            else:
                size_str = f"{size_kb:.1f}K"

            line = f" {name:<{width-20}} {type_str} {mode_str} {size_str:>7}"

            # Truncate if too long
            if len(line) > width - 4:
                line = line[:width-7] + "..."

            # Highlight selected item
            if list_index == self.selected_index:
                # Use colored highlight for active panel
                attr = curses.A_REVERSE
                if is_active:
                    attr |= curses.color_pair(2)  # Green for active selection
            else:
                attr = curses.A_NORMAL

            try:
                self.window.addstr(y_pos, 2, line[:width-4], attr)
            except curses.error:
                pass

        self.window.refresh()

    def get_selected_entry(self) -> Optional[DirectoryEntry]:
        """Get selected directory entry"""
        item = self.get_selected_item()
        if item:
            _, entry, _ = item
            return entry
        return None


class CoCoCommander:
    """Main Norton Commander-style interface"""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.active_panel = 0  # 0=left(PC), 1=right(DSK)
        self.running = True

        # Initialize colors
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_RED, -1)

        # Setup windows
        self._setup_windows()

    def _setup_windows(self):
        """Create panel windows"""
        height, width = self.stdscr.getmaxyx()

        # Split screen vertically
        panel_width = width // 2

        # Create left panel (PC files)
        self.left_win = curses.newwin(height - 2, panel_width, 0, 0)
        self.left_win.keypad(True)  # Enable arrow keys
        self.pc_panel = PCPanel(self.left_win)

        # Create right panel (DSK files)
        self.right_win = curses.newwin(height - 2, width - panel_width, 0, panel_width)
        self.right_win.keypad(True)  # Enable arrow keys
        self.dsk_panel = DSKPanel(self.right_win)

        # Status bar window
        self.status_win = curses.newwin(2, width, height - 2, 0)

    def draw_status_bar(self):
        """Draw status bar with function key hints"""
        self.status_win.erase()
        height, width = self.status_win.getmaxyx()

        # Function key hints
        hints = [
            ("F2", "Info"),
            ("F3", "View"),
            ("F4", "Edit"),
            ("F5", "Copy"),
            ("F6", "Move"),
            ("F7", "Format"),
            ("F8", "Delete"),
            ("F10", "Quit")
        ]

        x = 1
        for key, label in hints:
            if x + len(key) + len(label) + 3 > width:
                break
            self.status_win.addstr(0, x, key, curses.color_pair(1) | curses.A_BOLD)
            self.status_win.addstr(0, x + len(key), f" {label} ", curses.A_NORMAL)
            x += len(key) + len(label) + 3

        # Active panel indicator
        panel_name = "PC Files" if self.active_panel == 0 else "DSK Image"
        status_text = f" TAB: Switch Panels | Active: {panel_name} "

        # Copyright text (right-aligned)
        copyright_text = "CoCo-Commander V1 (C)2025 by Chipshift - CoCoByte Club"

        # Calculate position to right-align the copyright
        copyright_x = width - len(copyright_text) - 2
        if copyright_x > len(status_text):
            # Display both status and copyright
            self.status_win.addstr(1, 1, status_text, curses.A_BOLD)
            try:
                self.status_win.addstr(1, copyright_x, copyright_text, curses.A_DIM)
            except curses.error:
                pass
        else:
            # Not enough space, just show status
            self.status_win.addstr(1, 1, status_text[:width-2], curses.A_BOLD)

        self.status_win.refresh()

    def draw(self):
        """Draw all panels"""
        self.pc_panel.draw(self.active_panel == 0)
        self.dsk_panel.draw(self.active_panel == 1)
        self.draw_status_bar()

    def show_message(self, message: str, error: bool = False):
        """Show a message box"""
        lines = message.split('\n')
        max_width = max(len(line) for line in lines) + 4
        height = len(lines) + 4

        screen_h, screen_w = self.stdscr.getmaxyx()
        y = (screen_h - height) // 2
        x = (screen_w - max_width) // 2

        msg_win = curses.newwin(height, max_width, y, x)
        msg_win.box()

        attr = curses.color_pair(4) | curses.A_BOLD if error else curses.color_pair(2) | curses.A_BOLD
        title = " Error " if error else " Message "
        msg_win.addstr(0, 2, title, attr)

        for i, line in enumerate(lines):
            msg_win.addstr(i + 2, 2, line)

        msg_win.addstr(height - 2, 2, "Press any key ...", curses.A_DIM)
        msg_win.refresh()
        msg_win.getch()

    def confirm_dialog(self, message: str) -> bool:
        """Show confirmation dialog"""
        lines = message.split('\n')
        max_width = max(len(line) for line in lines) + 4
        height = len(lines) + 5

        screen_h, screen_w = self.stdscr.getmaxyx()
        y = (screen_h - height) // 2
        x = (screen_w - max_width) // 2

        msg_win = curses.newwin(height, max_width, y, x)
        msg_win.box()
        msg_win.addstr(0, 2, " Confirm ", curses.color_pair(3) | curses.A_BOLD)

        for i, line in enumerate(lines):
            msg_win.addstr(i + 2, 2, line)

        msg_win.addstr(height - 3, 2, "Y = Yes, N = No", curses.A_BOLD)
        msg_win.refresh()

        while True:
            key = msg_win.getch()
            if key in (ord('y'), ord('Y')):
                return True
            elif key in (ord('n'), ord('N'), 27):  # 27 = ESC
                return False

    def yes_no_dialog(self, title: str, message: str, default: bool = True) -> Optional[bool]:
        """Show yes/no dialog with default option"""
        lines = message.split('\n')
        max_width = max(len(line) for line in lines) + 4
        height = len(lines) + 6

        screen_h, screen_w = self.stdscr.getmaxyx()
        y = (screen_h - height) // 2
        x = (screen_w - max_width) // 2

        dialog_win = curses.newwin(height, max_width, y, x)
        dialog_win.keypad(True)

        selected = 0 if default else 1  # 0=Yes, 1=No

        while True:
            dialog_win.erase()
            dialog_win.box()
            dialog_win.addstr(0, 2, f" {title} ", curses.color_pair(3) | curses.A_BOLD)

            for i, line in enumerate(lines):
                dialog_win.addstr(i + 2, 2, line)

            # Draw Yes/No buttons
            button_y = height - 3
            yes_attr = curses.A_REVERSE if selected == 0 else curses.A_NORMAL
            no_attr = curses.A_REVERSE if selected == 1 else curses.A_NORMAL

            dialog_win.addstr(button_y, 2, " [ Yes ] ", yes_attr | curses.A_BOLD)
            dialog_win.addstr(button_y, 12, " [ No ] ", no_attr | curses.A_BOLD)

            dialog_win.addstr(height - 2, 2, "LEFT/RIGHT: Select | ENTER: Confirm | ESC: Cancel", curses.A_DIM)
            dialog_win.refresh()

            key = dialog_win.getch()
            if key == curses.KEY_LEFT:
                selected = 0
            elif key == curses.KEY_RIGHT:
                selected = 1
            elif key in (curses.KEY_ENTER, 10, 13):
                return selected == 0  # Return True for Yes, False for No
            elif key == 27:  # ESC
                return None
            elif key in (ord('y'), ord('Y')):
                return True
            elif key in (ord('n'), ord('N')):
                return False

    def handle_f3_view(self):
        """F3 - View file contents"""
        if self.active_panel == 0:
            # View PC file
            item = self.pc_panel.get_selected_item()
            if not item:
                return
            name, is_dir, _ = item
            if is_dir:
                return
            file_path = self.pc_panel.current_path / name
            self.view_file(file_path)
        else:
            # View DSK file
            entry = self.dsk_panel.get_selected_entry()
            if not entry or not self.dsk_panel.dsk:
                return
            data = self.dsk_panel.dsk.extract_file(entry)
            full_name = f"{entry.filename}.{entry.extension}" if entry.extension else entry.filename
            self.view_data(full_name, data)

    def view_file(self, file_path: Path):
        """View PC file contents"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read(8192)  # Read first 8KB
            self.view_data(file_path.name, data)
        except Exception as e:
            self.show_message(f"Error reading file:\n{e}", error=True)

    def view_data(self, title: str, data: bytes):
        """View data in hex/text viewer"""
        screen_h, screen_w = self.stdscr.getmaxyx()
        viewer_win = curses.newwin(screen_h - 4, screen_w - 4, 2, 2)
        viewer_win.keypad(True)

        offset = 0
        bytes_per_line = 16
        visible_lines = screen_h - 8

        while True:
            viewer_win.erase()
            viewer_win.box()
            viewer_win.addstr(0, 2, f" {title} ({len(data)} bytes) ", curses.A_BOLD)

            # Draw hex/ASCII view
            for i in range(visible_lines):
                line_offset = offset + (i * bytes_per_line)
                if line_offset >= len(data):
                    break

                line_data = data[line_offset:line_offset + bytes_per_line]

                # Hex part
                hex_str = ' '.join(f'{b:02X}' for b in line_data)

                # ASCII part
                ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in line_data)

                try:
                    viewer_win.addstr(i + 2, 2, f"{line_offset:08X}: {hex_str:<48} {ascii_str}")
                except curses.error:
                    pass

            viewer_win.addstr(screen_h - 6, 2, "UP/DOWN: Scroll | Q/ESC: Close", curses.A_BOLD)
            viewer_win.refresh()

            key = viewer_win.getch()
            if key in (ord('q'), ord('Q'), 27):  # Q or ESC
                break
            elif key == curses.KEY_DOWN:
                if offset + (visible_lines * bytes_per_line) < len(data):
                    offset += bytes_per_line
            elif key == curses.KEY_UP:
                if offset > 0:
                    offset -= bytes_per_line
            elif key == curses.KEY_NPAGE:  # Page Down
                offset = min(offset + (visible_lines * bytes_per_line),
                           len(data) - bytes_per_line)
            elif key == curses.KEY_PPAGE:  # Page Up
                offset = max(0, offset - (visible_lines * bytes_per_line))

    def handle_f5_copy(self):
        """F5 - Copy file"""
        if self.active_panel == 0:
            # Copy PC file to DSK
            if not self.dsk_panel.dsk:
                self.show_message("No DSK image loaded.\nLoad a DSK file first.", error=True)
                return

            item = self.pc_panel.get_selected_item()
            if not item:
                return
            name, is_dir, _ = item
            if is_dir:
                return

            file_path = self.pc_panel.current_path / name

            # Ask for DSK filename and type
            dsk_name = self.input_dialog("Upload to DSK",
                                        f"Upload: {name}\nDSK filename (8.3):",
                                        name.upper())
            if not dsk_name:
                return

            # Ask for file type
            type_choice = self.choice_dialog("File Type",
                                            ["BASIC (0)", "DATA (1)", "ML (2)", "TEXT (3)"],
                                            2)  # Default to ML
            if type_choice is None:
                return

            # Ask for mode
            mode_choice = self.choice_dialog("File Mode",
                                            ["Binary", "ASCII"],
                                            0)  # Default to Binary
            if mode_choice is None:
                return

            ascii_flag = 0xFF if mode_choice == 1 else 0x00

            try:
                if self.dsk_panel.dsk.upload_from_pc(str(file_path), dsk_name,
                                                     type_choice, ascii_flag):
                    self.dsk_panel.dsk.save()
                    self.dsk_panel.refresh()
                    self.show_message(f"File uploaded!:\n{dsk_name}")
                else:
                    self.show_message("Upload failed!", error=True)
            except Exception as e:
                self.show_message(f"Error uploading file:\n{e}", error=True)
        else:
            # Copy DSK file to PC
            entry = self.dsk_panel.get_selected_entry()
            if not entry or not self.dsk_panel.dsk:
                return

            full_name = f"{entry.filename}.{entry.extension}" if entry.extension else entry.filename

            # Check if it's a BASIC file (type 0x00)
            is_basic = entry.file_type == 0x00
            detokenize = False

            # Ask if user wants to detokenize BASIC files
            if is_basic and DETOKENIZER_AVAILABLE:
                result = self.yes_no_dialog("BASIC File Detected",
                                           f"File: {full_name}\nFile Type: BASIC\n\nDetokenize to readable text?",
                                           default=True)
                if result is None:  # User cancelled
                    return
                detokenize = result

            # Ask for PC filename
            default_name = full_name.lower()
            if detokenize and not default_name.endswith('.txt'):
                # Change extension to .txt for detokenized files
                default_name = default_name.rsplit('.', 1)[0] + '.txt' if '.' in default_name else default_name + '.txt'

            pc_name = self.input_dialog("Download from DSK",
                                       f"Download: {full_name}\nPC filename:",
                                       default_name)
            if not pc_name:
                return

            output_path = self.pc_panel.current_path / pc_name

            try:
                # Copy file from DSK
                if self.dsk_panel.dsk.copy_to_pc(full_name, str(output_path)):
                    # If detokenize was requested, process the file
                    if detokenize:
                        try:
                            detokenized = detokenize_file(str(output_path))
                            Path(output_path).write_text(detokenized, encoding='utf-8')
                            self.show_message(f"File downloaded & detokenized:\n{pc_name}")
                        except Exception as e:
                            self.show_message(f"Downloaded but detokenization failed:\n{e}", error=True)
                    else:
                        self.show_message(f"File downloaded:\n{pc_name}")

                    self.pc_panel.refresh()
                else:
                    self.show_message("Download failed!", error=True)
            except Exception as e:
                self.show_message(f"Error downloading file:\n{e}", error=True)

    def handle_f7_format(self):
        """F7 - Format new DSK image"""
        # Ask for filename
        dsk_name = self.input_dialog("Format New DSK",
                                     "New DSK filename:",
                                     "newdisk.dsk")
        if not dsk_name:
            return

        # Ask for tracks
        tracks_choice = self.choice_dialog("Number of Tracks",
                                          ["35 tracks (160K)", "40 tracks (180K)", "80 tracks (360K)"],
                                          0)
        if tracks_choice is None:
            return
        tracks = [35, 40, 80][tracks_choice]

        # Ask for sides
        sides_choice = self.choice_dialog("Number of Sides",
                                         ["Single-sided", "Double-sided"],
                                         0)
        if sides_choice is None:
            return
        sides = sides_choice + 1

        # Ask for JVC header
        jvc_choice = self.choice_dialog("JVC Header",
                                       ["No header (Real CoCo format)", "Add JVC header (For emulators)"],
                                       0)
        if jvc_choice is None:
            return
        add_jvc = jvc_choice == 1

        # Confirm
        total_kb = (tracks * sides * 18 * 256) // 1024
        jvc_text = " + JVC header" if add_jvc else " (No JVC)"
        if not self.confirm_dialog(f"Format new DSK:\n{dsk_name}\n{tracks}T/{sides}S ({total_kb}KB){jvc_text}\n\nProceed?"):
            return

        try:
            dsk_path = self.pc_panel.current_path / dsk_name
            DSKImage.format_disk(str(dsk_path), tracks=tracks, sides=sides, add_jvc_header=add_jvc)
            self.pc_panel.refresh()
            self.show_message(f"DSK formatted successfully:\n{dsk_name} ({total_kb}KB)")
        except Exception as e:
            self.show_message(f"Error formatting DSK:\n{e}", error=True)

    def handle_f8_delete(self):
        """F8 - Delete file"""
        if self.active_panel == 0:
            # Delete PC file
            item = self.pc_panel.get_selected_item()
            if not item:
                return
            name, is_dir, _ = item
            if is_dir:
                return

            file_path = self.pc_panel.current_path / name

            if self.confirm_dialog(f"Delete PC file:\n{name}\n\nAre you sure?"):
                try:
                    file_path.unlink()
                    self.pc_panel.refresh()
                    self.show_message(f"File deleted:\n{name}")
                except Exception as e:
                    self.show_message(f"Error deleting file:\n{e}", error=True)
        else:
            # Delete DSK file
            entry = self.dsk_panel.get_selected_entry()
            if not entry or not self.dsk_panel.dsk:
                return

            full_name = f"{entry.filename}.{entry.extension}" if entry.extension else entry.filename

            if self.confirm_dialog(f"Delete from DSK:\n{full_name}\n\nAre you sure?"):
                try:
                    if self.dsk_panel.dsk.delete_file(full_name):
                        self.dsk_panel.dsk.save()
                        self.dsk_panel.refresh()
                        self.show_message(f"File deleted from DSK:\n{full_name}")
                    else:
                        self.show_message("Delete failed!", error=True)
                except Exception as e:
                    self.show_message(f"Error deleting file:\n{e}", error=True)

    def handle_f4_edit(self):
        """F4 - Edit PC file (text editor)"""
        if self.active_panel != 0:
            self.show_message("Edit only works on PC files.\nSelect a file in the left panel.", error=True)
            return

        item = self.pc_panel.get_selected_item()
        if not item:
            return
        name, is_dir, _ = item
        if is_dir:
            return

        file_path = self.pc_panel.current_path / name

        try:
            # Read file (limit to text files under 64KB)
            with open(file_path, 'rb') as f:
                data = f.read(65536)

            # Check if it's text
            try:
                text = data.decode('utf-8')
            except UnicodeDecodeError:
                # Try ASCII
                try:
                    text = data.decode('ascii')
                except UnicodeDecodeError:
                    self.show_message("File is not a text file.\nCannot edit binary files.", error=True)
                    return

            # Simple text editor
            edited_text = self.text_editor(name, text)
            if edited_text is not None and edited_text != text:
                if self.confirm_dialog(f"Save changes to:\n{name}\n\nAre you sure?"):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(edited_text)
                    self.show_message(f"File saved:\n{name}")

        except Exception as e:
            self.show_message(f"Error editing file:\n{e}", error=True)

    def text_editor(self, title: str, text: str) -> Optional[str]:
        """Simple text editor"""
        screen_h, screen_w = self.stdscr.getmaxyx()
        editor_win = curses.newwin(screen_h - 4, screen_w - 4, 2, 2)
        editor_win.keypad(True)

        lines = text.split('\n')
        cursor_y = 0
        cursor_x = 0
        offset_y = 0
        offset_x = 0
        visible_lines = screen_h - 8
        visible_cols = screen_w - 8
        modified = False

        curses.curs_set(1)

        while True:
            editor_win.erase()
            editor_win.box()
            status = " [MODIFIED]" if modified else ""
            editor_win.addstr(0, 2, f" Edit: {title}{status} ", curses.A_BOLD)

            # Draw visible lines
            for i in range(visible_lines):
                line_num = offset_y + i
                if line_num >= len(lines):
                    break

                line = lines[line_num]
                visible_part = line[offset_x:offset_x + visible_cols]

                try:
                    editor_win.addstr(i + 2, 2, visible_part[:visible_cols])
                except curses.error:
                    pass

            # Draw status bar
            status_text = f"Line {cursor_y + 1}/{len(lines)} Col {cursor_x + 1} | F9: Save | F10/ESC: Exit"
            editor_win.addstr(screen_h - 6, 2, status_text[:screen_w - 8], curses.A_BOLD)

            # Position cursor
            screen_y = (cursor_y - offset_y) + 2
            screen_x = (cursor_x - offset_x) + 2
            try:
                editor_win.move(screen_y, screen_x)
            except curses.error:
                pass

            editor_win.refresh()

            key = editor_win.getch()

            # Navigation
            if key == curses.KEY_UP:
                if cursor_y > 0:
                    cursor_y -= 1
                    cursor_x = min(cursor_x, len(lines[cursor_y]))
                    if cursor_y < offset_y:
                        offset_y = cursor_y
            elif key == curses.KEY_DOWN:
                if cursor_y < len(lines) - 1:
                    cursor_y += 1
                    cursor_x = min(cursor_x, len(lines[cursor_y]))
                    if cursor_y >= offset_y + visible_lines:
                        offset_y = cursor_y - visible_lines + 1
            elif key == curses.KEY_LEFT:
                if cursor_x > 0:
                    cursor_x -= 1
                    if cursor_x < offset_x:
                        offset_x = max(0, offset_x - 10)
            elif key == curses.KEY_RIGHT:
                if cursor_x < len(lines[cursor_y]):
                    cursor_x += 1
                    if cursor_x >= offset_x + visible_cols:
                        offset_x = cursor_x - visible_cols + 1
            elif key == curses.KEY_HOME:
                cursor_x = 0
                offset_x = 0
            elif key == curses.KEY_END:
                cursor_x = len(lines[cursor_y])
            # Editing
            elif key == curses.KEY_BACKSPACE or key == 127:
                if cursor_x > 0:
                    lines[cursor_y] = lines[cursor_y][:cursor_x-1] + lines[cursor_y][cursor_x:]
                    cursor_x -= 1
                    modified = True
                elif cursor_y > 0:
                    # Join with previous line
                    cursor_x = len(lines[cursor_y - 1])
                    lines[cursor_y - 1] += lines[cursor_y]
                    del lines[cursor_y]
                    cursor_y -= 1
                    modified = True
            elif key == curses.KEY_DC:  # Delete
                if cursor_x < len(lines[cursor_y]):
                    lines[cursor_y] = lines[cursor_y][:cursor_x] + lines[cursor_y][cursor_x+1:]
                    modified = True
                elif cursor_y < len(lines) - 1:
                    # Join with next line
                    lines[cursor_y] += lines[cursor_y + 1]
                    del lines[cursor_y + 1]
                    modified = True
            elif key in (curses.KEY_ENTER, 10, 13):  # Enter
                rest = lines[cursor_y][cursor_x:]
                lines[cursor_y] = lines[cursor_y][:cursor_x]
                lines.insert(cursor_y + 1, rest)
                cursor_y += 1
                cursor_x = 0
                modified = True
            # Control keys
            elif key == curses.KEY_F9:  # Save
                curses.curs_set(0)
                return '\n'.join(lines)
            elif key == curses.KEY_F10 or key == 27:  # Exit
                curses.curs_set(0)
                if modified:
                    if self.confirm_dialog("Discard changes?\n\nAre you sure?"):
                        return None
                else:
                    return None
            # Printable characters
            elif 32 <= key <= 126:
                char = chr(key)
                lines[cursor_y] = lines[cursor_y][:cursor_x] + char + lines[cursor_y][cursor_x:]
                cursor_x += 1
                modified = True

    def handle_f6_move(self):
        """F6 - Move/Rename file in DSK"""
        if self.active_panel != 1:
            self.show_message("Rename only works on DSK files.\nSelect a file in the right panel.", error=True)
            return

        if not self.dsk_panel.dsk:
            return

        entry = self.dsk_panel.get_selected_entry()
        if not entry:
            return

        old_name = f"{entry.filename}.{entry.extension}" if entry.extension else entry.filename

        # Ask for new name
        new_name = self.input_dialog("Rename DSK File",
                                     f"Current: {old_name}\nNew name (8.3):",
                                     old_name)
        if not new_name or new_name == old_name:
            return

        # Parse new name into filename and extension
        if '.' in new_name:
            new_filename, new_ext = new_name.rsplit('.', 1)
        else:
            new_filename, new_ext = new_name, ''

        new_filename = new_filename[:8].ljust(8).upper()
        new_ext = new_ext[:3].ljust(3).upper()

        # Update directory entry
        try:
            # Find and update the directory entry
            for sector_num in range(self.dsk_panel.dsk.DIR_START_SECTOR,
                                   self.dsk_panel.dsk.DIR_END_SECTOR + 1):
                sector_data = bytearray(self.dsk_panel.dsk.read_sector(
                    self.dsk_panel.dsk.DIR_TRACK, sector_num))

                for i in range(8):
                    offset = i * self.dsk_panel.dsk.ENTRY_SIZE
                    entry_data = sector_data[offset:offset + self.dsk_panel.dsk.ENTRY_SIZE]

                    if entry_data[0] not in (0x00, 0xFF):
                        parsed_entry = self.dsk_panel.dsk._parse_directory_entry(entry_data)
                        if parsed_entry and parsed_entry.first_granule == entry.first_granule:
                            # Found the entry - update it
                            sector_data[offset:offset+8] = new_filename.encode('ascii')
                            sector_data[offset+8:offset+11] = new_ext.encode('ascii')

                            self.dsk_panel.dsk.write_sector(
                                self.dsk_panel.dsk.DIR_TRACK, sector_num, bytes(sector_data))
                            self.dsk_panel.dsk.save()
                            self.dsk_panel.refresh()

                            self.show_message(f"File renamed:\n{old_name}\n→\n{new_name}")
                            return

            self.show_message("Failed to find directory entry", error=True)

        except Exception as e:
            self.show_message(f"Error renaming file:\n{e}", error=True)

    def handle_f2_info(self):
        """F2 - Show file/disk info"""
        screen_h, screen_w = self.stdscr.getmaxyx()
        info_win = curses.newwin(screen_h - 6, screen_w - 8, 3, 4)
        info_win.box()
        info_win.addstr(0, 2, " Information ", curses.A_BOLD)

        y = 2

        if self.active_panel == 0:
            # PC file info
            item = self.pc_panel.get_selected_item()
            if item:
                name, is_dir, size = item
                if not is_dir:
                    file_path = self.pc_panel.current_path / name
                    try:
                        stat = file_path.stat()
                        info_win.addstr(y, 2, f"PC File: {name}", curses.A_BOLD)
                        y += 2
                        info_win.addstr(y, 2, f"Path: {file_path}")
                        y += 1
                        info_win.addstr(y, 2, f"Size: {size} bytes ({size/1024:.2f} KB)")
                        y += 1
                        info_win.addstr(y, 2, f"Granules needed for DSK: {(size + 2303) // 2304}")
                    except Exception as e:
                        info_win.addstr(y, 2, f"Error: {e}")
        else:
            # DSK file info
            if self.dsk_panel.dsk:
                entry = self.dsk_panel.get_selected_entry()
                if entry:
                    full_name = f"{entry.filename}.{entry.extension}" if entry.extension else entry.filename

                    type_names = {0x00: "BASIC", 0x01: "DATA", 0x02: "Machine Language", 0x03: "TEXT"}
                    type_str = type_names.get(entry.file_type, f"Unknown ({entry.file_type})")
                    mode_str = "ASCII" if entry.ascii_flag == 0xFF else "Binary"

                    info_win.addstr(y, 2, f"DSK File: {full_name}", curses.A_BOLD)
                    y += 2
                    info_win.addstr(y, 2, f"Type: {type_str}")
                    y += 1
                    info_win.addstr(y, 2, f"Mode: {mode_str}")
                    y += 1
                    info_win.addstr(y, 2, f"First Granule: {entry.first_granule}")
                    y += 1
                    info_win.addstr(y, 2, f"Last Sector Bytes: {entry.last_sector_bytes}")
                    y += 2

                    # Show granule chain
                    chain = self.dsk_panel.dsk._get_granule_chain(entry.first_granule)
                    granule_nums = ', '.join(str(g) for g, _ in chain)
                    info_win.addstr(y, 2, f"Granule Chain ({len(chain)} granules):", curses.A_BOLD)
                    y += 1
                    info_win.addstr(y, 2, granule_nums)
                    y += 2

                # Disk statistics
                free_granules = sum(1 for g in self.dsk_panel.dsk.fat if g == 0xFF)
                used_granules = 68 - free_granules

                info_win.addstr(y, 2, "Disk Statistics:", curses.A_BOLD)
                y += 1
                info_win.addstr(y, 2, f"Total Granules: 68")
                y += 1
                info_win.addstr(y, 2, f"Used: {used_granules} ({used_granules * 2304} bytes)")
                y += 1
                info_win.addstr(y, 2, f"Free: {free_granules} ({free_granules * 2304} bytes)")

        info_win.addstr(screen_h - 8, 2, "Press any key to close...", curses.A_DIM)
        info_win.refresh()
        info_win.getch()

    def input_dialog(self, title: str, prompt: str, default: str = "") -> Optional[str]:
        """Show input dialog and return entered text"""
        curses.curs_set(1)

        lines = prompt.split('\n')
        max_width = max(len(title), max(len(line) for line in lines), 40) + 6
        height = len(lines) + 6

        screen_h, screen_w = self.stdscr.getmaxyx()
        y = (screen_h - height) // 2
        x = (screen_w - max_width) // 2

        input_win = curses.newwin(height, max_width, y, x)
        input_win.keypad(True)
        input_win.box()
        input_win.addstr(0, 2, f" {title} ", curses.A_BOLD)

        for i, line in enumerate(lines):
            input_win.addstr(i + 2, 2, line)

        input_y = len(lines) + 2
        input_win.addstr(input_y, 2, "> ")

        # Manual input handling with pre-filled default text
        buffer = list(default)
        cursor_pos = len(buffer)
        max_input_width = max_width - 8

        while True:
            # Display current buffer
            display_text = ''.join(buffer)[:max_input_width]
            input_win.addstr(input_y, 4, ' ' * max_input_width)  # Clear line
            input_win.addstr(input_y, 4, display_text)
            input_win.move(input_y, 4 + min(cursor_pos, max_input_width - 1))
            input_win.refresh()

            key = input_win.getch()

            if key in (curses.KEY_ENTER, 10, 13):  # Enter
                break
            elif key == 27:  # ESC
                curses.curs_set(0)
                return None
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                if cursor_pos > 0:
                    buffer.pop(cursor_pos - 1)
                    cursor_pos -= 1
            elif key == curses.KEY_DC:  # Delete
                if cursor_pos < len(buffer):
                    buffer.pop(cursor_pos)
            elif key == curses.KEY_LEFT:
                if cursor_pos > 0:
                    cursor_pos -= 1
            elif key == curses.KEY_RIGHT:
                if cursor_pos < len(buffer):
                    cursor_pos += 1
            elif key == curses.KEY_HOME:
                cursor_pos = 0
            elif key == curses.KEY_END:
                cursor_pos = len(buffer)
            elif 32 <= key <= 126:  # Printable characters
                if len(buffer) < max_input_width:
                    buffer.insert(cursor_pos, chr(key))
                    cursor_pos += 1

        curses.curs_set(0)
        result = ''.join(buffer)
        return result if result else None

    def choice_dialog(self, title: str, choices: List[str], default: int = 0) -> Optional[int]:
        """Show choice dialog and return selected index"""
        max_width = max(len(title), max(len(c) for c in choices)) + 10
        height = len(choices) + 6

        screen_h, screen_w = self.stdscr.getmaxyx()
        y = (screen_h - height) // 2
        x = (screen_w - max_width) // 2

        choice_win = curses.newwin(height, max_width, y, x)
        choice_win.keypad(True)

        selected = default

        while True:
            choice_win.erase()
            choice_win.box()
            choice_win.addstr(0, 2, f" {title} ", curses.A_BOLD)

            for i, choice in enumerate(choices):
                attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
                choice_win.addstr(i + 2, 2, f" {choice} ", attr)

            choice_win.addstr(height - 2, 2, "ENTER: Select | ESC: Cancel", curses.A_DIM)
            choice_win.refresh()

            key = choice_win.getch()
            if key == curses.KEY_UP and selected > 0:
                selected -= 1
            elif key == curses.KEY_DOWN and selected < len(choices) - 1:
                selected += 1
            elif key in (curses.KEY_ENTER, 10, 13):
                return selected
            elif key == 27:  # ESC
                return None

    def handle_enter(self):
        """Handle Enter key - navigate or load DSK"""
        if self.active_panel == 0:
            # PC panel - navigate into directory or load DSK
            result = self.pc_panel.navigate_into()
            if result and result.suffix.lower() in ('.dsk', '.jvc'):
                # Try to load DSK image
                if self.dsk_panel.load_dsk(result):
                    self.show_message(f"Loaded DSK image:\n{result.name}")
                else:
                    self.show_message(f"Failed to load DSK:\n{result.name}", error=True)
        else:
            # DSK panel - show info
            self.handle_f2_info()

    def run(self):
        """Main event loop"""
        self.stdscr.clear()
        self.stdscr.refresh()

        while self.running:
            self.draw()

            # Get active panel
            active_win = self.left_win if self.active_panel == 0 else self.right_win
            active_panel = self.pc_panel if self.active_panel == 0 else self.dsk_panel

            # Get input
            key = active_win.getch()

            # Handle keys
            if key == curses.KEY_UP:
                active_panel.scroll_up()
            elif key == curses.KEY_DOWN:
                active_panel.scroll_down()
            elif key == 9:  # TAB
                self.active_panel = 1 - self.active_panel
                # Reset DSK panel selection to top when switching to it
                if self.active_panel == 1:
                    self.dsk_panel.selected_index = 0
                    self.dsk_panel.scroll_offset = 0
            elif key in (curses.KEY_ENTER, 10, 13):  # ENTER
                self.handle_enter()
            elif key == curses.KEY_F2:
                self.handle_f2_info()
            elif key == curses.KEY_F3:
                self.handle_f3_view()
            elif key == curses.KEY_F4:
                self.handle_f4_edit()
            elif key == curses.KEY_F5:
                self.handle_f5_copy()
            elif key == curses.KEY_F6:
                self.handle_f6_move()
            elif key == curses.KEY_F7:
                self.handle_f7_format()
            elif key == curses.KEY_F8:
                self.handle_f8_delete()
            elif key == curses.KEY_F10 or key == ord('q') or key == ord('Q'):
                if self.confirm_dialog("Exit CoCo Commander?\n\nAre you sure?"):
                    self.running = False


def main(stdscr):
    """Main entry point"""
    # Hide cursor
    curses.curs_set(0)

    # Initialize commander
    commander = CoCoCommander(stdscr)
    commander.run()


if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
