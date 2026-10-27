# File: mysite/models.py
import inspect

print('importing {} from {}'.format(__name__, \
    inspect.getframeinfo(inspect.getouterframes(inspect.currentframe())[1][0])[0]))

from sqlalchemy import Boolean, Column, Text, Integer, String, DateTime, ForeignKey

from mysite import db
from mysite import app # why no error if this is left out????

# from .config import SESSION_KEY_LENGTH # why not just use app.config['SESSION_KEY_LENGTH']?
SESSION_KEY_LENGTH = app.config['SESSION_KEY_LENGTH']

USER_LENGTH = app.config['USER_LENGTH']
EMAIL_LENGTH = app.config['EMAIL_LENGTH']
HASHEDPASSWORD_LENGTH = app.config['HASHEDPASSWORD_LENGTH']
SALT_LENGTH = app.config['SALT_LENGTH']
RANDOM_LENGTH = app.config['RANDOM_LENGTH']

TABLE_ARGS = { 'extend_existing': True,
               'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8',
               'mysql_collate': 'utf8_general_ci' }


class User(db.Model):
    """
    In vm, this is Person and Student
    """
    __tablename__ = 'User'
    __table_args__ = TABLE_ARGS
    id = Column(Integer, primary_key=True)
    user = Column(String(USER_LENGTH), unique=True, nullable=False)
    email = Column(String(EMAIL_LENGTH), unique=True, nullable=False)
    hashedpassword = Column(String(HASHEDPASSWORD_LENGTH), nullable=False)
    salt = Column(String(SALT_LENGTH), nullable=False)

    # TODO: membership_date

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        # False if user is banned
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def __repr__(self):
        return '<User %s %s %s>' %\
            (self.id, self.user, self.email,
             #self.hashedpassword,
             #self.salt,
            )

    def __str__(self):
        return self.__repr__()


class Admin(db.Model):
    __tablename__ = 'Admin'
    __table_args__ = TABLE_ARGS
    id = Column(Integer, primary_key=True)
    User_id = Column(Integer, ForeignKey('User.id'), unique=True, nullable=False)
    def __repr__(self):
        return '<Admin %s %s>' %\
            (self.id, self.User_id)
    def __str__(self):
        return self.__repr__()

class Registration(db.Model):
    '''
    user: must not be in Registration or User
    email: must not be in Registration or User
    '''
    __tablename__ = 'Registration'
    __table_args__ = TABLE_ARGS

    id = Column(Integer, primary_key=True)
    user = Column(String(USER_LENGTH), unique=True, nullable=False)
    email = Column(String(EMAIL_LENGTH), unique=True, nullable=False)
    hashedpassword = Column(String(HASHEDPASSWORD_LENGTH), nullable=False)
    salt = Column(String(SALT_LENGTH), nullable=False)
    code = Column(String(RANDOM_LENGTH), nullable=False)
    expiration = Column(DateTime, nullable=False)

    def __repr__(self):
        return '<Registration %s %s %s %s %s %s %s>' % \
            (self.id, self.user, self.email, self.hashedpassword,
             self.salt, self.code, self.expiration)


class ResetPassword(db.Model):
    '''
    Change user_id to User_id
    '''
    __tablename__ = 'ResetPassword'
    __table_args__ = TABLE_ARGS

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('User.id'))
    code = Column(String(RANDOM_LENGTH), nullable=False)
    expiration = Column(DateTime, nullable=False)

    def __repr__(self):
        return '<ResetPassword %s %s %s %s>' % \
            (self.id, self.user_id, self.code, self.expiration)


class Session(db.Model):
    '''
    Session identification
    key: identify the session for a given user
    User_id: id of the user logged in
    '''
    __tablename__ = 'Session'
    __table_args__ = TABLE_ARGS

    key = Column(String(SESSION_KEY_LENGTH), nullable=False, unique=True, primary_key=True)
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False)
    active = Column(Boolean, nullable=False)

