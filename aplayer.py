
from asyncio.subprocess import PIPE
from concurrent.futures import thread
from glob import glob
from math import floor
import re
import subprocess
from sys import stdin, stdout
import time
import threading
from tracemalloc import start

class Aplayer:
    MPLAYER_DIR = 'C:\\Users\\anton\\Downloads\\mplayer-svn-38151-x86_64\\mplayer.exe'
    aplayer = None
    startingVolume = 100
    startingSpeed = 1
    blockForInit = False
    song = None
    posText = ''
    pos = 0
    noFile = True
    songsRunning = 0
    
    # Will open a aplayer.exe
    # args is a list of additional arguments after -slave and before the fully qualified filename
    def __genProcess(FQFN, args=[]):
        # -pausing 2 means that no matter what command is passed through the PIPE, 
        # the pause/play state stays the same        
        argslist = (
            [Aplayer.MPLAYER_DIR]
          + [   '-slave', '-pausing', '2', 
                '-volume', str(Aplayer.startingVolume),
                '-speed', str(Aplayer.startingSpeed)    ] 
          + args 
          + [FQFN]
        )
        return subprocess.Popen(
            argslist, 
            stdout=subprocess.PIPE, 
            stdin=subprocess.PIPE,
            stderr=stdout,
            universal_newlines=True, 
            bufsize=1
            )

    def terminate():
        if Aplayer.aplayer != None:
            while Aplayer.songsRunning > 0:
                Aplayer.aplayer.terminate()
        if Aplayer.songsRunning < 0: Aplayer.songsRunning = 0

    def init(songDict: dict, play = True, args: list=[]):
        Aplayer.terminate()
        Aplayer.song = songDict
        Aplayer.FQFN = Aplayer.song['FQFN']
        Aplayer.duration = Aplayer.song['duration']
        Aplayer.ctext = '_'
        Aplayer.playing = True
        Aplayer.aplayer = Aplayer.__genProcess(Aplayer.FQFN, args)
        Aplayer.songsRunning += 1
        if play == False:
            Aplayer.pauseplay()
        else:
            threading.Thread(target=Aplayer.__playpriv).start()

    def pwrite(text='') -> bool:
        sign = Aplayer.signsOfLife()
        if sign:
            Aplayer.aplayer.stdin.write(text + "\n")
        return sign
        

    def __playpriv():
        """
        This function will ensure the playing audio keeps going normally.
        It must be threaded. pauseplay() wraps it in a thread.
        """
        while (Aplayer.ctext != ''):
            Aplayer.ctext = Aplayer.aplayer.stdout.readline()
            if Aplayer.ctext.startswith('A:'):
                Aplayer.pos = floor(float(Aplayer.ctext.split()[1]))
        Aplayer.pos = Aplayer.song['duration']
        Aplayer.songsRunning -= 1
        return         

    def pauseplay():
        Aplayer.pwrite('pause')
        if Aplayer.playing == True:
            Aplayer.playing = False
        

    def clearctext():
        Aplayer.ctext = ''

    def signsOfLife() -> bool:
        if Aplayer.aplayer == None:
            return False
        ret = Aplayer.aplayer.poll() == None
        if ret == False:
            Aplayer.playing = False
        if Aplayer.songsRunning < 1:
            return False
        return ret

    def seek(plusMinusTime):
        timeLeft = Aplayer.song['duration'] - Aplayer.pos
        if plusMinusTime > timeLeft:
            plusMinusTime = timeLeft
        startTime = plusMinusTime + Aplayer.pos
        if startTime >= Aplayer.song['duration'] or startTime < 0:
            Aplayer.terminate()
            return
        Aplayer.pwrite('seek ' + str(startTime) + ' 2\n')

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


        
