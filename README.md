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

Picture                      | Text
-----------------------------|-----
[`A  3`](test-image/a03.png) | `A0A/aaa`
[`A  6`](test-image/a06.png) | `Aaa/B0A/bbB`
[`A 17`](test-image/a17.png) | `AB/2b/AB`
[`B  9`](test-image/b09.png) | `ABC/abc/ABC`
[`B 18`](test-image/b18.png) | `BAC/022/0c2/CAB`
[`B 25`](test-image/b25.png) | `ACB/2C2/acb/B2A`
