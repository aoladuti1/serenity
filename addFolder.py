from email.mime import image
from fileinput import filename
from turtle import update
from pymediainfo import MediaInfo
import os
import math
import re
import db
from tkinter import filedialog
from config import *
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import cred
from pathlib import Path

numgex = re.compile("^\d+") #matches leading digits

def getAudioInfo(FQFN):
    media_info = MediaInfo.parse(filename=FQFN)
    for track in media_info.tracks:
        if track.format == None:
            raise Exception(
                """
                Error: file not accessible, likely an online-only file 
                whose storage app (such as OneDrive) either
                isn't running properly on this computer or is offline.
                It is highly recommended for all library files to be downloaded.
                Please retry.
                """
            )
        elif track.track_type == "Audio":
            #print(track.to_data()) gives the whole dict
            duration = str(math.floor(track.duration/1000))
            bitRateInfo = track.other_bit_rate[0]
            samplingRateInfo = track.other_sampling_rate[0]
            channelCount = str(track.channel_s)
            audioFormat = track.other_format[0]
            return [duration, bitRateInfo, samplingRateInfo, channelCount, audioFormat] #returning here is an optimization
    return ["0", "0", "0", "0", "0"]

# Returns false if it fails to find or assign art
# music is either the track name or album name, dependent on if isAlbum is true
def getArt(music, artist, artName, isAlbum):
    target = ART_PATH + artName + ".jpg"
    if os.path.exists(target) == True: return target
    artFile = DEFAULT_ART
    auth_manager = SpotifyClientCredentials(
        client_id=cred.CLIENT_ID,
        client_secret=cred.CLIENT_SECRET
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)

    if artist == UNKNOWN_ARTIST:
        artistqtext = ""
    else:
        artistqtext = "artist:" + artist
    if isAlbum == True:
        try:
            results = sp.search(q='album:' + music + ' ' + artistqtext, type='album', limit=1)
            items = results['albums']['items']
        except:
            return artFile
    else:
        try:
            results = sp.search(q=artistqtext + ' ' + 'track:' + music, type='track', limit=2)
            items = results['tracks']['items']
        except:
            return artFile

    neededArtistArt = False
    if len(items) == 0:
        try:
            if artistqtext == "": return artFile
            results = sp.search(q=artistqtext, type="artist", limit = 3)
            items = results['artists']['items']
            if len(items) > 0:
                target = ART_PATH + artist + ".jpg"
                neededArtistArt = True
        except:
            return artFile             

    if len(items) > 0:
        webRip = items[0]
        if neededArtistArt == False:
            if isAlbum == True:
                image_url = webRip['images'][0]['url']
            else:
                image_url = webRip['album']['images'][0]['url']
        else:
            image_url = webRip['images'][0]['url']
        img_data = requests.get(image_url).content
        try:
            artFile = target
            with open(artFile, 'wb') as handler:
                handler.write(img_data)
        except:
            artFile = DEFAULT_ART
    return artFile

def getTrackInfo(song):
    """
    Returns an array of ["", track, trackNum]
    """
    trackNum = 0
    try:       
        track = song.split(SPLITTER)[-1]
    except IndexError:
        track = song
    if not (match := numgex.search(track)) == None:
        trackNum = int(match.group())
    return ["",track, str(trackNum)]    

def getTrackAndArtistInfo(song, folderName):
    """
    Returns an array of [artist, track, trackNumber]
    """

    trackNum = 0
    try:       
        track = song.split(SPLITTER)[-1]
        artist = song.split(SPLITTER)[-2]
    except IndexError:
        track = song
        artist = UNKNOWN_ARTIST
    if not (match := numgex.search(track)) == None:
        trackNum = int(match.group())
    if artist == UNKNOWN_ARTIST:
        try:
            artist = folderName.split(SPLITTER)[-2]
        except:
            ""
    if artist[0].isnumeric() == True and trackNum == 0:
        try:
            artistAttempt = re.search(r"\S*\s*(.*)\s+" + SPLITTER_CHAR + r"\s+", song).group(1)
            artist = artistAttempt
            if artist == "": artist = UNKNOWN_ARTIST
            trackNum = int(numgex.search(song).group())
        except: ""
    return [artist, track, str(trackNum)]

