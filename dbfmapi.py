import urllib
import httplib
import json
import re
import random

class DoubanRadio():
	def __init__ (self, username, password):
		self.uid = None
		self.dbcl2 = None
		self.bid = None
		self.channel = 0
		self.__login__(username, password)
		pass
	
	def set_channel(self, channel):
		self.channel = channel

	def __login__(self, username, password):
#		bid = self.__get_bid_cookie__()
		conn = httplib.HTTPConnection ("www.douban.com")
		data = urllib.urlencode({
				'form_email':username, 'form_password':password})
#		cookie = 'bid=%s; ue="%s"; as="http://www.douban.com/";' % (bid, username)
		contentType = "application/x-www-form-urlencoded"
		headers = {"Content-Type":contentType}
		conn.request("POST", "/accounts/login", data, headers)
		
		r1 = conn.getresponse()
		resultCookie = r1.getheader('Set-Cookie')

		conn.close()

		dbcl2 = re.findall('dbcl2="(.*?)"', resultCookie)[0]
		self.dbcl2 = dbcl2
		
		uid = dbcl2.split(':')[0]
		self.uid = uid

		bid = re.findall('bid="(.*?)"', resultCookie)[0]
		self.bid = bid
	
	def __format_list__(self, sidlist, verb=None):
		if sidlist is None or len(sidlist) == 0:
			return ''
		else:
			if verb is not None:
				return ''.join(map(lambda s: '|'+str(s)+':'+str(verb), sidlist))
			else:
				return ''.join(map(lambda s: '|'+str(s), sidlist))
				

	def new_playlist(self, history=[]):
		params = self.__get_default_params__('n')
		params['h'] = self.__format_list__(history, True)

		results = self.__remote_fm__(params)

		return json.loads(results)['song']
	
	def __get_default_params__ (self, typename=None):
		params = {}
		for i in ['aid', 'channel', 'du', 'h', 'r', 'rest', 'sid', 'type', 'uid']:
			params[i] = ''

		params['r'] = random.random()
		params['uid'] = self.uid
		params['channel'] = self.channel
		if typename is not None:
			params['type'] = typename

		return params

	
	def __remote_fm__(self, params):
		conn = httplib.HTTPConnection("douban.fm")
		data = urllib.urlencode(params)
		cookie = 'dbcl2="%s"; bid="%s"' % (self.dbcl2, self.bid)
		header = {"Cookie": cookie}

		conn.request('GET', "/j/mine/playlist?"+data, None, header)
		result = conn.getresponse().read()

		conn.close()
		return result

	def del_song(self, sid, aid, rest=[]):
		params = self.__get_default_params__('b')
		params['sid'] = sid
		params['aid'] = aid
		params['rest'] = self.__format_list__(rest)

		result = self.__remote_fm__(params)
		return json.loads(result)['song']

	def fav_song(self, sid, aid):
		params = self.__get_default_params__('r')
		params['sid'] = sid
		params['aid'] = aid

		self.__remote_fm__(params)
		## ignore the response

	def unfav_song(self, sid, aid):
		params = self.__get_default_params__('u')
		params['sid'] = sid
		params['aid'] = aid

		self.__remote_fm__(params)

	def skip_song(self, sid, aid, history=[]):
		params = self.__get_default_params__('s')
		params['h'] = self.__format_history__(history)
		params['sid'] = sid
		params['aid'] = aid
	
		result = self._remote_fm__(params)
		return json.loads(result)['song']

	def played_song(self, sid, aid):
		params  = self.__get_default_params__('e')
		params['sid'] = sid
		params['aid'] = aid

		self.__remote_fm__(params)

	def played_list(self, history=[]):
		params = self.__get_default_params__('p')
		params['h'] = self.__format_history__(history)
		
		results = self.__remote_fm__(params)
		return json.loads(results)['song']



