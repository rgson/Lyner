#!/usr/bin/env python3

import argparse
import sys
import time

from lyner import *
from lyner.linux import LiveSourceTarget

################################################################################
### Manual mode
################################################################################

def manual_mode(args):
    solver = GuidedDepthFirstSolver()
    source = TextSource(args.puzzle) if args.puzzle else ImageSource(args.image)
    target = TextTarget() if args.dont_draw else DrawTarget()
    lyner  = Lyner(source, solver, target)
    lyner.run()

################################################################################
### Automatic mode
################################################################################

def auto_mode(args):
    source = LiveSourceTarget()
    solver = GuidedDepthFirstSolver()
    target = source if not args.dont_act else TextTarget()
    lyner = Lyner(source, solver, target)
    try:
        while True:
            try:
                lyner.run()
            except LynerException as e:
                print(str(e), file=sys.stderr)
            time.sleep(2)
    except KeyboardInterrupt:
        pass

################################################################################
### Arguments
################################################################################

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
auto.add_argument('--dont-act', help='print the solution instead of acting it out', action='store_true')
auto.set_defaults(func=auto_mode)

args = parser.parse_args()

try:
    args.func(args)
except Exception as e:
    print(str(e), file=sys.stderr)
