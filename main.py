from requests_oauthlib import OAuth2Session
import json, csv, os, requests, re
from time import time
from flask import Flask, request, url_for, redirect, render_template, Session, flash, get_flashed_messages
from flask_sslify import SSLify

app = Flask(__name__)
app.secret_key = os.urandom(24)
session = Session()

# Credentials you get from registering a new application
client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")
#redirect_uri = "https://nimpf.akimbo.com"
# OAuth endpoints given in the Google API documentation
authorization_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
token_url = "https://www.googleapis.com/oauth2/v4/token"
refresh_url = token_url
scope = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
    "https://www.googleapis.com/auth/gmail.settings.basic",
    "https://www.googleapis.com/auth/gmail.modify",
]

def refresh_token():
    extra = {
        'client_id': client_id,
        'client_secret': client_secret,
    }
    session['token'] = google.refresh_token(refresh_url, **extra)
    session.modified = True
    print('token updated!')

def remove_label(message_id):
    google = OAuth2Session(client_id, token=session['token'])
    if session['token']['expires_at'] < time()+10:
        refresh_token()
    params = {"removeLabelIds": ['CATEGORY_PROMOTIONS'], "addLabelIds": ['CATEGORY_PERSONAL']}
    headers = {"Content-Type": "application/json"}
    r = google.post("https://www.googleapis.com/gmail/v1/users/me/messages/{}/modify".format(message_id), data=json.dumps(params), headers=headers)
    return r.text

def create_filter(whitelist):
    google = OAuth2Session(client_id, token=session['token'])
    if session['token']['expires_at'] < time()+10:
        refresh_token()
    headers = {"Content-Type": "application/json"}
    params = {
        "criteria": {
            "from": " OR ".join(whitelist)
        },
        "action": {
            "removeLabelIds": ["SPAM"],
            "addLabelIds": ["CATEGORY_PERSONAL"]
        }
    }
    r = google.post("https://www.googleapis.com/gmail/v1/users/me/settings/filters", data=json.dumps(params), headers=headers)
    return r.text

whitelist = ['sethgodin.com', 'adobe.com']

@app.route("/")
def index():
    if 'logged_in' in session.keys() and session['logged_in'] == True:
        google = OAuth2Session(client_id, token=session['token'])
        if session['token']['expires_at'] < time()+10:
            refresh_token()
        r = google.get('https://www.googleapis.com/oauth2/v1/userinfo')
        #print(r.json())
        data = r.json()
        email, img, name = data['email'], data['picture'], data['name']
        return render_template('index.html', email=email, img=img, name=name)
    else:
        redirect_response = request.url
        if request.args.get('state') not in ('', None):
            google = OAuth2Session(client_id, scope=scope, redirect_uri=session['redirect_uri'], state=session['state'])
            # Fetch the access token
            token = google.fetch_token(token_url, client_secret=client_secret,
                    authorization_response=redirect_response)
            session['token'] = token
            session.modified = True

            # Fetch a protected resource, i.e. user profile
            r = google.get('https://www.googleapis.com/oauth2/v1/userinfo')
            session['logged_in'] = True
            session.modified = True
            return redirect('/')
        else:
            return redirect('/login')



@app.route("/login")
def login():
    global redirect_uri 
    session['redirect_uri'] = request.url_root.rstrip('/login')
    google = OAuth2Session(client_id, scope=scope, redirect_uri=session['redirect_uri'])

    # Redirect user to Google for authorization
    authorization_url, state = google.authorization_url(authorization_base_url,
        # offline for refresh token
        # force to always make user click authorize
        access_type="offline", prompt="select_account")
    session['state'] = state
    session.modified = True
    return redirect(authorization_url)


@app.route('/process')
def process():
    google = OAuth2Session(client_id, token=session['token'])
    if session['token']['expires_at'] < time()+10:
        refresh_token()
    r = google.get("https://www.googleapis.com/gmail/v1/users/me/messages?labelIds=CATEGORY_PROMOTIONS")
    promo_messages = r.json()['messages']
    for i, row in enumerate(promo_messages):
        r = google.get("https://www.googleapis.com/gmail/v1/users/me/messages/{}".format(row['id']))
        message = r.json()
        for val in message['payload']['headers']:
            if val['name'] == 'From':
                sender = val['value']
                string = re.compile("@(.+)>")
                match = re.search(string, sender)
                domain = match.group(1)
                for whitelisted_domain in whitelist:
                    if whitelisted_domain in domain: # gracefully handle subdomains
                        print(domain, 'removed')
                        remove_label(row['id'])

    flash('Promo folder cleaned')
    return redirect(url_for('index'))

@app.route('/process2')
def process2():
    print(create_filter(whitelist))
    flash('Filter made')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(ssl_context='adhoc')