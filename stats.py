# import __builtin__
# __builtin__.running_locally = True
import yaml

import mysite.db_util as db_util

from mysite.models import *

matches = Match.query.all()
AIs = set([match.Player_one for match in matches])
AIs |= set([match.Player_two for match in matches])

for AI in AIs:
    wins = 0
    losses = 0
    timeouts = 0
    illegals = 0
    ties = 0
    black_matches = AI.black_matches
    for match in black_matches:
        verdict = yaml.safe_load(match.verdict)

        if verdict["result"] == "B":
            wins += 1

        elif verdict["result"] == "W":
            losses += 1
            if verdict["conclusion"] == "timeout":
                timeouts += 1
            elif verdict["conclusion"] == "illegal":
                illegals += 1

        elif verdict["result"] == "T":
                ties += 1

    white_matches = AI.white_matches
    for match in white_matches:
        verdict = yaml.safe_load(match.verdict)

        if verdict["result"] == "W":
            wins += 1

        elif verdict["result"] == "B":
            losses += 1
            if verdict["conclusion"] == "timeout":
                timeouts += 1
            elif verdict["conclusion"] == "illegal":
                illegals += 1

        elif verdict["result"] == "T":
                ties += 1

    stats = {
        'wins': wins,
        'losses': losses,
        'timeouts': timeouts,
        'illegals': illegals,
        'ties': ties,
     }

    db_util.save_stats(AI, stats)


