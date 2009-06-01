import friendfeed
import urllib
import logging
from utils import selfmemoize

timeout = 600

class FriendFeed(object):
    def __init__(self, auth_nickname=None, auth_key=None):
        """Creates a new FriendFeed session for the given user.

        The credentials are optional for some operations, but required for
        private feeds and all operations that write data, like publish_link.
        """
        self.service = friendfeed.FriendFeed(auth_nickname, auth_key)
    
    @selfmemoize("friendfeed.fetch_services", time = timeout)
    def fetch_services(self, **kwargs):
        """ Returns a list of all the available services """
        return self.service._fetch_feed("/api/services", **kwargs)
	
    @selfmemoize("friendfeed.fetch_public_feed", time = timeout)
    def fetch_public_feed(self, **kwargs):
        """Returns the public feed with everyone's public entries.

        Authentication is not required.
        """
        return self.service._fetch_feed("/api/feed/public", **kwargs)

    #@selfmemoize("friendfeed.fetch_user_feed:%s", time = timeout)
    def fetch_user_feed(self, nickname, **kwargs):
        """Returns the entries shared by the user with the given nickname.

        Authentication is required if the user's feed is not public.
        """
        return self.service._fetch_feed(
            "/api/feed/user/" + urllib.quote_plus(nickname), **kwargs)

    @selfmemoize("friendfeed.fetch_user_service_feed:%s,%s", time = timeout)
    def fetch_user_service_feed(self, nickname, service, **kwargs):
        """Returns the entries shared by the user with the given nickname.

        Authentication is required if the user's feed is not public.
        """
		
        kwargs["service"] = service
		
        return self.service._fetch_feed(
            "/api/feed/user/" + urllib.quote_plus(nickname), **kwargs)
	
    @selfmemoize("friendfeed.fetch_user_profile:%s", time = timeout)
    def fetch_user_profile(self, nickname, **kwargs):
        """Returns the user profile with the given nickname.

        Authentication is required if the user's feed is not public.
        """
        return self.service._fetch_feed(
            "/api/user/" + urllib.quote_plus(nickname) + "/profile", **kwargs)
	
    @selfmemoize("friendfeed.fetch_entry:%s", time = timeout)
    def fetch_entry(self, entry, **kwargs):
        """Returns the user profile with the given nickname.
        Authentication is required if the user's feed is not public.
        """
		
        kwargs.update(entry_id = entry)

        return self.service._fetch_feed(
            "/api/feed/entry", **kwargs)
    
    @selfmemoize("friendfeed.search:%s", time = timeout)
    def search(self, q, **kwargs):
        """Searches over entries in FriendFeed.

        If the request is authenticated, the default scope is over all of the
        entries in the authenticated user's Friends Feed. If the request is
        not authenticated, the default scope is over all public entries.

        The query syntax is the same syntax as
        http://friendfeed.com/advancedsearch
        """
        return self.service.search(q, **kwargs)