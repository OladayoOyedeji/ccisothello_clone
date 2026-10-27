import __builtin__
__builtin__.running_locally = True

from mysite.models import *
from mysite import db_util

# fall2022
user_ids    = [21, 22, 23, 24]
ai_ids      = [143, 136, 163, 150]

# fall 2022
#user_ids    = [13, 14, 15, 16, 17]
#ai_ids      = [97, 107, 104]

"""
user id         AI id
13              97      "noobdaAI"
14              107     "Nevada"
15
16              104     "RasMalAI"
17

FALL 2022
21 zach				143
22 grant			117, 118, 119, 121, 128, 136
23 dumpsterfire (landon) 	157, 163
24 micah			145,146,147,149,150

match data

6x6 board, 150000 millisec.
8x8 board, 180000 millisec.
8x8 board, 150000 millisec.

"""
options = [(6, 150000),
            (8, 150000),
            (8, 180000),
            (10, 180000),
            ]


for ai_id0 in ai_ids:
    for ai_id1 in ai_ids:
        if ai_id0 < ai_id1:
            for board_size, max_time_limit_ms in options:
                print(ai_id0, ai_id1, board_size, max_time_limit_ms)
                Match_id = db_util.add_match(game_id=1,
                            board_size=board_size,
                            max_time_limit_ms=max_time_limit_ms,
                            player_one_id=ai_id0,
                            player_two_id=ai_id1,
                            )
                print(ai_id1, ai_id0, board_size, max_time_limit_ms)
                Match_id = db_util.add_match(game_id=1,
                            board_size=board_size,
                            max_time_limit_ms=max_time_limit_ms,
                            player_one_id=ai_id1,
                            player_two_id=ai_id0,
                            )
            #import sys; sys.exit()
