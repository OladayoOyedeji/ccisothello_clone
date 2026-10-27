import string

from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, PasswordField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length

from mysite import app
from mysite import db
from .models import User, Registration, ResetPassword

#======================================================
# Custom validators
#======================================================
from wtforms.validators import ValidationError

#================================================================
# The following checks that a value does not occur in the  field
# for a table. For instance when adding a user, we need to check
# that it does not exists in the User table.
#================================================================
class NotExistsTableField(object):
    """ Check that a given value does not exists in Table.Field """
    def __init__(self,
                 model=User,
                 field=User.email,
                 message=u'An account exists with the same email.'):
        self.model = model
        self.field = field
        self.message = message

    def __call__(self, form, field):
        if self.model.query.filter(self.field == field.data).first():
            raise ValidationError(self.message)

class NotExistsUserUser(NotExistsTableField):
    # Checks that a value does not exists in User.usr
    def __init__(self):
        NotExistsTableField.__init__(self,
                                     model=User,
                                     field=User.user,
                                     message=u'This user has already been taken.')

class NotExistsUserEmail(NotExistsTableField):
    # Checks that a value does not exists in User.email
    def __init__(self):
        NotExistsTableField.__init__(self,
                                     model=User,
                                     field=User.email,
                                     message=u'An account exists with the same email.')

class NotExistsRegistrationUser(NotExistsTableField):
    # Checks that a value does not exists in Registration.user
    def __init__(self):
        NotExistsTableField.__init__(self,
                                     model=Registration,
                                     field=Registration.user,
                                     message=u'The user has already been registered.')

class NotExistsRegistrationEmail(NotExistsTableField):
    # Checks that a value does not exists in Registration.email
    def __init__(self):
        NotExistsTableField.__init__(self,
                                     model=Registration,
                                     field=Registration.email,
                                     message=u'Someone with the same email has registered.')



#================================================================
# The following checks that a value does occur in the  field
# for a table. For instance when doign a password reset, the
# email supplied by the user must correspond with a row in the
# User table.
#================================================================
class ExistsTableField(object):
    """ Check that a given value exists in Table.Field """
    def __init__(self,
                 model=User,
                 field=User.email,
                 message=u'There is no user with the given email.'):
        self.model = model
        self.field = field
        self.message = message
    def __call__(self, form, field):
        if self.model.query.filter(self.field == field.data).first() == None:
            raise ValidationError(self.message)

ExistsUserEmail = ExistsTableField

class ExistsResetPasswordCode(ExistsTableField):
    def __init__(self,
                 model=ResetPassword,
                 field=ResetPassword.code,
                 message=u'The password reset code cannot be found.'):
        ExistsTableField.__init__(self, model=model, field=field, message=message)

#================================================================
# Character set validators
# Maybe have a regex version too.
#================================================================
class CharsValidator(object):
    def __init__(self,
                 chars=string.ascii_letters,
                 message='Use a-z, A-Z, 0-9 and . for user.'):
        self.chars = chars
        self.message = message
    def __call__(self, form, field):
        for c in field.data:
            if c not in self.chars:
                raise ValidationError(self.message)

class UserCharsValidator(CharsValidator):
    def __init__(self,
                 chars=app.config['USER_CHARS'],
                 message='Use a-z, A-Z, 0-9 and . (period).'):
        CharsValidator.__init__(self,
                                chars=chars,
                                message=message)

#================================================================
# Substrings validator
# To check that a field has at least one substring from given
# list.
#================================================================
class SubstringValidator(object):
    def __init__(self,
                 substrings=app.config['EMAIL_SUBSTRINGS'],
                 message=None):
        self.substrings = substrings
        if message==None:
            x = ' or '.join(substrings)
            message = 'Email must end with %s' % x
        self.message = message
    def __call__(self, form, field):
        pass

EmailSubstringValidator = SubstringValidator

#================================================================
# Required fields
#================================================================
class Reqd(DataRequired):
    # Shorten the message
    def __init__(self):
        DataRequired.__init__(self, message='Required.')

