#!/usr/bin/env python3

import argparse
import collections
import itertools
import os
import PIL.Image
import subprocess
import sys
import tempfile
import time

################################################################################
### Lyner
################################################################################

class Lyner:

    def __init__(self, source, solver, target):
        self.source = source
        self.solver = solver
        self.target = target

    def run(self):
        puzzle = self.source.get_puzzle()
        if not puzzle:
            raise LynerException('Failed to get puzzle')
        solution = self.solver.solve_puzzle(puzzle)
        if not solution:
            raise LynerException('Failed to solve puzzle')
        self.target.put_solution(solution)

################################################################################
### Source
################################################################################

class Source:

    def get_puzzle(self):
        raise NotImplementedError('Must use a Source subclass')

################################################################################
### Solver
################################################################################

class Solver:

    def solve_puzzle(self, puzzle):
        raise NotImplementedError('Must use a Solver subclass')

################################################################################
### Target
################################################################################

class Target:

    def put_solution(self, solution):
        raise NotImplementedError('Must use a Target subclass')

################################################################################
### LynerException
################################################################################

class LynerException(Exception):
    pass

################################################################################
### TextSource
################################################################################

class TextSource(Source):

    def __init__(self, puzzle=None):
        self.puzzle = puzzle

    def get_puzzle(self):
        return self.puzzle

################################################################################
### ImageSource
################################################################################

class ImageSource(Source):

    def __init__(self, image=None):
        self.image = image

    def get_puzzle(self):
        if self.image is None:
            raise LynerException('No image has been provided')
        return _parse_image(self.image)

def _parse_image(imagefile, return_coords=False):
    colors = {(168, 219, 168): 'a', # Triangle
              ( 59, 134, 134): 'b', # Diamond
              (194, 120,  92): 'c', # Square
              (206, 240, 183): 'A', # Triangle (goal)
              ( 11,  72, 107): 'B', # Diamond (goal)
              (190,  79,  35): 'C', # Square (goal)
              (167, 219, 216): '0'} # Neutral
    bgcolor = (121, 189, 154)       # Background
    # Load image.
    image = PIL.Image.open(imagefile)
    image = image.convert(mode='RGB')
    width, height = image.size
    pixels = image.load()
    # Find sections containing nodes.
    sections = collections.defaultdict(list)
    current = None # The currently relevant (symbol, rectangle). Optimization.
    for x, y in itertools.product(range(width), range(height)):
        if pixels[x, y] in colors:
            symbol = colors[pixels[x, y]]
            if current is None or current[0] != symbol:
                try:
                    rect = next(r for r in sections[symbol] if r.near(x, y))
                except StopIteration:
                    rect = Rectangle(x, y)
                    sections[symbol].append(rect)
                current = (symbol, rect)
            current[1].expand(x, y)
        else:
            current = None
    # Remove false positives within goal nodes.
    for lower in ('a', 'b', 'c'):
        for goal in sections[lower.upper()]:
            for rect in [r for r in sections[lower] if r.center() in goal]:
                sections[lower].remove(rect)
    # Count the holes in the neutral nodes.
    for r in sections['0']:
        cx, cy = r.center()
        num = sum((any(pixels[cx, y] == bgcolor for y in range(cy, r.top, -1)),  # Up
                   any(pixels[cx, y] == bgcolor for y in range(cy, r.bottom)),   # Down
                   any(pixels[x, cy] == bgcolor for x in range(cx, r.left, -1)), # Left
                   any(pixels[x, cy] == bgcolor for x in range(cx, r.right))))   # Right
        sections[str(num)].append(r)
    del sections['0']
    # Find grid structure.
    nodes = [(symbol, rect) for symbol, sect in sections.items() for rect in sect]
    grid_rows, grid_cols = {}, {}
    row_known, col_known = set(), set()
    for node in nodes:
        if node not in row_known:
            cx, cy = node[1].center()
            grid_rows[cy] = [n for n in nodes if n[1].top <= cy <= n[1].bottom]
            row_known |= set(grid_rows[cy])
        if node not in col_known:
            cx, cy = node[1].center()
            grid_cols[cx] = [n for n in nodes if n[1].left <= cx <= n[1].right]
            col_known |= set(grid_cols[cx])
    row_coords = sorted(grid_rows)
    col_coords = sorted(grid_cols)
    grid = [[''] * len(grid_cols) for row in grid_rows]
    for i, row in enumerate(grid):
        for j in range(len(row)):
            r, c = row_coords[i], col_coords[j]
            row[j] = next((n[0] for n in grid_rows[r] if n in grid_cols[c]), '0')
    # Convert to textual description.
    puzzle = '/'.join(''.join(row) for row in grid)
    return puzzle if not return_coords else (puzzle, row_coords, col_coords)

