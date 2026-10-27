# import __builtin__
# __builtin__.running_locally = True

from collections import OrderedDict
from mysite.models import *
from mysite import util
from mysite import db_util

'''
print "reset password for smaug ..."
smaug_id = 5
password = "Yli*ow24"
user = User.query.filter(User.id==smaug_id).first()
print "smaug is ...", user
salt = util.randstring()
hashedpassword = util.hashfunc(password=password, salt=salt)
user.hashedpassword = hashedpassword
user.salt = salt
db.session.commit()
print "done"
'''

'''
print "deleting the following matches ..."
for x in range(366, 396):
    print "delete match", x
    Match.query.filter(Match.id == x).delete()
    db.session.commit()
import sys; sys.exit()
'''

'''
users = User.query.all()
print "users:"
for user in users:
    print user
'''

'''
AIs = AI.query.all()
print "AIs:"
for ai in AIs:
    print ai
'''

matches = Match.query.all()
'''
print "all matches:"
if len(matches) == 0:
    print "None"
else:
    for m in matches:
        print m
import sys; sys.exit()
'''

'''
stats = Stats.query.all()
print "all stats:"
if len(stats) == 0:
    print "None"
else:
    for stat in stats:
        print stat
'''

# DELETE ALL STATS
'''
print "deleting stats ..."
for s in stats:
    Stats.query.filter(Stats.id == s.id).delete()
    db.session.commit()
import sys; sys.exit()
'''

# Recreate Stats row for each AT
'''
AIs = AI.query.all()
for ai in AIs:
    statsobj = Stats(AI_id=ai.id)
    db.session.add(statsobj)
    db.session.commit()
import sys; sys.exit()
'''

# create matches
'''
AIs = [35, 94, 70, 77, 91, 93]
print "create matches ..."
for x in AIs:
    for y in AIs:
        if x == y: continue
        Match_id = db_util.add_match(game_id=1,
                                    board_size=8,
                                    max_time_limit_ms=180000,
                                    player_one_id=x,
                                    player_two_id=y)
        print Match_id
#import sys; sys.exit()
'''

AIs = set([match.Player_one for match in matches])
AIs |= set([match.Player_two for match in matches])

by_wins = sorted([(AI.name, AI.owner.user, AI.stats.wins) for AI in AIs],
                 key=lambda t: t[2], reverse=True)

by_losses = sorted([(AI.name, AI.owner.user, AI.stats.losses) for AI in AIs],
                   key=lambda t: t[2])

by_timeouts = sorted([(AI.name, AI.owner.user, AI.stats.timeouts) for AI in AIs],
                     key=lambda t: t[2])

by_illegals = sorted([(AI.name, AI.owner.user, AI.stats.illegals) for AI in AIs],
                     key=lambda t: t[2])

by_ties = sorted([(AI.name, AI.owner.user, AI.stats.ties) for AI in AIs],
                 key=lambda t: t[2], reverse=True)

points = []
for AI in AIs:
    stats = AI.stats
    point = stats.wins * 3 + stats.ties - 1 * stats.timeouts - 3 * stats.illegals
    points.append((AI.name, AI.owner.user, point))

by_points = sorted(points, key=lambda t: t[2], reverse=True)

print "======================================================================"
print "Best AIs by most wins:"
print "======================================================================"
for name, owner, value in by_wins:
    print "Name: {name:<18} Owner: {owner:<18} wins: {wins:<5}".format(
        name=name, owner=owner, wins=value)
    print "----------------------------------------------------------------------"

print "\n\n\n"
print "======================================================================"
print "Best AIs by least losses:"
print "======================================================================"
for name, owner, value in by_losses:
    print "Name: {name:<18} Owner: {owner:<18} losses: {losses:<5}".format(
        name=name, owner=owner, losses=value)
    print "----------------------------------------------------------------------"

print "\n\n\n"
print "======================================================================"
print "Best AIs by least timeouts:"
print "======================================================================"
for name, owner, value in by_timeouts:
    print "Name: {name:<18} Owner: {owner:<18} timeouts: {timeouts:<5}".format(
        name=name, owner=owner, timeouts=value)
    print "----------------------------------------------------------------------"

print "\n\n\n"
print "======================================================================"
print "Best AIs by least number of illegal moves:"
print "======================================================================"
for name, owner, value in by_illegals:
    print "Name: {name:<18} Owner: {owner:<18} illegals: {illegals:<5}".format(
        name=name, owner=owner, illegals=value)
    print "----------------------------------------------------------------------"

print "\n\n\n"
print "======================================================================"
print "AIs with most ties:"
print "======================================================================"
for name, owner, value in by_ties:
    print "Name: {name:<18} Owner: {owner:<18} ties: {ties:<5}".format(
        name=name, owner=owner, ties=value)
    print "----------------------------------------------------------------------"


print "\n\n\n======================================================================"
print """Point system:
----------------------------------------------------------------------
+3 for Wins,
+1 for Ties,
0 for Losses,
-1 for timeouts and
-3 for illegal moves."""
print "======================================================================"
print "AIs with most points:"
print "======================================================================"
for name, owner, value in by_points:
    print "Name: {name:<18} Owner: {owner:<18} points: {points:<5}".format(
        name=name, owner=owner, points=value)
    print "----------------------------------------------------------------------"


