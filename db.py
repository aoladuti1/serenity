import sqlite3
from typing import Sequence
from config import *


SONG_COLUMNS = (
    'FQFN', 'artist', 'album', 'track', 'trackNum',
    'bitRateInfo', 'samplingRateInfo', 'codec', 'art',
    'listens'
)

def init():
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
    conn.close()


class DBLink:

    def __init__(self):
        self.conn = sqlite3.connect(DATABASE)
    
    def quick_commit(self, string: str, bindings: Sequence = []):
        with self.conn as conn:
            conn.cursor().execute(string, bindings)

    def song_registered(self, FQFN: str):
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM Songs
                WHERE FQFN = ?
                LIMIT 1
                """, [FQFN]
                ) 
            return cursor.fetchone() != None

    def directory_registered(self, path: str):
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM Directories
                WHERE directory = ?
                LIMIT 1
                """, [path]
            ) 
            return cursor.fetchone() != None

    def get_artists(self) -> list[tuple[str]]:
        """
        Returns:
            a list of 1 dimensional tuples, each
            containing the name of a registered artist, or
            an empty list if there are no registered artists
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute(
            """
            SELECT artist from Songs
            GROUP BY artist
            """
            )
            return cursor.fetchall()

    def get_albums(self, artist: str = '') -> list[tuple]:
        """
        Returns:
            a list of 1 dimensional tuples, each
            containing the name of a registered artist, or
            an empty list if there are no registered artists
        """
        with self.conn as conn:
            cursor = conn.cursor()
            if artist == '':
                sql_string = """
                SELECT album from Songs
                GROUP BY album
                """
                cursor.execute(sql_string)
            else:
                sql_string = """
                SELECT album from Songs
                WHERE artist = ?
                GROUP BY album
                """
                cursor.execute(sql_string, [artist])
            return cursor.fetchall()

    def __gen_song_dicts(self, fetchedRows: list):
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

    def get_songs_by_artist(self, artist: str) -> list[dict]:
        """
        Returns:
            a list of dicts, each
            containing a column name and value key-value pairing
            for a registered song by the specified artist, or
            an empty list if there are no registered songs
            by that artist
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * from Songs
                WHERE artist = ?
                """,
                [artist]
            )
            fetch = cursor.fetchall()
            return self.__gen_song_dicts(fetch)

    def get_songs_by_album(self, album: str, artist: str) -> list[dict]:
        """
        Returns:
            a list of dicts, each
            containing a column name and value key-value pairing
            for a registered song in the specified album, or
            an empty list if there are no registered songs
            in the album
        """
        with self.conn as conn:
            cursor = conn.cursor()
            cursor.execute(
            """
            SELECT * from Songs
            WHERE album = ? AND artist = ?
            """,
            [album, artist]
            )
            fetch = cursor.fetchall()
            return self.__gen_song_dicts(fetch)

    def del_song_if(self, conditions: dict,
                    negate_all: bool = False, conjunction: bool = True):
        """
        Deletes records from the database of Songs based off a dictionary of conditions.
        e.g. del_song_if( {'artist' : 'Drake'} ) deletes all rows where Drake is the artist.
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
        if negate_all == True:
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
        self.quick_commit("DELETE FROM Songs WHERE " + body, conditions)

    def del_directory(self, path: str):
        self.quick_commit(
            "DELETE FROM Directories " +
            "WHERE directory = ?", [path]
        )    

    def del_song_if_absent(self, FQFN: str) -> bool: 
        """
        Deletes songs from the database that do not exist
        based off their primary key FQFN (Fully Qualified Filename)

        Parameters:
        
        FQFN: the Fully Qualified Filename of the song in question

        Returns:
            True if there was a record deleted from the database,
            meaning the song is absent, and False otherwise
        """
        if path_exists(FQFN) == True:
            return False
        self.quick_commit(
            "DELETE FROM Songs " +
            "WHERE FQFN = ?", [FQFN]
        )
        return True

    def del_song(self, FQFN: str):
        """
        Deletes a song from the database
        
        Parameters:
        
        path: the fully qualified filename of the song to delete
        """
        self.quick_commit(
            "DELETE FROM Songs " +
            "WHERE FQFN = ?", [FQFN]
        )


    def update_song(self, newData: dict):
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
        self.quick_commit(fullSQL, newData)

    def add_song(self, songData: dict):
        """
        Adds a song to the database.

        Parameters:

        songData: a dict where each key corresponds to a Song table column
            
        """
        if songData == None:
            return
        self.quick_commit(
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

    def add_directory(
            self, path: str, folder_is_album: bool, AAT_structure: bool):
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
        self.quick_commit(
            "INSERT INTO Directories VALUES (?,?)", 
            [path, i]
        )
