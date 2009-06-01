from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.db import djangoforms

from django.utils import simplejson

import friendfeedproxy

import simplejsondate
import model
import logging
import pinger

class SettingsForm(djangoforms.ModelForm):
	class Meta():
		model = model.Settings

class Settings(webapp.RequestHandler):
	def post(self):
		data = SettingsForm(data = self.request.POST)
		if data.is_valid():
			settings = data.save(commit = False)
			
			saved_settings = model.Settings(key_name="default_setting", **dict([(prop, getattr(settings, prop)) for prop in model.Settings.properties()]))
			saved_settings.save()
			
			self.redirect("/")
		else:
			self.response.out.write('<html><body>'
                            '<form method="POST" '
                            'action="/Settings"><input type=hidden value=\"default_setting\" />'
                            '<table>')
			# This generates our shopping list form and writes it in the response
			self.response.out.write(SettingsForm(instance = model.Settings.Get()))
			self.response.out.write('</table>'
                            '<input type="submit">'
                            '</form></body></html>')

	def get(self):
		self.response.out.write('<html><body>'
                            '<form method="POST" '
                            'action="/Settings">'
                            '<table>')
		# This generates our shopping list form and writes it in the response
		self.response.out.write(SettingsForm(instance = model.Settings.Get()))
		self.response.out.write('</table>'
                            '<input type="submit">'
                            '</form></body></html>')