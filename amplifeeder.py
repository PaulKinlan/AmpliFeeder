#!/usr/bin/env python

import wsgiref.handlers
import re # Regular expressions
import random

import os
import datetime
import time

import md5
import base64
import urllib
import sys
import logging

from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.db import djangoforms

from django.utils import simplejson

import friendfeedproxy

import simplejsondate
import model
import pinger
import admin

def prettydate(timestamp):
	ageresult = datetime.datetime.today() - timestamp
	
	if ageresult.days < 1:
		hours = ageresult.seconds / 3600
		if hours == 0:
			return "not long "
		elif hours == 1:
			return str(hours) + " hour "
		else:
			return str(hours) + " hours "
	else:
		days = str(ageresult.days)
		if days == "1":
			return days + " day "
		else:
			return days + " days "
	
	return 

def smart_bool(s):
	if s is True or s is False:
		return s
	s = str(s).strip().lower()
	return not s in ['false','f','n','0','']		

def RenderThemeTemplate(templatename, data):
	path = os.path.join(os.path.dirname(__file__), "Templates", templatename)
	logging.info(path)
	return template.render(path, data)

def Render(name, data):
	path = os.path.join(os.path.dirname(__file__), name)
	return template.render(path, data)

channelMap = {
	"blog" : "CustomRSS20",
	"delicious" : "Delicious",
	"digg" : "Digg",
	"disqus" : "Digg",
	"facebook" : "Facebook",
	"flickr" : "Flickr",
	"googlereader": "GoogleReader",
	"internal" : "Internal",
	"linkedin" : "LinkedIn",
	"reddit" : "Reddit",
	"twitter": "Twitter",
	"vimeo" : "Vimeo",
	"mixx" : "Mixx",
	"youtube" : "YouTube",
	"picasa" : "Picasa",
	"tumblr" : "Tumblr",
	"upcoming" : "Upcoming",
	"stumbleupon" : "Stumbleupon"
}

serviceTypeMap = {
	"Bookmark" : ["digg", "delicious", "reddit", "stumbleupon", "mixx"],
	"Video" : ["youtube", "vimeo"],
	"Image" : ["flickr", "picasa"],
	"Post" : ["upcoming", "tumblr", "microblog", "customatom", "customrss20", "googlereader"],
	"Note": ["twitter", "facebook", "lastfm", "brighkite"]
}

class FriendFeedConverter():
	def ConvertChannels(self, profile):	
		channels = []
		for service in profile[u"services"]:
			
			if u"profileUrl" in service:
				
				channel = {}
				channel.update(ChannelType = service[u"name"])
				channel.update(FeedUri = service[u"profileUrl"])
				channel.update(Name = service[u"name"])
				channel.update(Title = service[u"name"])
				channel.update(IsEnabled = True)
				channel.update(Id = service[u"id"])
				channel.update(SourceTypeName = channelMap[service[u"id"]])
				channels.append(channel)
		
		return channels
	
	def ConvertUserFeed(self, profile):		
		#Get The Service
		# Convert Comment Counts
		d = {}
		feeditems = []
		comments = []
		for entry in profile[u"entries"]:
			item = {}
						
			timeago = prettydate(entry[u"published"])
			
			item.update(Title = entry[u"title"])
			item.update(PublishDate = entry[u"published"])
			item.update(PrettyDate = timeago + " ago")
			item.update(Date = entry[u"published"])
			item.update(Description = entry[u"title"])
			
			
			#If the link contains media embed that.
			if u"media" in entry and len(entry[u"media"]) > 0:
				logging.info(entry)
				if u"thumbnails" in entry[u"media"][0] and entry[u"media"][0][u"thumbnails"] != "None":
					item.update(ItemContentPreview = entry[u"media"][0][u"thumbnails"][0][u"url"])
			
			item.update(SourceLink = entry[u"link"])
			item.update(SourceTypeName = channelMap[entry[u"service"][u"id"]])
			item.update(SourceTitle = entry[u"service"][u"name"])
			item.update(Id = entry[u"id"])
			
			item.update(CommentCount = len(entry[u"comments"]))
			
			for comment in entry[u"comments"]:
				comm = {}
				comm.update(Date = comment[u"date"])
				comm.update(CommentDate = comment[u"date"])
				comm.update(CommentBody = comment[u"body"])
				comm.update(Name = comment[u"user"][u"name"])
				comm.update(Email = comment[u"user"][u"profileUrl"])
				comm.update(AmplifeederItemId = entry[u"id"])
				comments.append(comm)
			
			feeditems.append(item)
		
		d.update(FeedItems = feeditems)
		d.update(Comments = comments)
		
		return d
	
	def ConvertEntry(self, entry):
		
		#Get The Service
		# Convert Comment Counts
		d = {}
		feeditems = None
		comments = []
		for entry in entry[u"entries"]:
			item = {}
						
			timeago = prettydate(entry[u"published"])
			
			item.update(Title = entry[u"title"])
			item.update(PublishDate = entry[u"published"])
			item.update(PrettyDate = timeago + " ago")
			item.update(Date = entry[u"published"])
			item.update(SourceLink = entry[u"link"])
			item.update(SourceTypeName = channelMap[entry[u"service"][u"id"]])
			item.update(SourceTitle = entry[u"service"][u"name"])
			item.update(Description = "")
			item.update(Id = entry[u"id"])
			#If the link contains media embed that.
			if u"media" in entry and len(entry[u"media"]) > 0:
				logging.info(entry)
				item.update(ItemContent = entry[u"media"][0][u"thumbnails"][0][u"url"])
				#Work out a decent way to get the data inline.
				item.update(Data = "<img src=\"%s\" />" %entry[u"media"][0][u"content"][0][u"url"])
			
			item.update(CommentCount = len(entry[u"comments"]))
			
			for comment in entry[u"comments"]:
				comm = {}
				
				comm.update(Date = comment[u"date"])
				comm.update(CommentDate = comment[u"date"])
				comm.update(CommentBody = comment[u"body"])
				comm.update(Name = comment[u"user"][u"name"])
				comm.update(Email = comment[u"user"][u"profileUrl"])
				comm.update(AmplifeederItemId = entry[u"id"])
				comments.append(comm)
			
			feeditems = item 
		
		d.update(Item = feeditems)
		d.update(Comments = comments)
		
		return d
		
