import smtplib, os, sys

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

from log import Logging

class Mailer():

	def __init__(self):
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
		try:
			msg = MIMEMultipart()
			msg['From'] = self.sender
			msg['To'] = self.to
			msg['Date'] = formatdate()
			msg['Subject'] = "[PRP] " + (subject if len(subject) > 0 else "Notification")
			msg.attach(MIMEText(text))

			client = smtplib.SMTP(host=self.server, port=self.port)
			if debug:
				client.set_debuglevel(1)
			client.ehlo()
			client.starttls()
			client.ehlo()
			client.login(self.user, self.password)

			try:
				client.sendmail(self.sender, self.to, msg.as_string())
			finally:
				client.quit()

		except:
			Logging.log("Error sending mail!", Logging.LEVEL_ERROR)

if __name__ == "__main__":
	mailer = Mailer()
	mailer.send(
		"Hello user,\nthis is a testmail to verify that SMTP is configured correctly.\n\nProtective Reverse Proxy",
		"Testmail",
		debug=len(sys.argv) > 1 and sys.argv[1] == "--debug"
	)