class Game(db.Model):
    __tablename__ = 'Game'
    __table_args__ = TABLE_ARGS

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    logic_lang = Column(String(255), nullable=False)
    draw_lang = Column(String(255), nullable=False)
    logic_script_path = Column(String(255), nullable=False)
    draw_script_path = Column(String(255), nullable=False)
    max_players = Column(Integer, nullable=False)

    # ADDED 11/30/2018
    def __repr__(self):
        return '<Game %s %s %s %s %s %s %s>' %\
            (self.id, self.name, self.description,
             self.logic_lang, self.draw_lang, self.logic_script_path, self.max_players,
            )

class AI(db.Model):
    __tablename__ = 'AI'
    __table_args__ = TABLE_ARGS

    id = Column(Integer, primary_key=True)
    User_id = Column(Integer, ForeignKey('User.id'), nullable=False)

    # 2024/12/10 commented out 'owner'
    #owner = db.relationship('mysite.models.User', backref=db.backref('AIs', lazy='dynamic')) # 2024/12/05 ???????
    Game_id = Column(Integer, ForeignKey('Game.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    filepath = Column(String(255), nullable=False)

    # 2024/12/10 commented out 'stats'
    #stats = db.relationship('mysite.models.Stats', backref='AI', uselist=False)

    # ADDED 12/10/2018
    def __repr__(self):
        return '<AI %s %s %s %s>' %\
            (self.id, self.User_id, self.name, self.filepath
            )

class Match(db.Model):
    __tablename__ = 'Match'
    __table_args__ = TABLE_ARGS

    id = Column(Integer, primary_key=True)
    Game_id = Column(Integer, ForeignKey('Game.id'), nullable=False)
    board_size = Column(Integer, default=8, nullable=False)
    max_time_limit_ms = Column(Integer, nullable=False)
    max_space_kb = Column(Integer, default=1024, nullable=False)
    extra_settings = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False)

    Player_one_id = Column(Integer, ForeignKey('AI.id'), nullable=False)
    print(">>>>>>>> Player_one ...") # 2024/12/10

    # 2024/12/10: commented out Player_one and Player_two
    #Player_one = db.relationship('mysite.models.AI',
    #                             foreign_keys=[Player_one_id],
    #                             backref='black_matches')
    #Player_one = AI.query.filter_by(id=ai_id).first()

    Player_two_id = Column(Integer, ForeignKey('AI.id'), nullable=False)
    #Player_two = db.relationship('mysite.models.AI',
    #                             foreign_keys=[Player_two_id],
    #                             backref='white_matches')

    result = Column(String(255), nullable=True)

    move_history = Column(Text, nullable=True)
    board_states = Column(Text, nullable=True)
    verdict = Column(Text, nullable=True)

    # ADDED 11/30/2018
    def __repr__(self):
        return '<Match %s Game_id:%s size:%s max_time:%s max_space:%s extra:%s start_time:%s ai_1:%s ai_2:%s result:%s moves: states: verdict:%s>' %\
            (self.id, self.Game_id, self.board_size,
            self.max_time_limit_ms, self.max_space_kb, self.extra_settings,
            self.start_time, self.Player_one_id, self.Player_two_id,
            self.result,
            #self.move_history,
            #self.board_states,
            self.verdict,
            )

class Stats(db.Model):
    __tablename__ = 'Stats'
    __table_args__ = TABLE_ARGS

    id = Column(Integer, primary_key=True)
    AI_id = Column(Integer, ForeignKey('AI.id'), nullable=False)
    wins = Column(Integer, default=0, nullable=False)
    losses = Column(Integer, default=0, nullable=False)
    timeouts = Column(Integer, default=0, nullable=False)
    illegals = Column(Integer, default=0, nullable=False)
    ties = Column(Integer, default=0, nullable=False)

# WARNING
with app.app_context():
    db.create_all()
    db.session.commit()
