# LYNER

**Lyner** solves [LYNE](http://store.steampowered.com/app/266010/) puzzles.

Primarily, Lyner features a small program for solving puzzles. It can solve puzzles from textual input or interact directly with the game.

Additionally, Lyner sports a modular and extensible design to support experimentation with other solver algorithms. It should also be fairly easy to implement new input sources and output targets for various purposes and platforms.

## How is it used?

Lyner features two modes: a manual mode with manual puzzle input, and an automatic mode which interacts directly with the LYNE game.

The available options can be seen by running `lyner.py -h`. Mode-specific instructions are found through `lyner.py manual -h` and `lyner.py auto -h`.

### Manual mode

Manual mode solves puzzles from manually specified input, given either as text or as an image.

A LYNE puzzle is described textually as follows:

- Letters define colored nodes. Each unique letter represents a separate color.
- Uppercase letters (A-Z) denote start and goal nodes. There should be exactly two of the same kind.
- Lowercase letters (a-z) denote regular colored nodes.
- Digits (1-9) denote uncolored nodes of a specific capacity.
- Zero (0) denotes a missing node.
- Forward slash (/) denotes a line break

Some examples:

Level                      | Text
---------------------------|-----
[A  3](test-images/a03.png) | `A0A/aaa`
[A  6](test-images/a06.png) | `Aaa/B0A/bbB`
[A 17](test-images/a17.png) | `AB/2b/AB`
[B  9](test-images/b09.png) | `ABC/abc/ABC`
[B 18](test-images/b18.png) | `BAC/022/0c2/CAB`
[B 25](test-images/b25.png) | `ACB/2C2/acb/B2A`

In LYNE, puzzles include at most three colors (A, B, C) and uncolored nodes have a capacity of at most four (1, 2, 3, 4). Values outside these ranges should work, but have not been actively tested.

Input can also be passed in the form of a picture, in which case it should be a screenshot of LYNE using the default color scheme. Refer to the `test-images` directory (or the links in the table above) for examples.

### Automatic mode

Automatic mode solves puzzles directly on a running instance of the LYNE game. It relies on screenshots and automated mouse actions.

Automatic mode currently only works on Linux. It requires the programs [timeout](https://www.gnu.org/software/coreutils/manual/html_node/timeout-invocation.html#timeout-invocation), [import](https://www.imagemagick.org/script/import.php) and [xdotool](http://www.semicomplete.com/projects/xdotool) to function. All of the programs are available in the Ubuntu software repositories. For non-Ubuntu-based Linux distributions, refer to your distrobution's package manager or the programs' websites directly.

*A Windows version of automatic mode would be great. Pull requrests are warmly welcomed.*

## How does it work?

The default solver (`GuidedDepthFirstSolver`) models the puzzle as a graph and finds solutions using recursive depth first searches with backtracking, guided by a simple heuristic.

The graph consists of nodes and edges (as usual). Each node has a type, a capacity, and edges to adjacent nodes. Edges also have a capacity and diagonal edges are linked to their crossing edge.

A start node for one color is arbitrarily selected. A depth-first search is performed to find a path to the corresponding goal node which passes through all nodes of that color. The procedure then repeats using another arbitrarily selected start node for another color. When there are no remaining colors, the solution is checked to make sure all uncolored nodes have also been filled. Otherwise, it backtracks and tries another solution.

The search is guided by a simple heuristic to prioritize uncolored nodes, particularly those with a high remaining capacity. This speeds up the search by reducing the risk of ending up with an incomplete solution after going through all of the colors.

## How can it be extended?

Lyner can be extended to use a different solver algorithm or to support new input sources and output targets.

Pull requests with new solvers or sources/targets to support automatic mode on other platforms are warmly welcomed.

### New solver algorithms

If you have an idea for another solver algorithm, please do implement it! The `GuidedDepthFirstSolver` is pretty good, but it struggles with a few puzzles with particularly vast search spaces. It would be great if you managed to out-perform it.

To implement a new solver, extend `lyner.Solver` and override `solve_puzzle(self, puzzle)`. The `puzzle` parameter is a textual description of the puzzle and `solve_puzzle` should return a list of lists, one for each color, containing the zero-based coordinates of the nodes in the order in which they are visited. For example, if `puzzle` is `A0A/aaa`, the returned value should be `[[(0, 0), (1, 0), (1, 1), (1, 2), (0, 2)]]`.

### New sources/targets

Lyner can also use other input sources/output targets to support new platforms or use cases.

To support a new input source or output target, extend `lyner.Source` or `lyner.Target` and override `get_puzzle(self)` or `put_solution(self, solution)`, respectively. The `get_puzzle` function should return a textual representation of a puzzle, while `put_solution` is passed a solution (in the format returned by the solver) to do with as you please.
