import json
import os

import os
# disable tf warnings and infos
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 
import tensorflow as tf

import pandas

from src.transformation.HTTPTransformer import HTTPTransformer
from src.transformation.HTTPHeaders import transform_header_dict, HTTP_RELEVANT_HEADERS

class NNPredictor():

	BLOCK_CRAWLING = os.environ.get("BLOCK_CRAWLING") == "true"

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

	def predict(self, request_data):
		data = request_data.create_dict()
		processed_data = self.process(data)

		dataframe = pandas.DataFrame(processed_data, index=[0])
		dataframe['bin_label'] = dataframe.apply(lambda x: binarize_label(x), axis=1)
		labels = dataframe.pop('bin_label')
		ds = tf.data.Dataset.from_tensor_slices((dict(dataframe), labels))

		self.model.predict(ds)

		is_attack = False
		predicted = [['rfi', 0.05]]

		return is_attack, predicted[:5]

def binarize_label(row):
    return 'without zap-id' if row['label'] == "no zap id" else 'with zap-id'