################################################################################
### DefaultSolver
################################################################################

class DefaultSolver(Solver):

    def solve_puzzle(self, puzzle, extras=None):
        try:
            return next(_solutions(Board(puzzle)))
        except StopIteration:
            raise LynerException('Failed to solve puzzle')

def _solutions(board):
    for solution in _next_type(board, collections.defaultdict(list)):
        yield [[node.position for node in path] for path in solution.values()]

def _next_type(board, paths):
    remaining = board.remaining_goals()
    if len(remaining) == 0:
        if len(board.remaining_nodes()) == 0:
            yield paths # This is a valid solution.
    else:
        yield from _next_node(board, paths, remaining[0].nodetype, remaining[0])

def _next_node(board, paths, nodetype, node):
    node.visit()
    paths[nodetype].append(node)
    if len(board.remaining_goals(nodetype)) == 0:
        if len(board.remaining_nodes(nodetype)) == 0:
            yield from _next_type(board, paths)
    else:
        for edge, other in _find_candidates(node, nodetype):
            edge.visit()
            yield from _next_node(board, paths, nodetype, other)
            edge.unvisit()
    node.unvisit()
    paths[nodetype].pop()

def _find_candidates(node, nodetype):
    candidates = [(e, e.a if e.b is node else e.b) for e in node.remaining_edges()]
    candidates = [(e, n) for e, n in candidates if n.is_compatible(nodetype) and n.capacity > 0]
    candidates = sorted(candidates, key=_candidate_priority)
    return candidates

def _candidate_priority(candidate):
    edge, node = candidate
    return -(node.capacity + int(node.symbol.isdigit())) # Prefer neutral nodes.

################################################################################
### Board
################################################################################

class Board:

    def __init__(self, puzzle):
        self.puzzle = puzzle
        # Create nodes.
        self.nodes_2d = [[Node(value, (i, j))
                         for j, value in enumerate(row)]
                         for i, row in enumerate(puzzle.split('/'))]
        self.nodes = [node for row in self.nodes_2d for node in row]
        # Create edges.
        last_se = None
        for node in self.nodes:
            n0, n1 = node.position
            neighbors = (self.node(n0 + i, n1 + j)
                         for i, j in [(0, 1), (1, 0), (1, 1), (1, -1)])
            e, s, se, sw = (Edge(node, neighbor) if neighbor is not None else None
                            for neighbor in neighbors)
            # Add edges to nodes.
            for edge in (e, s, se, sw):
                if edge is not None:
                    edge.a.edges.append(edge)
                    edge.b.edges.append(edge)
            # Connect crossing edges.
            if sw is not None and last_se is not None:
                sw.crosses = last_se
                last_se.crosses = sw
            last_se = se

    def node(self, row, col):
        if 0 <= row < len(self.nodes_2d) and 0 <= col < len(self.nodes_2d[row]):
            return self.nodes_2d[row][col]
        return None

    def remaining_nodes(self, nodetype=None):
        return [n for n in self.nodes
                if n.capacity > 0 and (nodetype is None or n.nodetype == nodetype)]

    def remaining_goals(self, nodetype=None):
        return [n for n in self.remaining_nodes(nodetype) if n.is_goal()]

################################################################################
### Node
################################################################################

