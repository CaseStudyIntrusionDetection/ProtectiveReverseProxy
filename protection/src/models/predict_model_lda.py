import gensim 
import json
import time

from src.features.build_features_lda import build_bow_dict

def transform_topics_for_hellinger(*topics):
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

def load_model(settings):
	"""Loads the LDA model which should be used for prediction (testing).

	Args:
		settings (dict): The settings object for all kinds of parameters.

	Returns:
		(array of dict, numpy.ndarray, dict): The bag of words corpus; the LDA model
		and the probability distributions of the topics.
	"""

	# load corpus (as bow) and dictionary
	corpus = json.load(open(settings['output']['dir'] + 'temp/' + settings['output']['name'] + '_bow.json', 'r'))
	trainedTopics = json.load(open(settings['output']['dir'] + 'lda_trained/' + settings['output']['name'] + '_trained.json', 'r'))
	dict = gensim.corpora.Dictionary.load(settings['output']['dir'] + 'temp/' + settings['output']['name'] + '.dict')
	model = gensim.models.ldamodel.LdaModel.load( settings['output']['dir'] + 'temp/' + settings['output']['name'] + '.ldamodel' )

	return corpus, model, dict, \
		transform_topics_for_hellinger(trainedTopics['requestTopics']['types'], trainedTopics['requestTopics']['emulators'], trainedTopics['requestTopics']['zap-ids'])

# predict a document
def predict(settings, model, bow, learnedTopics, useOlda=False, incrementallyLearnOldaModel=False):
	"""Takes a bag of words and computes Hellinger distances between the given bag of words
	and each document in the corpus.

	Args:
		settings (dict): The settings object for all kinds of parameters.
		model (numpy.ndarray): The LDA model which should be used for prediction.
		bow (dict): The bag of words for which the prediction should be made.
		learnedTopics (dict): The probability distributions of the learned topics.
		useOlda (bool, optional): Indicates whether to use OLDA (True) or FIGS (false). Defaults to False.
		incrementallyLearnOldaModel (bool, optional): Indicates whether the OLDA model should be learned
		incrementally, i.e., if the model should be updated in each prediction step. Defaults to False.

	Returns:
		(array of [str, float]): An array containing the class and the corresponding Hellinger distance for each
		class.
	"""

	if useOlda: # update model via OLDA
		model.update([bow])
	
	predictedTopics = model.get_document_topics(bow, minimum_probability=settings['lda']['min_probability'], minimum_phi_value=settings['lda']['min_phi_value'], per_word_topics=False)

	# compare predictions to all known distributions of types and emulators
	hds = []
	for distType,distValues in learnedTopics.items():
		hds.append([distType, gensim.matutils.hellinger(predictedTopics, distValues)])

	#  sort in a way, such that most similar label is first
	hds.sort(key=lambda t: t[1])

	if useOlda and not incrementallyLearnOldaModel: # reload model for next try
		model = gensim.models.ldamodel.LdaModel.load( settings['output']['dir'] + 'temp/' + settings['output']['name'] + '.ldamodel' )

	return hds

def eval_corpus(settings, model, corpus, learnedTopics):
	"""Evaluates a given LDA model on a given corpus by computing the predictions of the
	model and comparing them with the real outcomes.

	Args:
		settings (dict): The settings object for all kinds of parameters.
		model (numpy.ndarray): The LDA model which should be used for prediction (testing).
		corpus (array of dict): The bag of words corpus to use for testing.
		learnedTopics (dict): The probability distributions of the learned topics.

	Returns:
		(dict): A dictionary containing the evaluation of the model (true positives, false
		positives, true negatives, false negatives, precision, recall and the predictions
		made by the model).
	"""

	# run and log predictions
	truePositives, falsePositives, falseNegatives, trueNegatives = 0, 0, 0, 0
	predictions = []

	overall_time = 0

	for d in corpus:
		predict_start = time.time_ns()
		predicted = predict(settings, model, d['bow'], learnedTopics, settings['predict']['use_olda'], settings['predict']['incrementally_learn_olda_model'])
		overall_time += time.time_ns() - predict_start

		# the best prediction is the one with the lowest hellinger distance
		# 	but if "only zap id is attack", we learn on ZAP-files attacks (id != -1) and non attacks (id == -1) as "attack" so we ignore the prediction "attack"
		#	and use only ids and emulators
		if predicted[0][0] == 'attack' and settings['predict']['only_zap-id_is_attack']:
			best_predicted = predicted[1][0]
		else:
			best_predicted = predicted[0][0]

		if settings['predict']['only_zap-id_is_attack']: # any != -1 in a window will classify window as attack
			isAttackBaseline = False
			for zap_id in d['zap-id'].split(' '):
				isAttackBaseline |= zap_id != '-1'
		else:
			isAttackBaseline = d['type'] == 'attack'
		isAttackAssumption = best_predicted != 'benign' and best_predicted != 'none' and best_predicted != '-1'

		predictions.append({
			"corpus" : d['corpus'],
			"type" : d['type'],
			"emulator" : d['emulator'],
			"zap-id" : d['zap-id'],
			"prediction" : best_predicted,
			"predictions" : predicted[:5]
		})

		if isAttackBaseline and isAttackAssumption:
			truePositives += 1
		elif not isAttackBaseline and isAttackAssumption:
			falsePositives += 1
		elif isAttackBaseline and not isAttackAssumption:
			falseNegatives += 1
		elif not isAttackBaseline and not isAttackAssumption:
			trueNegatives += 1

	print("Prediction Only Seconds:", overall_time / 1000000000 )

	return {
		'truePositives' : truePositives,
		'falsePositives' : falsePositives,
		'falseNegatives' : falseNegatives,
		'trueNegatives' : trueNegatives,
		'precision' : -1 if truePositives + falsePositives == 0 else truePositives / (truePositives + falsePositives),
		'recall' : -1 if truePositives + falsePositives == 0 else truePositives / (truePositives + falseNegatives),
		'predictions' : predictions
	}

def main(settings):
	corpus, model, dict, learnedTopics = load_model(settings)

	# load documents and build bow for test set
	test_corpus = json.load(open(settings['output']['dir'] + 'processed/' + settings['output']['name'] + '_testset.json', 'r'))
	test_bow = build_bow_dict(dict, test_corpus, updateDictionary=False)

	report = eval_corpus(settings, model, test_bow, learnedTopics)

	f = open(settings['output']['dir'] + 'temp/' + settings['output']['name'] + '_prediction.json', "w+")
	f.write(json.dumps(report, indent=4, sort_keys=False))
	f.close()