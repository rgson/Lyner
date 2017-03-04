def solve_lyne_board(template, flatten = True):
	"""
	Solves a LYNE board.

	The board to be solved is represented in a textual template format, as follows:
	  Letters define colored nodes. Each letter is interpreted as one color.
	  Uppercase letters (A-Z) define head nodes, i.e. start or goal nodes.
	  Lowercase letters (a-z) define regular colored nodes.
	  Non-colored nodes are defined by single digits (0-9) corresponding to the
	  node's capacity. A value of 0 should be used to denote an empty/missing node.
	  The break between rows are represented by a forward slash (/). There should
	  be no trailing slash at the end.
	For example: b2B0/B22A/a02C/C32c/aAcc

	The returned result is a list containing the solution for each color on the
	board in the form of separate lists. The individual solution lists contain the
	nodes involved in the solution in order. Connecting the nodes in the given
	order for each color will produce the solution for the board.
	"""

	import string

	class LyneBoard:

		def __init__(self, description = None):
			self.columns = 0             # Number of columns.
			self.rows = 0                # Number of rows.
			self.node_capacities = []    # List of node capacities.
			self.mandatory_nodes = set() # Set of mandatory nodes.
			self.head_nodes = set()      # Set of head nodes (start/goal).
			self.edges = []              # Matrix (2D list) of edges as boolean values.

			if (description != None):
				self.columns = description.index('/')
				self.rows = len(description.split('/'))

				self.node_capacities = [0] * (self.columns * self.rows)
				for index, char in enumerate([x for x in description if x != '/']):
					if char in string.digits:
						self.node_capacities[index] = int(char)
					elif char in string.ascii_letters:
						self.node_capacities[index] = 1
						self.mandatory_nodes.add(index)
						if char in string.ascii_uppercase:
							self.head_nodes.add(index)

				# Half 2D matrix, without duplicates or edges to self.
				self.edges = [[False] * node for node in range(len(self.node_capacities))]
				for i, node in enumerate(self.node_capacities):
					if (node != 0):
						for j in self._find_neighbors(i):
							self.edges[max(i, j)][min(i, j)] = True

		def copy(self):
			copy = LyneBoard()
			copy.columns = self.columns
			copy.rows = self.rows
			copy.node_capacities = self.node_capacities.copy()
			copy.mandatory_nodes = self.mandatory_nodes.copy()
			copy.head_nodes = self.head_nodes.copy()
			copy.edges = [[edge for edge in row] for row in self.edges]
			return copy

		def is_full(self):
			for node_capacity in self.node_capacities:
				if node_capacity > 0:
					return False
			return True

		def apply_path(self, path):
			for move in path:
				self._walk(*move)

		def find_paths(self):
			start, goal = list(self.head_nodes)
			self.node_capacities[start] -= 1
			return self._find_paths_recursively(start, goal, [])

		def _find_neighbors(self, index):
			neighbors = []
			row = index // self.columns
			col = index % self.columns
			# Adjacent
			if col != 0:
				neighbors.append(index - 1) # Left
			if col != self.columns - 1:
				neighbors.append(index + 1) # Right
			# Above
			if row != 0:
				neighbors.append(index - self.columns) # Top
				if col != 0:
					neighbors.append(index - self.columns - 1) # Top left
				if col != self.columns - 1:
					neighbors.append(index - self.columns + 1) # Top right
			# Below
			if row != self.rows - 1:
				neighbors.append(index + self.columns) # Bottom
				if col != 0:
					neighbors.append(index + self.columns - 1) # Bottom left
				if col != self.columns - 1:
					neighbors.append(index + self.columns + 1) # Bottom right
			# Only include neighbors with a capacity
			return [n for n in neighbors if self.node_capacities[n] > 0]

		def _walk(self, start, destination):
			self.node_capacities[destination] = max(0, self.node_capacities[destination] - 1)
			i, j = sorted([start, destination])
			self.edges[j][i] = False
			# Check blocked diagonals
			if j == i + self.columns + 1:       # Right diagonal \
				self.edges[j - 1][i + 1] = False
			elif j == i + self.columns - 1:  # Left diagonal /
				self.edges[j + 1][i - 1] = False

		def _valid_edge(self, i, j):
			return self.edges[max(i, j)][min(i, j)]

		def _covered_all_mandatory_nodes(self):
			nodes_left = set([node for node, capacity in enumerate(self.node_capacities) if capacity > 0])
			return nodes_left.isdisjoint(self.mandatory_nodes)

		def _find_paths_recursively(self, start, goal, path):
			# TODO prune identical paths
			if start != goal:
				possible_moves = [(start, j) for j in self._find_neighbors(start) if self._valid_edge(start, j)]
				if possible_moves:
					for move in possible_moves:
						resulting_board = self.copy()
						resulting_board._walk(*move)
						yield from resulting_board._find_paths_recursively(move[1], goal, path + [move])
			elif self._covered_all_mandatory_nodes():
					yield path

	### End of class LyneBoard

	def split_template(template):
		templates = []
		letters = set([c for c in template if c in string.ascii_uppercase])
		for letter in letters:
			template2 = ''.join([c if c.upper() == letter or c in string.digits or c == '/' else '0' for c in template])
			templates.append(template2)
		return templates

	def solve(boards):
		current_board = boards.pop()
		for path in current_board.find_paths():
			if boards:
				remaining_boards = [b.copy() for b in boards]
				for board in remaining_boards:
					board.apply_path(path)
				solution = solve(remaining_boards)
				if solution != None:
					solution.append(path)
					return solution
			else:
				result_state = current_board.copy()
				result_state.apply_path(path)
				if (result_state.is_full()):
					return [path]
		return None

	def flatten_solution(solution):
		flattened = []
		for path in solution:
			steps = []
			for index, move in enumerate(path):
				if index == 0:
					steps.append(move[0])
				steps.append(move[1])
			flattened.append(steps)
		return flattened

	### End of function definitions

	templates = split_template(template)
	split_boards = [LyneBoard(template) for template in templates]
	if flatten:
		return flatten_solution(solve(split_boards))
	return solve(split_boards)

### End of function: solve_lyne_board
