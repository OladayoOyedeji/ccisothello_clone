import builtins
import sys

try:
    builtins.FORCE_REBUILD = True if sys.argv[1] == '-f' else False
except IndexError:
    builtins.FORCE_REBUILD = False

from mysite import rebuild
