from enum import Enum
from lyne_solver import solve_lyne_board
from PIL import Image
from PIL import ImageGrab
import win32gui

#input_string = 'A0A/aaa'
#input_string = 'B22B/2a22/AbbA'
#input_string = 'b2B0/B22A/a02C/C32c/aAcc'
#print(solve_lyne_board(input_string))

colors = {
	(198,   0,   0): NodeType.red,
	( 74, 178, 255): NodeType.blue,
	(206, 137,  48): NodeType.orange,
	(209, 207, 184): NodeType.neutral,
	(252,  31,  32): NodeType.master_red,
	(  0, 134, 255): NodeType.master_blue,
	(255, 165,  21): NodeType.master_orange,
	#( 59,  59,  57): ColorType.empty,
	#(239, 235, 223): ColorType.master_center,
}

# ------------------------------------------------------------------------------

class NodeType(Enum):
	red = 1
	blue = 2
	orange = 3
	neutral = 4
	master_red = 5
	master_blue = 6
	master_orange = 7
	empty = 8

class Node:
	def __init__(self, nodetype, x, y, width, height):
		self.nodetype = nodetype
		self.x = x
		self.y = y
		self.width = width
		self.height = height

	def center():
		return (self.x1 + self.width / 2, self.y + self.height / 2)

	def contains(x, y):
		return bool(self.x <= x < (self.x + width) and self.y <= y < (self.y + height))

# ------------------------------------------------------------------------------

def find_hwnd(title):
	hwnds = []
	win32gui.EnumWindows(lambda hwnd, results: hwnds.append(hwnd), None)
	for hwnd in hwnds:
		if win32gui.GetWindowText(hwnd) == title:
			return hwnd
	return None

def screenshot_window(hwnd):
	win32gui.SetForegroundWindow(hwnd)
	rect = win32gui.GetWindowRect(hwnd)
	screenshot = ImageGrab.grab(rect)
	width, height = screenshot.size
	#screenshot.show()
	return screenshot

def crop_waste_of_space(img):
	width, height = img.size
	pixels = img.load()
	start_x, start_y, end_x, end_y = width, height, 0, 0
	for y in range(height):
		for x in range(width):
			if pixels[x, y] in colors:
				start_x = min(start_x, x)
				start_y = min(start_y, y)
				end_x = max(end_x, x)
				end_y = max(end_y, y)
	img = img.crop((start_x, start_y, end_x, end_y))
	#img.show()
	return (img, (start_x, start_y))

def scan_for_nodes(img):


	# Do a messy first scan, catching every change in color
	colortypes = []
	for y in range(height):
		colortypes_line = []
		last_color = None
		for x in range(width):
			color = pixels[x, y]
			if color != last_color:
				last_color = color
				if color in colors:
					colortypes_line.append(colors[color])
		colortypes.append(colortypes_line)







lyne_hwnd = find_hwnd('LYNE')
img = screenshot_window(lyne_hwnd)
img, offset = crop_waste_of_space(img)

#print(pixels[50, 50])

