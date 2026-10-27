"""
File: rebuild.py (put this in mysite/)
Clear some tables and create
1. User yliow as instructor
2. User jdoe
3. Semester Fall 2016
4. Course CISS240, CISS362, CISS450
5. Section CISS240A Fall 2016, CISS362A Fall 2016,
   and CISS450A Fall 2016.
6. Add jdoe to CISS240A Fall 2016 and CISS450A Fall
   2016
"""
import random; random.seed()
import hashlib, string, re

import datetime
import os

import sys
sys.path.append('/')

from models import *

def randstring(length=app.config['RANDOM_LENGTH']):
    cs = list(string.ascii_letters + string.digits)
    random.shuffle(cs)
    return ''.join(cs[:length])

def hashfunc(password, salt):
    """ ERROR: get password is None -- check why """
    h = password
    for i in range(app.config['HASH_ROUNDS']):
        h += salt + str(i * i)
        h = hashlib.sha256(h.encode('utf-8')).hexdigest()
    return h

base_path = app.config['BASEDIR']
othello_path = base_path + "/games/Othello/Othello.py"
othello_draw_path = base_path + "/games/Othello/Othello.js"
upload_path = base_path + "/data"

try:
    if FORCE_REBUILD:
        pass
    else:
        try:
            FORCE_REBUILD = True if sys.argv[1] == '-f' else False
        except IndexError:
            FORCE_REBUILD = False
except NameError:
    try:
        FORCE_REBUILD = True if sys.argv[1] == '-f' else False
    except IndexError:
        FORCE_REBUILD = False

print ("db:%s" % db)

def drop_everything(db):
    """Use this if db.drop_all() is broken."""
    from sqlalchemy.engine import reflection
    from sqlalchemy.schema import (
        MetaData,
        Table,
        DropTable,
        ForeignKeyConstraint,
        DropConstraint,
        Index,
        DropIndex
    )

    inspector = reflection.Inspector.from_engine(db.engine)

    metadata = MetaData()

    tables = []
    all_foreign_keys = []
    all_indices = []

    for table_name in inspector.get_table_names():
        foreign_keys = []
        for foreign_key in inspector.get_foreign_keys(table_name):
            if not foreign_key['name']:
                continue
            foreign_keys.append(ForeignKeyConstraint((), (), name=foreign_key['name']))

        indices = []
        for index in inspector.get_indexes(table_name):
            try:
                if not index['name']:
                    continue
                indices.append(Index(name=index['name']))
            except KeyError as e:
                print ("KEY NOT FOUND. %s" % e)

        t = Table(table_name, metadata, *foreign_keys)
        tables.append(t)
        all_foreign_keys.extend(foreign_keys)
        all_indices.extend(indices)

    for foreign_key_constraint in all_foreign_keys:
        db.engine.execute(DropConstraint(foreign_key_constraint))

    for index in all_indices:
        try:
            print (index)
            # db.engine.execute(DropIndex(index))
        except AttributeError as e:
            print ("Attibute not found. %s" % e)

    for table in tables:
        db.engine.execute(DropTable(table))

    return metadata

yorn = raw_input("clear tables? [y/n]: ")
if yorn == 'y':
    datapath = "rm -rf '{}/data'/*".format(base_path)
    print (datapath)
    os.system(datapath)
    #--------------------------------------------------------------------------
    # Warning, use this only if drop_all is failing and you must rebuild.
    # In that case, uncomment this and comment drop_all
    #--------------------------------------------------------------------------
    if FORCE_REBUILD:
        drop_everything(db)
    #--------------------------------------------------------------------------
    else:
        db.drop_all()
    db.session.commit()
    print ("Run again and choose 'n' to get the data back up.")
    exit()


salt = randstring()
hashedpassword=hashfunc(password='watevs',
                        salt=salt)
user = User(user='smaug',
            email='yliow@ccis.edu',
            hashedpassword=hashedpassword,
            salt=salt)
db.session.add(user)
db.session.commit()
user = User.query.filter_by(user='smaug').first()
print ("user:%s" % user)

admin = Admin(User_id=user.id)
db.session.add(admin)
db.session.commit()
admin = Admin.query.filter_by(User_id=user.id).first()
print ("admin:%s" % admin)

game = Game(name="Othello", description="Reversi",
            logic_lang="python",
            draw_lang="javascript",
            logic_script_path=othello_path,
            draw_script_path=othello_draw_path,
            max_players=2)
db.session.add(game)
db.session.commit()
print ("game: %s" % game.id)

salt = randstring()
hashedpassword=hashfunc(password='111!!!qqq',
                        salt=salt)
user = User(user='fake',
            email='yliow@yahoo.com',
            hashedpassword=hashedpassword,
            salt=salt)
db.session.add(user)
db.session.commit()
user = User.query.filter_by(user='fake').first()
print ("user:%s" % user)

filepath = os.path.join(upload_path, user.user, '0')
os.makedirs(filepath)
filepath += '/randfakeai.py'
os.system("cp '{}' '{}'".format(othello_path, filepath)) # ????
with open(filepath, 'w') as f:
    f.write("""
def get_move(board_size, board_state, turn, time_left, opponent_time):
    return None""")
ai = AI(User_id=user.id, Game_id=1, name='FakeTest', description='RANDOM MOVES',
        filepath=filepath)
ai_stats = Stats(AI_id=ai.id)
ai.stats = ai_stats
db.session.add(ai)
db.session.add(ai_stats)
db.session.commit()
print ("ai created for fake user")

'''
salt = randstring()
hashedpassword=hashfunc(password='MEHmeh2016',
                        salt=salt)
user = User(user='ujpandey1',
            email='ujpandey1@cougars.ccis.edu',
            hashedpassword=hashedpassword,
            salt=salt)
db.session.add(user)
db.session.commit()
user = User.query.filter_by(user='ujpandey1').first()
print "user:", user

filepath = os.path.join(upload_path, user.user, '0')
os.makedirs(filepath)
filepath += '/randai.py'
os.system("cp '{}' '{}'".format(othello_path, filepath))
ai = AI(User_id=user.id, Game_id=1, name='UjpRandom', description='RANDOM MOVES',
        filepath=filepath)
ai_stats = Stats(AI_id=ai.id)
ai.stats = ai_stats
db.session.add(ai)
db.session.add(ai_stats)
db.session.commit()
print "ai created for ujjwal"
'''

filepath = os.path.join(upload_path, user.user, '1')
os.makedirs(filepath)
filepath += '/illegal_ai.py'
with open(filepath, 'w') as f:
    f.write("""
def get_move(board_size, board_state, turn, time_left, opponent_time):
    return [-1, -1]""")
ai = AI(User_id=user.id, Game_id=1, name='illegal_ai', description='Illegal MOVES',
        filepath=filepath)
ai_stats = Stats(AI_id=ai.id)
ai.stats = ai_stats
db.session.add(ai)
db.session.add(ai_stats)
db.session.commit()
print ("illegal ai created for ujjwal")
