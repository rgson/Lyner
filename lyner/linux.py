import os
import subprocess
import sys
import tempfile
import time

from .base import Source, Target, LynerException
from .utility import parse_image

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
            self.window = _XWindow.search('LYNE')
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
                    res = subprocess.run(['timeout', '1', 'import', '-screen', '-window', 'LYNE', imagefile],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    puzzle, self.row_coords, self.col_coords = parse_image(imagefile, return_coords=True)
                    if not puzzle:
                        print('Failed to find puzzle')
                        time.sleep(2)
                print('Puzzle:', puzzle)
                return puzzle
        except subprocess.CalledProcessError:
            raise LynerException('Failed to take screenshot')

    def put_solution(self, solution):
        print('Solution:', solution)
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
### _XWindow
################################################################################

class _XWindow:

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
            return _XWindow.getactivewindow().id == self.id
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
