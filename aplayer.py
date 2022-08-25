
from asyncio.subprocess import PIPE
from glob import glob
import subprocess
from sys import stdout
import time
import threading

class Aplayer:
    MPLAYER_DIR = 'C:\\Users\\anton\\Downloads\\mplayer-svn-38151-x86_64\\mplayer.exe'
    instances = 0
    aplayer = None
    startingVolume = 100
    startingSpeed = 1

    # Will open a aplayer.exe
    # args is a list of additional arguments after -slave and before the fully qualified filename
    def genProcess(self, FQFN, args=[]):
        # -pausing 2 means that no matter what command is passed through the PIPE, 
        # the pause/play state stays the same        
        argslist = (
            [Aplayer.MPLAYER_DIR]
          + [   '-slave', '-idle', '-pausing', '2', 
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

    def pauseplayInit(self, playing: bool):
        if playing == True:
            threading.Thread(target=self.__playpriv).start()
            self.playing = True
        else:
            Aplayer.aplayer.stdin.write('pause\n')


    def __init__(self, FQFN='', play: bool=True, args: list=[]):
        self.FQFN = FQFN
        self.ctext = ''
        if FQFN == '':
            Aplayer.aplayer = None
            self.playing = False
            return
        else:
            Aplayer.aplayer = self.genProcess(FQFN, args)
            self.playing = play
        Aplayer.instances += 1
        if Aplayer.instances > 1:
            Aplayer.aplayer.terminate()
        self.pauseplayInit(self.playing)

    def terminate():
        Aplayer.aplayer.terminate()

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
        while self.signsOfLife():
            self.ctext += Aplayer.aplayer.stdout.readline()
        Aplayer.terminate()
        return
             

    def pauseplay(self):
        self.pwrite('pause')
        if self.playing == True:
            self.playing = False
        else:
            self.playing = True
            t1 = threading.Thread(target=self.__playpriv)
            t1.start()    

    def clearctext(self):
        self.ctext = ''

    def signsOfLife(self) -> bool:
        time.sleep(0.01)
        ret = Aplayer.aplayer.poll() == None
        if ret == False:
            self.playing = False
        return ret
  
    def quit(self):
        self.playing = False
        if not self.pwrite('quit'):
            Aplayer.aplayer.terminate()
 
    def seek(self, plusMinusTime):
        self.pwrite("seek " + str(plusMinusTime))

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

    
    def loadfile(self, FQFN, play: bool=True):
        if FQFN == '':
            return
        self.FQFN = FQFN
        if Aplayer.aplayer != None:
            Aplayer.terminate()
        Aplayer.aplayer = self.genProcess(FQFN)
        self.pauseplayInit(play)

        
