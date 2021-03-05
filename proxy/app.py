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

from request_data import RequestData
from request_check import RequestChecker
from captcha_handler import Captcha

app = Flask(__name__)

app.secret_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=50))
app.config['SESSION_COOKIE_NAME'] = "protection_session"

checker = RequestChecker()
connection_id = 0

use_captcha = "ALLOW_AFTER_CAPTCHA" in os.environ and os.environ.get("ALLOW_AFTER_CAPTCHA") == "true"
if use_captcha:
	captcha = Captcha()

@app.errorhandler(404)
def check_request(e):
	global connection_id

	session.permanent = True
	if not 'connection-id' in session:
		session['connection-id'] = connection_id
		connection_id += 1

	data = RequestData(request, session['connection-id'])

	if checker.is_save(data):
		# X-Accel Header
		res = make_response("Request approved!")
		res.headers['X-Accel-Redirect'] = '@protected'
		return res
	else:
		# display error template
		if use_captcha:
			return captcha.handle()
		else:
			return render_template("blocked.html")


