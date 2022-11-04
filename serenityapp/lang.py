def rellipsis(text) -> str:
    '''Return text with three periods appended.'''
    return text + '...'


def lspace(text) -> str:
    '''Returns text with a space prepended.'''
    return ' ' + text


def wrap_dots(text) -> str:
    '''Returns text with two periods appended and prepended.'''
    return '..{}..'.format(text)


def wrap_sqb(text) -> str:
    """ Returns text with an open square bracket prepended and a
        closed square bracket appended. """
    return '[{}]'.format(text)


def wd_ls(text) -> str:
    """ Returns the equivalent of calling
        wrap_dots() and then lspace() on text. """
    return ' ..{}..'.format(text)


EN = 0

REGION = EN

# _EXCL = ends with exclamation mark
# _COL = ends with colon
# _CAP = starts with a capital
# _REL = ends with ellipsis
# _F = contains a pair of format braces {}

LANG = [
    {
        'UNKNOWN_ARTIST': 'Unknown Artist',
        'STARTING': 'starting',
        'ADDING': 'adding',
        'QUEUING': 'queuing',
        'ARTISTS': 'artists',
        'ALBUMS': 'albums',
        'TRACKS': 'tracks',
        'MORE': 'More',
        'PLAYLISTS': 'playlists',
        'DOWNLOADS': 'downloads',
        'PLAY': 'play',
        'PLAY_ALL': 'play all',
        'QUEUE': 'queue',
        'QUEUE_ALL': 'queue all',
        'EXPAND': 'expand',
        'CONTRACT': 'contract',
        'WELCOME': 'welcome',
        'LIBRARY': 'library',
        'ADD_LIBRARY': 'add library',
        'ADD_FOLDERS': 'add folders',
        'ADD_TO_PLAYLIST_CAP_REL': 'Add to playlist...',
        'DELETE_PLAYLISTS_CAP_REL': 'Delete playlists...',
        'DELETE_PLAYLIST': 'delete playlist',
        'DELETING': 'deleting',
        'REFRESH': 'refresh',
        'DONE_EXCL': 'done!',
        'SEARCH': 'search',
        'STREAM': 'stream',
        'STREAM+DOWNLOAD': 'stream + download',
        'DOWNLOAD': 'download',
        'LOADING': 'loading',
        'DOWNLOADING': 'downloading',
        'LOADING_AND_DOWNLOADING': 'loading and downloading',
        'NOW_PLAYING_COL_CAP': 'Now playing:',
        'NOW_STREAMING_COL_CAP': 'Now streaming:',
        'CONVERTING': 'converting',
        'CURRENTLY_PLAYING_COL_CAP': 'Currently playing:',
        'CLEAR_QUEUE': 'clear queue',
        'CLEAR_SELECTION': 'clear selection',
        'REMOVE_SELECTION': 'remove selection',
        'CLOSE_WARNING_WINTITLE': 'Hold on!',
        'CLOSE_WARNING_MSG': 'Files are still converting/downloading. Quit?',
        'SAVE': 'save',
        'SAVING_TO': 'saving to',
        'SAVELIST_REJECTS_MSG_F': """
The following titles could not be added to '{}' \
likely because streams are not permitted \
in saved playlists:
            """,
        'SAVELIST_REJECTS_WINTITLE_F': 'Files unable to be added to {}',
        'GUIDE': """Click 'More...' to add some music!

Then, click [add library] if each song file is in an album-named folder, and \
each album-named folder is inside an artist-named folder.
For example (assuming you add a directory called "Music") \
the full directory of the song "Don't" may be \
"Music/Bryson Tiller/T R A P S O U L/05 - Don't.mp3."

Otherwise, click [add folders] and we'll try our best to get all your music \
added and organised nicely :-)

When you choose a directory all music files in its subdirectories will be \
added to the database.

Don't worry too much about the EXACT file / folder names, Serenity is flexible!
[Note: Serenity does not use metadata at all. Data like track number can be \
signalled by being present in the filename like .../01 - Intro.mp3.]"""
    }
]

L = LANG[REGION]
