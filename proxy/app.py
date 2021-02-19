from flask import Flask, request, make_response, render_template
from werkzeug.routing import Rule

from request_data import RequestData
from request_check import RequestChecker

app = Flask(__name__)

checker = RequestChecker()

@app.errorhandler(404)
def check_request(e):

	data = RequestData(request)
	if checker.is_save(data):
		# X-Accel Header
		res = make_response("Request approved!")
		res.headers['X-Accel-Redirect'] = '@protected'
		return res
	else:
		# display error template
		return render_template("blocked.html")


