import base64, random, string

from captcha.image import ImageCaptcha
from flask import session, render_template, request

import nginx

class Captcha():

	CHARS = 'abcdefghjkmnpqrstuvwxyz23456789'
	LEN = 5

	def __init__(self):
		self.captcha = ImageCaptcha()

	def generate_captcha(self):
		"""
			Generates a random captcha as a base64 encoded image.

			Returns: The base64 encoded image source which can be
			embedded directly into the html source (string).
		"""
		value = ''.join(random.choices(Captcha.CHARS, k=Captcha.LEN))
		image = self.captcha.generate(value)
		image = base64.b64encode(image.read()).decode()
		session['CAPTCHA_VALUE'] = value

		return 'data:image/png;base64,' + image

	def is_captcha_post(self):
		"""
			Determines whether the request to be handled is a post request
			containing a solution to the captcha.
			
			Returns: True if a captcha solving post request was received, else false.
		"""
		return 'CAPTCHA_VALUE' in session and 'NONCE_VALUE' in session \
			and 'captcha' in request.form and 'nonce' in request.form
	
	def is_captcha_safe(self):
		"""
			Is the current request authenticated by a correctly solved captcha?
		"""
		return 'CAPTCHA_SOLVED' in session and session['CAPTCHA_SOLVED']

	def handle(self):
		"""
			Handles blocked requests based on the session. Redirects the
			user to the requested page if the captcha was already solved
			correctly, otherwise displays a random captcha to be solved.

			Returns the Flask template for the corresponding html page.
		"""
		if "favicon.ico" in request.full_path:
			return nginx.block()

		if self.is_captcha_safe() or \
			( self.is_captcha_post() \
			and session['NONCE_VALUE'] == request.form['nonce'] \
			and session['CAPTCHA_VALUE'] == request.form['captcha'] ):

				session['CAPTCHA_SOLVED'] = True
				return nginx.approve()
		else:
			image = self.generate_captcha()
			nonce = ''.join(random.choices(string.ascii_letters, k=50))
			session['NONCE_VALUE'] = nonce
			return render_template("captcha.html", CAPTCHA=image, NONCE=nonce)

