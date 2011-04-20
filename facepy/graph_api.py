import requests
from urllib import urlencode

from exceptions import *

try:
    import json
except ImportError:
    import simplejson as json

class GraphAPI(object):
    
    def __init__(self, oauth_token=None):
        self.oauth_token = oauth_token
        
    def get(self, path='', **options):
        """Get an item from the Graph API."""

        # Convert option lists to comma-separated values
        for option in options:
            if type(options[option]) == list:
                options[option] = ','.join(options[option])
        
        response = self._query(
            path = path,
            method = 'GET',
            data = options
        )
        
        if response is False:
            raise APIError('Could not get "%s".' % path)
            
        return response
        
    def post(self, path='', **data):
        """Post an item to the Graph API."""
        
        response = self._query(
            path = path,
            method = 'POST',
            data = data
        )
        
        if response is False:
            raise APIError('Could not post to "%s"' % path)
            
        return response
        
    def delete(self, path):
        """Delete an item in the Graph API."""
        
        response = self._query(
            path = path,
            method = 'DELETE'
        )
        
        if response is False:
            raise APIError('Could not delete "%s"' % path)
            
        return response
        
    def search(self, term, type, **options):
        """
        Search for an item in the Graph API.
        
        Arguments:
        term -- A string describing the search term.
        type -- A string describing the type of items to search for *.
        **options -- Additional data, such as 'center' and 'distance'. See Facebook's Graph API documentation for details.
        
        Supported types are 'post', 'user', 'page', 'event', 'group', 'place' and 'checkin'.
        """
        
        options = dict({
            'q': term,
            'type': type,
        }, **options)
        
        response = self._query(
            path = 'search',
            method = 'GET',
            data = options
        )
        
        return response
        
        
    def _query(self, method, path, data={}):
        """Low-level access to Facebook's Graph API."""
        
        if self.oauth_token:
            data.update({'access_token': self.oauth_token })
        
        response = requests.request(method, 'https://graph.facebook.com/' + path, data=data)

        return self._parse(response.content)
        
    def _parse(self, data):
        """Parse the response from Facebook's Graph API."""
        try:
            data = json.loads(data)
        except ValueError as e:
            raise APIError(e.message)
        
        # Facebook's Graph API sometimes responds with 'true' or 'false'. Facebook offers no documentation
        # as to the prerequisites for this type of response, though it seems that it responds with 'true'
        # when objects are successfully deleted and 'false' when attempting to delete or access an item that
        # one does not have access to.
        # 
        # For example, the API would respond with 'false' upon attempting to query a feed item without having
        # the 'read_stream' extended permission. If you were to query the entire feed, however, it would respond
        # with an empty list instead.
        # 
        # Genius.
        #
        # We'll handle this discrepancy as gracefully as we can by implementing logic to deal with this behavior
        # in the high-level access functions (get, post, delete etc.).
        if type(data) is bool:
            return data
        
        if type(data) is dict:
            
            if 'error' in data:
                raise APIError(data['error']['message'])
                
            # If the response contains a 'data' key, strip everything else (it serves no purpose)
            if 'data' in data:
                data = data['data']
        
            return data