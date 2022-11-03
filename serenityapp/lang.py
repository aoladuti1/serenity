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

LANG = [
    {
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
        'QUEUE': 'queue',
        'EXPAND': 'expand',
        'CONTRACT': 'contract',
        'ADD_LIBRARY': 'add library',
        'ADD_FOLDERS': 'add folders',
        'REFRESH': 'refresh',
        'DONE_EXCL': 'done!',
        'CLOSE_WARNING': ['Hold on!',
                          'Files are still converting/downloading. Quit?'],
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
