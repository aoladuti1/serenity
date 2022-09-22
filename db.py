import sqlite3
from typing import Sequence
from config import *


SONG_COLUMNS = (
    'FQFN', 'artist', 'album', 'track', 'trackNum',
    'bitRateInfo', 'samplingRateInfo', 'codec', 'art',
    'listens'
)

def executeAndCommit(string: str, bindings: Sequence = []):
    conn.cursor().execute(string, bindings)
    conn.commit()


def init():
    global conn
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE if not exists Songs (
            FQFN text,
            artist text COLLATE NOCASE,
            album text COLLATE NOCASE,
            track text COLLATE NOCASE,
            trackNum integer,
            bitRateInfo text,
            samplingRateInfo text,
            codec text,
            art text COLLATE NOCASE,
            listens integer,
            PRIMARY KEY(FQFN)
        )
        """
    )
    cursor.execute(
        # 0 = not structured/album, 1 = album, 2 = structured for structure
        """
        CREATE TABLE if not exists Directories (
            directory text,
            structure integer,
            PRIMARY KEY(directory)
        )
        """
    )
    conn.commit()

def songRegistered(FQFN: str):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM Songs 
        WHERE FQFN = ?
        LIMIT 1
        """, [FQFN]
        ) 
    return cursor.fetchone() != None

def directoryRegistered(path: str):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM Directories 
        WHERE directory = ?
        LIMIT 1
        """, [path]
    ) 
    return cursor.fetchone() != None

def getArtists() -> list[tuple[str]]:
    """
    Returns:
        a list of 1 dimensional tuples, each
        containing the name of a registered artist, or
        an empty list if there are no registered artists
    """
    cursor = conn.cursor()
    cursor.execute(
    """
    SELECT artist from Songs
    GROUP BY artist
    """
    )
    return cursor.fetchall()

def getAlbumsByArtist(artist: str) -> list[tuple[str]]:
    """
    Returns:
        a list of 1 dimensional tuples, each
        containing the name of a registered artist, or
        an empty list if there are no registered artists
    """
    cursor = conn.cursor()
    cursor.execute(
    """
    SELECT album from Songs
    WHERE artist = ?
    GROUP BY album
    """,
    [artist]
    )
    return cursor.fetchall()

def __genSongDicts(fetchedRows: list):
    """Takes a list of Song tuples returned by 
    sqlite3.connection.cursor.fetchall()
    and converts it into a list of dicts

    Returns:
        a list of dicts, each
        containing a column name and value key-value pairing
        for a registered song
    """
    fetchLen = len(fetchedRows)
    ret = [{} for _ in range(fetchLen)]
    for i in range(fetchLen):
        for j in range(len(SONG_COLUMNS)):
            ret[i][SONG_COLUMNS[j]] = fetchedRows[i][j]    
    return ret

def getSongsByArtist(artist: str) -> list[dict]:
    """
    Returns:
        a list of dicts, each
        containing a column name and value key-value pairing
        for a registered song by the specified artist, or
        an empty list if there are no registered songs
        by that artist
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * from Songs
        WHERE artist = ?
        """,
        [artist]
    )
    fetch = cursor.fetchall()
    return __genSongDicts(fetch)

def getSongsByAlbum(album: str, artist: str) -> list[dict]:
    """
    Returns:
        a list of dicts, each
        containing a column name and value key-value pairing
        for a registered song in the specified album, or
        an empty list if there are no registered songs
        in the album
    """
    cursor = conn.cursor()
    cursor.execute(
    """
    SELECT * from Songs
    WHERE album = ? AND artist = ?
    """,
    [album,artist]
    )
    fetch = cursor.fetchall()
    return __genSongDicts(fetch)

def delSongIf(conditions: dict, negateConditions = False, conjunction: bool = True):
    """
    Deletes records from the database of Songs based off a dictionary of conditions.
    e.g. delSongIf( {'artist' : 'Drake'} ) deletes all rows where Drake is the artist.
    (equiv. sql: "WHERE artist = 'Drake'").
    The NOT operator puts NOT in front of every boolean operator (AND / OR etc.)
    like in the following example: if negateConditions == True and
    conditions = {'artist' : 'Bryson Tiller', 'album' : 'T R A P S O U L'}
    then the corresponding SQL would be: 
    "WHERE NOT artist = 'Bryson Tiller' AND NOT album = 'T R A P S O U L'"

    Parameters:
    
    conditions: the dictionary of conditions
    negateConditions: if True then NOT is prepended to each boolean operator
    conjunction: if True, the main boolean operator between conditions is "AND", otherwise it is "OR"

    Returns:
    True if something was deleted
    """
    body = ''
    if negateConditions == True:
        negationText = 'NOT '
    else:
        negationText = ''
    spacedAndOr = ' and '
    walk = -5
    if conjunction == False:
        spacedAndOr = ' or '
        walk = -4
    for key, val in conditions.items():
        body += negationText + key + ' = :' + key + spacedAndOr
    body = body[0:walk]
    executeAndCommit("DELETE FROM Songs WHERE " + body, conditions)

def delDirectory(path: str):
    executeAndCommit(
        "DELETE FROM Directories " +
        "WHERE directory = ?", [path]
    )    

def delSongIfAbsent(FQFN: str) -> bool: 
    """
    Deletes songs from the database that do not exist
    based off their primary key FQFN (Fully Qualified Filename)

    Parameters:
    
    FQFN: the Fully Qualified Filename of the song in question

    Returns:
    True if there was a record deleted from the database,
    and False otherwise

    """
    if os.path.exists(FQFN) == True:
        return False
    executeAndCommit(
        "DELETE FROM Songs " +
        "WHERE FQFN = ?", [FQFN]
    )
    return True

def delSong(FQFN: str):
    """
    Deletes a song from the database
    
    Parameters:
    
    path: the fully qualified filename of the song to delete
    """
    executeAndCommit(
        "DELETE FROM Songs " +
        "WHERE FQFN = ?", [FQFN]
    )


def updateSong(newData: dict):
    """
    Updates a song record.

    Parameters:

    newData: a dict containing key-value pairings 
    in which the key corresponds directly to a column name
    in Songs. FQFN must be a present key.
    """ 
    body = ''
    for key, val in newData.items():
        body += key + ' = :' + key + ',\n'
    body = body[0:-2]
    fullSQL = (
        "UPDATE Songs SET\n"
        + body + "\n"
        + "WHERE FQFN = :FQFN\n"
    )
    executeAndCommit(fullSQL, newData)

def addSong(songData: dict):
    """
    Adds a song to the database.

    Parameters:

    songData: a dict where each key corresponds to a Song table column
        
    """
    if songData == None:
        return
    executeAndCommit(
        """
        INSERT INTO Songs VALUES (
            :FQFN,
            :artist,
            :album,
            :track,
            :trackNum,
            :bitRateInfo,
            :samplingRateInfo,
            :codec,
            :art,
            :listens
        )
        """,
        songData
    ) 

def addDirectory(path: str, folder_is_album: bool, AAT_structure: bool, include_subfolders = True):
    if AAT_structure is True:
        i = 2
    elif folder_is_album is True:
        i = 1
    else:
        i = 0
    """
    Adds a directory to the database to scan for music
    
    Parameters:
    
    path: directory to add (ensure it ends with os.sep)
    """
    executeAndCommit(
        "INSERT INTO Directories VALUES (?,?)", 
        [path, i]
    )
