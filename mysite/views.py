# mysite/views.py

import os, json, sys, yaml, functools
#import subprocess32 as subprocess # 2024/12/05: ERROR subprocess32. commented out. added next line
import subprocess

#===================================================================
# Note that for the login view (the index):
# - LoginForm class is in forms.py
# - login.html in templates/
# - login function is in views.py
#===================================================================
from mysite import app, db, session

from flask import request
from flask import render_template
from flask import flash, redirect, url_for, send_from_directory, send_file
from markupsafe import escape, Markup

from sqlalchemy.orm.exc import NoResultFound

# for forms
from .forms import LoginForm, RegistrationForm, ResetPasswordForm
from .forms import RegistrationCodeForm, NewPasswordForm, AddToSectionForm

# for models
from .models import User, ResetPassword, Registration, Session, Match, AI, Game, Stats # 12/11/2024, added Stats

import sys; sys.path.append('/home/ciss450othello2/mysite/') # ?????? why cannot find db_util
from mysite import db_util

# utility functions
from mysite import util
from .util import randstring, hashfunc, sendemail, extract_emails

game_runner_path = os.path.join(app.config['BASEDIR'], '..', 'game_runner.sh')

#==============================================================--
# security headers
# https://flask.palletsprojects.com/en/1.1.x/security/
#==============================================================--
@app.after_request
def add_security_headers(resp):
    resp.headers['X-Frame-Options'] = 'DENY'
    resp.headers['X-XSS-Protection'] = '1; mode=block'
    resp.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    #resp.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self'"
    #resp.headers['Content-Security-Policy'] = "default-src 'https'; default-src 'self'; style-src 'self'"
    return resp


#==============================================================--
# Session related functions
# ** session_user: Set authenticated user
# ** is_logged_in: Put this at the top of all functions for
#                  authenticated users
#==============================================================--

def get_session_key():
    try:
        return session['key'][-1]
    except (IndexError, KeyError):
        return None

def get_logged_in_user():
    return db_util.get_user_from_session(get_session_key())

def is_logged_in():
    if not get_session_key():
        return False

    # Just to be safe: check user
    try:
        user = db_util.get_user_from_session(get_session_key())
    except NoResultFound:
        session.pop('key', None)
        return False
    else:
        return True

def session_login(user):
    # And other things ... maybe also add logged in time?
    db_util.add_session(user)
    session['breadcrumbs'] = [(url_for('index'), 'home'),
                              (url_for('index'), 'classes'),
                              (url_for('index'), 'ciss240'),]

def session_logout():
    """ What will happen to other keys """
    db_util.deactivate_session(session)
#=================================================================
# Breadcrumbs
# Probably use session as JSON as
# list of (href, string)OA
#=================================================================
def breadcrumbs():
    pass


#==============================================================--
# Some useful decorators.
#==============================================================--
def redirect_if_logged_in(f):
    @functools.wraps(f)
    def _f(*args, **kwargs):
        if is_logged_in():
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return _f


