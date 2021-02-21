import json
import datetime, time 
import ipaddress
import re
from urllib.parse import unquote

def getTextFromRequest(request, settings):
	"""Converts a JSON request into text.

	Args:
		request (dict): The JSON request to transform into text.
		settings (dict): The settings object for all kinds of parameters.

	Returns:
		str: The transformed request.
	"""
	regToCategory = {
		'alphanum' : r'[A-Za-z0-9]',
		'onlyText' : r'^[ \,\:\.\!\?\;A-Za-z0-9]+$',
		'alpha' : r'[A-Za-z]',
		'alphaUpper' : r'[A-Z]',
		'alphaLower' : r'[a-z]',
		'url' : r'[/?&]',
		'email' : r'\w+@\w+\.\w',
		'tag' : r'[<>/]',
		'function' : r'\(.*\) *;?',
		'num' : r'\d*[.,]?\d+',
		'onlyNum' : r'^\d*[.,]?\d+$',
		'short_string' : r'^.{1,100}$',
		'empty' : r'^$',
		'long_string' : r'^.{101}.*$',
		'reversepath' : r'\.\.(\/|\\)'
	}

	def headerToText(header, isRequest=False, isResponse=False):
		"""Converts a HTTP header into a list of words. Several value parameters are transformed:
		- Version numbers are deleted or replaced by the string 'version'
		- For dates, minutes and seconds are removed
		- And others (see code).

		Args:
			header (dict): HTTP header as dict (representing the key-value pairs)
			isRequest (bool, optional): Flag for request header. Defaults to False.
			isResponse (bool, optional): Flag for response header. Defaults to False.

		Returns:
			list: A list of words generated from the header.
		"""
		t = []

		if isRequest:
			typePrefix = "request"
		elif isResponse:
			typePrefix = "response"
		else:
			typePrefix = ""			

		for key,value in header.items():
			key_low = key.lower()
			if key_low == 'cookie':
				t.append(paramsToText(value, prefix=typePrefix + '_cookie', delimiter=';'))
			elif key_low != 'x-zap-scan-id': # nothing to do for 'x-zap-scan-id' (internal zap flag for later classification)
				
				if key_low not in ['accept', 'accept-encoding', 'accept-language', 'cache-control', 'connection', 'content-length', 'content-type', 'referer']:
					t.append( typePrefix + '_header_' + key_low)
			
				if key_low in ['date', 'expires', 'last-modified', 'if-modified-since', 'if-unmodified-since']:
					if settings['corpus']['use_times']:
						t.append( re.sub(r':\d\d:\d\d', '', value).replace(' ', '') )
				elif key_low in ['x-powered-by', 'server', 'user-agent']: 
					t.append( re.sub(r'(\d+(.|_))*\d+', 'version', value).replace(' ', '') )
				#elif key_low in ['accept', 'accept-language']: 
				#	t.append( re.sub(r';?q=[\d.]+', '', value).replace(' ', '') )
				elif key_low in ['accept', 'accept-encoding', 'accept-language', 'connection', 'referer']:
					pass
				else:
					t.append( re.sub(r'[^a-zA-Z0-9]', '', value) )
		return t

	def bodyToText(body):
		"""Converts the body of a HTTP post request into a string of words. The
		words represent the relevant classes of characters which appear in the value,
		e.g. value_alphanum for alphanumerical characters (for the complete list,
		see the dict called regToCategory above). Example: `key=123` becomes
		`post_key value_alphanum value_onlyText value_short_string value_num value_onlyNum`.

		Args:
			body (dict): HTTP body key-value pairs.

		Returns:
			str: transformed body.
		"""
		t = ""
		for name, value in body.items():
			if t != "":
				t += " "

			t += "post_" + name
			for category, regex in regToCategory.items():
				t += "" if re.search(regex, value) == None else " value_" + category
		return t

	def paramsToText(params, prefix='get', delimiter='&'):
		"""Converts url parameters into a string of words. The words represent the
		relevant classes of characters which appear in the values of the key-value
		pairs. This is analogous to the `bodyToText` function.

		Args:
			params (str): The url parameters to transform.
			prefix (str, optional): Prefix specifying the request type. Defaults to 'get'.
			delimiter (str, optional): The delimiter at which the parameters are split. Defaults to '&'.

		Returns:
			str: transformed url parameters.
		"""
		t = ""
		for param in params.split(delimiter):
			if t != "":
				t += " "

			parts = param.split('=')
			if len(parts) > 1:
				name, value = parts[0], parts[1]

				value_last = None # double url decode
				while value_last != value:
					value_last = value
					value = unquote(value)

				t += prefix + "_" + name
				for category, regex in regToCategory.items():
					t += "" if re.search(regex, value) == None else " value_" + category
			else:
				t += prefix + "_" + param

		return t

	text = []
	text.extend(headerToText(request['header'], isRequest=True))
	text.extend(headerToText(request['honeypot']['response-header'], isResponse=True))
	if settings['corpus']['use_times']:
		text.append(datetime.datetime.fromtimestamp(request['timestamp']).fromtimestamp(request['timestamp']).strftime("request_day_%a request_hour_%H request_minute_%M"))
	text.append('request_method_' + request['request']['method'] + ' request_protocol_' + request['request']['protocol'])
	text.append(request['honeypot']['response-hash'] + " response_size_" + str(request['honeypot']['response-size'])
		+ " response_status_" + str(request['honeypot']['response-status-code']) )

	# url as two parts => path to file and get params
	if '?' in request['request']['uri']:
		filepart = request['request']['uri'][0:request['request']['uri'].find('?')]
		text.append(paramsToText(request['request']['uri'][request['request']['uri'].find('?')+1:]))
	else:
		filepart = request['request']['uri']
	
	path_string = 'path_'
	text.append( path_string )
	for path in filepart.split('/'):
		if path != "":
			path_string += 'file_' if '.' in path else 'folder_'
			text.append( path_string )

	if request['request']['method'] == "POST":
		text.append(bodyToText(request['request']['body']))

	ip_object = ipaddress.ip_address(request['sender']['ip'])
	text.append( ("private_ip " if ip_object.is_private else "" )
			+ ( "global_ip " if ip_object.is_global else "" )
			+ ( "reserved_ip" if ip_object.is_reserved else "" ) )

	return ' '.join(text).lower()

