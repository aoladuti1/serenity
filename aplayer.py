
from math import floor
import random
from re import A
import subprocess
import threading
import time

LEN_LIST = -69
def shuffle(list: list, fromIndex = 0, toIndex = LEN_LIST):
    if toIndex == LEN_LIST: toIndex = len(list)
    for i in range(toIndex - 1, fromIndex, -1):
        temp = list[i]
        j = random.randrange(fromIndex, i) 
        list[i] = list[j]
        list[j] = temp

class Aplayer:
    MPLAYER_DIR = 'C:\\Users\\anton\\Downloads\\mplayer-svn-38151-x86_64\\mplayer.exe'
    TRACK = 'track'
    QUEUE = 'queue'
    VOID = ''
    aplayer = None
    ctext='_'
    volume = 100
    speed = 1.0
    playing = False
    songs = []
    songIndex = 0
    pos = 0
    songRunning = False
    queuing = False
    genNow = False
    repeatMode = VOID
    __skipLock = False
    __shuffleSignal = False
    __firstRun = True
    __args = []
    __manualSwitch = False
    __forceStop = False
    __repeatIndex = 0
    __modes = [VOID, TRACK, QUEUE]


    # Will open a aplayer.exe
    # __args is a list of additional arguments after -slave and before the fully qualified filename
    def __genProcess(FQFN, args=[]):
        print('gp')
        # -pausing 2 means that no matter what command is passed through the PIPE, 
        # the pause/play state stays the same
        Aplayer.kill()
        argslist = (
            [Aplayer.MPLAYER_DIR]
          + [   '-slave', '-pausing', '2', '-idle', '-v',
                '-volume', str(Aplayer.volume),
                '-speed', str(Aplayer.speed)    ] 
          + args 
          + [FQFN]
        )
        return subprocess.Popen(
            argslist, 
            stdout=subprocess.PIPE, 
            stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
            )

    def kill():
        # call only once
        Aplayer.songRunning = True # breaks the idle playpriv loop
        if Aplayer.aplayer == None: return
        Aplayer.aplayer.terminate()
        

    def getSong() -> dict:
        return Aplayer.songs[Aplayer.songIndex]

    def __loadFile(songDict: dict, queue = False, args: list=[], init=False):
        if queue == False:
            Aplayer.songs = [songDict]
            Aplayer.songIndex = 0
        else:
            Aplayer.songs.append(songDict)
            Aplayer.songs[len(Aplayer.songs) - 1] = songDict
        Aplayer.queuing = queue
        Aplayer.__args = args
        if init == True:
            Aplayer.aplayer = Aplayer.__genProcess(songDict['FQFN'], args)
            Aplayer.playing = True
            threading.Thread(target=Aplayer.__playpriv).start()
        elif queue == False:
            Aplayer.__forceStop = True
            Aplayer.__manualSwitch = True
        elif Aplayer.songRunning == False:
            Aplayer.genNow = True

    # only call if signsOfLife() is True
    def __prepNext():
        Aplayer.__skipLock = True
        if not Aplayer.songIndex >= len(Aplayer.songs) - 1:
            Aplayer.songIndex += 1
            Aplayer.genNow = True
        else:
            print("X")
            Aplayer.genNow = Aplayer.repeatMode == Aplayer.TRACK

    def next(muteBeforeNext: bool = True):
        if Aplayer.__skipLock == True: return
        if Aplayer.signsOfLife() == True:
            Aplayer.__prepNext()
            Aplayer.__manualSwitch = True
            if muteBeforeNext == True:
                Aplayer.aplayer.stdin.write('mute\n')
            Aplayer.aplayer.stdin.write('seek 101 1\n')
        Aplayer.pos = 0
    
    def prev():
        if Aplayer.signsOfLife() == True:
            if Aplayer.songIndex > 0:
                Aplayer.__manualSwitch = True
                Aplayer.songIndex -= 1
                Aplayer.genNow = True
                Aplayer.aplayer.stdin.write('mute\n')
                Aplayer.aplayer.stdin.write('seek 101 1\n')
            else:
                Aplayer.seek(0,"")
        Aplayer.pos = 0
        
    def play(songDict: dict, queue = False, __args: list=[]):
        isInit = Aplayer.aplayer == None
        if isInit == True:
            queue = False
        Aplayer.__loadFile(songDict, queue, __args, init=isInit)

    def pauseplay():
        if Aplayer.songRunning == True:
            Aplayer.playing = not Aplayer.playing
            Aplayer.pwrite('pause')

    def pwrite(text: str) -> bool:
        """Writes raw string inputs to the mplayer subprocess,
        after calling Aplayer.signsOfLife() to ensure the process
        is writable.

        __args:
            text (str): the input to pass

        Returns:
            bool: returns the result of Aplayer.signsOfLife()
        """
        ret = Aplayer.signsOfLife()
        if ret == True:
            Aplayer.aplayer.stdin.write(r"{}".format(text) + "\n") 
        return ret

    def __toNextSong():
        return  ((not Aplayer.songIndex >= len(Aplayer.songs)-1
                or Aplayer.repeatMode == Aplayer.QUEUE) 
                and not Aplayer.repeatMode == Aplayer.TRACK)

    def __handleOutput():
        if Aplayer.songRunning == True:
            Aplayer.ctext = Aplayer.aplayer.stdout.readline()
        if Aplayer.ctext.startswith('ds_fill') == True or Aplayer.__forceStop==True or not Aplayer.songRunning:
            if not Aplayer.genNow: Aplayer.genNow = Aplayer.repeatMode == Aplayer.TRACK
            if Aplayer.__manualSwitch == True:
                pass
            elif Aplayer.songRunning == True:
                while Aplayer.aplayer.stdout.readline().startswith("ao_") == False: pass
            Aplayer.songRunning = False
            Aplayer.playing = False
            # this branch is run EVERY time a song changes
            if (Aplayer.__toNextSong() == True):
                # we are going to next song
                if Aplayer.songIndex >= len(Aplayer.songs) - 1: # means repeatMode is QUEUE
                    Aplayer.songIndex = 0
                elif Aplayer.__manualSwitch == False: # song ended naturally
                    Aplayer.songIndex += 1
                Aplayer.aplayer = Aplayer.__genProcess(Aplayer.getSong()['FQFN'], Aplayer.__args)
                while Aplayer.aplayer.stdout.readline().startswith("Play") == False: pass
                Aplayer.genNow = False
                Aplayer.songRunning = True
                Aplayer.playing = True
                Aplayer.__forceStop = False
            else:
                if Aplayer.genNow == True:
                    Aplayer.aplayer = Aplayer.__genProcess(Aplayer.getSong()['FQFN'], Aplayer.__args)
                    while Aplayer.aplayer.stdout.readline().startswith("Play") == False: pass
                    Aplayer.genNow = False
                    Aplayer.playing = True
                    Aplayer.songRunning = True
                    Aplayer.__forceStop = False
            Aplayer.__manualSwitch = False
            Aplayer.__skipLock = False
        elif Aplayer.ctext.startswith('A:'):
            exactPos = float(Aplayer.ctext.split()[1]) # class var in future
            Aplayer.pos = floor(exactPos)
        elif Aplayer.ctext.startswith('EOF'):
            Aplayer.songRunning = False
            Aplayer.playing = False
        elif Aplayer.ctext.startswith('Play'):
            Aplayer.songRunning = True
            if Aplayer.__firstRun == True:
                Aplayer.__firstRun = False 
            else:
                Aplayer.songIndex += 1
            Aplayer.playing = True

    def __playpriv():
        """
        This function will ensure the playing audio keeps going normally.
        It must be threaded, and only called once, ever.
        """
        Aplayer.songRunning = True
        while (Aplayer.ctext != ''):
            Aplayer.__handleOutput()
            if Aplayer.__shuffleSignal == True:
                threading.Thread(target=Aplayer.__shuffle).start()
                while (Aplayer.__shuffleSignal == True):
                    threading.Thread(target=Aplayer._handleOutput).start()

    def signsOfLife() -> bool:
        """Checks if there is a live, writable mplayer subprocess
        on a best-effort basis.

        Returns:
            bool: True if there is a writable mplayer subprocess
        """
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

    def seek(seconds: int, type=""):
        if type == "+":
            if Aplayer.__skipLock == True: return
            if Aplayer.pos >= Aplayer.getSong()['duration']: return
            duration = Aplayer.getSong()['duration']
            if Aplayer.pos + seconds >= duration - 1:
                seekString = str(duration) + ' 2'
                Aplayer.pos = duration
            else: seekString = str(seconds)
        elif type == "-":
            if Aplayer.pos == 0 and Aplayer.songIndex > 0:
                Aplayer.prev()
                return
            else:
                seekString = type + str(seconds)
        else:
            if seconds < 0:
                seekString = '0 2'
            elif seconds >= Aplayer.getSong()['duration']:
                if Aplayer.__skipLock == True: return  
            else:
                seekString = str(seconds) + ' 2'
        Aplayer.pwrite('seek ' + seekString)
    
    def __shuffle():
        list = Aplayer.songs.copy()
        fromIndex = Aplayer.songIndex + 1
        shuffle(list, fromIndex)
        Aplayer.songs = list
        Aplayer.__shuffleSignal = False

    def shuffle():
        Aplayer.__shuffleSignal = True

    def repeat():
        """Repeats either the track, the queue
        or not at all, depending on when it is called.
        
        The first repeat() call will repeat the current track and set
        Aplayer.repeatMode to Aplayer.TRACK.  
        The next repeat() call will repeat the whole queue instead,
        and set Aplayer.repeatMode to Aplayer.QUEUE.
        The repeat() call after that will stop all repetition and set
        Aplayer.repeatMode to Aplayer.VOID (the empty string)
        And then it cycles back round (call no. 4 == first repeat() call)
        """
        if Aplayer.__repeatIndex >= len(Aplayer.__modes) - 1: 
            Aplayer.__repeatIndex = 0
        else:
            Aplayer.__repeatIndex += 1
        Aplayer.repeatMode = Aplayer.__modes[Aplayer.__repeatIndex]

    def setVolume(volume: int):
        """
        Sets the volume of the audio

        Parameters:
        
        volume: the new volume (between 1 and 100)
        """
        Aplayer.volume = volume
        Aplayer.pwrite('volume ' + str(volume) + ' 1')
    
    def setSpeed(speed: float):
        """
        Sets the speed of the audio

        Parameters:
        
        speed: the new speed multiplier (e.g. speed = 1.5 means 1.5x speed)
        """
        Aplayer.speed = speed
        Aplayer.pwrite('speed_set ' + str(speed))