import argparse
import json
import sys
import traceback

if __name__ == "__main__":
    board_state = json.loads(input()) # 2024/12/11: change raw_input to input

    parser = argparse.ArgumentParser()
    parser.add_argument("script_path", help="Absolute path to the script to run")
    parser.add_argument("board_size", help="Board dimensions.", type=int)
    parser.add_argument("turn", help="'B' for black, 'W' for white")
    parser.add_argument("time_left", help="time left for this script in milliseconds",
                        type=float)
    parser.add_argument("opponent_time", help="time left for opponent in milliseconds",
                        type=float)
    args = parser.parse_args()

    script_path = args.script_path.split('/')
    script_name = script_path.pop()[:-3]
    script_path = '/'.join(script_path)

    if script_path not in sys.path:
        sys.path.append(script_path)

    try:
        exec('import {} as script'.format(script_name))

        move = script.get_move(args.board_size, board_state, args.turn, args.time_left,
                           args.opponent_time)

        sys.stdout.write('\n')
        sys.stdout.write(json.dumps(move))
    except:
        sys.stdout.write('\n')
        sys.stdout.write(json.dumps(traceback.format_exc(limit=1)))
        sys.stdout.write('\n')
        sys.stdout.write('error')
