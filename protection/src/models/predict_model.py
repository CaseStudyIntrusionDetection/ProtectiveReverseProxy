from abc import ABC, abstractmethod

class Predictor(ABC):
	"""
		Abstract class specifying the interface a classification of a request can be
		obtained from a model
	"""

	@abstractmethod
	def __init__(self, index, models_dir):
		"""
			Initialize the prediction: Loading the models and checking the 
			model given from the user.
			=> Prepare for precitions

			Args:
				index (dict): The part of the index.json of a model represeting the model to load.
				models_dir (string): The basepath where the models are located.
		"""
		raise NotImplementedError("__init__(...) not implemented.")

	@abstractmethod
	def predict(self, request_data):
		"""
			Predicts whether a request is assumed to be benign or malicious.
			
			Args:
				request_data (RequestData): RequestData object containing the
				information for the request to predict.

			Returns two values: is attack? (bool), five most probable attack types [['type', distance], ...] (array)
		"""
		raise NotImplementedError("predict(...) not implemented.")