import os, json

from log import Logging

from src.models.predict_model_lda import LDAPredictor
from src.models.predict_model_nn import NNPredictor

class RequestChecker():

	MODELS_DIR = "/protection/model/"

	def __init__(self):
		if not os.path.isdir(RequestChecker.MODELS_DIR) or not os.path.isfile(RequestChecker.MODELS_DIR + "index.json"):
			Logging.log("Missing Model!", Logging.LEVEL_ERROR)
			exit()

		self.models = json.load(open(RequestChecker.MODELS_DIR + "index.json", 'r'))
		if 'lda' not in self.models or 'name' not in self.models or 'nn-crawl' not in self.models or 'nn-attack' not in self.models  or 'nn-types' not in self.models:
			Logging.log("Invalid Model Index!", Logging.LEVEL_ERROR)
			exit()

		Logging.log("Found Model " + self.models['name'], Logging.LEVEL_INFO)

		self.lda = LDAPredictor(self.models['lda'], RequestChecker.MODELS_DIR)
		if os.environ.get("BLOCK_CRAWLING") == "true":
			self.nn = NNPredictor(self.models['nn-crawl'], RequestChecker.MODELS_DIR)
		else:
			self.nn = NNPredictor(self.models['nn-attack'], RequestChecker.MODELS_DIR)

		if "BLOCK_TYPES" in os.environ or "ALLOW_TYPES" in os.environ:
			self.nn_types = NNPredictor(self.models['nn-types'], RequestChecker.MODELS_DIR)

	def is_save(self, request_data):

		lda_is_attack, lda_predictions = self.lda.predict(request_data)
		print(lda_is_attack, lda_predictions)

		nn_is_attack, nn_predictions = self.nn.predict(request_data)
		print(nn_is_attack, nn_predictions)

		Logging.log( json.dumps( { 'nn' : (nn_is_attack, nn_predictions), 'lda' : (lda_is_attack, lda_predictions)}) , Logging.LEVEL_ERROR )
		
		return not lda_is_attack or not nn_is_attack