def getAlbum(folderName, inAlbumMode):
    if inAlbumMode == True:
            return folderName
    try:
        album = folderName.split(SPLITTER)[-2]
    except IndexError:
        album = UNKNOWN_ALBUM
    return album    


def getSongNoStructure(song, folderName, inAlbumMode):
    info = getTrackAndArtistInfo(song, folderName)
    artist = info[0]
    album = getAlbum(folderName, inAlbumMode)
    track = info[1]
    trackNum = info[2]
    return [artist, album, track, trackNum] 

def getSong(song, filePath, inAlbumMode, tightStructure):
    """
    Get the artist and track from a song marked as being in an
    Artist-Album-Track folder structure. i.e. inside the Artist
    folder are all the albums, which themselves contain pure audio files like so:
    C:/Bryson Tiller/The Best Album Ever/The Best Track Ever.mp3

    Parameters:

    ~song: "bryson tiller - dont" for instance

    ~filePath: full path to the folder containing the file

    ~inAlbumMode: if the folder addition is in album mode or not (for corner cases)

    Returns:
    
    array of {artist, album, track, trackNum}
    """
    structure = Path(filePath).parents
    folderName = filePath.split(os.sep)[-2] #filePath has an appended slash so we do -2 instead of -1
    if tightStructure == False or len(structure) < 2:
        return getSongNoStructure(song, folderName, inAlbumMode)
    else:
        artist = str(structure[0]).rpartition(os.sep)[-1]
        album = folderName
        info = getTrackInfo(song)
        track = info[1]
        trackNum = info[2]
        return [artist, album, track, trackNum]
    


# The following assumes the config.SPLITTER variable is " - "
# Adds folders and subfolders of music
# track format: 
# [optional number][space][artist][space][SPLITTERCHAR][space][track]
def addFolderBox(updateDir = False, albumMode = False, tightStructure = False, findArt=True):
    chosenDir = filedialog.askdirectory()
    if chosenDir == "":
        return None
    for subdir, dirs, files in os.walk(chosenDir):
        absdir = os.path.abspath(subdir) #no appended slash
        filePath = absdir + os.sep #full directory with an appended slash
        for fileName in files:
            if fileName.endswith(SUPPORTED_EXTENSIONS):
                FQFN = filePath + fileName
                songRegistered = db.songRegistered(FQFN)
                if updateDir == False and songRegistered == True:
                    continue
                song = fileName.rpartition(".")[0]
                folderName = absdir.split(os.sep)[-1]
                duration, bitRateInfo, samplingRateInfo, channelCount, audioFormat = getAudioInfo(FQFN)
                dataSet = getSong(song, filePath, albumMode, tightStructure)
                artist, album, track, trackNum = dataSet
                hasAlbum = album != UNKNOWN_ALBUM
                #from this point on parentFolderName and folderName may not exactly correlate to the file structure!
                try:
                    parentFolderName = filePath.split(os.sep)[-3]
                except:
                    parentFolderName = '' #corner case - defensive programming isn't obsessive... right?
                if parentFolderName.endswith(':') == True:
                    parentFolderName = parentFolderName[0:-1]
                else:
                    if folderName.endswith(":") == True:
                        folderName = folderName[0:-1] #for music a little below the a drive
                        parentFolderName = ''
                if findArt == True:
                    if hasAlbum == True:
                        dlMusic = album
                        artName = parentFolderName + "-" + folderName
                    else:
                        dlMusic = track
                        artName = parentFolderName + "-" + folderName + "-" + song
                    art = getArt(dlMusic, artist, artName, hasAlbum)
                else:
                    art = DEFAULT_ART
                songData = {
                    "FQFN": FQFN,
                    "artist": artist, 
                    "album": album,
                    "track": track,
                    "trackNum": trackNum, 
                    "duration": duration,
                    "bitRateInfo": bitRateInfo,
                    "samplingRateInfo": samplingRateInfo, 
                    "channelCount":channelCount, 
                    "audioFormat": audioFormat, 
                    "art": art, 
                    "listens": 0,
                    "startingSpeed": 1
                }
                if db.directoryRegistered(filePath) == False:
                    db.addDirectory(filePath)
                if updateDir == True and songRegistered == True:
                    db.updateSong(songData)
                else:
                    db.addSong(songData)


                    
               


                
                
                
                
                
                

                

                  

                   
                    
                
