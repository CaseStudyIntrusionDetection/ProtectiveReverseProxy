import smtplib

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

from log import Logging

class Mailer():

	def __init__(self):

		self.server = "system"
      	self.port = int("587")
		self.user = "aaa@system"
		self.password = "secret"
		self.sender = "me@system"
		self.to = "admin@system"

	def send(self, text, subject=""):
		try:
			msg = MIMEMultipart()
			msg['From'] = self.sender
			msg['To'] = self.to
			msg['Subject'] = "[PRP] " + (subject if len(subject) > 0 else "Notification")
			msg.attach(MIMEText(text))

			client = smtplib.SMTP(host=self.server, port=self.port)
			client.ehlo()
			client.starttls()
			client.ehlo()
			client.login(self.user, self.password)

			try:
				client.sendmail(self.sender, self.to, msg.as_string())
			finally:
				client.quit()

		except:
			Logging.log("Error sending mail!", Logging.LEVEL_WARN)