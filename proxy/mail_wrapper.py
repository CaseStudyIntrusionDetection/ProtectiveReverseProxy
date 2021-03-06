import os, time
from datetime import date

from mail import Mailer

class Notifications():
	"""
		Class to send notification about attacks  to theadmin
	"""

	# the system can not keep all events in the memory, therefore it
	# cleans up the memory from time to time, the following values 
	# allow to influence the cleaning.
	#	values kept on cleanup (keeping n newest)
	CONNECTION_IDS_KEEP_ON_CLEANUP = 100
	#	starts a cleanup when this limit is reached
	MAX_CONNECTION_IDS = 200
	#	number of request logged by connection (id)/ user
	MAX_REQUESTS_PER_ID = 10

	@staticmethod
	def is_active():
		"""
			Check if MAIL_TO is set in the environment variables, it this is the
			case, we assume that the users wants to get notifications.
		"""
		return "MAIL_TO" in os.environ and len(os.environ.get("MAIL_TO")) > 0

	def __init__(self):
		"""
			Initialize mail setup 
		"""
		self.mailer = Mailer()
		self.attacks = {}
		self.counts = {}

		self.send_daily = "SEND_DAILY_REPORT" in os.environ and os.environ.get("SEND_DAILY_REPORT") == "true"
		self.send_emerg = "SEND_EMERGENCY" in os.environ and os.environ.get("SEND_EMERGENCY") == "true"

		self.last_attackmail = 0
		self.last_reportmail = int(time.time())

	def log_attack(self, connection_id, lda_is_attack, nn_is_attack, lda_types, nn_types = []):
		"""
			Logs a detected attack
			Args:
				connection_id (int): the connection id of the user
				lda_is_attack (bool): answer by lda to "is attack?" 
				nn_is_attack (bool): answer by nn to "is attack?"
				lda_types (array): most probable attack types by lda; [['type', distance], ...], e.g. [['rfi', 0.2], ['lfi', 0.3], ...]]
				nn_types (array): most probable attack types by nn; [['type', distance], ...]
		"""
		# create a new dict entry for a new suspicious connection id 
		if connection_id not in self.attacks:
			self.attacks[connection_id] = []

		# we only save up to a certain amount of request per id
		if len(self.attacks[connection_id]) >= Notifications.MAX_REQUESTS_PER_ID:
			self.attacks[connection_id].pop(0)
		
		# specify a suspicious entry for a request
		self.attacks[connection_id].append({
			'is_attack' : {
				'lda' : lda_is_attack,
				'nn' : nn_is_attack
			},
			'types' : {
				'lda' : self.format_types(lda_types),
				'nn' : self.format_types(nn_types) if nn_types != [] else 'not calculated'
			},
			'time' : int(time.time())
		})

		# track how many attacks are launched within a day
		today = int(date.today().strftime("%s"))
		if today not in self.counts:
			self.counts[today] = 0
		self.counts[today] += 1

		# if attack is detected, send an emergency mail(1h interval)
		self.send_emergency()

		# free dict entries, only save up to a certain amount of connection ids
		self.keep_memory_free()
		
	def format_types(self, types):
		"""
			Formats the assumed attack types and their distances for email dispatch.
			
			Args:
				types (list): List of lists containing the attack type and its
				distance for the most probable attack types: [['type', distance], ...].
		"""
		s = []
		for t,p in types:
			s.append(t + ' (' + ("%.3f" % p) + ')')
		return ', '.join(s)

	def keep_memory_free(self):
		"""
			Makes sure that the dictionary of connection ids does not get too big
			by deleting the oldest entries when the maximum size has been reached.
		"""
		if len(self.attacks) > Notifications.MAX_CONNECTION_IDS:
			for cid,_ in sorted(self.attacks.items(), key=lambda l: l['time'], reverse=True)[Notifications.CONNECTION_IDS_KEEP_ON_CLEANUP:]:
				del self.attacks[cid]

	def send_emergency(self):
		"""
			Sends an emergency mail to the admin. In order to avoid spam,
			emergency emails are sent at most once per hour. The mail
			contains information about the attackers and the assumed attack types.
		"""
		current_time = int(time.time())
		if self.send_emerg and current_time - self.last_attackmail > 3600:
			self.last_attackmail = current_time
			time_range = current_time - 3600
		
			# setup mail content: Table containing user ID and potential attacks
			text = '<html><style>table,th,tr,td { border:solid 1px black; border-collapse: collapse; padding: 2px; }</style><table>'
			text += '<tr><th align="left">User ID</th><th align="left">Is Attack?</th><th align="left">Types (distance)</th></tr>'
			count = 0
			for cid, attacks in self.attacks.items():
				for data in attacks:
					if data['time'] > time_range:
						count += 1
						text += '<tr><td align="right">' + str(cid) + '</td>'
						text += '<td align="left">LDA: '+ ('&check;' if data['is_attack']['lda'] else '&cross;') + '<br/> NN: ' + ('&check;' if data['is_attack']['nn'] else '&cross;') + '</td>'
						text += '<td align="left">LDA: '+ data['types']['lda'] + '<br/> NN: ' + data['types']['nn'] + '</td></tr>'

			text += '</table></html>'

			self.mailer.send(text, "Emergency – "+ str(count) +" attacks in the last hour")

	def send_daily_report(self):
		"""
			Sends a daily report to the admin, containing information about
			the number of attack attempts per day.
		"""
		current_time = int(time.time())
		if self.send_daily and current_time - self.last_reportmail > 86400:
			self.last_reportmail = current_time

			# setup mail content: Table containing user ID and potential attacks
			text = '<html><style>table,th,tr,td { border:solid 1px black; border-collapse: collapse; padding: 2px; }</style><table>'
			text += '<tr><th align="left">Day</th><th align="left">Number of attacks</th></tr>'
			dellist = []
			for day, count in self.counts.items():
				text += '<tr><td>' + date.fromtimestamp(day).strftime("%Y-%m-%d") + '</td><td align="right">' + str(count) + '</td></tr>'

				if current_time - day > 86400*21: # only keep last 21 days
					dellist.append(day)
			text += '</table></html>'

			if len(dellist) > 0:
				for day in dellist:
					del self.counts[day]

			self.mailer.send(text, "Daily Report")


# Code for testing the email dispatch
#	will not take care of the limits (e.g. one mail per day or hour!)
if __name__ == "__main__":

	n = Notifications()
	n.log_attack(12, True, False, [['aa', 0.3], ['bb', 0.7]], [])
	n.log_attack(12, True, False, [['aa', 0.3], ['bb', 0.7]], [['aa', 0.1], ['bb', 0.938373939443]])
	n.log_attack(12, True, False, [['aa', 0.3], ['bb', 0.7]], [])
	n.log_attack(12, True, False, [['aa', 0.3], ['bb', 0.7]], [])
	n.log_attack(1, True, False, [['aa', 0.3], ['bb', 0.7]], [])

	if False:
		n.counts[1000] = 2
		n.counts[900000] = 30

		n.send_daily_report()
		n.send_daily_report()
		n.send_daily_report()
