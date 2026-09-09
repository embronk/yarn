#!/usr/bin/env python3
"""
Yarn — a stack-based esoteric programming language based on crochet patterns.

Usage:
    yarn                 start an interactive session (a REPL)
    yarn pattern.yarn    run a pattern file
"""

import re
import sys


class YarnError(Exception):
    pass


class YarnInterpreter:
    def __init__(self):
        self.stack = []
        self.markers = {}
        self.output = []
        self.fastened_off = False

    # ---------- top level ----------

    def run(self, source):
        for raw_line in source.splitlines():
            line = self.preprocess_line(raw_line)
            if line is None:
                continue
            self.execute_row(line)
            if self.fastened_off:
                break

        return ''.join(self.output)

    def preprocess_line(self, raw_line):
        """Strip comments, metadata, and 'Row N:' labels off a single line.
        Returns None if the line has nothing left to execute."""
        line = raw_line.strip()
        if not line or self._is_comment_or_metadata(line):
            return None

        m = re.match(r'^Row\s+[\w\-]+\s*:\s*(.*)$', line, re.IGNORECASE)
        if m:
            line = m.group(1).strip()
        elif re.match(r'^magic ring\b', line, re.IGNORECASE):
            return None

        return line or None

    def _is_comment_or_metadata(self, line):
        lowered = line.lower()
        if line.startswith(('--', ';;', '#')):
            return True
        for prefix in ('materials:', 'gauge:', 'hook:', 'yarn weight:', 'notes:'):
            if lowered.startswith(prefix):
                return True
        return False

    # ---------- row parsing ----------

    def execute_row(self, line):
        for stitch in self.tokenize(line):
            self.execute_stitch(stitch)
            if self.fastened_off:
                return

    def tokenize(self, line):
        line = re.sub(r'\bturn\.?\s*$', '', line, flags=re.IGNORECASE).strip()
        tokens = []
        loop_pattern = re.compile(r'\*(.*?)\*\s*rep\s+(\d+)\s+times?', re.IGNORECASE)
        pos = 0
        for match in loop_pattern.finditer(line):
            tokens.extend(self._split(line[pos:match.start()]))
            inner_tokens = self._split(match.group(1))
            times = int(match.group(2))
            for _ in range(times):
                tokens.extend(inner_tokens)
            pos = match.end()
        tokens.extend(self._split(line[pos:]))
        return [t for t in tokens if t]

    def _split(self, text):
        return [p.strip() for p in text.split(',') if p.strip()]

    # ---------- stitches ----------

    def execute_stitch(self, st):
        low = st.lower()

        m = re.match(r'^ch\s+(-?\d+)$', low)
        if m:
            self.stack.append(int(m.group(1)))
            return

        if low == 'sc':
            self._need(1); self.stack.append(self.stack.pop() + 1); return
        if low == 'dc':
            self._need(1); self.stack.append(self.stack.pop() + 2); return
        if low == 'tr':
            self._need(1); self.stack.append(self.stack.pop() + 3); return
        if low == 'hdc':
            self._need(1); self.stack.append(self.stack.pop() + 1); return

        if low == 'dec':
            self._need(2)
            b = self.stack.pop(); a = self.stack.pop()
            self.stack.append(a - b)
            return

        if low == 'inc':
            self._need(1)
            a = self.stack.pop()
            self.stack.append(a); self.stack.append(a)
            return

        if low in ('sl st', 'slst', 'sl-st'):
            self._need(1); self.stack.pop(); return

        if low == 'pull through':
            self._need(1)
            self.output.append(chr(self.stack.pop()))
            return

        if low == 'snip':
            self._need(1)
            self.output.append(str(self.stack.pop()) + '\n')
            return

        m = re.match(r'^place marker "([^"]+)"$', st, re.IGNORECASE)
        if m:
            self._need(1)
            self.markers[m.group(1)] = self.stack[-1]
            return

        m = re.match(r'^work into "([^"]+)"$', st, re.IGNORECASE)
        if m:
            name = m.group(1)
            if name not in self.markers:
                raise YarnError(f'No stitch marker named "{name}"')
            self.stack.append(self.markers[name])
            return

        if low in ('fo', 'fasten off', 'fasten off.'):
            self.fastened_off = True
            return

        raise YarnError(f'Unrecognized stitch: "{st}"')

    def _need(self, n):
        if len(self.stack) < n:
            raise YarnError(f'Dropped stitch! Not enough loops on the hook '
                             f'(needed {n}, had {len(self.stack)}).')


HELP_TEXT = """\
Stitches:
  ch N                    chain — push N onto the hook
  sc / hdc                push a+1
  dc                       push a+2
  tr                       push a+3
  inc                      duplicate the top loop
  dec                      pop two loops, push their difference
  sl st                    drop the top loop
  pull through             pop and print as a character
  snip                     pop and print as a number
  place marker "name"      remember the top loop as "name" (doesn't pop it)
  work into "name"         push a fresh copy of a marked value
  *st, st* rep N times     repeat a group of stitches N times
  FO                       fasten off (ends the session)

REPL-only commands:
  :stack, :s      show what's currently on the hook
  :markers, :m    show stitch markers in use
  :help, :h       show this list
  :quit, :q       leave without fastening off
"""


def repl():
    print("Yarn REPL — type stitches a row at a time.")
    print("':help' for the stitch dictionary, 'FO' or Ctrl-D to fasten off.\n")

    interp = YarnInterpreter()
    row_num = 1

    while True:
        try:
            raw = input(f"Row {row_num}: ")
        except EOFError:
            print("\nFastened off. Bye!")
            break
        except KeyboardInterrupt:
            print()
            continue

        stripped = raw.strip()
        if not stripped:
            continue

        lowered = stripped.lower()
        if lowered in (':q', ':quit'):
            print("Left mid-row — nothing's fastened off.")
            break
        if lowered in (':h', ':help'):
            print(HELP_TEXT)
            continue
        if lowered in (':s', ':stack'):
            print(f"On the hook: {interp.stack}")
            continue
        if lowered in (':m', ':markers'):
            print(f"Markers: {interp.markers}" if interp.markers else "No markers placed yet.")
            continue

        line = interp.preprocess_line(stripped)
        if line is None:
            continue

        before = len(interp.output)
        try:
            interp.execute_row(line)
        except YarnError as e:
            print(f"Yarn error: {e}")
            continue
        except Exception as e:
            print(f"Error: {e}")
            continue

        new_output = ''.join(interp.output[before:])
        if new_output:
            print(new_output, end='' if new_output.endswith('\n') else '\n')
        print(f"  (hook: {interp.stack})")

        if interp.fastened_off:
            print("Fastened off. Bye!")
            break

        row_num += 1


def run_file(path):
    with open(path, 'r') as f:
        source = f.read()
    interp = YarnInterpreter()
    try:
        result = interp.run(source)
    except YarnError as e:
        print(f"Yarn error: {e}")
        sys.exit(1)
    print(result, end='')


def main():
    if len(sys.argv) == 1:
        repl()
    elif len(sys.argv) == 2 and sys.argv[1] not in ('-h', '--help'):
        run_file(sys.argv[1])
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
