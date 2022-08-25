from multiprocessing.sharedctypes import Value
import sqlite3
from typing import Sequence
from config import *


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
        """
        CREATE TABLE if not exists Directories (
            directory text,
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

def deleteIf(conditions: dict, negateConditions = False, conjunction: bool = True):
    """
    Deletes records from the database of Songs based off a dictionary of conditions.
    e.g. deleteIf( {'artist' : 'Drake'} ) deletes all rows where Drake is the artist.
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
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Songs WHERE " + body, conditions)
    conn.commit()

def deleteIfAbsent(FQFN: str) -> bool: 
    """
    Deletes music from the database that do not exist
    based off their primary key FQFN (Fully Qualified Filename)

    Parameters:
    
    FQFN: the Fully Qualified Filename of the song in question

    Returns:
    True if there was a record deleted from the database,
    and False otherwise

    """
    cursor = conn.cursor()
    if os.path.exists(FQFN) == True:
        return False
    cursor.execute(
        "DELETE FROM Songs " +
        "WHERE FQFN = ?", [FQFN]
    )
    conn.commit()
    return True


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

    cursor = conn.cursor()
    cursor.execute(fullSQL, newData)
    conn.commit()
    

def addSong(songData: dict):
    """
    Adds a song to the database.

    Parameters:

    songData: a dict where each key corresponds to a Song table column
        
    """
    if songData == None:
        return
    cursor = conn.cursor()
    cursor.execute(
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
    conn.commit()