class Node:

    def __init__(self, symbol, position):
        self.symbol = symbol
        self.nodetype = symbol.upper()
        self.position = position
        self.capacity = int(symbol) if symbol.isdigit() else 1
        self.edges = []

    def visit(self):
        self.capacity -= 1

    def unvisit(self):
        self.capacity += 1

    def is_compatible(self, symbol):
        return self.symbol.isdigit() or symbol.upper() == self.nodetype

    def is_goal(self):
        return self.symbol.isupper()

    def remaining_edges(self):
        return [edge for edge in self.edges if not edge.occupied]

################################################################################
### Edge
################################################################################

class Edge:

    def __init__(self, node_a, node_b):
        self.a = node_a
        self.b = node_b
        self.occupied = False
        self.crosses = None

    def visit(self):
        self.occupied = True
        if self.crosses is not None:
            self.crosses.occupied = True

    def unvisit(self):
        self.occupied = False
        if self.crosses is not None:
            self.crosses.occupied = False

################################################################################
### Rectangle
################################################################################

class Rectangle:

    def __init__(self, x, y):
        self.left = self.right  = x
        self.top  = self.bottom = y

    def __contains__(self, point):
        return (self.left <= point[0] <= self.right and
                self.top  <= point[1] <= self.bottom)

    def near(self, x, y, threshold=10):
        return (self.left - threshold <= x <= self.right  + threshold and
                self.top  - threshold <= y <= self.bottom + threshold )

    def center(self):
        return (round((self.left + self.right) / 2),
                round((self.top + self.bottom) / 2))

    def expand(self, x, y):
        if (x, y) not in self:
            self.left   = min(self.left,   x)
            self.right  = max(self.right,  x)
            self.top    = min(self.top,    y)
            self.bottom = max(self.bottom, y)

################################################################################
### TextTarget
################################################################################

class TextTarget(Target):

    def put_solution(self, solution):
        print('Solution:', solution)

################################################################################
### DrawTarget
################################################################################

class DrawTarget(Target):

    def put_solution(self, solution):
        rows = 1 + max(position[0] for path in solution for position in path)
        cols = 1 + max(position[1] for path in solution for position in path)
        for n, path in enumerate(solution):
            out = [[' '] * (cols * 2 - 1) for i in range(rows * 2 - 1)]
            first, last = path[0], path[-1]
            for i in range(len(path) - 1):
                (a0, a1), (b0, b1) = path[i], path[i + 1] # The edge A->B was used.
                if b0 < a0 or b0 == a0 and b1 < a1: # Make sure A comes before B.
                    a0, a1, b0, b1 = b0, b1, a0, a1
                # Draw nodes.
                out[a0 * 2][a1 * 2] = 'o'
                out[b0 * 2][b1 * 2] = 'o'
                # Draw edge.
                south, west, east = a0 < b0, b1 < a1, a1 < b1
                if south and west:
                    out[a0 * 2 + 1][a1 * 2 - 1] = '/'
                elif south and east:
                    out[a0 * 2 + 1][a1 * 2 + 1] = '\\'
                elif south:
                    out[a0 * 2 + 1][a1 * 2 + 0] = '|'
                elif east:
                    out[a0 * 2 + 0][a1 * 2 + 1] = '-'
                else:
                    raise LynerException('Invalid solution (self-loop)'.format(a0, a1))
            # Uppercase goal nodes.
            out[path[ 0][0] * 2][path[ 0][1] * 2] = 'O'
            out[path[-1][0] * 2][path[-1][1] * 2] = 'O'
            # Print drawing
            print('Path {0}'.format(n), '\n')
            print('\t', '\n\t'.join(''.join(x) for x in out), '\n', sep='')

################################################################################
### LiveSourceTarget
################################################################################

