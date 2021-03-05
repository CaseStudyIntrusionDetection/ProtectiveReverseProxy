import os, time
from datetime import date

from mail import Mailer

class Notifications():

	CONNECTION_IDS_KEEP_ON_CLEANUP = 100
	MAX_CONNECTION_IDS = 200
	MAX_REQUESTS_PER_ID = 10

	@staticmethod
	def is_active():
		return "MAIL_TO" in os.environ and len(os.environ.get("MAIL_TO")) > 0

	def __init__(self):
		self.mailer = Mailer()
		self.attacks = {}
		self.counts = {}

		self.send_daily = "SEND_DAILY_REPORT" in os.environ and os.environ.get("SEND_DAILY_REPORT") == "true"
		self.send_emerg = "SEND_EMERGENCY" in os.environ and os.environ.get("SEND_EMERGENCY") == "true"

		self.last_attackmail = 0
		self.last_reportmail = int(time.time())

	def log_attack(self, connection_id, lda_is_attack, nn_is_attack, lda_types, nn_types = []):
		if connection_id not in self.attacks:
			self.attacks[connection_id] = []

		if len(self.attacks[connection_id]) >= Notifications.MAX_REQUESTS_PER_ID:
			self.attacks[connection_id].pop(0)
		
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

		today = int(date.today().strftime("%s"))
		if today not in self.counts:
			self.counts[today] = 0
		self.counts[today] += 1

		self.send_emergency()
		self.keep_memory_free()
		
	def format_types(self, types):
		s = []
		for t,p in types:
			s.append(t + ' (' + ("%.3f" % p) + ')')
		return ', '.join(s)

	def keep_memory_free(self):
		if len(self.attacks) > Notifications.MAX_CONNECTION_IDS:
			for cid,_ in sorted(self.attacks.items(), key=lambda l: l['time'], reverse=True)[Notifications.CONNECTION_IDS_KEEP_ON_CLEANUP:]:
				del self.attacks[cid]

	def send_emergency(self):
		current_time = int(time.time())
		if self.send_emerg and current_time - self.last_attackmail > 3600:
			self.last_attackmail = current_time
			time_range = current_time - 3600

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
		current_time = int(time.time())
		if self.send_daily and current_time - self.last_reportmail > 86400:
			self.last_reportmail = current_time

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
