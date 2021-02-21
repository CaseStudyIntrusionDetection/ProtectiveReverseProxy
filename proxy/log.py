from datetime import datetime

class Logging():

	messages = []
	logfile = open("/tmp/prp.log", "a+")

	LEVEL_ERROR = "ERROR"
	LEVEL_WARN = "WARN"
	LEVEL_INFO = "INFO"

	@staticmethod
	def log(message, level=""):
		if level == "":
			level = Logging.LEVEL_INFO
		
		entry = (level, datetime.now().strftime("%d.%m.%Y %H:%M:%S"), message)
		print(entry)
		Logging.messages.append(entry)
		Logging.write(entry)

	@staticmethod
	def get_last(n=5):
		return Logging.messages[-k:]

	@staticmethod
	def write(entry):
		if entry[0] == Logging.LEVEL_ERROR:
			Logging.logfile.write(entry[0] + " -- " + entry[1] + "\n" + entry[2] + "\n\n" )
			Logging.logfile.flush()
		