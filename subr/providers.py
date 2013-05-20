#!/usr/bin/env python

import sys
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from math import ceil
from time import sleep

from utils import logger
import settings
import requests

class Bierdopje:
	API_BASE = "http://api.bierdopje.com/%s/%s/%s"
	SHOWIDS = {}

	def __init__(self, api_key, interactive=False):
		self.api_key = api_key
		self.interactive = interactive

	def _get_url(self, url):
		"""
			private helper to perform an http call
		"""
		response = requests.get(url).text

		# detect api limits reached
		try:
			doc = ET.fromstring(response)
			ec = doc.find("./response/error_code")

			if ec is not None:
				ec = ec.text
				print ec

				if ec == "50":
					timeout = ceil(float(doc.find("./response/retry_after").text)) + 1
					logger.info("api limits reached, sleeping for %s second." % timeout)
					sleep(timeout)
					return self._get_url(url)
		except:
			pass

		return response

	def _get(self, method, args):
		"""
			private helper to perform an api call
		"""
		url = self.API_BASE % (self.api_key, method, "/".join(args))
		logger.debug("fetching url '%s'" % url)
		return self._get_url(url)

	def find_subtitles(self, file, attributes):
		"""
			find all subtitles for the video with the given attributes,
			returns a list of TODO
		"""
		# lookup show id first, using the title
		show_id = str(self._get_showid(attributes))
		season_number = str(attributes["season"])
		episode_number = str(attributes["episodeNumber"])

		# do the api call
		response = self._get("GetAllSubsFor", [show_id, season_number, episode_number, "nl"])
		# parse response
		doc = ET.fromstring(response)
		results = []
		for result in doc.findall("./response/results/result"):
			srt_filename = result.find("filename").text
			download_link = result.find("downloadlink").text
			results.append((srt_filename, download_link))

		return results

	def _get_showid(self, attributes):
		"""
			find the show id, cache locally
		"""
		title = attributes["series"]

		if (title in Bierdopje.SHOWIDS):
			return Bierdopje.SHOWIDS[title]

		# do the api call
		response = self._get("GetShowByName", [title])
		# parse response
		try:
			doc = ET.fromstring(response)
			showid = doc.find("./response/showid").text
			logger.debug("show id for '%s' = '%s'" % (title, showid))
		except:
			logger.debug("unable to resolve show id for '%s'" % title)
			showid = self._get_showid_tryharder(attributes)

		Bierdopje.SHOWIDS[title] = showid
		return showid

	def _get_showid_tryharder(self, attributes):
		"""
			find the show id by querying for all series with the given name,
			either resolve interactively or pick the best match
		"""
		title = attributes["series"]
		response = self._get("FindShowByName", [title])

		#try:
		doc = ET.fromstring(response)
		results = doc.findall("./response/results/result")
		matches = []
		
		for result in results:
			matches.append({
					"showid": result.find("showid").text,
					"title": result.find("showname").text,
					"similarity": round(SequenceMatcher(a=title.lower(),
														b=result.find("showname").text.lower())
										.ratio(),
										2)
			})

		matches = sorted(matches, key=lambda x:x["similarity"], reverse=True)

		if len(matches) == 0:
			raise Exception("unable to find showid for '%s'" % title)

		input = -1

		print "> I found these matches for '%s'." % title
		for index, match in enumerate(matches):
			print "\t[%s]\t%s\t[~%s]" % (index, match["title"], match["similarity"])

		if not self.interactive:
			input = 0
			print "I'm picking '%s'." % matches[0]
		else:
			while not (input >= 0 and input < len(matches)):
				print "Enter your choice [%s, %s] and press [ENTER]:" % (0, len(matches))
				try:
					input = int(raw_input())
				except:
					print "invalid input"

		return matches[input]["showid"]

		#except:
		#	raise Exception("unable to find showid for show '%s'" % title)

	def get_subtitle(self, url):
		"""
			simply GETs the url and returns a tuple of the original filename and the srt contents as text
		"""
		return requests.get(url).text