# luca_of_math_lean

A zero-cost artificial life kernel where Lean 4 compiler laws and non-Markovian Pólya urn dynamics drive open-ended mathematical evolution.

## The Long Run Hypothesis

The most famous attempt at this kind of experiment was **Genetic Programming (GP)** proposed by John Koza in the 1990s. He had computers randomly generate LISP code, using the compiler as natural selection, trying to let machines "grow" programs that could solve specific problems.

It didn't work.

But I believe the problem is simpler than people think: **they were just too impatient.** They didn't let the program run long enough.

Human beings have never successfully synthesized life from a primordial soup either — something always seems to be missing. That "key first factor." But what if nothing is missing? What if the only missing ingredient is **time** — not hours, not days, not years, but decades, centuries, even hundreds of millions of years?

This project is designed to run for that long.

### Design for Deep Time

`luca_of_math_lean` is built from the ground up with **immortal processes** in mind:

- **State persistence**: The entire Pólya urn state (token weights, generation counter, alive/dead tallies) is periodically saved to disk as plain JSON. A process killed at any moment can be resumed exactly where it left off via `python main.py --resume`.
- **Incremental output**: Every successfully compiled Lean definition is appended to `evolved_library.lean` — a living fossil record that grows forever.
- **Zero external dependencies during evolution**: Once started, the loop requires no network, no API keys, no cloud services. Just a CPU, a Lean 4 binary, and electricity.
- **Catastrophe resilience**: The built-in catastrophe system (mass extinctions, asteroid impacts, ice ages) ensures that even if the urn stagnates for millennia, a random event will shake things up and open new evolutionary pathways.

The ambition is not to produce a useful program in 100 generations. The ambition is to let it run for 100 million generations and see what mathematics looks like when it evolves on its own terms, under the absolute physical law of the Lean 4 type checker, with no human intervention except patience.

> "We have not failed. We have simply not waited long enough."
