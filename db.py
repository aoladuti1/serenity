import sqlite3
from config import *

cursor = None

def initDB():
    global cursor
    cursor = sqlite3.connect(DATABASE).cursor()
    cursor.execute(
        """
        CREATE TABLE if not exists Songs (
            FQFN text,
            artist text,
            album text,
            track text,
            trackNum integer,
            duration integer,
            bitRate text,
            samplingRate text,
            channelCount integer,
            audioFormat text,
            art text,
            listens integer,
            PRIMARY KEY(FQFN)
        )
        """
    )

    



