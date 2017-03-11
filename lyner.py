#!/usr/bin/env python3

import argparse
import collections
import itertools
import PIL.Image
import subprocess
import sys
import tempfile
import time

################################################################################
# Base

## Solve puzzle

class Node():

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

class Edge():

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

class Board():

    def __init__(self, description):
        self.description = description
        # Create nodes.
        self.nodes_2d = [[Node(value, (i, j))
                         for j, value in enumerate(row)]
                         for i, row in enumerate(description.split('/'))]
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

    def solutions(self):
        for solution in self._next_type(collections.defaultdict(list)):
            yield [[node.position for node in path] for path in solution.values()]

    def _next_type(self, paths):
        remaining = self.remaining_goals()
        if len(remaining) == 0:
            if len(self.remaining_nodes()) == 0:
                yield paths # This is a valid solution.
        else:
            yield from self._next_node(paths, remaining[0].nodetype, remaining[0])

    def _next_node(self, paths, nodetype, node):
        node.visit()
        paths[nodetype].append(node)
        if len(self.remaining_goals(nodetype)) == 0:
            if len(self.remaining_nodes(nodetype)) == 0:
                yield from self._next_type(paths)
        else:
            for edge in node.remaining_edges():
                other = edge.a if edge.b is node else edge.b
                if other.is_compatible(nodetype) and other.capacity > 0:
                    edge.visit()
                    yield from self._next_node(paths, nodetype, other)
                    edge.unvisit()
        node.unvisit()
        paths[nodetype].pop()

def solve(description):
    return next(Board(description).solutions(), None)

## Parse image

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

def parse_image(imagefile, return_coords=False):
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
    description = '/'.join(''.join(row) for row in grid)
    return description if not return_coords else (description, row_coords, col_coords)

################################################################################
# Manual mode

def manual_mode(args):
    if args.image:
        puzzle = parse_image(args.image)
        if not puzzle:
            return print('Failed to parse image', file=sys.stderr)
    else:
        puzzle = args.puzzle
        if not puzzle:
            return print('Puzzle is empty', file=sys.stderr)
    solution = solve(puzzle)
    if not solution:
        return print('Failed to solve puzzle', file=sys.stderr)
    print('Puzzle:', puzzle)
    if args.dont_draw:
        print('Solution:', solution)
    else:
        print('Solution:')
        draw(solution)

def draw(solution):
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
                raise Exception('Invalid solution (self-loop)'.format(a0, a1))
        # Uppercase goal nodes.
        out[path[ 0][0] * 2][path[ 0][1] * 2] = 'O'
        out[path[-1][0] * 2][path[-1][1] * 2] = 'O'
        # Print drawing
        print('Path {0}'.format(n), '\n')
        print('\t', '\n\t'.join(''.join(x) for x in out), '\n', sep='')

################################################################################
# Automatic mode

def auto_mode(args):
    if not sys.platform.startswith('linux'):
        return print('Unsupported platform', file=sys.stderr)
    wnd = XWindow('LYNE')
    wnd.activate()
    puzzle, row_coords, col_coords = parse_screenshot(return_coords=True)
    if not puzzle:
        return print('Failed to find puzzle', file=sys.stderr)
    print('Puzzle:', puzzle)
    solution = solve(puzzle)
    if not solution:
        return print('Failed to solve puzzle', file=sys.stderr)
    print('Solution:', solution)
    for path in solution:
        row, col = path[0]
        x, y = col_coords[col], row_coords[row]
        wnd.mousemove(x, y)
        wnd.mousedown()
        for row, col in path[1:]:
            x, y = col_coords[col], row_coords[row]
            wnd.mousemove(x, y)
        wnd.mouseup()

class XWindow:

    def __init__(self, title, action_delay=0.1):
        self.title = title
        self.delay = action_delay
        self.id = str(self.search().stdout, 'utf-8').strip()

    def _action(self, cmd):
        res = subprocess.run(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        time.sleep(self.delay)
        return res

    def search(self):
        return self._action('xdotool search --name ^{0}$'.format(self.title))

    def activate(self):
        return self._action('xdotool windowactivate {0}'.format(self.id))

    def mousemove(self, x, y):
        return self._action('xdotool mousemove --window {0} {1} {2}'.format(self.id, x, y))

    def mousedown(self):
        return self._action('xdotool mousedown 1')

    def mouseup(self):
        return self._action('xdotool mouseup 1')

def parse_screenshot(return_coords=False):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Capture window to temporary image file.
        imagefile = tmpdir + '/screenshot.png'
        res = subprocess.run(['timeout', '1', 'import', '-screen', '-window', 'LYNE', imagefile],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0:
            return parse_image(imagefile, return_coords=return_coords)

################################################################################
# Arguments

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
auto.set_defaults(func=auto_mode)

args = parser.parse_args()
args.func(args)
