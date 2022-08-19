from asyncio.subprocess import DEVNULL, PIPE
from pymediainfo import MediaInfo
import os
import math
import subprocess
from tkinter import filedialog
from config import *
newDir = ""
   
def getTrackLength(fullFileName):
    duration = 0
    media_info = MediaInfo.parse(fullFileName)
    for track in media_info.tracks:
        duration = max(duration, track.duration)
        return track.to_data()
    #return math.floor(duration/1000)

    

    
   
    
def addFolderBox():
    newDir = filedialog.askdirectory()
    if newDir == "":
        return
    for subdir, dirs, files in os.walk(newDir):
        for fileName in files:
            if fileName.endswith(SUPPORTED_EXTENSIONS):
                filePath = os.path.abspath(subdir) + os.sep #full directory with an appended slash
                song = fileName.rpartition(".")[0]
                folder = subdir.split(os.sep)[-1]
                fullFileName = filePath + fileName
                duration = (getTrackLength(fullFileName))
                try:
                    track = song.split(SPLITTER)[1]
                    artist = song.split(SPLITTER)[0]
                except IndexError:
                    track = song
                    artist = UNKNOWN_ARTIST
                    song = UNKNOWN_ARTIST + SPLITTER + track
                try:
                    album = folder.split(SPLITTER)[1]
                    albumArtist = folder.split(SPLITTER)[0]
                except IndexError:
                    album = UNKNOWN_ALBUM
                    albumArtist = UNKNOWN_ALBUM_ARTIST
                print(getTrackLength(fullFileName))
                
                

                

                  

                   
                    
                