def authenticate(f):
    @functools.wraps(f)
    def _f(*args, **kwargs):
        if not is_logged_in():
            flash('You must be logged in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return _f


#=================================================================
# CPU usage
#=================================================================
@app.route('/cpuusage', methods=['GET', 'POST'])
@authenticate
def cpu():
    from util import cpuusage
    return cpuusage()


#=================================================================
# Homepage
#=================================================================
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@authenticate
def index():
    print("")
    print(80*"*")
    print(40*"*")
    print(80*"*")
    print("")
    try:
        user = db_util.get_user_from_session(get_session_key())
        ais = [ai for ai in db_util.get_user_ais(user)]
    except:
        session_logout()
        return redirect(url_for('login'))

    self = 'index'
    for ai in ais:
            ai.stats = Stats.query.filter(Stats.AI_id==ai.id).first() # 12/11/2024, get ai stats data
    return render_template('index.html',
                           title=app.config['TITLE'],
                           page_title='Home',
                           action=self,
                           ais=ais,
                           footer='This is the footer')

@app.route('/users', methods=['GET', 'POST'])
def users():
    self = 'users'
    if request.method == 'POST':
        searched = request.form.get('search')
        users = User.query.filter(User.user.like("%{}%".format(searched)))
    else:
        users = db_util.get_all_users()

    return render_template('users.html',
                           title=app.config['TITLE'],
                           page_title='Othello Users',
                           action=url_for(self),
                           users=users,
                           footer='This is the footer')


@app.route('/users/<int:user_id>', methods=['GET'])
@app.route('/user', methods=['GET'])
def user(user_id=None):
    if user_id:
        user = db_util.get_user(user_id)
    else:
        try:
            user = db_util.get_user_from_session(get_session_key())
        except:
            session_logout()
            return redirect(url_for('login'))

    ais = [ai for ai in db_util.get_user_ais(user)]

    return render_template('user.html',
                           title=app.config['TITLE'],
                           page_title="{}'s Profile Page".format(user.user),
                           user=user,
                           ais=ais,
                           footer='This is the footer')


#==================================================================
# Login
#==================================================================
@app.route('/login', methods=['GET', 'POST'])
@redirect_if_logged_in
def login():
    form = LoginForm()
    self = 'login'
    if request.method == 'POST':
        if form.validate():
            reqform = request.form # shorthand
            user = reqform.get('user', None) # should not be None
            password = reqform.get('password', None)
            if db_util.is_authenticated(user, password):
                flash('User %s is logged in.' % user, 'success')
                session_login(user)
                return redirect(url_for('index')) # or 'next' page
            else:
                flash('Incorrect user or password.', 'error')
        else:
            flash('Incorrect user or password.', 'error')
    return render_template('login.html',
                           title=app.config['TITLE'],
                           page_title='Login',
                           footer='This is the footer',
                           form=form,
                           action=self)

#==================================================================
# spoof Added by Andrew Woods 10/03/2016
#==================================================================
@app.route('/spoof', methods=['GET', 'POST'])
@authenticate
def spoof():
    '''
    Allow approved users to 'spoof' as another user.
    '''
    self = 'spoofs'
    if not db_util.can_spoof(get_logged_in_user().user):
        flash('You do not have permission to use this page', 'error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        reqform = request.form # shorthand
        user = reqform.get('user', None) # should not be None
        if User.query.filter_by(user=user).first():
            flash('User %s is logged in.' % user, 'success')
            session_login(user)
            return redirect(url_for('index')) # or 'next' page
        else:
            flash('Incorrect user or password.', 'error')
    return render_template('spoof.html',
                           title=app.config['TITLE'],
                           page_title='spoof',
                           footer='This is the footer',
                           action=self)

# Register load_user with LoginManager through @lm.user_load.
# This is required by LoginManager and must load a User object.
# User table uses int for id LoginManager uses unicode.
def load_user(id):
    return User.query.get(int(id))

#==================================================================
# Logout
#==================================================================
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session_logout()
    flash('You have been successfully logged out.', 'success')
    return redirect(url_for('login'))

#==================================================================
# Registration
#==================================================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Check user and email against the DB:
    #
    # 1. If user exists in User -- ERROR
    # 2. If email exists in User -- ERROR
    # 3. If (user, email) in Registration, probably same person
    #    So delete all Registration rows with given (user, email).
    #    NO ERROR (There can only be at most one such row).
    # 4. If user appears in Registration but email is different,
    #    probably someone else wanted that user -- ERROR
    # 5. If email appears in Registration but the user is
    #    different -- maybe same person but changed his/her
    #    mind about user name? Delete all rows with given email.
    #    -- NO ERROR
    # 3 and 5 -- combine: Delete all rows with same email and
    # add the new row. There's a chance that someone is
    # masquerading -- but the change is small especially since the
    # confirmation time is 15 minutes. Note that email is unique
    # in Registration -- so there's only one row.
    #
    # Note: If John Doe has previous registered and now tries to
    # register with jdoe, jdoe@gmail.com, then his previous
    # registration is deleted AND if another person has
    # registered jdoe, then John Doe does not have any
    # registration rows.
    #--------------------------------------------------------------
    self = 'register'
    form = RegistrationForm(request.form)

    if request.method == 'POST':
        print("register ... 0")
        # CASE: Submit
        # WARNING: How to prevent overuse of delete expireds?
        print("register ... 1")
        db_util.delete_expired_registrations()
        print("register ... 2")
        email = request.form.get('email', None)
        print("register ... 3 ... email:%s" % email)
        db_util.delete_registrations(email)
        print("register ... 4")
        if form.validate():
            print("register ... 5")
            # CASE: Submit and no errors
            addregistration()
            print("register ... 6")
            # pull out email code here?
            return redirect(url_for('registrationcode',
                                    user=request.form.get('user', None),
                                    email=request.form.get('email', None)))
        else:
            # CASE: Submit with errors
            print("register ... 7")
            flash('There are errors with your registration. Please try again.',
                  'error')

    print("register ... 8")
    dtime = app.config['DTIME_FOR_REGISTRATION']
    print("register ... 9")
    return render_template('registration.html',
                           title=app.config['TITLE'],
                           page_title='Sign Up',
                           form=form,
                           dtime=dtime,
                           action=url_for(self))


def addregistration():
    print("addregistration ... 0")
    user = request.form.get('user', None)
    print("addregistration ... 1 ... user:%s" % user)
    email = request.form.get('email', None)
    print("addregistration ... 2 ... email:%s" % email)
    password = request.form.get('password', None)
    print("addregistration ... 3 ... password:%s" % password)
    code = randstring()
    print("addregistration ... 4 ... code:%s" % code)
    db_util.add_registration(user=user, email=email,
                             password=password, code=code)
    print("addregistration ... 5")
    def email_registration_code(user, email, code):
        #--------------------------------------------------------
        # Email registration code
        # WARNING: for now recipients is yliow@ccis.edu
        #
        # TODO: Remove form
        #--------------------------------------------------------
        print("email_registration_code ... 0")
        form = RegistrationCodeForm() # redundant?
        print("email_registration_code ... 1")
        form.user.data = user
        print("email_registration_code ... 2")
        form.email.data = email
        print("email_registration_code ... 3")
        form.code.data = code
        print("email_registration_code ... 4")
        dtime = app.config['DTIME_FOR_REGISTRATION']
        print("email_registration_code ... 5")
        html = render_template('registrationcodeemail.html',
                           title=app.config['TITLE'],
                           page_title='Sign Up Confirmation',
                           user=user,
                           email=email,
                           code=code,
                           url=url_for('registrationcode',
                                       user=user,
                                       email=email,
                                       code=code,
                                       _external=True),
                           DTIME_FOR_REGISTRATION=dtime,
                           form=form,
                           )
        print("email_registration_code ... 6")
        sendemail(subject="%s registration" % app.config['TITLE'],
                  body="email body",
                  recipients=[email],
                  html=html)
        print("email_registration_code ... 7")

    print("addregistration ... 6")
    email_registration_code(user=user, email=email,
                            code=code)
    print("addregistration ... 7")

#===============================================================
# Enter registration confirmation code
#===============================================================
@app.route('/registrationcode', methods=['GET', 'POST'])
def registrationcode():
    """
    NOTE: There are two entry points --
    1. from register()
    and
    2. through the URL link in the email.
    """
    self = 'registrationcode'
    form = RegistrationCodeForm(request.form)

    # Data should be from form.
    # However will be from request.args
    # if I put the code in the email as well
    if request.method == 'POST':
        source = request.form
    else:
        source = request.args
    user = source.get('user', None)
    email = source.get('email', None)
    code = source.get('code', None)

    if request.method == 'POST': #  and form.validate():
        # CASE: Submit
        errmsg = adduser(user, code)
        if errmsg==None:
            flash('user successfully created', 'success')
            return redirect(url_for('login'))
        else:
            flash(errmsg, 'error')
            # need to put user, ... into form
            return redirect(url_for(self, user=user, email=email))

    # CASE: The form was shown, not submitted
    form.user.data = user
    form.email.data = email
    form.code.data = code
    dtime = app.config['DTIME_FOR_REGISTRATION']
    action = url_for(self)
    return render_template('registrationconfirmation.html',
                           title=app.config['TITLE'],
                           action=action,
                           page_title='Confirm registration',
                           DTIME_FOR_REGISTRATION=dtime,
                           form=form)

#==================================================================
# Add user to database based on user in Registration
#==================================================================
@app.route('/adduser', methods=['GET', 'POST'])    # ???
def adduser(user, code):
    #--------------------------------------------------------------
    # Delete expired registrations.
    # Look for registration.
    # Note: What happens when two registrations come in with
    # either same user or same email?
    # -- If it's from the same user (the code arrived late), then
    #    need to delete earlier registration row.
    # -- If it's from two different persons (not likely), the
    #    later person is disallowed.
    # -- So:
    #    1. delete expired registrations
    #    2. delete all registrations from user except for latest
    #    WAIT: Actually if user X registers, then all registrations
    #    from X should be deleted.
    #--------------------------------------------------------------
    db_util.delete_expired_registrations()
    registration = Registration.query.filter_by(user=user).first()
    if not registration:
        return "Cannot find user %s in Registration." % user
    if code != registration.code:
        return "Invalid code."
    user = registration.user
    email = registration.email
    hashedpassword = registration.hashedpassword
    salt = registration.salt
    db.session.delete(registration)
    db_util.add_user(user=user, email=email,
                     hashedpassword=hashedpassword, salt=salt,
                     commit=False)
    db.session.commit()
    return

#==================================================================
# Reset password
#     resetpassword -- shows form
#     newpassword   -- enter new password and code
#==================================================================
@app.route('/resetpassword', methods=['GET', 'POST'])
def resetpassword():
    self = 'resetpassword'
    form = ResetPasswordForm(request.form)

    if request.method == 'POST':
        # delete expired rows
        # add reset password row
        # email
        # display new password (same page? Then email needs to
        # land here.
        #
        # NOTE: User can enter either user or email.
        #return "1..."
        email = request.form.get('email', None)
        if email != None:
            db_util.delete_expired_resetpasswords()
            db_util.delete_resetpasswords(email=email)
            if form.validate():
                # form has checked that there is a user for the
                # given email.
                user = User.query.filter(User.email==email).first()
                user_id = user.id
                code = randstring()
                dtime = app.config['DTIME_FOR_REGISTRATION']
                db_util.add_resetpassword(user_id=user_id,
                                          code=code)
                html = render_template('resetpasswordcodeemail.html',
                           title=app.config['TITLE'],
                           page_title='Reset password',
                           user=user.user,
                           email=email,
                           code=code,
                           url=url_for('newpassword',
                                       user=user_id,
                                       email=email,
                                       code=code,
                                       _external=True),
                           DTIME_FOR_REGISTRATION=dtime,
                           form=form, # ??
                                   )
                sendemail(subject="%s reset password" % app.config['TITLE'],
                          body="email body",
                          recipients=[email],
                          html=html)
                return redirect(url_for('newpassword',
                                        user_id=user_id,
                                        code=None))
            else:
                flash('There is no user with that email.', 'error')
        else:
            flash('No email input', 'error')
    dtime = app.config['DTIME_FOR_REGISTRATION']
    return render_template('resetpassword.html',
                           title=app.config['TITLE'],
                           page_title='Reset password',
                           footer='This is the footer',
                           dtime=dtime,
                           action=self,
                           form=form,
                           )

@app.route('/newpassword', methods=['GET', 'POST'])
def newpassword(user_id=None):
    # Should user_id be included in ResetPassword
    form = NewPasswordForm(request.form)
    self = 'newpassword'

    if request.method == 'POST':
        source = request.form
    else:
        source = request.args
    user_id = source.get('user_id', None)
    code = source.get('code', None) # leave as blank (for email, will it with code)
    form.code.data = code
    dtime = app.config['DTIME_FOR_REGISTRATION']

    if request.method=='POST':
        if form.validate():
            code = request.form.get('code', None)
            password = request.form.get('password', None)
            Res = ResetPassword # shorthand
            res = Res.query.filter(Res.code==code).first()
            user = User.query.filter(User.id==res.user_id).first()
            salt = randstring()
            hashedpassword = hashfunc(password=password, salt=salt)
            user.hashedpassword = hashedpassword
            user.salt = salt
            db_util.delete_resetpasswords(email=user.email)
            db.session.commit()
            flash('Password changed successfully.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Error in resetting password.', 'error')
    return render_template('newpassword.html',
                           title=app.config['TITLE'],
                           user_id=user_id,
                           code=code,
                           page_title='Reset password',
                           footer='This is the footer',
                           dtime=dtime,
                           action=url_for(self),
                           form=form)

@app.route('/add_ai', methods=['GET', 'POST'])
@authenticate
def add_ai():
    self = 'add_ai'

    user = db_util.get_user_from_session(get_session_key())
    games = db_util.get_games()

    if request.method == 'POST':
        err = validate_ai()
        if err:
            flash(err, 'error')
            return redirect(request.url)

        file = request.files['file']

        db_util.add_ai(user=user,
                       game_id=request.form.get('game'),
                       name=request.form.get('name'),
                       description=request.form.get('description'),
                       ai_file_data=file)
        flash('AI uploaded successfully.', 'success')

    return render_template('add_ai.html',
                           title=app.config['TITLE'],
                           page_title='Add AI',
                           games=games,
                           footer='This is the footer',
                           action=url_for(self))


def validate_ai():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']

    # If user does not select file, browser also
    # submit a empty part without filename
    if file.filename == '':
        return 'No selected file'
    if not db_util.game_exists(game_id=int(request.form.get('game'))):
        return 'Invalid game ID.'
    return ''

@app.route("/ais", methods=['GET', 'POST'])
def ais():
    self = 'ais'
    if request.method == 'POST':
        searched = request.form.get('search')
        ais = AI.query.filter(AI.name.like("%{}%".format(searched)))
    else:
        ais = db_util.get_all_ais()

    for ai in ais: # 12/11/2024
        ai.stats = Stats.query.filter(Stats.AI_id==ai.id).first() # 12/11/2024, get ai stats data

    ais = [{'ai': ai, 'user': db_util.get_user(ai.User_id)} for ai in ais]

    return render_template('ais.html',
                           title=app.config['TITLE'],
                           page_title='Othello Ais',
                           action=url_for(self),
                           ais=ais,
                           footer='This is the footer')

@app.route("/ais/<int:ai_id>", methods=['GET'])
def ai(ai_id):
    ai = db_util.get_ai(ai_id=ai_id)

    owner = db_util.get_user(user_id=ai.User_id)
    if is_logged_in():
        user = db_util.get_user_from_session(get_session_key())
    else:
        user = None
    is_owner = (owner == user)

    ai.stats = Stats.query.filter(Stats.AI_id==ai.id).first() # 12/11/2024, get ai stats data
    ais = [ai]
    return render_template('ai.html',
                           title=app.config['TITLE'],
                           ai=ai,
                           ais=ais,
                           owner=owner,
                           is_owner=is_owner,
                           page_title="%s's Stats" % ai.name)



@app.route("/edit_ai/<int:ai_id>", methods=['GET', 'POST'])
@authenticate
def edit_ai(ai_id):
    ai = db_util.get_ai(ai_id=ai_id)

    owner = db_util.get_user(user_id=ai.User_id)
    user = db_util.get_user_from_session(get_session_key())
    games = db_util.get_games()

    if user != owner:
        flash('You must own this AI to edit it.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        file = request.files['file']
        if file.filename == '':
            file = None

        if not db_util.game_exists(game_id=int(request.form.get('game'))):
            flash('Invalid game ID.', 'error')
            return redirect(request.url)

        db_util.update_ai(old_ai=ai,
                          user=user,
                          name=request.form.get('name'),
                          description=request.form.get('description'),
                          game_id=request.form.get('game'),
                          ai_file_data=file)
        flash('AI updated successfully', 'success')

    ai.stats = Stats.query.filter(Stats.AI_id==ai.id).first() # 12/11/2024, get ai stats data
    return render_template('edit_ai.html',
                           title=app.config['TITLE'],
                           ai=ai,
                           games=games,
                           page_title="%s's Stats" % ai.name)

@app.route("/delete_ai/<int:ai_id>", methods=['GET'])
@authenticate
def delete_ai(ai_id):
    ai = db_util.get_ai(ai_id=ai_id)
    owner = db_util.get_user(user_id=ai.User_id)
    user = db_util.get_user_from_session(get_session_key())

    if user != owner:
        flash('You must own this AI to delete it.', 'error')
        return redirect(url_for('index'))

    db_util.delete_ai(ai)

    flash('AI Deleted successfully', 'success')
    return redirect(url_for('index'))

@app.route("/search", methods=['GET', 'POST'])
def search():
    reqform = request.form # shorthand
    searching = reqform.get('search', None) # should not be None
    if searching:
        ais = AI.query.filter(AI.name.like("%{}%".format(searching)))
        users = User.query.filter(User.user.like("%{}%".format(searching)))
    else:
        ais = db_util.get_all_ais()
        users = db_util.get_all_users()
    ai_u = []
    for ai in ais:
        ai_u.append((ai, db_util.get_user(ai.User_id)))

    return render_template('search.html',
                           title=app.config['TITLE'],
                           page_title='Search',
                           footer='This is the footer',
                           ais=ai_u,
                           users=users,
                           action=url_for('search'))

@app.route("/create_match", methods=['GET', 'POST'])
@authenticate
def create_match():
    self = 'create_match'

    games = db_util.get_games()
    AIs = db_util.get_all_ais()

    if request.method == 'POST':
        # try:
        board_size = int(request.form.get('board-size'))
        max_time_limit_ms = int(request.form.get('max-time-limit-ms'))
        # ADDED 2020/12/14: limit max time
        if board_size <= 6:
            if max_time_limit_ms > 150000:
                max_time_limit_ms = 150000
        elif board_size <= 8:
            if max_time_limit_ms > 180000:
                max_time_limit_ms = 180000
        if max_time_limit_ms > 180000:
            max_time_limit_ms = 180000

        Match_id = db_util.add_match(game_id=request.form.get('game'),
                                     board_size=board_size,
                                     max_time_limit_ms=max_time_limit_ms,
                                     player_one_id=request.form.get('player-one'),
                                     player_two_id=request.form.get('player-two'),
        )

        # 11/30/2018 - run the match
        # 12/14/2020 - DO NOT RUN MATCH. Do a long running process.
        #import os
        #os.system('python /home/ciss450othello/game_runner.py -1 -1')
        #return "Check your match now"

        #cmd = '{game_runner_path} {game_id} {match_id}'.format(
        #    game_runner_path=game_runner_path,
        #    game_id=request.form.get('game'),
        #    match_id=Match_id)
        #try:
        #    if running_locally:
        #        cmd += ' --local'
        #except NameError:
        #    cmd += ' --remote'
        #pid = subprocess.Popen(cmd.split()).pid
        #print("Spawned match with pid: %s" % pid)

        flash('Match created successfully. You can check its status in Matches.', 'success')
        return redirect(url_for('matches'))
        # except Exception as e:
        #     import traceback
        #     exc_type, exc_value, exc_traceback = sys.exc_info()
        #     print "*** print_tb:"
        #     traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
        #     print e
        #     flash("Something went wrong while running the match. Most likely one of the AIs doesn't follow get_move() specification. Contact admins.", 'error')
        #     return redirect(url_for('index'))
    import util
    return render_template('create_match.html',
                           title=app.config['TITLE'],
                           games=games,
                           AIs=AIs,
                           page_title="Creating a Match",
                           cpuusage=util.cpuusage(),)




# 2022/12/15 -- manually run matches. From create_match
@app.route("/ct", methods=['GET', 'POST'])
def create_tournament():

    #return "foobar"
    #self = 'create_tournament'

    board_size = 8
    max_time_limit_ms = 150000
    Match_id = db_util.add_match(game_id=1,
                                 board_size=board_size,
                                 max_time_limit_ms=max_time_limit_ms,
                                 player_one_id='150',
                                 player_two_id='163',
        )

    return "done ...%s" % Match_id




@app.route("/matches", methods=['GET'])
def matches():
    matches = db_util.get_all_matches()
    matches = matches[-100:]

    for match in matches: # 12/11/2024 Give matches the player objects
        match.Player_one = AI.query.filter_by(id=match.Player_one_id).first()
        match.Player_one.owner = User.query.filter_by(id=match.Player_one.User_id).first()
        match.Player_two = AI.query.filter_by(id=match.Player_two_id).first()
        match.Player_two.owner = User.query.filter_by(id=match.Player_two.User_id).first()


    return render_template('matches.html',
                           title=app.config['TITLE'],
                           matches=matches,
                           page_title="Othello Matches")

@app.route("/matches/<int:match_id>", methods=['GET'])
def match(match_id):
    match = Match.query.filter_by(id=match_id).one()
    if not match.result:
        flash("That match hasn't been played properly yet. You can't access it.", 'error')
        return redirect(request.referrer)

    game = Game.query.filter_by(id=match.Game_id).one()
    game_draw_script = ""
    with open(game.draw_script_path, "r") as f:
        game_draw_script = f.read()
    player_one = AI.query.filter_by(id=match.Player_one_id).one()
    player_two = AI.query.filter_by(id=match.Player_two_id).one()
    board_states = yaml.safe_load(match.board_states)
    verdict = yaml.safe_load(match.verdict)

    # Prettyprint for state output.
    for row in board_states:
        print(row)

    for i, t in enumerate(board_states):
        state_strs = []
        for row in t[1]:
            state_str = "    [" + ', '.join(['"%s"' % col for col in row]) + "]"
            state_strs.append(state_str)
        board_states[i][1] = "[\n" + ',\n'.join(state_strs) + "\n]"

    result_str = ""

    last_move_player = AI.query.filter_by(id=int(verdict["last_move_player"])).one()
    if verdict["conclusion"] == "normal":
        if verdict["result"] == "T":
            result_str = "It's a Tie!"
        else:
            winner = AI.query.filter_by(id=int(verdict["winner"])).one()
            result_str = "{name} won playing {color}".format(
                name=winner.name,
                color=verdict["winner_color"])
    elif verdict["conclusion"] == "timeout":
        result_str = "{name} playing {color} timed out!".format(
            name=last_move_player.name,
            color=verdict["last_move_color"])
    elif verdict["conclusion"] == "illegal":
        result_str = "{name} playing {color} made an illegal move!".format(
            name=last_move_player.name,
            color=verdict["last_move_color"])

    error = None
    if 'error' in verdict:
        error = verdict['error']
        error = json.loads(error)
        error = error.replace('\\n', ' <br> ')

    return render_template('match.html',
                           title=result_str,
                           player_one=player_one,
                           player_two=player_two,
                           match=match,
                           game=game,
                           result_str=result_str,
                           error=error,
                           board_states=board_states,
                           game_draw_script=game_draw_script,
                           footer='This is the footer')

@app.route("/game_draw/<int:game_id>")
def game_draw(game_id):
    game = Game.query.filter_by(id=game_id).one()
    return send_file(game.draw_script_path)



@app.route('/s', methods=['GET', 'POST'])
def s():
    users = ['YXJuIQgojosatoruoritadoriYGMWYRs', # added robert 2026/10/25
            ]
    print(">>>> running s()")
    user = request.args.get('user', None)
    if user in users:
        import os
        os.system('python /home/ciss450othello2/game_runner.py 1 0 > game_runner.py.out')
        return open('/home/ciss450othello2/game_runner.py.out', 'r').read()
    else:
        return "ERROR"
