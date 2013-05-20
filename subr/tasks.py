#!/usr/bin/env python

import providers
import settings
import guessit

from os import listdir
from os.path import join, isfile, isdir, splitext, basename
from utils import logger, ratio
from collections import defaultdict


"""
    wraps the processing of a single file or folder into one class
"""
class SubrTask():
    def __init__(self, input, interactive=False):
        self.interactive = interactive

        if isfile(input) and self.is_video(input):
            self.input_files = [input]
        elif isdir(input):
            self.input_files = self.filter_videos(input)
        else:
            raise RuntimeError("an invalid path was supplied '%s'" % input)

    def run(self):
        """
            scan a folder for video files which do not have subtitles, look them up if absent.
            Returns a triple of ints: (skipped, not_found, found)
        """
        for video_file in self.input_files:
            if self.needs_subtitles(video_file):
                logger.info("processing file '%s'" % basename(video_file))
                try:
                    self.fetch_subtitles(video_file)
                except:
                    logger.info("error while processing file '%s'" % video_file)
            else:
                logger.info("already subtitled '%s'" % video_file)

    def fetch_subtitles(self, video_file):
        """
            this is the main entry point for processing a single file
        """
        attributes = self.guess_attributes(video_file)

        logger.debug("guessed attributes for '%s':\n%s" % (basename(video_file), attributes.nice_string()))
        logger.info("fetching subtitles for '%s'" % basename(video_file))

        api = providers.Bierdopje(settings.BIERDOPJE_APIKEY, self.interactive)
        alternative_subtitles = api.find_subtitles(video_file, attributes)

        if not alternative_subtitles:
            logger.warn("no subtitles found for '%s'" % video_file)
            return

        srt_filename, best_url, similarity = self.find_best_subtitle_url(video_file, attributes, alternative_subtitles)

        logger.info("best fit: '%s' [%s]" % (srt_filename, similarity))
        name, _ = splitext(video_file)
        srt_file = "%s.srt" % name
        self.store_subtitle(api, best_url, srt_file)

    def store_subtitle(self, api, best_url, srt_file):
        """
            download the subtitle and store it on disk
        """
        subtitle = api.get_subtitle(best_url)
        with open(srt_file, "w") as f:
            logger.info("writing '%s'" % srt_file)
            f.write(subtitle.encode('utf-8'))

    def find_best_subtitle_url(self, video_file, attributes, alternative_subtitles):
        """
            this function will pick the 'best suited' subtitle for the given video attributes and alternative subtitles
            the input are the attributes of the local file and a list of tuples containing the subtitle file name and download url.
        """
        best_similarity = -1
        best_url = None

        for srt_filename, url in alternative_subtitles:
            # need to add extension to filename
            srt_filename = "%s.%s" % (srt_filename, attributes["container"])
            srt_attributes = self.guess_attributes(srt_filename)
            similarity = self.compute_similarity(attributes, srt_attributes)
            logger.debug("similarity: '%s'='%s' [%s]" % (video_file, srt_filename, similarity))

            if (similarity > best_similarity):
                best_url = url
                best_similarity = similarity

        return srt_filename, best_url, best_similarity

    def compute_similarity(self, attributes, other_attributes):
        def make_default_dict(dict):
            default_dict = defaultdict(str)
            for key, value in dict.items():
                default_dict[key] = str(value)
            return default_dict

        attributes, other_attributes = make_default_dict(attributes), make_default_dict(other_attributes)

        similarity = 0
        # TODO: check weights
        similarity += ratio(attributes["series"], other_attributes["series"]) * 5
        similarity += ratio(attributes["season"], other_attributes["season"]) * 4
        similarity += ratio(attributes["episode"], other_attributes["episode"]) * 4
        similarity += ratio(attributes["releaseGroup"], other_attributes["releaseGroup"]) * 3
        similarity += ratio(attributes["format"], other_attributes["format"]) * 2
        return similarity

    def needs_subtitles(self, video_file):
        """
            check if the video file already has subtitles
        """
        f, _ = splitext(video_file)
        return not isfile(f + ".srt")

    def filter_videos(self, folder):
        """
            filter out all video files in the folder
        """
        # TODO: make recursive using os.walk
        # files = []
        # for root, dirnames, filenames in os.walk(folder):

        return [ join(folder, f) for f in listdir(folder) if isfile(join(folder,f)) and self.is_video(join(folder, f)) ]

    def is_video(self, file):
        """
            predicate used for filtering process input
        """
        _, ext = splitext(file)
        return ext in settings.VIDEO_EXTENSIONS

    def guess_attributes(self, file):
        """
            guess the attributes (title, season, episode, ...) of a given video file name
        """
        return guessit.guess_video_info(file, info = ['filename'])

"""
	inherits from SubrTask but doens't actually set the subtitles, used for dry runs
"""
class DrySubrTask(SubrTask):
	def store_subtitle(self, api, best_url, srt_file):
		logger.info("dry run, so no writing '%s'" % basename(srt_file))