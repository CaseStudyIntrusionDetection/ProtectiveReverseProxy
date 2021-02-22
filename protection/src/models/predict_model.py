from abc import ABC, abstractmethod

class Predictor(ABC):

	@abstractmethod
	def __init__(self, index, models_dir):
		raise NotImplementedError("__init__(...) not implemented.")

	@abstractmethod
	def predict(self, request_data):
		raise NotImplementedError("predict(...) not implemented.")