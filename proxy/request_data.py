import json
import time 
import hashlib
import re

class RequestData():

	current_id = 0

	def __init__(self, request, connection_id):
		self.id = RequestData.current_id
		RequestData.current_id += 1

		self.connection_id = connection_id

		self.url = str(request.full_path)
		self.protocol = str(request.environ['SERVER_PROTOCOL'])
		self.remote_ip = str(request.environ['REMOTE_ADDR'])

		self.method = str(request.method)
		self.header_dict = dict(request.headers)
		self.time = int(time.time())

		if self.method == "POST":
			self.body = {}
			for name, value in request.form.items():
				self.body[str(name)] = str(value)
		else:
			self.body = ""

		self.clear_session_cookie(self.header_dict)

	def print(self):
		print(self.json())

	def json(self):
		return json.dumps(self.create_dict(), indent=2, sort_keys=False)

	def create_dict(self):
		return {
			"id" : self.id,
			"timestamp" : self.time,
			"connection-id" : self.connection_id,
			"request" : {
				"method": self.method,
				"uri": self.url,
				"protocol": self.protocol,
				"body": self.body
			},
			"header" : self.header_dict,
			"sender" : {
				"ip" : self.remote_ip
			},
			"honeypot" : {
				"used-emulator" : "",
				"response-hash" : "",
				"response-size" : 0,
				"response-status-code" : "", 
				"response-header" : {}
			}
		}

	def clear_session_cookie(self, header):
		"""Removes the systems session cookie from a given HTTP header.

			Args:
				header (dict): Dictionary containing the HTTP headers.
		"""
		field = ''
		if 'Set-Cookie' in header:
			field = 'Set-Cookie'
		elif 'Cookie' in header:
			field = 'Cookie'

		if field != '': # remove tanner session cookie
			header[field] = re.sub(r'protection_session=[0-9A-Za-z\_\.\-]+(; )?', '', header[field] )
			if header[field] == '':
				del header[field]