class Init(webapp.RequestHandler):
	def get(self):
		s = model.Settings.CreateDefault()
			
	
class Index(webapp.RequestHandler):
	def get(self):
		s = model.Settings.Get()
		
		#If there are no settings create them.
		if s is None:
			s = model.Settings.CreateDefault()
			
		output = ""
		if s.Configured == True:			
			output = RenderThemeTemplate("Default.tmpl", { "startup": "var ThemeName = '%s'" % s.Theme })
		else:
			s.Configured = True
			s.put()
		
		
		# First load will create load the user info in to the db.				
		self.response.out.write(output)

class Detail(webapp.RequestHandler):
	def get(self):
		s = model.Settings.Get()
		
		#If there are no settings create them.
		if s is None:
			s = model.Settings.CreateDefault()
			
		output = RenderThemeTemplate("Detail.tmpl", { "startup": "var ThemeName = '%s'" % s.Theme })
		
		
		self.response.out.write(output)
		
class AssetCombiner(webapp.RequestHandler):
	def get(self):
		filestr = self.request.get("files", "")
		
		files = filestr.split(',')
		
		for file in files:
			self.response.out.write(Render(file, {}))

class UIService(webapp.RequestHandler):
	def post(self, method):
		
		if method not in ["GetEnabledChannels","GetItemsPackage","GetPageCount", "SubmitComment", "GetFeature", "GetEnabledChannels", "GetDetailItem", "GetActiveSources", "GetTags","GetActiveSources","GetInitItemsPackage"]:
			# Don't allow anyone to call any un-meant method.
			return
		#Load this module so we can dyanmically load the class
		m = __import__("amplifeeder")
		#Import the module and then call it.
		m = getattr(m, method)()
		# Pass in the request object
		obj = m.Render(self)
	
class GetEnabledChannels():
	def Render(self, request):
		channels = model.Channel.GetChannelsByEnabled(True)
						
		request.response.out.write(simplejson.dumps(channels))
		
class GetTags():
	def Render(self, request):
		Page = request.request.get("Page", 1)
		Page = int(Page)
		
		tags = model.Tag.GetTags(Page, 10)		
		request.response.out.write("{ \"d\": [")
		tags_serialized = []
		
		for tag in tags:
			output = tag.to_json()		
			tags_serialized.append(output)
				
		request.response.out.write(','.join(tags_serialized))			
		request.response.out.write("]}")

