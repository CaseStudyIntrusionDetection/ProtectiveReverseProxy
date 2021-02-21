import gensim 
import json

def build_bow_dict(dict, documents, updateDictionary=True):
	"""Transforms each text document in the corpus to a bag of words dictionary.

	Args:
		dict (gensim.corpora.dictionary.Dictionary): The gensim corpus dictionary.
		documents (array of dict): The corpus of text documents.
		updateDictionary (bool, optional): Indicates whether the gensim dictionary
		should be updated, i.e., if missing words should be added (defaults to True).

	Returns:
		array of dict: The bag of words corpus.
	"""

	# create dict
	plainText = [filter(lambda t: len(t.strip()) > 0, d['document'].split(' ')) for d in documents]

	# add missing words to dictionary
	if updateDictionary:
		dict.add_documents(plainText)
		dict.filter_extremes(no_above=0.8)
	
	# convert to bag of words
	corpusBow = []
	for d in documents:
		corpusBow.append({
			"corpus" : d['corpus'],
			"type" : d['type'],
			"emulator" : d['emulator'],
			"zap-id" : d['zap-id'],
			"bow" : dict.doc2bow( filter(lambda t: len(t.strip()) > 0, d['document'].split(' ') ) )
		})

	return corpusBow

def main(settings):
	# load documents
	corpus = json.load(open(settings['output']['dir'] + 'processed/' + settings['output']['name'] + '_trainset.json', 'r'))

	dict = gensim.corpora.Dictionary()
	corpusBow = build_bow_dict(dict, corpus)
	dict.save(settings['output']['dir'] + 'temp/' + settings['output']['name'] + '.dict')

	

	# export to file
	f = open(settings['output']['dir'] + 'temp/' + settings['output']['name'] + '_bow.json', "w+")
	f.write(json.dumps(corpusBow, sort_keys=False))
	f.close()