import json
import os

# disable tf warnings and infos
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

import tensorflow as tf
import pandas, numpy
numpy.warnings.filterwarnings("ignore")

from src.transformation.HTTPTransformer import HTTPTransformer
from src.transformation.HTTPHeaders import transform_header_dict, HTTP_RELEVANT_HEADERS
from src.models.predict_model import Predictor

class NNPredictor(Predictor):

	def __init__(self, index, models_dir):
		self.model = tf.keras.models.load_model(models_dir + index["tfmodel"])

	def process(self, data):
		request = data['request']
		uri_obj = HTTPTransformer.uri_transformation_wrapper(request['uri'])
		r = {
			"label": "no zap id",
			"original-zap-id": "no zap id",
			"method": request['method'],
			"uri-path": uri_obj['path'],
			"uri-query": uri_obj['query'],
			"body": "" if request['body'] == "" else HTTPTransformer.handle_body(request['body']),
			"request-length": data['header']["Content-Length"] if "Content-Length" in data['header'] else -1,
			"uri-length": len(request['uri']),
			"body-length": len(request['body'])
		}

		header_dict = transform_header_dict(data['header'], headers=HTTP_RELEVANT_HEADERS)
		return {**r, **header_dict}

	def create_tf_dataset(self, processed_data):
		dataframe = pandas.DataFrame(processed_data, index=[0])
		dataframe['bin_label'] = dataframe.apply(lambda row: 'without zap-id' if row['label'] == "no zap id" else 'with zap-id', axis=1)
		labels = dataframe.pop('bin_label')
		ds = tf.data.Dataset.from_tensor_slices((dict(dataframe), labels))
		return ds.batch(1)

	def predict(self, request_data):
		data = request_data.create_dict()
		processed_data = self.process(data)

		dist = self.model.predict(self.create_tf_dataset(processed_data))
		if dist.shape[1] == 2: # binary classification
			is_attack = bool(tf.argmax(dist, axis=1) == 0)
			predictions = [['attack', 1-dist[0][0]], ['benign', 1-dist[0][1]]]
		else:
			is_attack = False
			predictions = [['dummy', 0.5]]

		#  sort in a way, such that most probable label (=small value) is first 
		predictions.sort(key=lambda t: t[1])

		return is_attack, predictions[:5]