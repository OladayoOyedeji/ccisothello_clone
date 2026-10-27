# run python game_runner.py 1 0 -- the two arguments are not used

NO_JOB_SLEEP = 5
JOB_SLEEP = 5
EXCEPTION_SLEEP = 5

import datetime, time, sys, argparse, traceback
from mysite.models import *

def log(s):
    NOW = str(datetime.datetime.now())
    s = '[%s] %s' % (NOW, s)
    f = open('log-%s.txt' % NOW, 'w')
    f.write(s)
    f.close()
    print(s)


game_scripts = {1: 'othello_match_runner'}


def main(args):

    # Either run one specific match or run all incomplete matches
    # To continually run, do while loop in __main__.

    try:
        game_script = game_scripts[args.game_id]
        print(">>>>>>>>", 'from mysite import {} as script'.format(game_script))

        # 2024/12/10: hardcode import
        #exec('from mysite import {} as script'.format(game_script))
        from mysite import othello_match_runner as script
        print(">>>>>>>> script", script)
        #print("commit ...")
        #db.session.commit() # clear cache
        #print("close ...")
        #db.session.close() # force close ?? to get reconnection?
        #matches = Match.query.filter(Match.verdict==None).order_by(Match.id.desc()) # all incomplete matches
        print("Attempting query...")
        matches = Match.query.filter(Match.verdict==None) # all incomplete matches
        print("finished query ...")

        if matches.count() == 0:
            log(s="no incomplete matches found")
            time.sleep(NO_JOB_SLEEP)
            return False # i.e., no matches
        else:
            if args.match_id not in [-1, 0]: # one job case
                found = False
                for match in matches:
                    if match == None: continue # should not happen
                    #if match.board_size > 8: continue # NOTE ... WHEN NOT ENOUGH CPU CYCLES
                    if match.id == args.match_id:
                        match_runner = script.Runner(match.id)
                        result = match_runner.execute()
                        db.session.commit() # clear cache ??
                        log(s="single-job case: match id %s done" % match.id)
                        time.sleep(JOB_SLEEP)
                        found = True
                        break
                if not found:
                    #log(s="**** single-job case: match id %s not found" % match.id)
                    return False
                else:
                    return True
            else: # run all matches case
                for match in matches:
                    if match == None: continue # should not happen
                    #if match.board_size > 8: continue # NOTE
                    print("game_runner 0 ...")
                    match_runner = script.Runner(match.id)
                    print("game_runner 1 ...")
                    result = match_runner.execute() # othello_match_runner.Othello.execute
                    print("game_runner 2 ...")
                    log(s="batch case: match id %s done" % match.id)
                    time.sleep(JOB_SLEEP)
                    break # run one
                return True

    except Exception as e:
        s = str(e) + "\n\n" + str(traceback.format_exc())
        log(s="**** exception and traceback: %s" % s)
        time.sleep(EXCEPTION_SLEEP) # prevent pythonanywhere task from frequent runs
        raise


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("game_id",
                        help="ID of the game you are trying to run.",
                        default=-1,
                        type=int)
    parser.add_argument("match_id", help="ID of the match to be run.", type=int, default=-1)
    parser.add_argument("--local", help="Running locally?", action="store_true")

    args = parser.parse_args()
    #print("1...")
    #print("game_id:", args.game_id
    #print("match_id: %s" % args.match_id)

    if args.game_id == -1:
        args.game_id = 0

    if args.local:
        import __builtin__
        __builtin__.running_locally = True

    #while 1:
    ran_match = main(args)
    #if ran_match: break
    #db.session.commit() # clear cache ??
    sys.exit()

    matches = Match.query.filter(Match.verdict==None) # all incomplete matches
    if matches.count() == 0:
        s = "no match"; log(s=s)
        time.sleep(NO_JOB_SLEEP)
        sys.exit()

    game_script = game_scripts[args.game_id]
    exec('from mysite import {} as script'.format(game_script))

    for match in matches:
        try:
            if match == None: continue # should not happen
            if match.verdict != None: continue # should not happen
            if args.match_id != 0:
                if match.id != args.match_id:
                    continue
            match_runner = script.Runner(match.id)
            result = match_runner.execute()
            s = "match id %s done" % match.id; log(s=s)
            time.sleep(JOB_SLEEP)
            #break # just run one match
        except Exception as e:
            s = "**** exception %s" % e; log(s=s)
            time.sleep(EXCEPTION_SLEEP)
            break
