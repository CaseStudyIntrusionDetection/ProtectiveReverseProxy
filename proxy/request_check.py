class RequestChecker():

	def __init__(self):
		pass

	def is_save(self, request_data):

		request_data.print()

		l = open("/tmp/r.log", "a")
		l.write(request_data.json())
		l.close()

		return True 
		# Here we have to connect to the TM and NN an check by the given data!
			
