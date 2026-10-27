"""
File: db_util.py
Utility functions for DB operations
Mostly add, delete, modify functions to handle DB operations
API:
    add_[table](..., commit=True)
Example:
     add_registration(..., commit=True)
FUNCTIONS:
    add_registration
    add_user
    delete_expired_registrations
"""
import datetime
import os

from sqlalchemy.orm.exc import NoResultFound

from flask import flash

from mysite import app, db, session
from mysite.config import SESSION_KEY_LENGTH

# utility functions
from mysite.util import randstring, hashfunc
from werkzeug.utils import secure_filename

from mysite.models import User, ResetPassword, Registration, Session, AI, Game, Match, Stats

def do_commit(commit):
    if commit: db.session.commit()

def close():
    db.session.close()


def add_registration(user, email, password, code, commit=True):
    salt = randstring()
    hashedpassword = hashfunc(password=password, salt=salt)
    dtime = app.config['DTIME_FOR_REGISTRATION']
    expiration = datetime.datetime.now() + dtime
    registration = Registration(user=user,
                                email=email,
                                hashedpassword=hashedpassword,
                                salt=salt,
                                code=code,
                                expiration=expiration)
    db.session.add(registration)
    do_commit(commit)


def get_user(user_id):
    return User.query.filter_by(id=user_id).first()


def add_user(user, email, hashedpassword, salt, commit=True):
    userobj = User(user=user,
                   email=email,
                   hashedpassword=hashedpassword,
                   salt=salt)
    db.session.add(userobj)
    do_commit(commit)


def delete_expired_registrations(commit=True):
    now = datetime.datetime.now()
    Reg = Registration # shorthand
    registrations = Reg.query.filter(Reg.expiration < now)
    for registration in registrations:
        db.session.delete(registration)
    do_commit(commit)


def delete_registrations(email, commit=True):
    Reg = Registration
    for x in Reg.query.filter(Reg.email==email):
        db.session.delete(x)
    do_commit(commit)


def delete_expired_resetpasswords(commit=True):
    now = datetime.datetime.now()
    Res = ResetPassword # shorthand
    resetpasswords = Res.query.filter(Res.expiration < now)
    for resetpassword in resetpasswords:
        db.session.delete(resetpassword)
    do_commit(commit)


def delete_resetpasswords(email, commit=True):
    # Delete all ResetPasswords row with email. Link email to
    # right user in User table.
    user = User.query.filter(User.email==email).first()
    if user != None:
        Res = ResetPassword # shorthand
        for x in Res.query.filter(Res.user_id == user.id):
            db.session.delete(x)
        do_commit(commit)


def add_resetpassword(user_id, code, commit=True):
    dtime = app.config['DTIME_FOR_REGISTRATION']
    expiration = datetime.datetime.now() + dtime
    resetpassword = ResetPassword(user_id=user_id,
                                  code=code,
                                  expiration=expiration)
    db.session.add(resetpassword)
    do_commit(commit)


def is_authenticated(user, password):
    #return True # ADDED 12/13
    userobj = User.query.filter(User.user==user).first()
    if userobj == None: return False
    # ADDED 2018/12/13
    #if userobj.user == 'smaug' and password == 'yliow24':
    #    return True
    salt = userobj.salt
    hashedpassword = hashfunc(password=password, salt=salt)
    return hashedpassword==userobj.hashedpassword


def get_user_from_session(session_key):
    session_ = Session.query.filter_by(key=session_key).first()
    if session_ is None:
        return None
    return User.query.filter_by(id=session_.User_id).first()


def add_session(user, commit=True):
    try:
        User_id = User.query.filter_by(user=user).one().id
        session['key'].append(randstring(SESSION_KEY_LENGTH))
    except KeyError:
        session['key'] = [randstring(SESSION_KEY_LENGTH),]
    except NoResultFound:
        flash("No user exists with that username.")
    finally:
        sessionobj = Session(key=session['key'][-1], User_id=User_id, active=True)
        db.session.add(sessionobj)
        do_commit(commit)


def deactivate_session(commit=True):
    try:
        session_obj = Session.query.filter_by(key=session['key'][-1]).one()
        session_obj.active = False;
        do_commit(commit)
        session['key'].pop()
        session.pop('section-id', None)
    except:
        session.pop('key', None)


def can_spoof(user):
    if user in ['rbfrappier1', 'smaug', 'NONAME36367', 'yliow', 'ryan']:
        return True
    return False


