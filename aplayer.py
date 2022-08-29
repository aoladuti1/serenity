
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
    instances = 0
    aplayer = None
    startingVolume = 100
    startingSpeed = 1
    blockForInit = False
    song = None
    posText = ''
    pos = 0
    
    # Will open a aplayer.exe
    # args is a list of additional arguments after -slave and before the fully qualified filename
    def genProcess(self, FQFN, args=[]):
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
            Aplayer.aplayer.terminate()
            Aplayer.instances -=1
        if Aplayer.instances < 0: Aplayer.instances = 0

    def __init__(self, songDict: dict = None, play = True, args: list=[]):
        if (songDict != None):
            self.FQFN = songDict['FQFN']
            Aplayer.song = songDict
            Aplayer.duration = songDict['duration']
        else:
            self.FQFN = Aplayer.song['FQFN']
            Aplayer.duration = Aplayer.song['duration']
        self.ctext = '_'
        self.playing = True
        Aplayer.instances += 1
        while Aplayer.instances > 1:
            Aplayer.terminate()
        Aplayer.aplayer = self.genProcess(self.FQFN, args)
        if play == False:
            self.pauseplay()
        else:
            threading.Thread(target=self.__playpriv).start()

    def pwrite(self, text='') -> bool:
        sign = self.signsOfLife()
        if sign:
            Aplayer.aplayer.stdin.write(text + "\n")
        return sign
        

    def __playpriv(self):
        """
        This function will ensure the playing audio keeps going normally.
        It must be threaded. pauseplay() wraps it in a thread.
        """
        while (self.ctext != ''):
            time.sleep(0.001)
            self.ctext = Aplayer.aplayer.stdout.readline()
            if self.ctext.startswith('A:'):
                Aplayer.pos = floor(float(self.ctext.split()[1]))
        return         

    def pauseplay(self):
        self.pwrite('pause')
        if self.playing == True:
            self.playing = False
        

    def clearctext(self):
        self.ctext = ''

    def signsOfLife(self) -> bool:
        if Aplayer.aplayer == None:
            return False
        ret = Aplayer.aplayer.poll() == None
        if ret == False:
            self.playing = False
        return ret

    def seek(self, plusMinusTime):
        timeLeft = Aplayer.song['duration'] - Aplayer.pos
        if plusMinusTime > timeLeft:
            plusMinusTime = timeLeft
        startTime = plusMinusTime + Aplayer.pos
        print(startTime)
        if startTime >= Aplayer.song['duration'] or startTime < 0:
            Aplayer.terminate()
            return
        Aplayer(Aplayer.song, play=self.playing, args=['-ss', str(startTime)])

    def setVolume(self, volume: int):
        """
        Sets the volume of the current audio (not the starting volume).

        Parameters:
        
        volume: the new volume (between 1 and 100)
        """
        self.pwrite('volume ' + str(volume) + ' 1\n')
    
    def setSpeed(self, speed: int):
        """
        Sets the volume of the current audio (not the starting volume).

        Parameters:
        
        volume: the new volume (between 1 and 100)
        """
        self.pwrite('speed_set ' + str(speed) + '\n')


        
