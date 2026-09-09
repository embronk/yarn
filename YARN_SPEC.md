# Yarn

A stack-based programming language where your code looks like a crochet pattern.

The stack is **the loops currently on your hook**. Every stitch either adds a
loop, removes a loop, or transforms the loop(s) already there — exactly like
real crochet. A program is a pattern; each line is a **Row**; you work it top
to bottom, left to right, just like following instructions off a printed
pattern card.

## Running it

```
python3 yarn_interpreter.py my_pattern.yarn    # run a pattern file
python3 yarn_interpreter.py                    # interactive REPL
```

In the REPL, each line you type is one row — it executes immediately and
shows you what's left on the hook. `:stack`, `:markers`, and `:help` are
REPL-only commands; `FO` (or Ctrl-D) fastens off and exits.

## Structure of a pattern

```
Materials: [ignored — flavor text for you, the crocheter]
Gauge: [ignored]

magic ring          -- optional, marks the start; does nothing

Row 1: <stitches>
Row 2: <stitches>
...

FO
```

- Lines starting with `Materials:`, `Gauge:`, `Hook:`, `Yarn weight:`, or
  `Notes:` are ignored — put whatever project notes you like there.
- Lines starting with `--`, `;;`, or `#` are comments.
- `magic ring` is an optional no-op that marks where the pattern begins.
- `FO` ("fasten off") ends the program immediately, wherever it appears.
- The `Row N:` label is decorative — rows execute in file order regardless
  of what number you give them, so you can write `Row 4-9:` for a repeated
  block, same as a real pattern.

## Stitch dictionary

| Stitch | Name | Effect |
|---|---|---|
| `ch N` | chain | push the number `N` onto the hook |
| `sc` | single crochet | pop `a`, push `a + 1` |
| `hdc` | half double crochet | pop `a`, push `a + 1` |
| `dc` | double crochet | pop `a`, push `a + 2` |
| `tr` | treble crochet | pop `a`, push `a + 3` |
| `inc` | increase | pop `a`, push `a`, push `a` (duplicate) |
| `dec` | decrease | pop `b`, pop `a`, push `a - b` (combines two loops into one) |
| `sl st` | slip stitch | pop and discard — joins/closes off a loop |
| `pull through` | — | pop `a`, print it as a character (`chr(a)`) |
| `snip` | — | pop `a`, print it as a number, followed by a newline |
| `place marker "name"` | stitch marker | **peek** the top of the hook and remember it as `name` (doesn't consume the loop) |
| `work into "name"` | — | push a fresh copy of whatever `name` was marking |
| `FO` | fasten off | end the program |

## Loops: `*...* rep N times`

Wrap a group of stitches in `*` `*` and follow it with `rep N times` to
repeat that group, exactly like a crochet pattern's repeat notation:

```
Row 2: *sc, dc* rep 5 times, sl st
```

This works the same as writing `sc, dc, sc, dc, sc, dc, sc, dc, sc, dc, sl st`.
Repeats always run a fixed number of times — real crochet patterns don't
have "if" statements either, you just follow the rows as written, so Yarn
doesn't either. It's a bounded-loop language, not Turing-complete, and
that's on purpose.

## Examples

**Hello, World!** (`examples/hello_world.yarn`) — chains up each character's
ASCII code and pulls it through directly.

**Count to Ten** (`examples/count_to_ten.yarn`) — a loop that duplicates,
prints, and increments a running count:

```
Row 1: ch 1
Row 2: *inc, snip, sc* rep 10 times
FO
```

**Stitch Markers** (`examples/markers_demo.yarn`) — shows `place marker` /
`work into` acting as named variables you can reuse without re-deriving the
value:

```
Row 1: ch 42, place marker "star"
Row 2: work into "star", pull through, work into "star", pull through, work into "star", pull through
FO
```

## Error messages

Yarn tries to stay in character:

- Popping from an empty stack raises **"Dropped stitch! Not enough loops on
  the hook"**.
- Working into an unknown marker raises an error naming the missing marker.
- An unrecognized stitch name raises **"Unrecognized stitch"**.

## Ideas for extending it

- `frog it` — pop the whole stack and start the row over (a "frog" undoes
  crochet: "rip it, rip it").
- `join in the round` — turn the stack into a circular buffer.
- `color change` — a second, separate stack for a "type" tag on each value.
- `blocking` — a final formatting pass over the output string.

Pull on any of these the way you'd pull out a new skein — the core stitch
dictionary above is deliberately small so it's easy to extend.
