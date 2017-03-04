#!/usr/bin/env python3

import collections

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

# Test boards:
description = 'A0A/aaa'
# description = 'B22B/2a22/AbbA'
#description = 'b2B0/B22A/a02C/C32c/aAcc'
print(solve(description))
