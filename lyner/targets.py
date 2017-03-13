from .base import Target, LynerException

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
