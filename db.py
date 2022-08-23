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
            FQFN text,
            artist text,
            album text,
            track text,
            trackNum integer,
            duration integer,
            bitRateInfo text,
            samplingRateInfo text,
            channelCount integer,
            audioFormat text,
            art text,
            listens integer,
            PRIMARY KEY(FQFN)
        )
        """
        
    )

def songRegistered(FQFN):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM Songs 
        WHERE FQFN = ?
        LIMIT 1
        """, [FQFN]
        ) 
    return cursor.fetchone() != None

def updateSong(newData: dict):
    """
    Updates a song record.

    Parameters:

    newData: a dict containing key-value pairings 
    in which the key corresponds directly to a column name
    in Songs. FQFN must be a key.
    """ 
    body = ''
    for key, val in newData.items():
        body += key + ' = :' + key + ',\n'
    fullSQL = (
        "UPDATE Songs SET\n"
        + body[0:-2] + "\n"
        + "WHERE FQFN = :FQFN\n"
    )

    cursor = conn.cursor()
    cursor.execute(fullSQL, newData)
    conn.commit()
    

def addSong(songData: dict):
    """
    Adds a song to the database.

    Parameters:

    songData: a string array of the correct format as returned
    from addFolder.addFolderBox()
        
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
            :listens
        )
        """,
        songData
    )
    conn.commit()


