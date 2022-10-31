
import asyncio
import os
from math import floor
from typing import Sequence

import youtube_title_parse as ytp
import yt_dlp
from PIL import Image
from youtubesearchpython.__future__ import VideosSearch

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
    __downloading_titles = []
    __converting_titles = []
    __downloading = False
    __finished = True

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

    def __prog_hook(d: dict):
        if d['status'] == 'finished':
            AudioDL.__download_index -= 1
            if AudioDL.__downloading_titles:
                AudioDL.__downloading_titles.pop()
                light_wait()
                AudioDL.__download_percent = 0
            else:
                AudioDL.__download_percent = 100
        if d['status'] == 'downloading':
            p = d['_percent_str']
            p = floor(float(p[0:-1]))
            if AudioDL.__download_index >= len(AudioDL.__downloading_titles)-1:
                AudioDL.__download_percent = p

    def validate_title(title: str) -> str:
        if title is None:
            return None
        txt = title.replace("|", "¦")
        txt = txt.encode('ascii', 'ignore').decode()
        return "".join(i for i in txt if i not in r'\/:*?"<>')

    def scrape_title(url: str, force_title: str = ''):
        if force_title != '':
            return force_title
        else:
            return yt_dlp.YoutubeDL(
                {
                    'logger': VoidLogger,
                    'skip_download': True,
                    'quiet': True
                }
            ).extract_info(url, download=False).get('title', None)

    def get_online_data(valid_title: str):
        options = {
            'defaultArtist': UNKNOWN_ARTIST,
            'defaultTitle': valid_title
        }
        artist, track = ytp.get_artist_title(valid_title, options)
        artist, track, trackNum = records.getTrackAndArtistInfo(valid_title)
        return [artist, track, trackNum, valid_title]

    async def __search_youtube(query):
        try:
            videosSearch = VideosSearch(query, limit=1)
            videosResult = await videosSearch.next()
            return [videosResult['result'][0]['link'],
                    videosResult['result'][0]['title']]
        except Exception:
            return [None, None]

    def get_link_and_title(query):
        loop = asyncio.new_event_loop()
        return loop.run_until_complete(AudioDL.__search_youtube(query))

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
                appended_c = False
                appended_d = False
                try:
                    dl.add_progress_hook(AudioDL.__prog_hook)
                    AudioDL.__download_index += 1
                    AudioDL.__downloading_titles.append(title)
                    appended_d = True
                    AudioDL.__downloading = False
                    AudioDL.__finished = False
                    AudioDL.__converting_titles.append(title)
                    dl.download(urls)
                    appended_c = True
                    if not AudioDL.__downloading_titles:
                        AudioDL.__downloading = False
                    dbLink = db.DBLink()
                    records.add_downloaded_song(full_path, data, dbLink)
                    light_wait()
                    if AudioDL.__converting_titles:
                        AudioDL.__converting_titles.pop()
                    AudioDL.__finished = (not AudioDL.__converting_titles
                                          and not AudioDL.__downloading_titles)
                except Exception:
                    if appended_c is True:
                        if AudioDL.__converting_titles:
                            AudioDL.__converting_titles.pop()
                    if appended_d is True:
                        if AudioDL.__downloading_titles:
                            AudioDL.__downloading_titles.pop()

    def download_percent():
        return AudioDL.__download_percent

    def is_downloading():
        return AudioDL.__downloading

    def download_started():
        return len(AudioDL.__downloading_titles) != 0

    def is_finished():
        return AudioDL.__finished

    def active_titles():
        return AudioDL.__converting_titles

    def data_on_disk(data):
        ''' Returns true if there is a file matching the data on disk. '''
        artist, track, _, _ = data
        dl_path = DOWNLOAD_PATH + os.sep + artist + os.sep + track
        full_path = "{}.{}".format(dl_path, DOWNLOADS_CODEC)
        return path_exists(full_path)
