from requests_oauthlib import OAuth2Session
import json, csv, os, requests, re
from datetime import datetime, timedelta
from time import time
from flask import Flask, request, url_for, redirect, render_template, session, flash, get_flashed_messages, abort
from flask_sslify import SSLify
from config import *
from user import User

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
app.permanent_session_lifetime = timedelta(days=365)

@app.route("/profile")
def profile():
    print("on / {}".format(session))
    if 'logged_in' in session.keys() and session['logged_in'] == True:
        u = User(session['user'])
        #u.get_by_email(u.email()) # refresh data
        data = u.user_info()
        session['user'] = u.json() # save any updates to session cookie
        session.modified = True
        email, img, name = data['email'], data['picture'], data['name']
        return render_template('profile.html', email=email, img=img, name=name)
    else:
        redirect_response = request.url
        if request.args.get('state') not in ('', None):
            google = OAuth2Session(client_id, scope=scope, redirect_uri=session['redirect_uri'], state=session['state'])
            # Fetch the access token
            token = google.fetch_token(token_url, client_secret=client_secret,
                    authorization_response=redirect_response)
            # Fetch a protected resource, i.e. user profile
            r = google.get('https://www.googleapis.com/oauth2/v1/userinfo')
            data = r.json()
            email, name = data['email'], data['name']
            u = User()
            if u.get_by_email(email) is None:
                print('creating new user')
                if u.create(email, name) == False:
                    print('failed to create new user')
                    abort(500)
            u.set_token(token)

            session['user'] = u.json()
            session['logged_in'] = True
            session.modified = True
            return redirect('/process')
        else:
            return redirect('/login')

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/login")
def login():
    print("on /login {}".format(session))
    session['redirect_uri'] = request.url_root.rstrip('/login') + '/profile'
    session.modified = True
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
    print("on /process {}".format(session))
    u = User(session['user'])
    if u.filter_made() == True:
        flash('Your inbox filter has already been created', 'info')
    else:
        """
        result1 = u.clear_promo_folder()
        if result1 == True:
            result2 = u.make_filter()
            if result2 == True:
                flash('Success', 'success')
            else:
                flash('Error making filter', 'danger')
        else:
            flash('Error cleaning promo folder', 'danger')
        """
        #job = q.enqueue(process_user, u.json())
        job_id = u.make_filter()
        flash('Success', 'success')
    session['user'] = u.json() 
    session.modified = True
    return redirect(url_for('profile'))


@app.route('/clear')
def clear():
    print("on /clear {}".format(session))
    session.clear()
    session.modified = True
    return redirect('/')

@app.route('/test')
def test():
    print("on /test {}".format(session))
    print(query())
    job = q.enqueue(query)
    return redirect('/')


if __name__ == '__main__':
    app.run(ssl_context='adhoc')

