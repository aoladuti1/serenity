
import os
from math import floor
from typing import Sequence

import youtube_title_parse as ytp
import yt_dlp
from PIL import Image

import db
import records
from config import *


class VoidLogger(object):

    def debug(msg):
        pass

    def warning(msg):
        pass

    def error(msg):
        pass


class AudioDL:

    audio_codec = 'mp3'
    current_title = ''
    __download_percent = 0
    __download_index = -1
    __downloding_titles = []
    __downloading = False
    __finished = False

    yt_dlp_options = {  # IMPORTANT. No OUTTMPL info.
        'extractaudio': True,
        'quiet': True,
        'format': 'bestaudio/best',
        'playlist': True,
        'logger': VoidLogger,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': audio_codec,
            'preferredquality': '192'
        }]
    }

    def set_codec(codec):
        AudioDL.audio_codec = codec
        AudioDL.yt_dlp_options['postprocessors']['preferredcodec'] = codec

    def _prog_hook(d: dict):
        if d['status'] == 'finished':
            AudioDL.__download_index -= 1
            if len(AudioDL.__downloding_titles) > 0:
                AudioDL.__downloading_titles.pop()
                light_wait()
                AudioDL.__download_percent = 0
            else:
                AudioDL.__download_percent = 100
        if d['status'] == 'downloading':
            p = d['_percent_str']
            p = floor(float(p[0:-1]))
            if AudioDL._download_index >= len(AudioDL.__downloding_titles) - 1:
                AudioDL.__download_percent = p

    def get_online_data(valid_title: str):
        options = {
            'defaultArtist': UNKNOWN_ARTIST,
            'defaultTitle': valid_title
        }
        artist, track = ytp.get_artist_title(valid_title, options)
        artist, track, trackNum = records.getTrackAndArtistInfo(valid_title)
        return [artist, track, trackNum, valid_title]

    def download(urls: list, data: Sequence):
        artist, track, _, title = data
        if title == '':
            return
        options = AudioDL.yt_dlp_options.copy()
        dl_path = DOWNLOAD_PATH + artist + os.sep + track
        options['outtmpl'] = dl_path + '.%(ext)s'
        downloader = yt_dlp.YoutubeDL(options)
        full_path = "{}.{}".format(dl_path, DOWNLOADS_CODEC)
        if not path_exists(full_path):
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with downloader as dl:
                appended = False
                try:
                    dl.add_progress_hook(AudioDL._prog_hook)
                    AudioDL.__download_index += 1
                    AudioDL.__downloding_titles.append(title)
                    appended = True
                    AudioDL.__downloading = False
                    AudioDL.__finished = False
                    dl.download(urls)
                except Exception:
                    if appended is True:
                        AudioDL.__downloding_titles.pop()
        if len(AudioDL.__downloding_titles) == 0:
            AudioDL.__downloading = False
        dbLink = db.DBLink()
        records.add_downloaded_song(full_path, data, dbLink)
        if len(AudioDL.__downloding_titles) == 0:
            AudioDL.__finished = True

    def download_percent():
        return AudioDL.__download_percent

    def is_downloading():
        return AudioDL.__downloading

    def is_finished():
        return AudioDL.__finished

    def data_on_disk(data):
        artist, track, _, _ = data
        dl_path = DOWNLOAD_PATH + os.sep + artist + os.sep + track
        full_path = "{}.{}".format(dl_path, DOWNLOADS_CODEC)
        return path_exists(full_path)
