import gensim 
import json
import time, os

from src.data.make_datasets_lda import get_text_from_request

class LDAPredictor():

	BLOCK_CRAWLING = os.environ.get("BLOCK_CRAWLING") == "true"
	CLEANUP_WINDOWS = 2000
	KEEP_ON_CLEANUP = 1000

	def __init__(self, index, models_dir):
		self.load_model(
			models_dir + index["topicmodel"],
			models_dir + index["dictionary"],
			models_dir + index["distribution"]
		)

		# store requests for window
		self.known_requests = {}
		self.connection_id_last = {}

	def load_model(self, tm_path, dict_path, dist_path):
		"""Loads the LDA model which should be used for prediction (testing).

		Args:
			settings (dict): The settings object for all kinds of parameters.

		Returns:
			(array of dict, numpy.ndarray, dict): The bag of words corpus; the LDA model
			and the probability distributions of the topics.
		"""

		# load corpus (as bow) and dictionary
		trained_topics = json.load(open(dist_path, 'r'))
		self.trained_dists = self.transform_topics_for_hellinger(
			trained_topics['requestTopics']['types'],
			trained_topics['requestTopics']['emulators'], 
			trained_topics['requestTopics']['zap-ids']
		)

		self.dict = gensim.corpora.Dictionary.load(dict_path)
		self.model = gensim.models.ldamodel.LdaModel.load(tm_path)


	def transform_topics_for_hellinger(self, *topics):
		"""Brings the topic distributions into a format that can be used to compute the
		Helldinger distance.

		Args:
			*topics (dict): The topic distributions which should be converted.

		Returns:
			(dict): A dictionary containing the probability distributions for each topic
			in a format usable with gensim.hellinger.
		"""

		# extract known distributions of types and emulators in a format that can be used with gensim.hellinger
		result = {}
		for topic in topics:
			for dist in topic.keys():
				result[dist] = []
				for tid,prob in enumerate(topic[dist], start=0):
					result[dist].append([tid,prob])

		return result

	def get_best_topics(self, bow):
		predicted_dist = self.model.get_document_topics(
			bow,
			minimum_probability=0.001,
			minimum_phi_value=0.001,
			per_word_topics=False
		)

		# compare predictions to all known distributions of types and emulators
		hellinger_distances = []
		for dist_type,dist_values in self.trained_dists.items():
			hellinger_distances.append([dist_type, gensim.matutils.hellinger(predicted_dist, dist_values)])

		#  sort in a way, such that most similar label is first
		hellinger_distances.sort(key=lambda t: t[1])

		return hellinger_distances

	def predict(self, request_data):
		data = request_data.create_dict()
		document = get_text_from_request(data)

		# create window of 5
		if data["connection-id"] not in self.known_requests:
			self.known_requests[data["connection-id"]] = []
		elif len(self.known_requests[data["connection-id"]]) > 4:
			self.known_requests[data["connection-id"]].pop(0)
		self.known_requests[data["connection-id"]].append(document)
		self.connection_id_last[data["connection-id"]] = int(time.time())

		self.keep_memory_free()

		bow = self.dict.doc2bow(
			filter(
				lambda t: len(t.strip()) > 0,
				' '.join(self.known_requests[data["connection-id"]]).split(' ')
			)
		)

		predicted = self.get_best_topics(bow)
		# the best prediction is the one with the lowest hellinger distance
		# 	but if "only zap id is attack", we learn on ZAP-files attacks (id != -1) and non attacks (id == -1) as "attack" so we ignore the prediction "attack"
		#	and use only ids and emulators
		if predicted[0][0] == 'attack' and not LDAPredictor.BLOCK_CRAWLING:
			predicted.pop(0)
		best_predicted = predicted[0][0]

		is_attack = best_predicted != 'benign' and best_predicted != 'none' and best_predicted != '-1'

		return is_attack, predicted[:5]

	def keep_memory_free(self):
		if len(self.known_requests) > LDAPredictor.CLEANUP_WINDOWS:
			for cid,_ in sorted(self.connection_id_last.items(), key=lambda l: l[1], reverse=True)[LDAPredictor.KEEP_ON_CLEANUP:]:
				del self.known_requests[cid]
				del self.connection_id_last[cid]