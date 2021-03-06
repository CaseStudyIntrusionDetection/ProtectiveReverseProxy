from datetime import datetime

class Logging():
	"""
		Logging class

		Will write into "/tmp/prp.log" and also log to STDOUT
	"""

	messages = []
	logfile = open("/tmp/prp.log", "a+")

	LEVEL_ERROR = "ERROR"
	LEVEL_WARN = "WARN"
	LEVEL_INFO = "INFO"

	@staticmethod
	def log(message, level=""):
		"""
			Logs a message
			Args:
				message (string): The message to log
				level (one of LEVEL_ERROR, LEVEL_WARN, LEVEL_INFO), default to LEVEL_INFO
		"""
		if level == "":
			level = Logging.LEVEL_INFO
		
		entry = (level, datetime.now().strftime("%d.%m.%Y %H:%M:%S"), message)
		print(entry)
		Logging.messages.append(entry)
		Logging.write(entry)

	@staticmethod
	def get_last(n=5):
		"""
			Returns the last n log messages.

			Args:
				n (int): The number of last messages, defaults to 5.
		"""
		return Logging.messages[-k:]

	@staticmethod
	def write(entry):
		"""
			Write the logfile (appends)
			=> Only errors of LEVEL_ERROR will be written to file!
		"""
		if entry[0] == Logging.LEVEL_ERROR:
			Logging.logfile.write(entry[0] + " -- " + entry[1] + "\n" + entry[2] + "\n\n" )
			Logging.logfile.flush()
		