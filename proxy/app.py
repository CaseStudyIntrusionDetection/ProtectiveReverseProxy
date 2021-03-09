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
from request_log import RequestLogger

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

# check if we use request logger
do_request_logging = "LOG_REQUESTS" in os.environ and os.environ.get("LOG_REQUESTS") in ["all", "attack"]
if do_request_logging:
	logger = RequestLogger()

# all request will be routed here by flask
@app.errorhandler(404)
def check_request(e):
	global connection_id

	try:
		# setup the session for this users
		session.permanent = True
		# assign a new connection id, if its an unknown user
		if not 'connection-id' in session:
			session['connection-id'] = connection_id
			connection_id += 1

		# create the request object
		data = RequestData(request, session['connection-id'])

		# check the request and respond
		if use_captcha:
			# authenticated by captcha?
			if captcha.is_captcha_safe():
				is_safe = None
				response = nginx.approve()
			# post values to solve captcha send?
			elif captcha.is_captcha_post():
				is_safe = None
				response = captcha.handle()
			# check request
			elif checker.is_safe(data):
				is_safe = True
				response = nginx.approve()
			# show captcha
			else:
				is_safe = False
				response = captcha.handle()
		else:
			if checker.is_safe(data):
				is_safe = True
				response = nginx.approve()
			else:
				is_safe = False
				response = nginx.block()

		# call logging if active
		if do_request_logging:
			logger.log(data, is_safe, captcha.is_captcha_safe() if use_captcha else None)

		return response
		
	except:
		# block everything which caused any type of error
		return nginx.block()

