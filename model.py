from google.appengine.ext import db
from google.appengine.api import memcache

from django.utils import simplejson

import logging
import re
import random

from utils import selfmemoize, memoize

class JsonModel(db.Model): 
	def to_json(self): 
		data = {} 
		for prop in self.properties().values(): 
			if not isinstance(prop, db.ReferenceProperty) :
				data[prop.name] = prop.get_value_for_datastore(self) 
		return simplejson.dumps(data) 
	
	def to_dict(self): 
		data = {} 
		for prop in self.properties().values(): 
			if not isinstance(prop, db.ReferenceProperty) :
				data[prop.name] = prop.get_value_for_datastore(self) 
		return data
		
class ChannelType(JsonModel):
	'Keyed off the FriendFeed Type'
	Name = db.StringProperty()
	AmplifeederType = db.IntegerProperty()
	
	@staticmethod
	def Create(friendfeedname, name, amplifeedertype):
		ct = ChannelType(key_name = friendfeedname)
		ct.Name = name
		ct.AmplifeederType = amplifeedertype
		
		ct.put()

	@staticmethod
	def Get(friendfeedname):
		return Channel.get_by_key_name(friendfeedname)
		
class Channel(JsonModel):
	ChannelType = db.StringProperty()
	Title = db.StringProperty()
	Data = db.StringProperty()
	DisplayStatus = db.StringProperty()
	FeedParameter = db.StringProperty()
	FeedStatus = db.StringProperty()
	FeedUri = db.StringProperty()
	Help = db.StringProperty()
	Id = db.StringProperty()
	IsCustomSource = db.BooleanProperty()
	IsEnabled = db.BooleanProperty()
	LastUpdated = db.DateTimeProperty(auto_now = True)
	SourceTypeName = db.StringProperty()
	
	@staticmethod
	def CreateDefault():
		c = Channel()
		c.Title = "You Tube"
		c.IsEnabled = True
		c.put()
	
	
	@staticmethod
	def GetNextChannelToPing():
		return db.Query(Channel).order("LastUpdated").get()
		
	@staticmethod
	def GetChannelsByEnabled(enabled):
		'unlikely to have more than 100 channels'
		return db.Query(Channel).filter("IsEnabled", enabled).fetch(100)		

class FeedItem(JsonModel):
	PrettyDate = db.DateTimeProperty()
	CommentCount = db.IntegerProperty(default = 0)
	Data = db.StringProperty()
	Date = db.DateTimeProperty()
	SourceTitle = db.StringProperty()
	SourceTypeName = db.StringProperty()
	Title = db.StringProperty()
	ChannelType = db.StringProperty()
	Description = db.TextProperty()
	DisplayStatus = db.StringProperty()
	Id = db.StringProperty()
	ItemContentPreview = db.StringProperty()
	ItemType = db.StringProperty()
	PublishDate = db.DateTimeProperty()
	SourceId = db.StringProperty()
	SourceLink = db.StringProperty()
	Channel = db.ReferenceProperty(Channel)
	
	@staticmethod
	def GetAllFeedItems():
		return db.Query(FeedItem).fetch(100)
	
	@staticmethod
	def GetFeedItemsForChannel(channel):
		return db.Query(FeedItem).filter("Channel", channel).fetch(100)

class Settings(JsonModel):
	Username = db.StringProperty(default = "kinlan")
	Configured = db.BooleanProperty(default = False)
	Title = db.StringProperty(default = "")
	Tagline = db.StringProperty(default = "")
	About = db.StringProperty(default = "")
	CustomCSS = db.StringProperty(default = "")
	Theme = db.StringProperty(default = "disorder")
	
	@staticmethod
	def CreateDefault():
		c = Settings(key_name="default_setting")
		c.Username = "kinlan"
		c.Title = "Cool Title"
		c.Tagline = "123"
		c.About = "About This"
		c.CustomCSS = ""
		c.Theme = "disorder"
		c.put()
		
		return c
	
	@staticmethod
	@memoize("Settings")	
	def Get():
		return Settings.get_by_key_name("default_setting")
	
	def Update(self):
		'Updates the settings and clears the cache.'
		memcache.set("Settings", self, 60)		
		self.put()
		
class Tag(JsonModel):
	Id = db.StringProperty()
	Name = db.StringProperty()
	
	@staticmethod
	def CreateDefault():
		c = Tag()
		c.Name = "You Tube"
		c.Id = "123"
		c.put()
	
	@staticmethod
	def GetTags(page = 1, limit = 10):
		return db.Query(Tag).fetch( limit)

