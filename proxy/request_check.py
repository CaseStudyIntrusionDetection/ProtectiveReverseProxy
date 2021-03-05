import os, json

from log import Logging
from attack_types import TypeHandler
from mail_wrapper import Notifications

from src.models.predict_model_lda import LDAPredictor
from src.models.predict_model_nn import NNPredictor

class RequestChecker():

	MODELS_DIR = "/protection/model/"

	def __init__(self):
		# check models directory and index
		if not os.path.isdir(RequestChecker.MODELS_DIR) or not os.path.isfile(RequestChecker.MODELS_DIR + "index.json"):
			Logging.log("Missing Model!", Logging.LEVEL_ERROR)
			exit()
		
		self.models = json.load(open(RequestChecker.MODELS_DIR + "index.json", 'r'))
		if 'lda' not in self.models or 'name' not in self.models or 'nn-crawl' not in self.models or 'nn-attack' not in self.models  or 'nn-types' not in self.models:
			Logging.log("Invalid Model Index!", Logging.LEVEL_ERROR)
			exit()

		Logging.log("Found Model " + self.models['name'])

		# load default 2 class models
		self.lda = LDAPredictor(self.models['lda'], RequestChecker.MODELS_DIR)
		if os.environ.get("BLOCK_CRAWLING") == "true":
			self.nn = NNPredictor(self.models['nn-crawl'], RequestChecker.MODELS_DIR)
		else:
			self.nn = NNPredictor(self.models['nn-attack'], RequestChecker.MODELS_DIR)

		# load models to get type
		self.type_handling = TypeHandler()
		if self.type_handling.is_active():
			Logging.log("TypeHandler active")
			self.nn_types = NNPredictor(self.models['nn-types'], RequestChecker.MODELS_DIR)

		# connector to use for models
		# 	or => one model classifies as safe
		#	and => both models classify as safe
		if "APPROACH_CONNECTOR" in os.environ:
			self.connector = "and" if os.environ.get("APPROACH_CONNECTOR") == "and" else "or" 
		else:
			self.connector = "or"
		Logging.log('Using connector "' + self.connector + '"')

		# model to use 
		if "APPROACH_USE" in os.environ:
			self.use_model = os.environ.get("APPROACH_USE") if os.environ.get("APPROACH_USE") in ['lda', 'nn'] else "lda,nn" 
		else:
			self.use_model = "lda,nn"
		Logging.log('Using model(s) "' + self.use_model + '"')

		# create a notification (=mail) object
		if Notifications.is_active():
			self.notifications = Notifications()

	def model_connector(self, lda_bool, nn_bool):
		if self.use_model == "lda" :
			return lda_bool
		elif self.use_model == "nn":
			return nn_bool
		else:
			if self.connector == "and":
				return lda_bool and nn_bool
			else:
				return lda_bool or nn_bool

	def is_save(self, request_data):
		is_save = None

		# two class prediction
		lda_is_attack, lda_types = self.lda.predict(request_data)
		nn_is_attack, _ = self.nn.predict(request_data)

		if self.type_handling.is_active():
			_, nn_types = self.nn_types.predict(request_data)

			for lda_type,nn_type in zip(lda_types,nn_types):
				
				# check blocked types
				no_block = self.model_connector(
					lda_type[0] not in self.type_handling.block_types,
					nn_type[0] not in self.type_handling.block_types
				)
				if not no_block:
					is_save = False
					break

				# check allowed types
				direct_allow = self.model_connector(
					lda_type[0] in self.type_handling.allow_types,
					nn_type[0] in self.type_handling.allow_types
				)
				if direct_allow:
					is_save = True
					break

		if is_save == None:
			# default handling
			is_save = self.model_connector( not lda_is_attack, not nn_is_attack)

		if Notifications.is_active():
			if not is_save:
				self.notifications.log_attack(
					request_data.connection_id,
					lda_is_attack, nn_is_attack,
					lda_types, nn_types if self.type_handling.is_active() else []
				)
			self.notifications.send_daily_report()

		return is_save

		
		