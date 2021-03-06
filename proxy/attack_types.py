import os

from log import Logging

class TypeHandler():
	"""
		Handles the different attack types a user may be choose by a category.

		Access the blocked or allowed types via the arrays
		self.block_types and self.allow_types.
	"""

	all_types = {
		"sql" : [
			"SQL Injection", "40018",
			"SQL Injection - Hypersonic SQL", "40020",
			"SQL Injection - MsSQL", "40027",
			"SQL Injection - MySQL", "40019",
			"SQL Injection - Oracle", "40021",
			"SQL Injection - PostgreSQL", "40022",
			"SQL Injection - SQLite", "40024",
			"sqli"
		],
		"xss" : [
			"Cross Site Scripting (Persistent) - Prime", "40016",
			"Cross Site Scripting (Reflected)", "40012",
			"Anti-CSRF Tokens Check", "20012",
			"xss"
		],
		"tampering" : [
			"Parameter Tampering", "40008",
			"Cookie Slack Detector", "90027"
			"CRLF Injection", "40003",
			"User Agent Fuzzer", "10104",
			"crlf"
		],
		"execution" : [
			"Remote Code Execution - Shell Shock", "10048",
			"Server Side Code Injection", "90019",
			"Server Side Include", "40009",
			"XPath Injection", "90021",
			"XSLT Injection", "90017",
			"Expression Language Injection", "90025",
			"Remote File Inclusion", "7",
			"Remote OS Command Injection", "90020",
			"Format String Error", "30002",
			"cmd_exec",
			"rfi",
			"php_code_injection"
		],
		"disclosure" : [
			"Source Code Disclosure - File Inclusion", "43",
			"Path Traversal", "6",
			"lfi"
		],
		"overflows" : [
			"Buffer Overflow", "30001",
			"Integer Overflow Error", "30003",
		],
		"encryption" : [
			"Generic Padding Oracle", "90024"
		],
		"cve" : [
			"Apache Range Header DoS (CVE-2011-3192)", "10053",
			"error"
		],
		"redirect" : [
			"External Redirect", "20019",
			"Httpoxy - Proxy Header Misuse", "10107"
		]
	}

	def __init__(self):
		"""
			Loads the types to block and allow from env. variables. Initialization fails
			if there are types listed both as blocked and allowed at the same time.
		"""
		self.block_types = self.load_types("BLOCK_TYPES")
		self.allow_types = self.load_types("ALLOW_TYPES")

		if len(list(set(self.block_types) & set(self.allow_types))) > 0:
			Logging.log( "Some types of requests are listed as allowed and also as blocked - choose one!" , Logging.LEVEL_ERROR )
			exit()

	def load_types(self, env_key):
		"""
			Loads the allowed or blocked types from the env. variable.

			Args:
				env_key (string): The key ('BLOCK_TYPES' or 'ALLOW_TYPES') which
				specifies from which environmental variable to read.
		"""
		types = []
		if env_key in os.environ:
			tl = os.environ.get(env_key)
			if len(tl) > 0:
				for t in tl.split(','):
					if t in TypeHandler.all_types:
						types.extend(TypeHandler.all_types[t])
		return types

	def is_active(self):
		"""
			Returns whether there are specific types given to be blocked or allowed.
		"""
		return len(self.block_types) > 0 or len(self.allow_types) > 0 

		