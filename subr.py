#!/usr/bin/env python

import providers
import settings

from utils import logger
from collections import defaultdict
from difflib import SequenceMatcher
from os import listdir
from os.path import join, isfile, isdir, splitext
from utils import load_libraries

# load after library path has been fixed
import guessit

"""
    wraps the processing of a single file or folder into one class
"""
class SubrTask():
    def __init__(self, input):
        if isfile(input) and self.is_video(input):
            self.input_files = [input]
        elif isdir(input):
            self.input_files = self.filter_videos(input)
        else:
            raise RuntimeError("an invalid path was supplied '%s'" % input)

    def run(self):
        """
            scan a folder for video files which do not have subtitles, look them up if absent
        """
        for video_file in self.input_files:
            if self.needs_subtitles(video_file):
                logger.info("processing file '%s'" % video_file)
                self.fetch_subtitles(video_file)
            else:
                logger.info("already subtitled '%s'" % video_file)

    def fetch_subtitles(self, video_file):
        """
            this is the main entry point for processing a single file
        """
        attributes = self.guess_attributes(video_file)

        logger.debug("guessed attributes for '%s':\n%s" % (video_file, attributes.nice_string()))
        logger.info("fetching subtitles for '%s'" % video_file)

        api = providers.Bierdopje(settings.BIERDOPJE_APIKEY)
        alternative_subtitles = api.find_subtitles(video_file, attributes)

        if not alternative_subtitles:
            logger.warn("no subtitles found for '%s'" % video_file)
            return

        best_url, similarity = self.find_best_subtitle_url(video_file, attributes, alternative_subtitles)

        logger.info("best fit: '%s'='%s' [%s]" % (video_file, best_url, similarity))
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

        return best_url, best_similarity

    def compute_similarity(self, attributes, other_attributes):
        def make_default_dict(dict):
            default_dict = defaultdict(str)
            for key, value in dict.items():
                default_dict[key] = str(value)
            return default_dict

        attributes, other_attributes = make_default_dict(attributes), make_default_dict(other_attributes)

        similarity = 0
        # TODO: check weights
        similarity += self.ratio(attributes["series"], other_attributes["series"]) * 5
        similarity += self.ratio(attributes["season"], other_attributes["season"]) * 4
        similarity += self.ratio(attributes["episode"], other_attributes["episode"]) * 4
        similarity += self.ratio(attributes["releaseGroup"], other_attributes["releaseGroup"]) * 3
        similarity += self.ratio(attributes["format"], other_attributes["format"]) * 2
        return similarity

    def ratio(self, a, b):
        """
            do a fuzzy string match between strings a and b, returns a value [0, 1]
        """
        return SequenceMatcher(a=a.lower(), b=b.lower()).ratio()

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


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="finds subtitles for video files in the given folder")
    parser.add_argument('-i', '--input', help="input file or folder", action="append", required=True)
    args = parser.parse_args()

    for folder in args.folder:
        subrTask = SubrTask(folder)
        subrTask.run()