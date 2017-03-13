from . import utility

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
