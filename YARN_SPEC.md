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
- Lines starting with `--`, `;;`, or `#` are comments; `--` can also trail
  after code on the same line (e.g. `sc  -- increment`), as long as it's
  outside any quoted marker name.
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
`rep` always runs a fixed number of times, decided when the pattern is
parsed — for a loop whose length depends on a value at runtime, use a
recursive special stitch with an `if` instead (see below).

## Conditionals, and Turing completeness

`if` / `otherwise` / `end if.` gives Yarn a real branch — and combined with
a special stitch calling itself, that's enough to make Yarn Turing-complete:
an unbounded stack, plus a conditional, plus recursion, is the same
ingredient list as any other Turing-complete language. (In practice this
implementation is bounded by the host machine's memory and Python's
recursion limit, the same caveat that applies to any real interpreter —
Yarn raises that limit on startup to give recursive patterns real headroom.)

```
Special Stitch: countdown
  if hook = 0
    sl st
  otherwise
    inc, snip, ch 1, dec, countdown
  end if.
End special stitch.

Row 1: ch 5
Row 2: countdown
FO
```

This prints `5 4 3 2 1`, each on its own line, and then actually stops —
the recursive call only happens in the `otherwise` branch, and each call
shrinks the count by one until it hits the `if hook = 0` base case.

A condition compares two operands with `=`, `!=`, `<`, `>`, `<=`, or `>=`.
Each operand is one of:

| Operand | Meaning |
|---|---|
| `hook` | the top of the loop stack — **peeked**, not popped |
| `count` | how many loops are currently on the hook |
| a literal number | e.g. `0`, `-3`, `42` |

`otherwise` is optional — an `if` with no `otherwise` just does nothing
when the condition is false.

Special stitches without a conditional will just recurse forever if they
call themselves — Yarn catches that (`RecursionError`) and reports it
rather than crashing.

## Special stitches (functions)

Real crochet patterns often define a custom stitch once, in a glossary at
the top ("Special Stitch: bobble — yo, insert hook..."), then just refer to
it by name in the rows below. Yarn does the same thing, and it's how you
write functions:

```
Special Stitch: step (adds one loop, prints the running count)
  inc, snip, sc
End special stitch.

Row 1: ch 1
Row 2: *step* rep 10 times
FO
```

A special stitch has **no parameter list** — it just operates on whatever's
on the hook when it's called and leaves its result there, the same way `sc`
or `dc` do. That keeps it consistent with every other stitch in the
language: arguments and return values both flow through the shared stack.

Special stitches can call other special stitches, including themselves —
paired with `if`/`otherwise` above, that's genuine recursion with a real
stopping condition, not just a bounded loop.

**Known limitation:** stitch markers (`place marker` / `work into`) are
global, not local to a special stitch — there's no scoping yet. Two special
stitches that both use a marker called `"x"` will stomp on each other.
Scoped markers are a natural next step — see "Ideas for extending it" below.

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

**Functions** (`examples/functions_demo.yarn`) — defines a reusable `step`
special stitch and calls it from a loop instead of repeating its body:

```
Special Stitch: step (adds one loop, prints the running count)
  inc, snip, sc
End special stitch.

Row 1: ch 1
Row 2: *step* rep 10 times
FO
```

**Countdown** (`examples/countdown.yarn`) — a recursive special stitch with
a real base case, counting down from 5 to 1.

## Error messages

Yarn tries to stay in character:

- Popping from an empty stack raises **"Dropped stitch! Not enough loops on
  the hook"**.
- Working into an unknown marker raises an error naming the missing marker.
- An unrecognized stitch name raises **"Unrecognized stitch"**.

## Ideas for extending it

- **Scoped markers** — give each special stitch its own marker namespace
  instead of sharing one global dict, so two functions can both use a
  marker called `"x"` without colliding.
- `frog it` — pop the whole stack and start the row over (a "frog" undoes
  crochet: "rip it, rip it").
- `join in the round` — turn the stack into a circular buffer.
- `color change` — a second, separate stack for a "type" tag on each value.
- `blocking` — a final formatting pass over the output string.

Pull on any of these the way you'd pull out a new skein — the core stitch
dictionary above is deliberately small so it's easy to extend.
