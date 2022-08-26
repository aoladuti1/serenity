import sqlite3
from typing import Sequence
from config import *

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
            FQFN text COLLATE NOCASE,
            artist text COLLATE NOCASE,
            album text COLLATE NOCASE,
            track text COLLATE NOCASE,
            trackNum integer,
            duration integer,
            bitRateInfo text COLLATE NOCASE,
            samplingRateInfo text COLLATE NOCASE,
            channelCount integer,
            audioFormat text COLLATE NOCASE,
            art text COLLATE NOCASE,
            listens integer,
            startingSpeed integer,
            PRIMARY KEY(FQFN)
        )
        """
    )
    cursor.execute(
        # 0 = false, 1 = true for visible
        """
        CREATE TABLE if not exists Directories (
            directory text,
            visible integer,
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

def hideDirectory(path: str):
    """
    Marks a music directory as invisible to Serenity in the database
    (visible = 0)
    
    Parameters:
    
    path: directory to hide (ensure it ends with os.sep)
    """
    executeAndCommit(
        "UPDATE Directories SET\n"
      + "visible = 0\n"
      + "WHERE directory = ?", [path]
    )

def showDirectory(path: str):
    """
    Marks a music directory as visible to Serenity in the database
    (visible = 1)
    
    Parameters:
    
    path: directory to make visible (ensure it ends with os.sep)
    """
    executeAndCommit(
        "UPDATE Directories SET\n"
      + "visible = 1\n"
      + "WHERE directory = ?", [path]
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
            :duration,
            :bitRateInfo,
            :samplingRateInfo,
            :channelCount,
            :audioFormat,
            :art,
            :listens,
            :startingSpeed
        )
        """,
        songData
    )

def addDirectory(path: str, visible: bool = True):
    """
    Adds a directory to the database to scan for music
    
    Parameters:
    
    path: directory to add (ensure it ends with os.sep)
    """
    executeAndCommit(
        "INSERT INTO Directories VALUES (?,?)", 
        [path, int(visible)]
    ) 


