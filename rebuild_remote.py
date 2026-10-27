import __builtin__
import sys

try:
    __builtin__.FORCE_REBUILD = True if sys.argv[1] == '-f' else False
except IndexError:
    __builtin__.FORCE_REBUILD = False

from mysite import rebuild