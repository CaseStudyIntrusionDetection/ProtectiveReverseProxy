import os, json

from log import Logging

from src.models.predict_model_lda import LDAPredictor

class RequestChecker():

	MODELS_DIR = "/protection/model/"

	def __init__(self):
		if not os.path.isdir(RequestChecker.MODELS_DIR) or not os.path.isfile(RequestChecker.MODELS_DIR + "/index.json"):
			Logging.log("Missing Model!", Logging.LEVEL_ERROR)
			exit()

		self.models = json.load(open(RequestChecker.MODELS_DIR + "/index.json", 'r'))
		if 'lda' not in self.models or 'nn' not in self.models or 'name' not in self.models:
			Logging.log("Invalid Model Index!", Logging.LEVEL_ERROR)
			exit()

		Logging.log("Found Model " + self.models['name'], Logging.LEVEL_INFO)

		self.lda = LDAPredictor(self.models['lda'], RequestChecker.MODELS_DIR)

	def is_save(self, request_data):

		is_attack, lda_predictions = self.lda.predict(request_data)

		print(is_attack, lda_predictions)
		
		return not is_attack 