from flask import request, make_response, render_template, send_file

def approve():
	"""
		Approves the received request.
	"""
	# X-Accel Header
	res = make_response("Request approved!")
	res.headers['X-Accel-Redirect'] = '@protected'
	return res

def block():
	"""
		Blocks the received request.
	"""

	# most webrowsers query for a favicon.ico on access, we only want to show our then
	if "favicon.ico" in request.full_path:
		return send_file( '/proxy/templates/favicon.ico')
	else:
		return render_template("blocked.html")