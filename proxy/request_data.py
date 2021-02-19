import json
import time 
import hashlib
import re

class RequestData():

	def __init__(self, request):

		print(vars(request))

		return

		if request.method == 'POST':
			post_data = request.post()
			data['post_data'] = dict(post_data)
		else:
			post_data = ""
		
		remote_ip, _ = request.transport.get_extra_info('peername')

		self.log(request.method, request.rel_url, request.version, request.headers, content,
			post_data, headers, remote_ip, status_code)

	def log(self, method, uri, protocol, header, response_body, emulator, request_body, response_header, remote_ip, status_code):
		"""Logs a request.

			Args:
				method (str): The request method (GET, POST, ...).
				uri (str): The requested URI.
				protocol (HttpVersion): The HTTP protocol version.
				header (dict): The HTTP headers.
				response_body (str): The body of the response.
				emulator (str): The emulator used by Tanner.
				request_body (dict): The body of the request (e.g. for POST requests).
				response_header (dict): The headers of the response.
				cur_sess_id (str): The id of the current session.
				prev_sess_id (str): The id of the previous session.
				remote_ip (str): The ip address of the remote party that sent the request.
				status_code (str): The status code of the response.
		"""

		uri_str = str(uri)

		protocol_str = 'HTTP/' + str(protocol.major) + '.' + str(protocol.minor)

		header_dict = {}
		for name, value in header.items():
			header_dict[name] = value
		self.clearSessionCookie(header_dict)

		response_header_dict = {}
		for name, value in response_header.items():
			response_header_dict[name] = value
		self.clearSessionCookie(response_header_dict)

		response_body_str = str(response_body)

		if request_body != "":
			request_body_dict = {}
			for name, value in request_body.items():
				request_body_dict[name] = value
		else:
			request_body_dict = ""

		logentry = {
			"id" : 0,
			"timestamp" : int(time.time()),
			"connection-id" : 0,
			"request" : {
				"method": method,
				"uri": uri_str,
				"protocol": protocol_str,
				"body": request_body_dict
			},
			"header" : header_dict,
			"sender" : {
				"ip" : remote_ip
			},
			"honeypot" : {
				"used-emulator" : emulator,
				"response-hash" : hashlib.sha512(response_body_str.encode('utf-8')).hexdigest(),
				"response-size" : len(response_body_str),
				"response-status-code" : status_code , 
				"response-header" : response_header_dict
			}
		}

		print(json.dumps(logentry, indent=4, sort_keys=False))

	def clearSessionCookie(self, header):
		"""Removes the Tanner session cookie from a given HTTP header.

			Args:
				header (dict): Dictionary containing the HTTP headers.
		"""
		field = ''
		if 'Set-Cookie' in header:
			field = 'Set-Cookie'
		elif 'Cookie' in header:
			field = 'Cookie'

		if field != '': # remove tanner session cookie
			header[field] = re.sub(r'sess_uuid=[0-9a-f\-]+(; )?', '', header[field] )
			if header[field] == '':
				del header[field]