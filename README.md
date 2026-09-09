# Yarn 🧶

A stack-based esoteric programming language where the code looks like a
crochet pattern. Chains push values, stitches transform them, and `*...* rep
N times` is your loop syntax.

```
Row 1: ch 1
Row 2: *inc, snip, sc* rep 10 times
FO
```

See [`YARN_SPEC.md`](./YARN_SPEC.md) for the full stitch dictionary and
language spec, and [`examples/`](./examples) for sample patterns.

## Running it

### Without Nix

```
python3 yarn_interpreter.py examples/hello_world.yarn
```

### With Nix

Run a pattern directly, without installing anything:

```
nix run github:<your-username>/yarn-lang -- examples/hello_world.yarn
```

Install the `yarn` command onto your profile:

```
nix profile install github:<your-username>/yarn-lang
yarn my_pattern.yarn
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
