import math
import os
import time
from serenityapp.audiodl import AudioDL
from pathlib import Path

import emoji
import mpv

from serenityapp.config import *

PLAYLIST_EXTENSION = '.m3u'


def gen_MPV():
    return mpv.MPV(
        video=False, ytdl=True, ytdl_format='best',
        ytdl_raw_options='yes-playlist=', keep_open=True)


class Aplayer:

    DEFAULT_QUEUE = 'Queue'
    MAX_SECS_NO_PREV = 3  # If get_time_pos < max, prev() = rewind to 0 secs
    player = gen_MPV()
    __online_queue = False
    __playlist_title = DEFAULT_QUEUE
    __loading_list = False
    __is_shuffling = False
    __last_batch_pos = -1
    __pl_change_prop = 'brightness'
    __pl_title_prop = 'contrast'
    __subqueue_creation_pos = 0
    __subqueue_length = 0

    def kill():
        Aplayer.player.quit(code=0)

    def filename() -> str:
        return Aplayer.player._get_property('path')

    def playlist_filenames():
        return Aplayer.player.playlist_filenames

    def next():
        pl_pos = Aplayer.get_playlist_pos()
        count = Aplayer.playlist_count()
        if Aplayer.is_looping_track():
            if pl_pos != count - 1:
                Aplayer.player._set_property('playlist-pos', pl_pos + 1)
            else:
                Aplayer.player.seek(0, 'absolute')
        elif pl_pos == count - 1:
            if math.ceil(100 * Aplayer.time_pos() / Aplayer.duration()) != 100:
                Aplayer.player.seek(100, 'absolute-percent')
        else:
            Aplayer.player.playlist_next()
        if Aplayer.get_playlist_pos() == -1:
            Aplayer.__mark_playlist_change()

    def __should_rewind_to_zero() -> bool:
        return (
            Aplayer.get_playlist_pos() == 0
            or Aplayer.time_pos() >= Aplayer.MAX_SECS_NO_PREV)

    def prev():
        if not Aplayer.is_active():
            return
        if Aplayer.__should_rewind_to_zero() is True:
            Aplayer.player.seek(0, 'absolute')
        else:
            Aplayer.player.playlist_prev('force')

    def is_online():
        return Aplayer.__online_queue

    def clear_subqueue():
        Aplayer.__subqueue_creation_pos = 0
        Aplayer.__subqueue_length = 0

    def clear_queue():
        Aplayer.player.playlist_clear()
        Aplayer.clear_subqueue()
        Aplayer.__playlist_title = Aplayer.DEFAULT_QUEUE
        Aplayer.__mark_playlist_change()
        Aplayer.__mark_playlist_title_change()

    def playlist_move(fromIndex: int, toIndex: int, from_gui: bool = False):
        if not Aplayer.is_loaded():
            return
        final_index = toIndex if fromIndex > toIndex else toIndex + 1
        Aplayer.player.playlist_move(fromIndex, final_index)
        Aplayer.__mark_playlist_change()

    def play_index(index):
        Aplayer.player.playlist_play_index(index)

    def _get_next_queue_index():
        return Aplayer.__subqueue_creation_pos + Aplayer.__subqueue_length

    def __queue_properly():
        light_wait()
        Aplayer.__subqueue_length += 1
        try_queue_insert_pos = Aplayer._get_next_queue_index()
        if try_queue_insert_pos <= Aplayer.get_playlist_pos():
            Aplayer.__subqueue_creation_pos = Aplayer.get_playlist_pos()
            Aplayer.__subqueue_length = 1
        elif try_queue_insert_pos > Aplayer.playlist_count() - 1:
            Aplayer.__subqueue_length = (
                Aplayer.playlist_count() - 1
                - Aplayer.get_playlist_pos())
            Aplayer.__subqueue_creation_pos = Aplayer.get_playlist_pos()
        final_queue_insert_pos = Aplayer._get_next_queue_index()
        Aplayer.playlist_move(
            Aplayer.playlist_count() - 1,
            final_queue_insert_pos)
        if Aplayer.__subqueue_length == 1:
            Aplayer.__subqueue_creation_pos = Aplayer.get_playlist_pos()

    def delete_playlist(title):
        pl_file = Aplayer.playlist_path(title)
        if path_exists(pl_file):
            os.remove(pl_file)

    def __dummy_property_mod(property):
        if Aplayer.player._get_property(property) == 0:
            Aplayer.player._set_property(property, 1)
        else:
            Aplayer.player._set_property(property, 0)

    def __mark_playlist_title_change():
        ''' do not use this with an mpv overlay. '''
        Aplayer.__dummy_property_mod(Aplayer.__pl_title_prop)

    def __mark_playlist_change():
        ''' do not use this with an mpv overlay. '''
        Aplayer.__dummy_property_mod(Aplayer.__pl_change_prop)

    # observer functions will have arg1 as property name and arg2 as value
    # e.g. def path_change_handler(propname, path): ......
    def observe_playlist_changes(observer):
        Aplayer.player.observe_property(Aplayer.__pl_change_prop, observer)

    def observe_playlist_pos(observer):
        Aplayer.player.observe_property('playlist-playing-pos', observer)

    def observe_playlist_title(observer):
        Aplayer.player.observe_property(Aplayer.__pl_title_prop, observer)

    def observe_path(observer):
        Aplayer.player.observe_property('path', observer)

    def observe_pause(observer):
        Aplayer.player.observe_property('pause', observer)

    def loadlist(
            playlist_title: str, index: int = -1, pause_on_load: bool = False):
        Aplayer.__loading_list = True
        Aplayer.clear_subqueue()
        index_chosen = index != -1
        playlist_path = PLAYLISTS_PATH + playlist_title + PLAYLIST_EXTENSION
        Aplayer.player.loadlist(playlist_path)
        Aplayer.__loading_list = False
        Aplayer.__playlist_title = playlist_title
        if Aplayer.is_paused() != pause_on_load:
            Aplayer.pauseplay()
        if Aplayer.__is_shuffling is True:
            if index_chosen is False:
                Aplayer.player.playlist_shuffle()
                Aplayer.player.playlist_play_index(0)
            else:
                Aplayer.player.playlist_play_index(index)
                Aplayer.player.playlist_shuffle()
                light_wait()
                Aplayer.playlist_move(Aplayer.get_playlist_pos(), 0)
        elif index_chosen is True:
            Aplayer.player.playlist_play_index(index)
            light_wait()
        else:
            light_wait()
        light_wait()
        Aplayer.__mark_playlist_change()
        Aplayer.__mark_playlist_title_change()

    def __get_set_batch_pos():
        pl_pos = Aplayer.get_playlist_pos()
        Aplayer.__last_batch_pos = pl_pos
        return pl_pos

    def __load_one_of_many(
            filename, play_type, zero_playlist_pos=False, queue=False):
        Aplayer.player.loadfile(filename, play_type)
        if not Aplayer.__online_queue:
            Aplayer.__online_queue = is_netpath(filename)
        if zero_playlist_pos:
            if queue and not Aplayer.is_paused():
                Aplayer.pauseplay()
            Aplayer.set_playlist_pos(0)
            Aplayer.__mark_playlist_title_change()
        Aplayer.__queue_properly()

    def get_title_from_file(
            filename: str = '', scraped_title: str = '', downloading=False):
        try:
            file = filename if filename != '' else Aplayer.filename()
            online = is_netpath(file)
            if online is True:
                if downloading is True:
                    return AudioDL.validate_title(
                        AudioDL.scrape_title(file, scraped_title))
                else:
                    return AudioDL.scrape_title(file, scraped_title)
            else:
                return Path(file).stem
        except Exception:
            return None

    def loadall(filenames: list, queue: bool = False):
        element_count = len(filenames)
        if element_count == 0:
            return
        if Aplayer.__last_batch_pos < Aplayer.__get_set_batch_pos():
            Aplayer.clear_subqueue()
        old_pl_count = Aplayer.playlist_count()
        first_playtype = 'replace' if old_pl_count == 0 else 'append'
        set_to_zero = old_pl_count < 1
        Aplayer.__load_one_of_many(
            filenames[0], first_playtype, set_to_zero, queue)
        if element_count > 1:
            for f in filenames[1:]:
                Aplayer.__load_one_of_many(f, 'append')
        if queue is False:
            if Aplayer.is_paused():
                Aplayer.pauseplay()
            if old_pl_count > 0:
                Aplayer.next()
        light_wait()
        Aplayer.__mark_playlist_change()

    def batch_clear(indices: list[int]):
        for i in indices:
            if i == Aplayer.get_playlist_pos():
                continue
            else:
                Aplayer.player.playlist_remove(i)
                light_wait()
        Aplayer.__mark_playlist_change()

    def savelist(new_playlist_title: str) -> list[tuple[int, PathLike]]:
        if (new_playlist_title == Aplayer.DEFAULT_QUEUE):
            return []
        playlist_name = new_playlist_title
        if not new_playlist_title.endswith(PLAYLIST_EXTENSION):
            playlist_name = new_playlist_title + PLAYLIST_EXTENSION
        dest = PLAYLISTS_PATH + playlist_name
        rejects = []
        files_accepted = []
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'w') as pl:
            indexed_files = enumerate(Aplayer.player.playlist_filenames)
            for i, filename in indexed_files:
                file = emoji.replace_emoji(filename)
                if file.startswith('https://'):
                    rejects.append((i, file))
                else:
                    files_accepted.append(file)
            if files_accepted:
                for good_file in files_accepted:
                    pl.write(good_file + '\n')
                Aplayer.__playlist_title = new_playlist_title
                Aplayer.__mark_playlist_title_change()
        return rejects

    def rename_playlist(old_playlist_title: str, new_playlist_title: str):
        if old_playlist_title == Aplayer.DEFAULT_QUEUE:
            return
        while Aplayer.__loading_list is True:
            time.sleep(0.01)
        os.rename(
            PLAYLISTS_PATH + old_playlist_title + PLAYLIST_EXTENSION,
            PLAYLISTS_PATH + new_playlist_title + PLAYLIST_EXTENSION
        )

    def rename_current_playlist(new_playlist_title: str):
        Aplayer.rename_playlist(
            Aplayer.get_current_playlist_title(), new_playlist_title)
        Aplayer.__playlist_title = new_playlist_title

    def titles_of_playlists() -> list:
        ret = []
        for _, _, filenames in os.walk(PLAYLISTS_PATH):
            for filename in filenames:
                ret.append(Path(filename).stem)
        return sorted(ret, key=lambda v: (v.casefold(), v))

    def playlist_path(title: str):
        return PLAYLISTS_PATH + title + PLAYLIST_EXTENSION

    def pauseplay():
        Aplayer.player._set_property('pause', not Aplayer.is_paused())

    def is_paused():
        return Aplayer.player._get_property('pause')

    def wait_until_playing():
        Aplayer.player.wait_until_playing()

    def seek_percent(percent):
        duration = Aplayer.duration()
        if duration == -1 or not Aplayer.is_active():
            return
        if percent == 100:
            Aplayer.next()
        else:
            Aplayer.player.seek(percent, 'absolute-percent')

    def seek(seconds: float, relative=True):
        """Seeks to seconds.
        Seek types are either relative or absolute seconds.
        """
        duration = Aplayer.duration()
        time_pos = Aplayer.time_pos()
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

    def duration() -> float:
        """Returns the duration position of the currently playling file,
        or -1 if there is no currently playing file.

        Returns:
            float: the duration of the current file
        """
        ret = Aplayer.player._get_property('duration')
        if ret is None:
            ret = -1
        return ret

    def time_pos() -> float:
        """Returns the time position of the currently playling file,
        or -1 if there is no currently playing file.

        Returns:
            float: the time position of the current file
        """
        ret = Aplayer.player._get_property('time-pos')
        if ret is None:
            ret = -1
        return ret

    def playlist_count():
        return Aplayer.player._get_property('playlist-count')

    def playlist_title():
        return Aplayer.__playlist_title

    def number_of_playlists():
        count = 0
        for _, _, filenames in os.walk(PLAYLISTS_PATH):
            for _ in filenames:
                count += 1
        return count

    def get_playlist_pos() -> int:
        return Aplayer.player._get_property('playlist-pos')

    def set_playlist_pos(index):
        Aplayer.player._set_property('playlist-pos', index)

    def is_active():
        return not Aplayer.get_playlist_pos() == -1

    def is_loaded():
        return Aplayer.is_active() is True and Aplayer.duration() > -1

    def is_shuffling():
        return Aplayer.__is_shuffling

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
        if Aplayer.__is_shuffling is False:
            Aplayer.player.playlist_shuffle()
        else:
            Aplayer.player.playlist_unshuffle()
        Aplayer.__is_shuffling = not Aplayer.__is_shuffling
        Aplayer.__mark_playlist_change()
        return Aplayer.__is_shuffling

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
