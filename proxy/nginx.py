from flask import make_response, render_template

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
	return render_template("blocked.html")