def group_by_connection_id(requests):
	"""Groups requests by their connection id, i.e., all requests with the same
	connection id are put together.

	Args:
		requests (array of dict): The requests to group.

	Returns:
		dict: A dictionary containing a key for each connection id with the
		corresponding requests for that id as a value.
	"""
	texts = {}
	for request in requests:
		if not request['connection-id'] in texts:
			texts[request['connection-id']] = {
				"corpus" : request['corpus'],
				"type" : request['type'],
				"emulator" : [ request['honeypot']['used-emulator'] ],
				"zap-id" : [ request['zap-id'] ],
				"document" : [ request ]
			}
		else:
			texts[request['connection-id']]['emulator'].append(request['honeypot']['used-emulator'])
			texts[request['connection-id']]['zap-id'].append(request['zap-id'])
			texts[request['connection-id']]['document'].append(request)

	return texts

def prepare_corpus(settings, key):
	"""Merges multiple datasets into one dataset to work with and groups requests by their
	connection id if enabled. Optionally, datasets are being filtered as well (e.g. only use
	data with a specific type of attack).

	Args:
		settings (dict): The settings object for all kinds of parameters.
		key (str): The key to the dataset which should be prepared, e.g.
		'training_data' or 'test_data'.

	Returns:
		array of dict: The corpus of text documents.
	"""

	# read all data from json into one big array
	requests = []
	#	make sure to have unique ids and connections ids
	overallIdOffset = 0
	overallConnectionIdOffset = 0
	for dataset in settings[key]:

		# allow filtering from settings
		if 'filter' in dataset:
			filter_request = eval("lambda r : " + dataset['filter'])
		else:
			filter_request = lambda r : True

		idMax = -1
		connectionIdMax = -1
		dataPart = json.load(open(dataset['file'], 'r'))
		for request in dataPart:
			request['id'] += overallIdOffset
			request['connection-id'] += overallConnectionIdOffset
			request['type'] = dataset['type']
			request['zap-id'] = str(request['header']['X-ZAP-Scan-ID']) if 'X-ZAP-Scan-ID' in request['header'] else '-1'
			request['corpus'] = dataset['name']
			if filter_request(request):
				requests.append(request)

			if idMax < request['id']:
				idMax = request['id']
			if connectionIdMax < request['connection-id']:
				connectionIdMax = request['connection-id']
			
		overallIdOffset += idMax + 1
		overallConnectionIdOffset += connectionIdMax + 1

	# preprocess texts
	if settings['corpus']['document_per_request'] ^ settings['corpus']['document_per_connection_id']:
		if settings['corpus']['document_per_request']:
			texts = []
			for request in requests:
				texts.append({
					"corpus" : request['corpus'],
					"type" : request['type'],
					"emulator" : request['honeypot']['used-emulator'],
					"zap-id" : request['zap-id'],
					"document" : getTextFromRequest(request, settings)
				})
		else:
			texts = []
			for request in group_by_connection_id(requests).values():
				request['emulator'] = ' '.join(request['emulator'])
				request['zap-id'] = ' '.join(request['zap-id'])
				request['document'] = ' '.join([getTextFromRequest(r, settings) for r in request['document']])
				texts.append(request)
	elif settings['corpus']['document_request_window_size'] > 0:
		texts = []
		for request in group_by_connection_id(requests).values():
			len_minus_window = len(request['emulator']) - settings['corpus']['document_request_window_size']
			for begin in range(1 if len_minus_window < 1 else len_minus_window):
				end = begin + settings['corpus']['document_request_window_size']
				texts.append({
					"corpus" : request['corpus'],
					"type" : request['type'],
					"emulator" : ' '.join(request['emulator'][begin:end]),
					"zap-id" : ' '.join(request['zap-id'][begin:end]),
					"document" : ' '.join([getTextFromRequest(r, settings) for r in request['document'][begin:end]])
				})
	else:
		print('Set exactly one of corpus.document_per_connection_id and corpus.document_per_request to True or give a window size corpus.document_request_window_size!')
		exit()

	return texts

def main(settings):
	f = open(settings['output']['dir'] + 'processed/' + settings['output']['name'] + '_trainset.json', "w+")
	f.write(json.dumps(prepare_corpus(settings, 'training_data'), indent=4, sort_keys=False))
	f.close()

	f = open(settings['output']['dir'] + 'processed/' + settings['output']['name'] + '_testset.json', "w+")
	f.write(json.dumps(prepare_corpus(settings, 'test_data'), indent=4, sort_keys=False))
	f.close()