#!/usr/bin/env python3
"""
Yarn — a stack-based esoteric programming language based on crochet patterns.

Usage:
    yarn                 start an interactive session (a REPL)
    yarn pattern.yarn    run a pattern file
"""

import operator
import re
import sys

# Recursive special stitches need real headroom, since each level of Yarn
# recursion costs several Python stack frames.
sys.setrecursionlimit(10000)


class YarnError(Exception):
    pass


DEF_START = re.compile(r'^Special Stitch:\s*([^(]+?)\s*(\(.*\))?\s*$', re.IGNORECASE)
DEF_END = re.compile(r'^End special stitch\.?\s*$', re.IGNORECASE)
IF_START = re.compile(r'^if\s+(.+?)\s*:?\s*$', re.IGNORECASE)
OTHERWISE = re.compile(r'^otherwise\s*:?\s*$', re.IGNORECASE)
IF_END = re.compile(r'^end if\.?\s*$', re.IGNORECASE)

CONDITION = re.compile(
    r'^(hook|count|-?\d+)\s*(=|!=|<=|>=|<|>)\s*(hook|count|-?\d+)$', re.IGNORECASE)
COMPARATORS = {
    '=': operator.eq, '!=': operator.ne,
    '<': operator.lt, '>': operator.gt,
    '<=': operator.le, '>=': operator.ge,
}


