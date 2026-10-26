import json
import resource
#import subprocess32 as subprocess # 2024/12/05: added next line
import subprocess
import sys

from models import *

def set_max_runtime(seconds):
    '''Sets resource limit to enforce a timeout.'''
    # Note that while a very nice idea, it seems resource has a bug in python
    # 2.7 at least where it kills the parent function upon passing a value less
    # than 1 second as the limit. Using ulimit with shell directly instead.
    # Decided to use a backport of Python 3's subprocess for timeouts.
    soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
    resource.setrlimit(resource.RLIMIT_CPU, (seconds, hard))

class Runner(object):
    '''Runs a turn based Othello game between two AIs.

If you want to run a different board game, most of this will probably be very
    similar, so you could try to subclass this runner. If nothing else, the
    structure should be similar enough to give you some ideas about how to proceed.
You will also need a script that has the following functions implemented correctly:
    1. give you the initial board state (init_board())
    2. validate a move for a given state and turn (is_valid_move())
    3. give you the updated state back when you give it a move (make_move())
    4. gives you the result of the game if its over, otherwise none (result())
Check Othello.py inside games/Othello folder for example.
    '''

    def __init__(self, Match_id):
        self.match = Match.query.filter_by(id=Match_id).one()

        game = Game.query.filter_by(id=self.match.Game_id).one()
        game_script_path = game.logic_script_path
        game_path = game_script_path.split('/')
        game_name = game_path.pop()[:-3]
        game_path = '/'.join(game_path)
        global sys
        if game_path not in sys.path:
            sys.path.append(game_path)

        # 2024/12/11: hardcoding self.game as Othello
        import sys; sys.path.append('/home/ciss450othello/mysite/games/Othello')
        import Othello
        # 29241211: Comment out.
        #exec('import {} as game'.format(game_name))
        #print('>>>>>>>> import {} as game'.format(game_name))
        #print(">>>>>>>> game:", game, type(game))
        #self.game = eval("game.%s()" % game_name) # 2024/12/11 ??????
        # 2024/12/11: ADDED BELOW
        self.game = Othello # .Othello(self.match.board_size)

        self.board_size = self.match.board_size
        self.board_state = self.game.init_board(self.board_size) # 2024/12/10: see Othello
        self.board_states = [('', json.loads(self.board_state))] # this is the old code, and now works correctly.
        self.move_history = []

        self.player_one = AI.query.filter_by(id=self.match.Player_one_id).one()
        self.player_two = AI.query.filter_by(id=self.match.Player_two_id).one()

        self.player_one_script_path = self.player_one.filepath
        self.player_two_script_path = self.player_two.filepath
        self.player_two_time = self.player_one_time = self.match.max_time_limit_ms

        self.turn = 'B'
        self.player = self.player_one
        self.turn_path = self.player_one_script_path
        self.turn_time = self.player_one_time

        self.other = 'W'
        self.opponent = self.player_two
        self.opponent_path = self.player_two_script_path
        self.opponent_time = self.player_two_time

        self.verdict = {'conclusion': 'normal'}


    def switch_turns(self):
        if self.turn == 'B':
            self.turn_time = self.player_two_time
            self.opponent_time = self.player_one_time
        elif self.turn == 'W':
            self.turn_time = self.player_one_time
            self.opponent_time = self.player_two_time

        self.turn, self.other = self.other, self.turn
        self.player, self.opponent = self.opponent, self.player
        self.turn_path, self.opponent_path = self.opponent_path, self.turn_path

    def update_times(self):
        if self.turn == 'B':
            self.player_one_time -= self.time_taken
        elif self.turn == 'W':
            self.player_two_time -= self.time_taken

    def fetch_move(self):
        time_left = self.turn_time / 1000.0
        # print "time_left:", self.turn_time

        cmd = "python {ai_runner_path} {script_path} {board_size} {turn} {time_left} {opponent_time}".format(
            ai_runner_path='mysite/othello_ai_runner.py',
            script_path=self.turn_path,
            board_size=self.board_size,
            turn=self.turn,
            time_left=self.turn_time,
            opponent_time=self.opponent_time)

        #print(">>>>>>>> othello_match_runner.Runner.fetch_move -1 ... cmd: [%s]" % cmd)
        start = resource.getrusage(resource.RUSAGE_CHILDREN)
        child = subprocess.Popen(cmd.split(),
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, encoding="utf-8")
        try:
            #print(">>>>>>>> othello_match_runner.Runner.fetch_move 0")
            stdout, stderr = child.communicate(input=self.board_state, timeout=time_left)
            #print(">>>>>>>> othello_match_runner.Runner.fetch_move 1 stdout: [%s]" % stdout)
            move = stdout.split('\n')[-1]
            #print(">>>>>>>> fetch_move 2 move, len, type: [%s] %s %s" % (move, len(move), type(move)))
            # print "stdout: ", stdout
            end = resource.getrusage(resource.RUSAGE_CHILDREN)
            time_taken = end.ru_utime + end.ru_stime - start.ru_utime - start.ru_stime
            time_taken *= 1000
            #print(">>>>>>>> othello_match_runner.Runner.fetch_move 3 time_taken: [%s]" % time_taken)
        except subprocess.TimeoutExpired as e:
            child.kill()
            stdout, stderr = child.communicate()
            # end = resource.getrusage(resource.RUSAGE_CHILDREN)
            # time_taken = end.ru_utime + end.ru_stime - start.ru_utime - start.ru_stime
            # time_taken *= 1000
            # print "time_left now:", self.turn_time - time_taken
            return 'timeout', e.timeout

        # print "time_left now:", self.turn_time - time_taken

        if move == 'error':
            self.traceback = stdout.split('\n')[-2]

        return move, time_taken

    def make_move(self):
        move = json.loads(self.move)
        self.move_history.append(move)
        self.board_state = self.game.make_move(self.board_size, self.turn,
                                               self.board_state, self.move)
        self.board_states.append((move, json.loads(self.board_state)))

    def save_match_data(self):
        import db_util

        winner_color = 'Tie'
        winner = None
        if self.result == self.turn:
            winner = self.player.id
            winner_color = self.turn
        elif self.result == self.other:
            winner = self.opponent.id
            winner_color = self.other

        if winner_color == 'B':
            winner_color = 'Black'
        elif winner_color == 'W':
            winner_color = 'White'

        last_move_color = 'Black' if self.turn == 'B' else 'White'

        self.verdict.update({'winner': winner,
                             'winner_color': winner_color,
                             'last_move_player': self.player.id,
                             'last_move_color': last_move_color,
                             'result': self.result})

        db_util.update_match_details(self.match,
                                     {'result': winner_color,
                                      'move_history': self.move_history,
                                      'board_states': self.board_states,
                                      'verdict': json.dumps(self.verdict)
                                     })

    def save_stats(self):
        import db_util

        # 2024/12/11: new version.
        player_stats = Stats.query.filter(Stats.AI_id==self.player.id).first()
        opponent_stats = Stats.query.filter(Stats.AI_id==self.opponent.id).first()
        if self.result == self.turn:
            db_util.save_stats(self.player, {'wins': player_stats.wins + 1})
            db_util.save_stats(self.opponent, {'losses': opponent_stats.losses + 1})
        elif self.result == self.other:
            db_util.save_stats(self.opponent, {'wins': opponent_stats.wins + 1})
            db_util.save_stats(self.player, {'losses': player_stats.losses + 1})
        elif self.result == 'T':
            db_util.save_stats(self.player, {'ties': player_stats.ties + 1})
            db_util.save_stats(self.opponent, {'ties': opponent.stats.ties + 1})

        # 2024/12/11: old version
        """
        if self.result == self.turn:
            db_util.save_stats(self.player,
                               {'wins': self.player.stats.wins + 1})
            db_util.save_stats(self.opponent,
                               {'losses': self.opponent.stats.losses + 1})
        elif self.result == self.other:
            db_util.save_stats(self.opponent,
                               {'wins': self.opponent.stats.wins + 1})
            db_util.save_stats(self.player,
                               {'losses': self.player.stats.losses + 1})
        elif self.result == 'T':
            db_util.save_stats(self.player,
                               {'ties': self.player.stats.ties + 1})
            db_util.save_stats(self.opponent,
                               {'ties': self.opponent.stats.ties + 1})
        """

    def timeout(self):
        #print("timeout ... 0")
        import db_util
        #print("timeout ... 1")
        self.move = json.dumps('timeout')
        #print("timeout ... 2")
        self.verdict['conclusion'] = 'timeout'
        #print("timeout ... 3")
        self.make_move()
        #print("timeout ... 4")
        db_util.save_stats(self.player,
                           {'timeouts': self.player.stats.timeouts + 1})
        #print("timeout ... 5")
        ret = self.finalize_result(self.other)
        #print("timeout ... 6")
        return ret

    def illegal(self): #, invalid = False): # 12/11/2024 invalidity check, dont move if the move is junk (JSON will throw exception otherwise)
        import db_util

        self.verdict['conclusion'] = 'illegal'
        #if not invalid:
        #    self.make_move()
        self.make_move()
        player_stats = Stats.query.filter(Stats.AI_id==self.player.id).first() # 12/11/2024, need stats here too
        db_util.save_stats(self.player,
                           {'illegals': player_stats.illegals + 1})
        return self.finalize_result(self.other)

    def error(self):
        self.move = json.dumps('error')
        self.verdict.update({'error': self.traceback})
        return self.illegal()

    def finalize_result(self, result):
        #print("finalize_result ... 0")
        self.result = result
        self.move_history = json.dumps(self.move_history)
        self.board_states = json.dumps(self.board_states)
        self.save_match_data()
        self.save_stats()
        #print("finalize_result ... 1")
        db.session.commit()
        #print("finalize_result ... 2")
        return self.board_states, self.move_history, \
            self.player_one_time, self.player_two_time, self.result

    def execute(self):
        #print(">>>>>>>> othello_match_runner.Runner.execute ... 0")
        while not self.game.result(self.board_size, self.board_state):
            #print(">>>>>>>> othello_match_runner.Runner.execute ... 0.5")
            db.session.commit() # force to close to reconnect
            self.move, self.time_taken = self.fetch_move()
            db.session.commit() # force to close to reconnect
            self.update_times()
            #print(">>>>>>>> othello_match_runner.Runner.execute .... 1 ... move, len, type: [%s] %s %s" % (self.move, len(self.move), type(self.move)))

            if self.move == 'timeout':
                #print(">>>>>>>> othello_match_runner.Runner.execute .... 2 ... timeout")
                return self.timeout()
            elif self.move == 'error':
                #print(">>>>>>>> othello_match_runner.Runner.execute .... 3 ... error")
                return self.error()

            '''
            try: # 12/11/2024 error handling when you send the json loads function junk.
                if not self.game.is_valid_move(self.board_size, self.turn,
                                               self.board_state, self.move):
                    print("execute .... 4 ... illegal")
                    return self.illegal()
                print("execute .... 5")
                self.make_move()
                print("execute .... 6")
                self.switch_turns()
                print("execute .... 7")
            except json.decoder.JSONDecodeError as e: # junk was loaded and an error was thrown.
                print("execute .... 4 ... invalid")
                return self.illegal(True) # true flag to denote the move as junk.
            '''
            if not self.game.is_valid_move(self.board_size, self.turn,
                                               self.board_state, self.move):
                #print("othello_match_runner.Runner.execute .... 4 ... illegal")
                return self.illegal()
            #print(">>>>>>>> othello_match_runner.Runner.execute .... 5")
            self.make_move()
            #print(">>>>>>>> othello_match_runner.Runner.execute .... 6")
            self.switch_turns()
            #print(">>>>>>>> othello_match_runner.Runner.execute .... 7")

        print("othello_match_runner.Runner.execute .... 8")
        return self.finalize_result(self.game.result(self.board_size, self.board_state))
