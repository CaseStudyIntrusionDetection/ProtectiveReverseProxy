
import time, os, atexit, json

class RequestLogger():
	"""
		This class handles the logging of the request in the format used by the IDS.
		The logs should be used to learn better models later.
	"""

	LOGPATH = "/proxy/logs/"
	
	def __init__(self):
		"""
			Open a new logfile and register a listener to close file on python shutdown
		"""
		filename = RequestLogger.LOGPATH + "/requests_"+ time.strftime( "%Y-%m-%d_%H-%M-%S" ) + ".json"

		self.logfile = open(filename, "w+")
		self.first_entry = True

		self.log_all = "LOG_REQUESTS" in os.environ and os.environ.get("LOG_REQUESTS") == "all"

		atexit.register(self.end_json)


	def log(self, request_data, is_safe, captcha):
		"""
			Log a request in our specified format. We append the given request by
			another property containing the status whether the request was assumed
			safe or not by the system. Furthermore, we track whether the captcha was 
			solved successfully.
		
			Args:
				request_data (RequestData): RequestData object holding the information
				about the received request.
				is_safe (bool): Indicates whether the IDS assumes the request to be safe.
				captcha (bool): Indicates whether the captcha has been solved successfully.
		"""
		if self.log_all or not is_safe:
			data = request_data.create_dict()
			data['prp'] = {
				'assumed_safe' : 'unknown' if is_safe == None else is_safe,
				'captcha_solved' : 'unknown' if captcha == None else captcha 
			}
			self.append_json(data)

	def append_json(self, logentry):
		"""Appends a given JSON object to the log.
			Args:
				logentry (dict): The JSON object to append.
		"""
		if self.first_entry:
			string = '[\n'
			self.first_entry = False
		else:
			string = ",\n"
		
		string += json.dumps([logentry], indent=4, sort_keys=False)[2:-2] # for indentation
		self.logfile.write(string)
		self.logfile.flush()

	def end_json(self):
		"""
			Finishes the logfile with the closing array bracket.
		"""
		self.logfile.write('\n]')
		self.logfile.close()
	
		
		