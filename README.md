# LYNER

**Lyner** solves [LYNE](http://store.steampowered.com/app/266010/) puzzles.

Lyner currently cannot see nor move. It relies on textual input and produces textual output. A full-fledged bot is in the making.


## Input format

The board to be solved is represented in a textual template format, as follows:

- Letters define colored nodes. Each unique letter represents a separate color.
- Uppercase letters (A-Z) denote start and goal nodes. There should be exactly two of the same kind.
- Lowercase letters (a-z) denote regular colored nodes.
- Digits (1-9) denote uncolored nodes of a specific capacity.
- Zero (0) denotes a missing node.
- Forward slash (/) denotes a line break

### Examples

Picture                                          | Text
-------------------------------------------------|---------------------------
[`test-image/1.png`](test-image/1.png)           | `A0A/aaa`
[`test-image/tuea14.png`](test-image/tuea14.png) | `B22B/2a22/AbbA`
[`test-image/f25.png`](test-image/f25.png)       | `b2B0/B22A/a02C/C32c/aAcc`