class YarnInterpreter:
    def __init__(self):
        self.stack = []
        self.markers = {}
        self.words = {}
        self.output = []
        self.fastened_off = False

    # ---------- parsing ----------
    #
    # A program is a list of instructions. Each instruction is one of:
    #   ('stitch', text)                          a single stitch or word call
    #   ('if', cond_text, then_instrs, else_instrs)   a conditional branch
    #
    # Loops (`*...* rep N times`) are expanded into plain 'stitch' entries
    # at parse time, since their count is always fixed.

    def parse_program(self, lines, i=0, stop=()):
        """Parse lines[i:] into a list of instructions. If `stop` is given,
        parsing halts (without consuming) at the first line whose stripped,
        Row-prefix-stripped content matches one of those patterns; otherwise
        parsing runs to the end of `lines`. Returns (instructions, next_index)."""
        instrs = []
        while i < len(lines):
            raw = lines[i]
            stripped = raw.strip()

            if not stripped:
                i += 1
                continue
            if self._is_comment_or_metadata(stripped):
                i += 1
                continue

            content = self._strip_row_prefix(self._strip_trailing_comment(stripped))

            if stop and any(p.match(content) for p in stop):
                return instrs, i

            if not content:
                i += 1
                continue

            m = DEF_START.match(content)
            if m:
                name = m.group(1).strip()
                body, i = self.parse_program(lines, i + 1, stop=(DEF_END,))
                if i >= len(lines):
                    raise YarnError(f'Special stitch "{name}" is missing "End special stitch."')
                i += 1  # consume "End special stitch."
                self.words[name.lower()] = body
                continue

            m = IF_START.match(content)
            if m:
                cond = m.group(1).strip()
                then_body, i = self.parse_program(lines, i + 1, stop=(OTHERWISE, IF_END))
                if i >= len(lines):
                    raise YarnError(f'"if {cond}" is missing "end if."')
                else_body = []
                if OTHERWISE.match(self._strip_row_prefix(lines[i].strip())):
                    i += 1
                    else_body, i = self.parse_program(lines, i, stop=(IF_END,))
                    if i >= len(lines):
                        raise YarnError(f'"if {cond}" is missing "end if."')
                i += 1  # consume "end if."
                instrs.append(('if', cond, then_body, else_body))
                continue

            instrs.extend(self.parse_row(content))
            i += 1

        if stop:
            raise YarnError('Reached the end of the pattern with an unfinished '
                             '"if" or "Special Stitch" block.')
        return instrs, i

    def parse_row(self, content):
        return [('stitch', t) for t in self.tokenize(content)]

    def _strip_row_prefix(self, line):
        m = re.match(r'^Row\s+[\w\-]+\s*:\s*(.*)$', line, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        if re.match(r'^magic ring\b', line, re.IGNORECASE):
            return ''
        return line

    def preprocess_line(self, raw_line):
        """Strip comments, metadata, and 'Row N:' labels off a single line.
        Returns None if the line has nothing left to execute. Used by the
        REPL for ordinary one-line rows."""
        line = raw_line.strip()
        if not line or self._is_comment_or_metadata(line):
            return None
        line = self._strip_row_prefix(self._strip_trailing_comment(line))
        return line or None

    def _strip_trailing_comment(self, line):
        """Strip a trailing '-- comment', respecting double-quoted strings
        so marker names like "a -- b" aren't mistaken for comments."""
        in_quotes = False
        i = 0
        while i < len(line) - 1:
            ch = line[i]
            if ch == '"':
                in_quotes = not in_quotes
            elif not in_quotes and line[i:i + 2] == '--':
                return line[:i].rstrip()
            i += 1
        return line

    def _is_comment_or_metadata(self, line):
        lowered = line.lower()
        if line.startswith(('--', ';;', '#')):
            return True
        for prefix in ('materials:', 'gauge:', 'hook:', 'yarn weight:', 'notes:'):
            if lowered.startswith(prefix):
                return True
        return False

    # ---------- row / loop tokenizing ----------

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

    # ---------- execution ----------

    def run(self, source):
        instrs, _ = self.parse_program(source.splitlines())
        self.execute_instructions(instrs)
        return ''.join(self.output)

    def execute_row(self, content):
        """Execute a single already-prefix-stripped line of stitches (no
        block constructs) — used by the REPL for ordinary rows."""
        self.execute_instructions(self.parse_row(content))

    def execute_instructions(self, instrs):
        for instr in instrs:
            if instr[0] == 'stitch':
                self.execute_stitch(instr[1])
            else:  # 'if'
                _, cond, then_body, else_body = instr
                if self._eval_condition(cond):
                    self.execute_instructions(then_body)
                else:
                    self.execute_instructions(else_body)
            if self.fastened_off:
                return

    def _eval_condition(self, cond_text):
        m = CONDITION.match(cond_text.strip())
        if not m:
            raise YarnError(
                f'Bad stitch check: "{cond_text}" (try something like '
                f'"hook = 0", "count > 3", or "hook != count")')
        left = self._eval_operand(m.group(1))
        right = self._eval_operand(m.group(3))
        return COMPARATORS[m.group(2)](left, right)

    def _eval_operand(self, tok):
        low = tok.lower()
        if low == 'hook':
            self._need(1)
            return self.stack[-1]
        if low == 'count':
            return len(self.stack)
        return int(tok)

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

        if low in self.words:
            try:
                self.execute_instructions(self.words[low])
            except RecursionError:
                raise YarnError(
                    f'"{st}" recursed too deep — check that its "if" '
                    f'condition actually reaches a base case.'
                )
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

Special stitches (functions) — define once, use like any other stitch:
  Special Stitch: name (optional note)
    st, st, st
  End special stitch.

  A special stitch takes whatever's on the hook as its input and leaves
  its result there too — no separate parameter list, same as sc or dc.
  It can call itself (recursion) — see "if" below for how to stop it.

if / otherwise — a conditional branch:
  if <condition>
    st, st          (used when the condition is true)
  otherwise
    st, st          (used when it's false — this part is optional)
  end if.

  Conditions compare two of: hook (top of the stack, peeked), count
  (how many loops are on the hook), or a literal number — using
  =, !=, <, >, <=, or >=. Examples: "if hook = 0", "if count > 3".

REPL-only commands:
  :stack, :s      show what's currently on the hook
  :markers, :m    show stitch markers in use
  :words, :w      list defined special stitches
  :help, :h       show this list
  :quit, :q       leave without fastening off
"""


def format_instrs(instrs, indent=1):
    pad = '  ' * indent
    lines = []
    for instr in instrs:
        if instr[0] == 'stitch':
            lines.append(pad + instr[1])
        else:
            _, cond, then_body, else_body = instr
            lines.append(f'{pad}if {cond}')
            lines.append(format_instrs(then_body, indent + 1))
            if else_body:
                lines.append(f'{pad}otherwise')
                lines.append(format_instrs(else_body, indent + 1))
            lines.append(f'{pad}end if.')
    return '\n'.join(lines)


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
        if lowered in (':w', ':words'):
            if interp.words:
                for name, body in interp.words.items():
                    print(f'{name}:')
                    print(format_instrs(body))
            else:
                print("No special stitches defined yet.")
            continue

        def_match = DEF_START.match(stripped)
        if def_match:
            name = def_match.group(1).strip()
            print(f'  defining "{name}" — type "End special stitch." when done')
            body_lines = []
            while True:
                try:
                    body_raw = input("     ... ")
                except EOFError:
                    print("\nFastened off. Bye!")
                    return
                if DEF_END.match(interp._strip_row_prefix(body_raw.strip())):
                    break
                body_lines.append(body_raw)
            try:
                body_instrs, _ = interp.parse_program(body_lines, 0)
            except YarnError as e:
                print(f"Yarn error: {e}")
                continue
            interp.words[name.lower()] = body_instrs
            print(f'Special stitch "{name}" saved.')
            row_num += 1
            continue

        if_match = IF_START.match(stripped)
        if if_match:
            cond = if_match.group(1).strip()
            print(f'  if "{cond}" — enter the true branch, then optionally '
                  f'"otherwise" and its branch, then "end if."')
            body_lines = [stripped]
            while True:
                try:
                    body_raw = input("     ... ")
                except EOFError:
                    print("\nFastened off. Bye!")
                    return
                body_lines.append(body_raw)
                if IF_END.match(interp._strip_row_prefix(body_raw.strip())):
                    break

            try:
                instrs, _ = interp.parse_program(body_lines, 0)
            except YarnError as e:
                print(f"Yarn error: {e}")
                continue

            before = len(interp.output)
            try:
                interp.execute_instructions(instrs)
            except YarnError as e:
                print(f"Yarn error: {e}")
                row_num += 1
                continue
            except Exception as e:
                print(f"Error: {e}")
                row_num += 1
                continue

            new_output = ''.join(interp.output[before:])
            if new_output:
                print(new_output, end='' if new_output.endswith('\n') else '\n')
            print(f"  (hook: {interp.stack})")

            if interp.fastened_off:
                print("Fastened off. Bye!")
                break
            row_num += 1
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
