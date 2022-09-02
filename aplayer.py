from math import floor
import os
import shlex
import subprocess
from sys import stdout
import threading
import time
from unittest import skip
from wsgiref.util import application_uri

def genShellString(string):
    return "\"" + string.replace("\\", "\\\\") + "\""

class Aplayer:
    MPLAYER_DIR = 'C:\\Users\\anton\\Downloads\\mplayer-svn-38151-x86_64\\mplayer.exe'
    aplayer = None
    startingVolume = 100
    startingSpeed = 1
    procInstances = 0
    playing=False
    songs = []
    songIndex = 0
    posText = ''
    pos = 0
    appendSong = False
    songRunning = False
    errorStop = False
    args = []

    # Will open a aplayer.exe
    # args is a list of additional arguments after -slave and before the fully qualified filename
    def __genProcess(FQFN, args=[]):
        # -pausing 2 means that no matter what command is passed through the PIPE, 
        # the pause/play state stays the same
        Aplayer.kill()        
        argslist = (
            [Aplayer.MPLAYER_DIR]
          + [   '-slave', '-pausing', '2', '-idle', '-v',
                '-volume', str(Aplayer.startingVolume),
                '-speed', str(Aplayer.startingSpeed)    ] 
          + args 
          + [FQFN]
        )
        Aplayer.procInstances += 1
        return subprocess.Popen(
            argslist, 
            stdout=subprocess.PIPE, 
            stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
            )

    def kill():
        if Aplayer.aplayer == None: return
        while Aplayer.procInstances > 0:
            Aplayer.aplayer.terminate()
            Aplayer.procInstances -= 1
        Aplayer.songRunning=False

    def getSong() -> dict:
        return Aplayer.songs[Aplayer.songIndex]

    def __loadFile(songDict: dict, skipOnLoad = False, args: list=[], init=False):
        Aplayer.songs.append(songDict)
        Aplayer.args = args
        Aplayer.songs[len(Aplayer.songs) - 1] = songDict
        song = songDict
        if init == True:
            Aplayer.ctext = '_'
            Aplayer.aplayer = Aplayer.__genProcess(songDict['FQFN'], args)
            Aplayer.playing = True
            threading.Thread(target=Aplayer.__playpriv).start()
        else:
            Aplayer.pwrite(
                "loadfile " 
                + genShellString(songDict['FQFN']) + " 2"
            )
        if skipOnLoad == True: 
            Aplayer.next()     

    def next():
        Aplayer.aplayer.stdin.write('pt_step 1 1\n')
        Aplayer.pos = 0
    
    def prev():
        Aplayer.aplayer.stdin.write('pt_step -1 1\n')
        Aplayer.pos = 0
        
    def play(songDict: dict, skipOnLoad = False, args: list=[]):
        isInit = Aplayer.aplayer == None
        if isInit == True:
            skipOnLoad = False
        Aplayer.__loadFile(songDict, skipOnLoad, args, init=isInit)

    def pauseplay():
        if Aplayer.songRunning == True:
            Aplayer.playing = not Aplayer.playing
            Aplayer.pwrite('pause')

    def pwrite(text=''):
        ret = Aplayer.signsOfLife()
        if ret == True:
            Aplayer.aplayer.stdin.write(r"{}".format(text) + "\n") 
        return ret

    def __playpriv():
        """
        This function will ensure the playing audio keeps going normally.
        It must be threaded.
        """
        Aplayer.songRunning = True
        firstRun = True
        while (Aplayer.ctext != ''):
            Aplayer.ctext = Aplayer.aplayer.stdout.readline()
            if Aplayer.ctext.startswith('ds_fill') == True or Aplayer.errorStop==True:
                while Aplayer.aplayer.stdout.readline().startswith("ao_") == False: pass
                if Aplayer.songIndex + 1 >= len(Aplayer.songs) and Aplayer.errorStop==False: #only / last song
                    Aplayer.aplayer.stdin.write('stop\n')                   
                    Aplayer.errorStop = True
                else:
                    if firstRun == True:
                        firstRun = False 
                    else:
                        Aplayer.songIndex += 1
                    Aplayer.aplayer = Aplayer.__genProcess(Aplayer.getSong()['FQFN'])
                    while Aplayer.aplayer.stdout.readline().startswith("Play") == False: ""
                    Aplayer.songRunning = True
                    Aplayer.playing = True
                    Aplayer.errorStop = False
            elif Aplayer.ctext.startswith('Play'):
                if firstRun == True:
                    firstRun = False 
                else:
                    Aplayer.songIndex += 1
                Aplayer.songRunning = True
                Aplayer.playing = True
            elif Aplayer.ctext.startswith('A:'):
                Aplayer.pos = floor(float(Aplayer.ctext.split()[1]))
            elif Aplayer.ctext.startswith('EOF'):
                Aplayer.songRunning = False
                Aplayer.playing = False

    def signsOfLife() -> bool:
        if Aplayer.aplayer == None:
            return False
        elif Aplayer.aplayer.poll() != None:
            return False 
        else:
            ret = Aplayer.songRunning
            if ret == False:
                if Aplayer.aplayer.poll() == None: return True
                Aplayer.playing = False
            return ret

    def seek(seconds, type=""):
        if Aplayer.signsOfLife() == False: return
        if type == "+":
            seekString = str(seconds)
        elif type == "-":
            seekString = type + str(seconds)
        else:
            if seconds < 0:
                seekString = '0 2'
            else:
                seekString = str(seconds) + ' 2'
        Aplayer.pwrite('seek ' + seekString)

    def setVolume(volume: int):
        """
        Sets the volume of the current audio (not the starting volume).

        Parameters:
        
        volume: the new volume (between 1 and 100)
        """
        Aplayer.pwrite('volume ' + str(volume) + ' 1\n')
    
    def setSpeed(speed: int):
        """
        Sets the volume of the current audio (not the starting volume).

        Parameters:
        
        volume: the new volume (between 1 and 100)
        """
        Aplayer.pwrite('speed_set ' + str(speed) + '\n')


        
