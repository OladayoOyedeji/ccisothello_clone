import random; random.seed()
import hashlib, string, re

from flask_mail import Mail, Message

from mysite import app

from flask import make_response
from functools import wraps, update_wrapper
from datetime import datetime

#==================================================================
# randstring
# - used for creating salt
#==================================================================
def randstring(length=app.config['RANDOM_LENGTH']):
    cs = list(string.ascii_letters + string.digits)
    random.shuffle(cs)
    return ''.join(cs[:length])

#==================================================================
# a hash function
#==================================================================
def hashfunc(password, salt):
    """ ERROR: get password is None -- check why """
    h = password
    for i in range(app.config['HASH_ROUNDS']):
        h += salt + str(i * i)
        h = hashlib.sha256(h.encode('utf-8')).hexdigest()
    return h

#=================================================================
# sendemail -- put this in a util module
#=================================================================
def sendemail(subject='ALEX',
              sender='ALEX',
              recipients=['yliow@ccis.edu'],
              body='[email body]',
              html='<b>[email html]</b>',
              filename=None,
              content_type='text/plain',
              fp=None,
              data=None):
    """
    NOTE: At most 1 attachment for now.
    NOTE: Global app passed in.
    """
    print("sendemail ... 0")
    if app.config['DEBUG']:
        recipients = [app.config['AUTHOR_EMAIL']]
    print("sendemail ... 1")
    mail = Mail(app)
    print("sendemail ... 2")
    msg = Message(subject, sender=sender, recipients=recipients)
    print("sendemail ... 3")
    msg.body = body
    print("sendemail ... 4")
    msg.html = html
    print("sendemail ... 5")
    if data != None:
        print("sendemail ... 6")
        # CASE: attachment data is given
        msg.attach(filename=filename,
                   content_type=content_type, data=data)
        print("sendemail ... 7")
    else:
        print("sendemail ... 8")
        # Case: data is not given
        if fp != None:
            print("sendemail ... 9")
            # CASE: file pointer passed in
            msg.attach(filename=filename,
                       content_type=content_type, data=fp.read())
            print("sendemail ... 10")
        elif filename != None:
            print("sendemail ... 11")
            # CASE: filename is given
            with app.open_resource(filename) as fp:
                msg.attach(filename=filename,
                           content_type=content_type,
                           data=fp.read())
            print("sendemail ... 12")
    print("sendemail ... 13")
    with app.app_context():
        print("sendemail ... 14")
        mail.send(msg)
        print("sendemail ... 15")

    # This email version uses gmail_in_one_file
    #print("using gmail_in_one_file ... 0")
    #import gmail_in_one_file
    #gmail_in_one_file.mail(to=recipients[0],
    #                        from_=sender,
    #                        subject=subject,
    #                        text=body,
    #                        html=html,
    #                        verbose=True)
    #print("using gmail_in_one_file ... 1")

def extract_emails(email_str):
    p = re.compile('([a-zA-Z0-9\.]+\@[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)+)')
    emails = p.findall(email_str)
    emails = [x[0] for x in emails]
    return emails

#==============================================================================
# CPU usage
#==============================================================================
def cpuusage():

    # ADDED 2024/12/02 TEMPORARILY BECAUSE requests MODULE NOT FOUND
    return "[NONE] of [NONE] ([NONE]) used. Daily CPU usage resets at 7AM."

    TOTAL = 4000.0
    RESET_TIME = "7AM"

    #from urlparse import urljoin
    import requests

    api_token = "946d45c18b117c5acc8420747e425789ba000896"
    username = "ciss450othello"
    pythonanywhere_host = "www.pythonanywhere.com"

    api_base = "https://{pythonanywhere_host}/api/v0/user/{username}/".format(
                pythonanywhere_host=pythonanywhere_host,
                username=username,
                )
    resp = requests.get(
        api_base + "cpu/",
        headers={"Authorization": "Token {api_token}".format(api_token=api_token)}
    )

    usage_seconds = round(float(resp.json()["daily_cpu_total_usage_seconds"]), 2)
    percentage = round(usage_seconds/TOTAL * 100, 2)
    return "%ss of %ss (%s%%) used. Daily CPU usage resets at %s." % (usage_seconds, TOTAL, percentage, RESET_TIME)
