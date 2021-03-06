import smtplib, os, sys

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

from log import Logging

class Mailer():
	"""
		This class sends mails via smtp and reads the configuration from
		env vars.
	"""

	def __init__(self):
		"""
			Get all configuration from env. vars.
		"""

		for k in ['MAIL_HOST', 'MAIL_PORT', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_FROM', 'MAIL_TO']:
			if k not in os.environ:
				Logging.log("Missing value "+ k +" in environment for mail configuration!", Logging.LEVEL_ERROR)

		self.server = os.environ.get("MAIL_HOST") 
		self.port = int(os.environ.get("MAIL_PORT"))
		self.user = os.environ.get("MAIL_USERNAME") 
		self.password = os.environ.get("MAIL_PASSWORD")
		self.sender = os.environ.get("MAIL_FROM")
		self.to = os.environ.get("MAIL_TO")

	def send(self, text, subject="", debug=False):
		"""
			Sends a mail via smtp to the adress specified in env. vars.
			Args:
				text (string): The content of the email (should be html)
				subject (string): The subject of the email.
				debug (bool): Active the smtp debugging (outputs all messages between smtp server and class)
		"""
		try:
			# create mail
			msg = MIMEMultipart()
			msg['From'] = self.sender
			msg['To'] = self.to
			msg['Date'] = formatdate()
			msg['Subject'] = "[PRP] " + (subject if len(subject) > 0 else "Notification")
			msg.attach(MIMEText(text, _subtype='html', _charset='utf-8'))

			# smtp connection and authentication
			client = smtplib.SMTP(host=self.server, port=self.port)
			if debug:
				client.set_debuglevel(1)
			client.ehlo()
			client.starttls()
			client.ehlo()
			client.login(self.user, self.password)

			# send the mail
			try:
				client.sendmail(self.sender, self.to, msg.as_string())
			finally:
				client.quit()

		except:
			Logging.log("Error sending mail!", Logging.LEVEL_ERROR)

# Testing code for users, run via:
# 	docker exec --user www-data protection_proxy python /proxy/mail.py
#	docker exec --user www-data protection_proxy python /proxy/mail.py --debug
if __name__ == "__main__":
	mailer = Mailer()
	mailer.send(
		"Hello user,\nthis is a testmail to verify that SMTP is configured correctly.\n\nProtective Reverse Proxy",
		"Testmail",
		debug=len(sys.argv) > 1 and sys.argv[1] == "--debug"
	)