def game_exists(game_id):
    return Game.query.filter_by(id=game_id).first()

def get_games():
    return Game.query.all()


def get_ai(ai_id):
    return AI.query.filter_by(id=ai_id).first()


def get_user_ais(user):
    return AI.query.filter_by(User_id=user.id)


def get_max_ai_folder_num(user):
    path = '%s/%s/ais' % (app.config['UPLOAD_FOLDER'], user.user)
    if not os.path.isdir(path):
        os.makedirs(path)
        return -1
    else:
        dirs = os.listdir(path)
        dir_nums = [int(d) for d in dirs]
        if len(dir_nums) == 0:
            return -1
        else:
            return max(dir_nums)

def add_ai(user, name, game_id, description, ai_file_data, commit=True):

    # Save the data in ai_file_data.
    max_ai_folder = get_max_ai_folder_num(user=user)
    filename = secure_filename(ai_file_data.filename)
    filepath = "%s/%s/ais/%d" % (app.config['UPLOAD_FOLDER'], user.user,
                                 max_ai_folder + 1)

    if not os.path.isdir(filepath):
        os.makedirs(filepath)

    filepath = os.path.join(filepath, filename)
    ai_file_data.save(filepath)

    ai = AI(User_id=user.id, Game_id=game_id, name=name,
            description=description, filepath=filepath)

    # 12/11/2024 Need to commit before the AI id is made
    db.session.add(ai)
    do_commit(commit)

    # 12/11/2024 Now we can make the stats because the ID exists
    ai_stats = Stats(AI_id=ai.id)
    ai.stats = ai_stats

    # ai.stats = Stats.query.filter(Stats.AI_id==ai.id).first()
    # db.session.add(ai)
    db.session.add(ai_stats)

    do_commit(commit)


def update_ai(user, old_ai, name, game_id, description, ai_file_data,
              commit=True):
    if ai_file_data:
        old_filepath = old_ai.filepath
        new_filepath = os.path.join('/'.join(old_filepath.split('/')[:-1]),
                                secure_filename(ai_file_data.filename))
        ai_file_data.save(old_filepath)
        if old_filepath == new_filepath:
            pass
        else:
            os.system("mv '{}' '{}'".format(old_filepath, new_filepath))

    old_ai.name = name
    old_ai.game_id = game_id
    old_ai.description = description

    do_commit(commit)


def delete_ai(ai, commit=True):
    path_parts = ai.filepath.split('/')
    container_dir = '/'.join(path_parts[:-1])
    if os.path.exists(ai.filepath):
        os.remove(ai.filepath)
    os.system("rm -rf '{}'".format(container_dir))

    Match.query.filter_by(Player_one_id=ai.id).delete()
    Match.query.filter_by(Player_two_id=ai.id).delete()
    Stats.query.filter_by(AI_id=ai.id).delete()
    AI.query.filter_by(id=ai.id).delete()

    do_commit(commit)

def get_all_ais():
    return AI.query.all()

def get_all_users():
    return User.query.all()

def add_match(game_id, board_size, max_time_limit_ms,
              player_one_id, player_two_id, commit=True):
    match = Match(Game_id=game_id, board_size=board_size,
                  max_time_limit_ms=max_time_limit_ms,
                  Player_one_id=player_one_id, Player_two_id=player_two_id,
                  start_time=datetime.datetime.now())
    db.session.add(match)
    do_commit(commit)

    return match.id

def update_match_details(match, details_dict, commit=True):
    # 2020/12/17: Connection lost ... refetch match object
    print("update_match_details ... 0")
    match = Match.query.filter(Match.id==match.id).one()
    print("update_match_details ... 1")
    for key, val in details_dict.items():
        val_t = val.__class__.__name__
        cmd = "match.{key} = {val_t}({val!r})".format(key=key, val_t=val_t, val=val)
        exec(cmd)
    print("update_match_details ... 2")
    do_commit(commit)
    print("update_match_details ... 3")

def save_stats(ai, details_dict, commit=True):
    for key, val in details_dict.items():
        val_t = val.__class__.__name__
        ai.stats = Stats.query.filter(Stats.AI_id==ai.id).first() # 12/11/2024, get ai stats data
        cmd = "ai.stats.{key} = {val_t}({val!r})".format(key=key, val_t=val_t, val=val)
        exec(cmd)

    do_commit(commit)

def get_all_matches():
    return Match.query.all()