class LiveSourceTarget(Source, Target):

    def __init__(self):
        if not sys.platform.startswith('linux'):
            raise Exception('Unsupported platform')
        for p in ('timeout', 'import', 'xdotool'):
            if not _program_exists(p):
                raise Exception('LiveSourceTarget requires the program "{0}"'.format(p))
        try:
            self.window = XWindow.search('LYNE')
        except subprocess.CalledProcessError:
            raise LynerException('Failed to find LYNE window')
        self.row_coords = None
        self.col_coords = None

    def get_puzzle(self):
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                imagefile = tmpdir + '/screenshot.png'
                puzzle = None
                while not puzzle:
                    _wait_until_active(self.window)
                    print('Looking for LYNE puzzle...')
                    res = subprocess.run(['timeout', '1', 'import', '-screen', '-window', 'LYNE', imagefile],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    puzzle, self.row_coords, self.col_coords = _parse_image(imagefile, return_coords=True)
                    if not puzzle:
                        print('Failed to find puzzle')
                        time.sleep(2)
                print('Puzzle:', puzzle)
                return puzzle
        except subprocess.CalledProcessError:
            raise LynerException('Failed to take screenshot')

    def put_solution(self, solution):
        _wait_until_active(self.window)
        for path in solution:
            row, col = path[0]
            x, y = self.col_coords[col], self.row_coords[row]
            self.window.mousemove(x, y)
            self.window.mousedown()
            for row, col in path[1:]:
                x, y = self.col_coords[col], self.row_coords[row]
                self.window.mousemove(x, y)
            self.window.mouseup()

def _wait_until_active(wnd):
    if not wnd.is_active():
        print('Paused. Please activate the LYNE window to resume.')
        while not wnd.is_active():
            time.sleep(1)

def _program_exists(name):
    try:
        subprocess.run([name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except OSError as e:
        return e.errno != os.errno.ENOENT

################################################################################
### XWindow
################################################################################

class XWindow:

    def __init__(self, id):
        self.id = id

    def activate(self):
        return _action('xdotool windowactivate {0}'.format(self.id))

    def mousemove(self, x, y):
        return _action('xdotool mousemove --window {0} {1} {2}'.format(self.id, x, y))

    def mousedown(self):
        return _action('xdotool mousedown 1')

    def mouseup(self):
        return _action('xdotool mouseup 1')

    def is_active(self):
        try:
            return XWindow.getactivewindow().id == self.id
        except:
            return False

    @classmethod
    def search(clazz, name):
        res = _action('xdotool search --name ^{0}$'.format(name), delay=0)
        id = str(res.stdout, 'utf-8').strip()
        return clazz(id)

    @classmethod
    def getactivewindow(clazz):
        res = _action('xdotool getactivewindow', delay=0)
        id = str(res.stdout, 'utf-8').strip()
        return clazz(id)

def _action(cmd, delay=0.025):
    res = subprocess.run(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    time.sleep(delay)
    return res

################################################################################
### Manual mode
################################################################################

def manual_mode(args):
    solver = DefaultSolver()
    source = TextSource(args.puzzle) if args.puzzle else ImageSource(args.image)
    target = TextTarget() if args.dont_draw else DrawTarget()
    lyner  = Lyner(source, solver, target)
    lyner.run()

################################################################################
### Automatic mode
################################################################################

def auto_mode(args):
    source = LiveSourceTarget()
    solver = DefaultSolver()
    target = source if not args.dont_act else TextTarget()
    lyner = Lyner(source, solver, target)
    try:
        while True:
            try:
                lyner.run()
            except LynerException as e:
                print(str(e), file=sys.stderr)
    except KeyboardInterrupt:
        pass

################################################################################
### Arguments
################################################################################

parser = argparse.ArgumentParser()
mode = parser.add_subparsers(title='mode', dest='mode')
mode.required = True

manual = mode.add_parser('manual', help='use manual input and produce textual output', description='use manual input and produce textual output')
manual.add_argument('--dont-draw', help='present the solution in raw textual form', action='store_true')
inputs = manual.add_argument_group('input method').add_mutually_exclusive_group(required=True)
inputs.add_argument('puzzle', help='read the puzzle from a textual representation', nargs='?')
inputs.add_argument('-i', '--image', help='read the puzzle from a saved image file')
manual.set_defaults(func=manual_mode)

auto = mode.add_parser('auto', help='solve live LYNE puzzles automatically', description='solve live LYNE puzzles automatically')
auto.add_argument('--dont-act', help='print the solution instead of acting it out', action='store_true')
auto.set_defaults(func=auto_mode)

args = parser.parse_args()

try:
    args.func(args)
except Exception as e:
    print(str(e), file=sys.stderr)
