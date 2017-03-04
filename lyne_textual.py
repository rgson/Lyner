from lyne_solver import solve_lyne_board

def print_path(template, path):
	columns = template.index('/')
	rows = len(template.split('/'))
	nodes = columns * rows
	path = set(path)

	prep_board = []
	for row in range(rows):
		prep_row = ['o', ' '] * columns
		prep_row.pop()    # Remove trailing space
		for col in range(columns):
			node1 = row * columns + col
			node2 = row * columns + col + 1
			if (node1, node2) in path or (node2, node1) in path:
				prep_row[1 + 2 * col] = '-'
		prep_board.append(prep_row)
		if row != rows - 1:
			prep_row = [' '] * (2 * columns - 1)
			for pos in range(len(prep_row)):
				if pos % 2 == 0:    # Straight edges
					node1 = row * columns + (pos // 2)
					node2 = (row + 1) * columns + (pos // 2)
					if (node1, node2) in path or (node2, node1) in path:
						prep_row[pos] = '|'
				else:    # Diagonals
					node1 = row * columns + (pos // 2)              # Top left
					node2 = (row + 1) * columns + (pos // 2) + 1    # Bottom right
					if (node1, node2) in path or (node2, node1) in path:
						prep_row[pos] = '\\'
					else:
						node3 = row * columns + (pos // 2) + 1        # Top right
						node4 = (row + 1) * columns + (pos // 2)      # Bottom left
						if (node3, node4) in path or (node4, node3) in path:
							prep_row[pos] = '/'
			prep_board.append(prep_row)
	output = '\n'.join([''.join(row) for row in prep_board])
	print(output)


## Testing
#input_string = 'A0A/aaa'
#input_string = 'B22B/2a22/AbbA'
#input_string = 'b2B0/B22A/a02C/C32c/aAcc'
while (True):

	input_string = input('Input board template (leave blank to exit): ')
	print()

	if not input_string:
		break

	try:
		solution = solve_lyne_board(input_string, flatten = False)
		if solution == None:
			print('No solution found!')
		else:
			for i, path in enumerate(solution):
				print('### Path', (i + 1), '###')
				print_path(input_string, path)

	except Exception as e:
		print(e)

	print()
