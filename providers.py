#!/usr/bin/env python

import xml.etree.ElementTree as ET

from utils import logger, load_libraries
load_libraries()

import requests

class Bierdopje:
	API_BASE = "http://api.bierdopje.com/%s/%s/%s"

	def __init__(self, api_key):
		self.api_key = api_key

	def _get_url(self, url):
		"""
			private helper to perform an http call
		"""
		return requests.get(url).text

	def _get(self, method, args):
		"""
			private helper to perform an api call
		"""
		url = self.API_BASE % (self.api_key, method, "/".join(args))
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
		# do the api call
		response = self._get("GetShowByName", [title])
		# parse response
		doc = ET.fromstring(response)
		showid = doc.find("./response/showid").text
		logger.debug("show id for '%s' = '%s'" % (title, showid))
		return showid

	def get_subtitle(self, url):
		"""
			simply GETs the url and returns a tuple of the original filename and the srt contents as text
		"""
		return requests.get(url).text