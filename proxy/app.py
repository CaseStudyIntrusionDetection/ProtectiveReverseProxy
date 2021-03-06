import os
'''
os.environ['BLOCK_CRAWLING'] = 'false'
os.environ['BLOCK_TYPES'] = '' 
os.environ['ALLOW_TYPES'] = '' 
os.environ['APPROACH_USE'] = 'lda,nn' 
os.environ['APPROACH_CONNECTOR'] = 'or'
os.environ['ALLOW_AFTER_CAPTCHA'] = 'true'
'''

import random, string

from flask import Flask, request, make_response, render_template, session
from werkzeug.routing import Rule

import nginx
from request_data import RequestData
from request_check import RequestChecker
from captcha_handler import Captcha

# create flask
app = Flask(__name__)

# set up session handling
app.secret_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=50))
app.config['SESSION_COOKIE_NAME'] = "protection_session"

# initialize the prediction
checker = RequestChecker()
# no users until now, start with it 0
connection_id = 0

# check if we use a captcha
use_captcha = "ALLOW_AFTER_CAPTCHA" in os.environ and os.environ.get("ALLOW_AFTER_CAPTCHA") == "true"
if use_captcha:
	# create captcha handler
	captcha = Captcha()

# all request will be routed here by flask
@app.errorhandler(404)
def check_request(e):
	global connection_id

	# setup the session for this users
	session.permanent = True
	# assign a new connection id, if its an unknown user
	if not 'connection-id' in session:
		session['connection-id'] = connection_id
		connection_id += 1

	# create the request object
	data = RequestData(request, session['connection-id'])

	# check the request and respond
	if checker.is_safe(data):
		return nginx.approve()
	else:
		# display error template or captcha
		if use_captcha:
			return captcha.handle()
		else:
			return nginx.block()


