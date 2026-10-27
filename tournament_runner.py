import subprocess32 as subprocess
import os
import time

import __builtin__
__builtin__.running_locally = True

from mysite.models import *
from mysite import db_util

matches = Match.query.all()
matches = [(match.Game_id, match.board_size, match.max_time_limit_ms,
            match.Player_one_id, match.Player_two_id) for match in matches]
new_matches = []
for game_id, board_size, time_limit, player_one, player_two in matches:
    new_matches.append(db_util.add_match(game_id, board_size, time_limit,
                                         player_two, player_one))

print (new_matches)
for match_id in new_matches:
    print ("Running match with id: %s" % match_id)
    subprocess.call('source venv/bin/activate', shell=True)
    subprocess.call('python game_runner.py --local 1 {match_id}'.format(match_id=match_id).split())
    print ("Finished running match with id: %s" % match_id)
    time.sleep(20)
