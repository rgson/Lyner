import collections

from .base import Solver, LynerException
from .utility import Board

################################################################################
### GuidedDepthFirstSolver
################################################################################

class GuidedDepthFirstSolver(Solver):

    def solve_puzzle(self, puzzle):
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
