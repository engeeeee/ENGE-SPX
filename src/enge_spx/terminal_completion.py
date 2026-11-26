"""Inline shortcuts anchored to an echoed shell prompt."""
import unicodedata

from wcwidth import wcswidth

from .terminal_shortcuts import BUILTINS

PROMPT_ENDS = ("$ ", "# ", "% ", "❯ ", "➜ ")


class ShellCompletion:
    def __init__(self, custom=()):
        self.set_commands(custom)

    def set_commands(self, custom):
        self.commands = tuple(dict.fromkeys(item.text for item in (*custom, *BUILTINS) if item.group == "shell"))
        self.clear()

    def clear(self):
        self.anchor = None
        self.prefix = ""

    @staticmethod
    def active(screen):
        # Readline/fish/zle advertise bracketed paste at an editable prompt.
        return screen.bracketed and screen.primary is None and not screen.mouse and not screen.cursor.hidden

    @staticmethod
    def text(line, blank, start, end):
        return "".join(line.get(column, blank).data for column in range(start, end))

    @staticmethod
    def empty_to_right(line, column):
        return all(cell.data in (" ", "") for x, cell in line.items() if x >= column)

    def input(self, screen, data):
        if not self.active(screen):
            self.clear()
            return
        if data == b"\x7f":
            self.prefix = self.prefix[:-1]
            return
        text = data.decode("utf-8", errors="replace")
        prefix = self.prefix + text
        # Keep only prefixes that match a configured command.
        if not text.isprintable() or not any(command.startswith(prefix) for command in self.commands):
            self.clear()
            return
        if self.anchor is None:
            row, column = screen.cursor.y, screen.cursor.x
            line = screen.buffer[row]
            prompt = self.text(line, screen.default_char, 0, column)
            marker = screen.shell_prompt == (row, column) if screen.marked_shell else (
                prompt.endswith(PROMPT_ENDS) or prompt.endswith("> ") and ("@" in prompt or prompt.startswith("PS ")))
            if not marker or not self.empty_to_right(line, column):
                return
            self.anchor = row, column, prompt
        self.prefix = prefix

    def preview(self, screen):
        if not self.prefix.strip() or self.anchor is None or not self.active(screen):
            return None
        row, start, prompt = self.anchor
        column = screen.cursor.x
        if row != screen.cursor.y or column != start + wcswidth(self.prefix) or column >= screen.columns:
            return None
        if screen.marked_shell and screen.shell_prompt != (row, start):
            return None
        line, blank = screen.buffer[row], screen.default_char
        echoed = self.text(line, blank, start, column)
        if (unicodedata.normalize("NFC", echoed) != unicodedata.normalize("NFC", self.prefix)
                or self.text(line, blank, 0, start) != prompt or not self.empty_to_right(line, column)):
            return None
        if self.prefix in self.commands:
            return None
        command = next((value for value in self.commands if value.startswith(self.prefix)), None)
        if command is None:
            return None
        suffix = command[len(self.prefix):]
        if 0 < wcswidth(suffix) <= screen.columns - column:
            return row, column, suffix
        return None
