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

def updateSong(songData):
    print("I AM NOT DEVELOPED YET !!!!```1`11`11111")


def addSong(songData: Sequence):
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
        INSERT INTO Songs VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        songData
    )
    conn.commit()


