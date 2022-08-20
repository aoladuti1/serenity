from asyncio.subprocess import DEVNULL, PIPE
import pprint
from pymediainfo import MediaInfo
import os
import math
import re
import asyncio
import subprocess
from get_cover_art import CoverFinder
from tkinter import filedialog
from config import *
import sacad
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import cred 
newDir = ""


def getTrackLength(fullFileName) -> int:
    duration = 0
    media_info = MediaInfo.parse(filename=fullFileName)
    for track in media_info.tracks:
        if track.duration == None:
            print("Error: File not found (likely online-only)")
            return -1
        else:
            duration = max(duration, track.duration)
    return math.floor(duration/1000)

# Returns false if it fails to find or attribute art
def DLart(trackOrAlbum, artist, artFile, albumMode) -> bool:
    if os.path.exists(artFile) == True: return True
    scope = ""
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=cred.CLIENT_ID, 
            client_secret= cred.CLIENT_SECRET, 
            redirect_uri=cred.REDIRECT_URL, 
            scope=scope
            )
    )
    if albumMode == True:
        
        results = sp.search(q='album:' + trackOrAlbum + ' ' + 'artist:' + artist, type='album', limit=2)
        print(results)
        items = results['albums']['items']
    else:
        results = sp.search(q='artist:' + artist + ' ' + 'track:' + trackOrAlbum, type='track', limit=2)
        items = results['tracks']['items']
    if len(items) > 0:
        albumOrTrack = items[0]
        if albumMode == True:
            print(albumOrTrack['name'], albumOrTrack['images'][0]['url'])
        else:
            print(albumOrTrack['name'], albumOrTrack['album']['images'][0]['url'])
        return True
    else:
        return False
   

    
def addFolderBox(albumMode = False):
    newDir = filedialog.askdirectory()
    if newDir == "":
        return
    for subdir, dirs, files in os.walk(newDir):
        for fileName in files:
            if fileName.endswith(SUPPORTED_EXTENSIONS):
                folderArt = ''
                filePath = os.path.abspath(subdir) + os.sep #full directory with an appended slash
                song = fileName.rpartition(".")[0]
                folderName = subdir.split(os.sep)[-1]
                fullFileName = filePath + fileName
                print(fullFileName)
                duration = (getTrackLength(fullFileName))
                hasAlbum = albumMode
                try:
                    track = song.split(SPLITTER)[1]
                    artist = song.split(SPLITTER)[0]
                except IndexError:
                    track = song
                    artist = UNKNOWN_ARTIST
                    song = UNKNOWN_ARTIST + SPLITTER + track
                try:
                    album = folderName.split(SPLITTER)[1]
                    albumArtist = folderName.split(SPLITTER)[0]
                    hasAlbum = True
                except IndexError:
                    album = UNKNOWN_ALBUM
                    albumArtist = UNKNOWN_ALBUM_ARTIST
                    if albumMode == True:
                        album = folderName
                if (match := re.search("^\d[0-9]+", track)) == None:
                    trackNum = 0
                else:
                    trackNum = int(match.group())
                    track = song
                    artist = albumArtist
                #folderArt exists so that later on 
                if hasAlbum == True:
                    if folderArt == '':
                        folderArt = ART_PATH + folderName + ".jpg"
                        if DLart(album, artist, folderArt, True) == False:
                            folderArt = DEFAULT_ART
                    art = folderArt
                else:
                    art = ART_PATH + song + ".jpg"
                    if DLart(track, artist, art, False) == False:
                        art = DEFAULT_ART
               


                
                
                
                
                
                

                

                  

                   
                    
                
