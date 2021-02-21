import json
import os

class NNPredictor():

	BLOCK_CRAWLING = os.environ.get("BLOCK_CRAWLING") == "true"

	def __init__(self, index, models_dir):
		pass

	
	def predict(self, request_data):
		data = request_data.create_dict()
		

		is_attack = False
		predicted = [['rfi', 0.05]]

		return is_attack, predicted[:5]

	