class GetInitItemsPackage():
	def Render(self, request):
		settings = model.Settings.Get()
		converter = FriendFeedConverter()
				
		input = simplejson.loads(request.request.body)
		#{"PageSize":"16", "PageNumber":"1", "ItemFilterType":"None", "ItemFilterArgument":"None"}
				
		json = {}
		pageNumber = int(input["PageNumber"])
		# Might want to cache this
		if input["ItemFilterType"] == u"None":
			# Front page
			ff = friendfeedproxy.FriendFeed()
			feed = ff.fetch_user_feed(settings.Username, pageNumber)
			json = converter.ConvertUserFeed(feed)
		
		feedItems = []
		item = None
		pageCount = 100
		channel = None
		comments = None
				
		#json = {}
		#json.update(FeedItems = feedItems)
		json.update(Item = item)
		json.update(PageCount = pageCount)
		json.update(Channel = channel)
		
		#json.update(Comments = comments)
		json.update(Settings = settings.to_dict())
		
		d = {}
		d.update(d = json)
		
		request.response.out.write(simplejsondate.dumps(d))

class GetItemsPackage():
	def Render(self, request):
		input = simplejson.loads(request.request.body)
		
		settings = model.Settings.Get()
		converter = FriendFeedConverter()
				
		feed = {}
		
		pageNumber = int(input["PageNumber"])
		
		if input["ItemFilterType"] is None or  input["ItemFilterType"] == "None" :
			ff = friendfeedproxy.FriendFeed()
			feed = ff.fetch_user_feed(settings.Username, pageNumber, service = input["ItemFilterArgument"])
		elif input["ItemFilterType"] == "Source":
			ff = friendfeedproxy.FriendFeed()
			feed = ff.fetch_user_service_feed(settings.Username, input["ItemFilterArgument"], pageNumber)
		elif input["ItemFilterType"] == "Search":
			ff = friendfeedproxy.FriendFeed()
			kwargs = {}
			kwargs["from"] = settings.Username
			query = input["ItemFilterArgument"]

			feed = ff.search(query, pageNumber,  **kwargs )
		elif input["ItemFilterType"] == "ItemType":
			argument = input["ItemFilterArgument"]
			logging.info("Filtering on Type %s" % argument)
						
			ff = friendfeedproxy.FriendFeed()
			feed = ff.fetch_user_services_feed(settings.Username, serviceTypeMap[argument], pageNumber)
		
		json = converter.ConvertUserFeed(feed)
		
		d= {}
		d.update ( d = json)
		
		request.response.out.write(simplejsondate.dumps(d))

class GetPageCount():
	def Render(self, request):
		PageSize = request.request.get("PageSize","")
		ItemFilterType = request.request.get("ItemFilterType","")
		ItemFilterArgument = request.request.get("ItemFilterArgument","")
		
		request.response.out.write("{}")

class SubmitComment():
	def Render(self, request):
		request.response.out.write("{}")

class GetEnabledChannels():
	def Render(self, request):
		request.response.out.write("{}")

class GetActiveSources():
	'Gets all Active Sources'
	def Render(self, request):		
		settings = model.Settings.Get()
		converter = FriendFeedConverter()
								
		channels = []
		
		ff = friendfeedproxy.FriendFeed()
		feed = ff.fetch_user_profile(settings.Username)
		channels = converter.ConvertChannels(feed)
		
		d = { }
		d.update(d = channels)
		
		request.response.out.write(simplejsondate.dumps(d))
		
class GetDetailItem():
	def Render(self, request):
		input = simplejson.loads(request.request.body)
		#{"itemID":"75377fc9-1b93-58ff-c066-defcb55ff45e", "numberToReturn":"10"}
		settings = model.Settings.Get()
		converter = FriendFeedConverter()
								
		channels = []
		
		ff = friendfeedproxy.FriendFeed()
		entry = ff.fetch_entry(input[u"itemID"])		
		detail = converter.ConvertEntry(entry)
		feed = ff.fetch_user_feed(settings.Username, 1 , service = detail["Item"]["SourceTypeName"].lower())
		json = converter.ConvertUserFeed(feed)
		
		detail.update(Settings = settings.to_dict())
		detail.update(FeedItems = json["FeedItems"])

		d = { }
		d.update(d = detail)
		
		request.response.out.write(simplejsondate.dumps(d))
		
class GetFeature():
	def Render(self, request):
		itemtype = request.request.get("itemtype", "")
		numberToReturn = request.request.get("numberToReturn", 10)
		numberToReturn = int(numberToReturn)
		
		request.response.out.write("{}")
	
def main():
    application = webapp.WSGIApplication([(r'/', Index), (r'/default.aspx', Index), (r'/admin/Settings', admin.Settings),(r'/Init', Init) ,(r'/friendfeed/ping', pinger.Ping), (r'/AssetCombiner.ashx', AssetCombiner), (r'/UIService.asmx/(.+)', UIService), (r'/detail.aspx', Detail)], debug=False)
    wsgiref.handlers.CGIHandler().run(application);

if __name__ == '__main__':
  main()