# Yarn 🧶

A stack-based esoteric programming language where the code looks like a
crochet pattern. Chains push values, stitches transform them, `*...* rep
N times` is your loop syntax, `Special Stitch: ... End special stitch.`
defines reusable functions, and `if hook = 0 ... otherwise ... end if.`
gives it real conditionals — recursion with a base case, which makes Yarn
Turing-complete.

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

See [`YARN_SPEC.md`](./YARN_SPEC.md) for the full stitch dictionary and
language spec, and [`examples/`](./examples) for sample patterns.

## Running it

### Without Nix

Run a pattern file:

```
python3 yarn_interpreter.py examples/hello_world.yarn
```

Or start an interactive session — type stitches a row at a time and watch
the hook after each one, the same way you'd work through a pattern by hand:

```
python3 yarn_interpreter.py
Yarn REPL — type stitches a row at a time.
':help' for the stitch dictionary, 'FO' or Ctrl-D to fasten off.

Row 1: ch 5
  (hook: [5])
Row 2: sc
  (hook: [6])
Row 3: snip
6
  (hook: [])
Row 4: FO
Fastened off. Bye!
```

`:stack`, `:markers`, and `:help` are REPL-only commands for peeking at
what's on the hook, what's marked, or the stitch dictionary.

### With Nix

Run a pattern directly, without installing anything:

```
nix run github:<your-username>/yarn-lang -- examples/hello_world.yarn
```

Or drop straight into the REPL:

```
nix run github:<your-username>/yarn-lang
```

Install the `yarn` command onto your profile:

```
nix profile install github:<your-username>/yarn-lang
yarn                          # REPL
yarn my_pattern.yarn          # run a file
```

Or build it locally from a clone:

```
git clone https://github.com/<your-username>/yarn-lang.git
cd yarn-lang
nix build
./result/bin/yarn examples/count_to_ten.yarn
```

## License

MIT — see [LICENSE](./LICENSE).
