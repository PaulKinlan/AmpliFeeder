import re
import urllib2

from google.appengine.ext import webapp

import model
import friendfeed
import logging


class Ping(webapp.RequestHandler):
	'Calls an channel to get the latest data'
	def get(self):
		channel = model.Channel.GetNextChannelToPing()
		service = friendfeed.FriendFeed()
		logging.info(channel.key().name())
		feed = service.fetch_user_feed("kinlan", service = channel.key().name())
		for entry in feed["entries"]:
			item = model.FeedItem(key_name = channel.key().name() + entry[u"id"])
			item.Id =  entry[u"id"]
			item.Title = entry[u"title"]
			item.Date = entry[u"published"]
			item.SourceLink = entry[u"link"]
			item.SourceTypeName = entry[u"service"][u"id"].title()
			item.PublishDate = entry[u"published"]
			item.Channel = channel
			
			item.put()
		
		#Update the Channel
		channel.put()
		
		# Do Something with data
		
		