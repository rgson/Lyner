import collections
import itertools

import PIL.Image

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
### _Rectangle
################################################################################

class _Rectangle:

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
### parse_image
################################################################################

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
                    rect = _Rectangle(x, y)
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
