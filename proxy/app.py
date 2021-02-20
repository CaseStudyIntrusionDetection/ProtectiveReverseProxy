import random, string

from flask import Flask, request, make_response, render_template, session
from werkzeug.routing import Rule

from request_data import RequestData
from request_check import RequestChecker

app = Flask(__name__)

app.secret_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=50))
app.config['SESSION_COOKIE_NAME'] = "protection_session"

checker = RequestChecker()
connection_id = 0

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
		return render_template("blocked.html")