#================================================================
# Shorthand for length checks
#================================================================
class Length_(Length):
    def __init__(self, min, max):
        Length.__init__(self,
                        min=min, max=max,
                        message='Length must be %s to %s.' \
                        % (min, max))

class UserLength(Length_):
    def __init__(self):
        Length_.__init__(self,
                         min=app.config['USER_MIN_LENGTH'],
                         max=app.config['USER_LENGTH'])

class PasswordLength(Length_):
    def __init__(self):
        Length_.__init__(self,
                         min=app.config['PASSWORD_MIN_LENGTH'],
                         max=app.config['PASSWORD_MAX_LENGTH'])

class EmailLength(Length_):
    def __init__(self):
        Length_.__init__(self,
                         min=4,
                         max=app.config['EMAIL_LENGTH'])

#================================================================
# Check that password is sufficiently secure.
# ADD MORE?
#================================================================
class PasswordHackable:
    def __init__(self):
        self.message = "Must contain at least 3 of: lowercase, uppercase, digits, punctuations."
    def __call__(self, form, field):
        lowercase = 0; uppercase = 0; digits = 0
        punctuations = 0
        others = 0 # ??
        for c in field.data:
            if c.islower():
                lowercase = 1
            elif c.isupper():
                uppercase = 1
            elif c.isdigit():
                digits = 1
            elif c in string.punctuation:
                punctuations = 1
            else:
                others = 1 # ??
        if lowercase + uppercase + digits + punctuations <= 2:
            raise ValidationError(self.message)

#================================================================
# Forms
#================================================================

class LoginForm(FlaskForm):
    user = StringField('user', validators=[Reqd(),
                                           UserLength(),
                                           UserCharsValidator(),
                                       ])
    password = PasswordField('password',
                             validators=[Reqd(),
                                         PasswordLength()])
    # Need to add password authentication ???
    remember_me = BooleanField('remember me', default=False)

class RegistrationForm(FlaskForm):
    user = StringField('user', validators=[Reqd(),
                                           UserLength(),
                                           UserCharsValidator(),
                                           NotExistsUserUser(),
                                           NotExistsRegistrationUser(),
                                       ])
    password = PasswordField('password',
                             validators=[Reqd(),
                                         PasswordLength(),
                                         PasswordHackable()])
    confirm_password = PasswordField('reenter password',
                                     validators=[Reqd(),
                                                 PasswordLength(),
                                                 EqualTo('password',
                                                         message='Passwords must match.')])
    email = StringField('email',
                        validators=[Reqd(),
                                    Email(),
                                    EmailLength(),
                                    NotExistsUserEmail(),
                                    NotExistsRegistrationEmail(),
                                    EmailSubstringValidator(),
                                ])

class ResetPasswordForm(FlaskForm):
    """ This is to get password reset code """
    email = StringField('email', validators=[Reqd(),
                                             ExistsUserEmail(),
                                             EmailSubstringValidator(),
                                         ])


class NewPasswordForm(FlaskForm):
    """ To enter new password """

    """
    user = StringField('user', validators=[Reqd(),
                                           UserLength(),
                                           UserCharsValidator(),
                                           ])
    email = StringField('email', validators=[DataRequired()])
    """

    password = PasswordField('password',
                             validators=[Reqd(),
                                         PasswordLength(),
                                         PasswordHackable()])
    confirm_password = PasswordField('reenter password',
                                     validators=[Reqd(),
                                                 PasswordLength(),
                                                 EqualTo('password', message='Passwords must match.')])
    code = StringField('code', validators=[Reqd(),
                                           ExistsResetPasswordCode()])


class RegistrationCodeForm(FlaskForm):
    user = StringField('user', validators=[Reqd()])
    email = StringField('email', validators=[Reqd()])
    code = StringField('code', validators=[Reqd()])

class AddToSectionForm(FlaskForm):
    section = SelectField('section', choices=[], validators=[Reqd()])
    emails = TextAreaField('emails', validators=[Reqd()])
