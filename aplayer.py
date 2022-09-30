
import math
from typing import Sequence
from config import *
from PIL import Image
from pathlib import Path
import os
import db
import time
import mpv
import records
import threading
import yt_dlp
import youtube_title_parse as ytp

PLAYLIST_EXTENSION = '.m3u'


def convertImage(filename):
    while not os.path.exists(filename):
        time.sleep(0.1)
    if filename.endswith(ART_FORMAT):
        savepath = filename
    else:
        im = Image.open(filename)
        savepath = filename.rsplit('.', maxsplit=1)[0] + '.' + ART_FORMAT
        rgb_im = im.convert('RGB')
        rgb_im.save(savepath)
        os.remove(filename)


class VoidLogger(object):

    def debug(msg):
        pass

    def warning(msg):
        pass

    def error(msg):
        pass


class ThumbnailConverter(object):
    def debug(msg):
        fine_msg = msg[7::]
        if not fine_msg.startswith('Writing video th'):
            pass
        else:
            unconverted_thumb = fine_msg.rpartition('to: ')[2]
            threading.Thread(
                target=convertImage, args=(unconverted_thumb,)).start()

    def warning(msg):
        pass

    def error(msg):
        pass


class Aplayer:

    DEFAULT_QUEUE = 'Queue'
    subqueue_creation_pos = 0
    subqueue_length = 0
    MAX_SECONDS_NO_PREV = 3  # If get_time_pos < max, prev() = rewind to 0 secs
    YT_DLP_OPTIONS = {  # IMPORTANT. No OUTTMPL info.
        'extractaudio': True,
        'quiet': True,
        'format': 'bestaudio/best',
        'playlist': True,
        'logger': VoidLogger,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': DOWNLOADS_CODEC,
            'preferredquality': '192'
        }]
    }

    player = mpv.MPV(
        video=False, ytdl=True, ytdl_format='best',
        ytdl_raw_options='yes-playlist=', keep_open=True)
    online_queue = False
    wait_stream_lock = False
    dl_on_stream = False
    _download_queue_titles = []
    _download_index = -1
    _current_download_percent = -1
    _current_playlist_title = DEFAULT_QUEUE
    _loading_list = False
    _is_shuffling = False
    _prog_hook_added = False

    def _mpv_wait():
        time.sleep(0.001)

    def _prog_hook(d: dict):
        # TODO: implement properly
        # TODO: Reports the progress of the least completed download
        if d['status'] == 'finished':
            Aplayer._download_index -= 1
            if Aplayer._download_index < 0:
                Aplayer._current_download_percent = -1
        if d['status'] == 'downloading':
            p = d['_percent_str']
            p = math.floor(float(p.replace('%', '')))
            title = Path(d['filename']).stem
            if Aplayer.getDownloadingTitle() == title:
                Aplayer._current_download_percent = p

    def kill():
        Aplayer.player.quit(code=0)

    def getFilename() -> dict:
        return Aplayer.player._get_property('path')

    def getDownloadingTitle() -> str:
        if Aplayer._download_index <= -1:
            return ''
        else:
            return Aplayer._download_queue_titles[Aplayer._download_index]

    def next():
        Aplayer.player.playlist_next('force')

    def _should_rewind_to_zero() -> bool:
        return (
            Aplayer.get_playlist_pos() == 0
            or Aplayer.get_time_pos() >= Aplayer.MAX_SECONDS_NO_PREV
        )

    def prev():
        if not Aplayer.is_active():
            return
        if Aplayer._should_rewind_to_zero() is True:
            Aplayer.player.seek(0, 'absolute')
        else:
            Aplayer.player.playlist_prev('force')

    def clear_subqueue():
        Aplayer.subqueue_creation_pos = 0
        Aplayer.subqueue_length = 0

    def playlist_move(fromIndex: int, toIndex: int):
        Aplayer.player.playlist_move(fromIndex, toIndex)

    def _get_next_queue_index():
        return Aplayer.subqueue_creation_pos + Aplayer.subqueue_length

    def _queue_properly():
        Aplayer._mpv_wait()
        Aplayer.subqueue_length += 1
        try_queue_insert_pos = Aplayer._get_next_queue_index()
        if try_queue_insert_pos <= Aplayer.get_playlist_pos():
            Aplayer.subqueue_creation_pos = Aplayer.get_playlist_pos()
            Aplayer.subqueue_length = 1
        elif try_queue_insert_pos > Aplayer.get_playlist_count() - 1:
            Aplayer.subqueue_length = (
                Aplayer.get_playlist_count() - 1
                - Aplayer.get_playlist_pos()
            )
            Aplayer.subqueue_creation_pos = Aplayer.get_playlist_pos()
        final_queue_insert_pos = Aplayer._get_next_queue_index()
        Aplayer.playlist_move(
            Aplayer.get_playlist_count() - 1,
            final_queue_insert_pos
        )
        if Aplayer.subqueue_length == 1:
            Aplayer.subqueue_creation_pos = Aplayer.get_playlist_pos()

    def loadfile(filename: str, queue=False):
        """Load/play a file. If queue == False, the file is played immediately
        in a new playlist. If queue == True, the file is appended
        to the current playlist, or loaded in a paused state if there isn't
        an active playlist (Aplayer.is_active() == False).
        A playlist can only be either online or offline,
        and if a multi-track playlist changes
        from online to offline or vice versa, it results in a new playlist.

        The queuing algorithm used will create a subqueue of tracks
        at the index after whatever the currently playing position is,
        which clears itself after a user listens past all subqueue tracks.
        It's essentially Spotify's queuing algorithm,
        but going to previous tracks doesn't affect the upcoming track order.

        Args:
            filename (str): the fully qualified filename or URL to play/queue
            queue (bool, optional): if True, queues file. Defaults to False.
        """
        online = filename.startswith('https:') is True
        Aplayer.online_queue = online
        if not queue:
            play_type = 'replace'
            if Aplayer.is_paused() is True:
                Aplayer.pauseplay()
        else:
            play_type = 'append-play'
        # TODO: IF ONLINE DOWNLOAD THUMBNAIL HERE
        title = Aplayer.get_title_from_file(filename)
        data = Aplayer.get_artist_track_trackNum(title)
        Aplayer.player.loadfile(filename, play_type)
        new_playlist_count = Aplayer.get_playlist_count()
        if queue is True and new_playlist_count > 1:
            Aplayer._queue_properly()
        elif new_playlist_count == 1:
            Aplayer.clear_subqueue()
            if queue is True and not Aplayer.is_paused():
                Aplayer.pauseplay()
        elif Aplayer.online_queue != online and queue is True:
            Aplayer.clear_subqueue()
            Aplayer.player.playlist_remove()
        if online is True and Aplayer.dl_on_stream is True:
            if Aplayer.download_thumbnail([filename], data) != '':
                t = threading.Thread(
                    target=Aplayer.download_to_audio,
                    args=([filename], data,)
                )
                t.start()
        Aplayer._mpv_wait()

    def gen_online_song():
        pass  # TODO: IMPLEMENT

    def _validate_title(url: str, known_title: str = '') -> str:
        if known_title != '':
            title = known_title.replace("|", "¦")
            return "".join(i for i in title if i not in r'\/:*?"<>')
        try:
            title = yt_dlp.YoutubeDL(
                {
                    'logger': VoidLogger,
                    'skip_download': True
                }
            ).extract_info(url, download=False).get('title', None)
        except Exception:
            return ''
        title = title.replace("|", "¦")
        return "".join(i for i in title if i not in r'\/:*?"<>')

    def get_title_from_file(filename: str = ''):
        online = Aplayer.online_queue
        if filename == '':
            filename = Aplayer.getFilename()
        if filename.startswith('http'):
            online = True
        if online is True:
            opts = {'skip_download': False, 'logger': VoidLogger}
            with yt_dlp.YoutubeDL(opts) as ydl:
                try:
                    info_dict = ydl.extract_info(filename, download=False)
                except Exception:
                    return ''
                title = info_dict.get('title', None)
                return Aplayer._validate_title(filename, title)
        else:
            return Path(filename).stem

    def get_artist_track_trackNum(title):
        options = {
            'defaultArtist': UNKNOWN_ARTIST,
            'defaultTitle': title
        }
        artist, track = ytp.get_artist_title(title, options)
        artist, track, trackNum = records.getTrackAndArtistInfo(title)
        return [artist, track, trackNum, title]

    def get_site_from_url(url: str):
        shrunk_url = url.rpartition('://www.')[2]
        if shrunk_url.startswith('http'):
            shrunk_url = url.rpartition('://')[2]
        return shrunk_url.split('/', 1)[0]

    def download_thumbnail(urls: list, data: Sequence = None):
        """
        Will download the relevant thumbnail and save it in the
        format config.ART_FORMAT. The filename will be the video title,
        with the format as the extension. Returns a the formatted title.

        This usually should not be threaded from an Aplayer function
        if this art is desired for immediate use.

        Returns:
            The path to the downloaded thumbnail, or the empty string if
            it was not downloaded.
        """
        if data is None:
            title = Aplayer.get_title_from_file(urls[0])
            artist, track, _, _ = Aplayer.get_artist_track_trackNum(title)
        else:
            artist, track, _, title = data
        if title == '':
            return ''
        dl_path = ART_PATH + DL_FOLDER_NAME + os.sep + artist + os.sep + track
        os.makedirs(os.path.dirname(dl_path), exist_ok=True)
        tdl = yt_dlp.YoutubeDL({
            'outtmpl': dl_path,  # TODO -> ART_PATH/-Downloads-
            'writethumbnail': True,
            "logger": ThumbnailConverter,
            'skip_download': True
        })
        with tdl:
            tdl.download(urls)
        full_path = dl_path + '.' + ART_FORMAT
        while not path_exists(full_path):
            time.sleep(0.1)
        return full_path
        # createSongDict(ThumbnailConverter.converted_thumb_paths[index]) thing

    def _is_download_index_writable() -> bool:
        """
        Returns True if the download index + 1 is within range of 0 inclusive
        and len(Aplayer._download_queue_titles) and False otherwise.

        Returns:
            True if the download index is in an acceptable range
            and False otherwise
        """
        return (
            Aplayer._download_index < len(Aplayer._download_queue_titles) - 1
            and len(Aplayer._download_queue_titles) > 0
        )

    def download_to_audio(urls: list, data: Sequence):
        # data is a sequence of artist, track, trackNum, title
        dl_index = Aplayer._download_index + 1
        if data is None:
            title = Aplayer.get_title_from_file(urls[0])
            data = Aplayer.get_artist_track_trackNum(title)
        artist, track, _, title = data
        if title == '':
            return
        options = Aplayer.YT_DLP_OPTIONS.copy()
        dl_path = DOWNLOAD_PATH + artist + os.sep + track
        options['outtmpl'] = dl_path + '.%(ext)s'
        downloader = yt_dlp.YoutubeDL(options)
        full_path = "{}.{}".format(dl_path, DOWNLOADS_CODEC)
        if not path_exists(full_path):
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with downloader as dl:
                try:
                    dl.add_progress_hook(Aplayer._prog_hook)
                    if Aplayer._is_download_index_writable() is False:
                        Aplayer._download_queue_titles.insert(dl_index, title)
                    else:
                        Aplayer._download_queue_titles[dl_index] = title
                    Aplayer._download_index += 1
                    last_dl_index = len(Aplayer._download_queue_titles) - 1
                    if Aplayer._download_index > last_dl_index:
                        Aplayer._download_index = last_dl_index
                    dl.download(urls)
                except Exception:
                    while not (Aplayer._download_index < dl_index):
                        Aplayer._download_index -= 1
        dbLink = db.DBLink()
        records.add_downloaded_song(full_path, data, dbLink)

    def loadlist(
            playlist_title: str, index: int = -1, pause_on_load: bool = False):
        Aplayer._loading_list = True
        Aplayer.clear_subqueue()
        index_chosen = index != -1
        playlist_path = PLAYLISTS_PATH + playlist_title + PLAYLIST_EXTENSION
        with open(playlist_path, 'r') as pl:
            Aplayer.online_queue = pl.readline().startswith('https:') is True
        Aplayer.player.loadlist(playlist_path)
        Aplayer._loading_list = False
        Aplayer._current_playlist_title = playlist_title
        if Aplayer.is_paused() != pause_on_load:
            Aplayer.pauseplay()
        if Aplayer._is_shuffling is True:
            if index_chosen is False:
                Aplayer.player.playlist_shuffle()
                Aplayer.player.playlist_play_index(0)
            else:
                Aplayer.player.playlist_play_index(index)
                Aplayer.player.playlist_shuffle()
                Aplayer._mpv_wait()
                Aplayer.playlist_move(Aplayer.get_playlist_pos(), 0)
        elif index_chosen is True:
            Aplayer.player.playlist_play_index(index)
            Aplayer._mpv_wait()
        else:
            Aplayer._mpv_wait()
        Aplayer._mpv_wait()

    def savelist(playlist_title: str):
        playlist_name = playlist_title
        if not playlist_title.endswith(PLAYLIST_EXTENSION):
            playlist_name = playlist_title + PLAYLIST_EXTENSION
        with open(PLAYLISTS_PATH + playlist_name, 'w') as pl:
            for filename in Aplayer.player.playlist_filenames:
                os.makedirs(os.path.dirname(pl), exist_ok=True)
                pl.write(filename)

    def save_current_playlist():
        Aplayer.savelist(Aplayer.get_current_playlist_title())

    def rename_playlist(old_playlist_title: str, new_playlist_title: str):
        if old_playlist_title == Aplayer.DEFAULT_QUEUE:
            return
        while Aplayer._loading_list is True:
            time.sleep(0.01)
        os.rename(
            PLAYLISTS_PATH + old_playlist_title + PLAYLIST_EXTENSION,
            PLAYLISTS_PATH + new_playlist_title + PLAYLIST_EXTENSION
        )

    def rename_current_playlist(new_playlist_title: str):
        Aplayer.rename_playlist(
            Aplayer.get_current_playlist_title(), new_playlist_title)
        Aplayer._current_playlist_title = new_playlist_title

    def get_playlist_names() -> list:
        ret = []
        for _, _, filenames in os.walk(PLAYLISTS_PATH):
            for filename in filenames:
                ret.append(os.path.abspath(PLAYLISTS_PATH + filename))
        return ret

    def set_dl_on_stream(dl_on_stream=False):
        Aplayer.dl_on_stream = dl_on_stream

    def pauseplay():
        Aplayer.player._set_property('pause', not Aplayer.is_paused())

    def is_paused():
        return Aplayer.player._get_property('pause')

    def is_finished_downloading():
        return Aplayer._download_index < 0

    def wait_until_playing():
        Aplayer.player.wait_until_playing()

    def try_wait_until_stream() -> bool:
        """Tries to wait for an audio stream to start.
        Fast-returns if the audio is paused, or is_loaded() == True.
        """
        if Aplayer.is_loaded() is True:
            return
        Aplayer._mpv_wait()
        if not Aplayer.is_paused():
            Aplayer.player.wait_until_playing()

    def try_wait_for_playback() -> bool:
        """Blocks until current title playback is finished
        if is_loaded() == True.
        """
        if not Aplayer.is_loaded():
            return
        Aplayer.player.wait_for_playback()
        return

    def seek(seconds: float, relative=True):
        """Seek types are either relative or absolute

        Args:
            seconds (int): _description_
            type (str, optional): _description_. Defaults to ''.
        """
        duration = Aplayer.get_duration()
        time_pos = Aplayer.get_time_pos()
        if duration == -1 or not Aplayer.is_active():
            return
        if relative is True:
            if time_pos + seconds >= duration - 1:
                Aplayer.next()
            elif time_pos + seconds <= 0.1:  # 0.1 in case of minor defects
                Aplayer.prev()
            else:
                Aplayer.player.seek(seconds, 'relative')
        else:
            if seconds >= duration:
                Aplayer.next()
            elif seconds < 0:
                Aplayer.prev()
            else:
                Aplayer.player.seek(seconds, 'absolute')

    def get_duration() -> float:
        ret = Aplayer.player._get_property('duration')
        if ret is None:
            ret = -1
        return ret

    def get_current_playlist_title():
        return Aplayer._current_playlist_title

    def get_current_downloading_title():
        return Aplayer._download_queue_titles[Aplayer._download_index]

    def get_current_downloading_percentage():
        return Aplayer._current_download_percent

    def get_playlist_pos() -> float:
        return Aplayer.player._get_property('playlist-pos')

    def get_time_pos() -> float:
        ret = Aplayer.player._get_property('time-pos')
        if ret is None:
            ret = -1
        return ret

    def get_playlist_count():
        return Aplayer.player._get_property('playlist-count')

    def get_number_of_playlists():
        count = 0
        for _, _, filenames in os.walk(PLAYLISTS_PATH):
            for filename in filenames:
                count += 1
        return count

    def get_playlist_pos() -> int:
        """Returns the index loaded for current playback.
        (This fetches the mpv 'playlist-pos' property.)

        Returns:
            int: currently playing position
        """
        return Aplayer.player._get_property('playlist-pos')

    def is_active():
        return not Aplayer.get_playlist_pos() == -1

    def is_loaded():
        return Aplayer.is_active() is True and Aplayer.get_duration() > -1

    def is_shuffling():
        return Aplayer._is_shuffling

    def is_looping_track() -> bool:
        return Aplayer.player._get_property('loop') == 'inf'

    def is_looping_queue() -> bool:
        return Aplayer.player._get_property('loop-playlist') == 'inf'

    def change_loop():
        """Loops either the track, the queue
        or not at all, depending on when it is called.

        The first change_loop() call will loop the currently playing track,
        The next change_loop() call will repeat the whole queue instead of the
        individual track.
        The change_loop() call after that will stop all is_looping.
        And then it cycles back round (call no. 4 == first change_loop() call)

        This is in reverse order to spotify after clicking.
        """
        is_looping_track = Aplayer.is_looping_track()
        is_looping_queue = Aplayer.is_looping_queue()
        if not is_looping_track and not is_looping_queue:
            Aplayer.player._set_property('loop', 'inf')
        elif is_looping_track and not is_looping_queue:
            Aplayer.player._set_property('loop', False)
            Aplayer.player._set_property('loop-playlist', 'inf')
        else:
            Aplayer.player._set_property('loop', False)
            Aplayer.player._set_property('loop-playlist', False)

    def shuffle():
        if Aplayer._is_shuffling is False:
            Aplayer.player.playlist_shuffle()
        else:
            Aplayer.player.playlist_unshuffle()
        Aplayer._is_shuffling = not Aplayer._is_shuffling
        return Aplayer._is_shuffling

    def set_volume(volume: int):
        """
        Sets the volume of the audio as a percentage

        Parameters:
        volume: the new volume
        """
        Aplayer.player._set_property('volume', volume)

    def set_speed(speed: float):
        """
        Sets the speed of the audio

        Parameters:
        speed: the new speed multiplier (e.g. speed = 1.5 means 1.5x speed)
        """
        Aplayer.player._set_property('speed', speed)

    def get_volume() -> int:
        return Aplayer.player._get_property('volume')

    def get_speed() -> float:
        return Aplayer.player._get_property('speed')