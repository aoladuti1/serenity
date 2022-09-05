from math import floor
import subprocess
import threading
from turtle import position

def genShellString(string):
    return "\"" + string.replace("\\", "\\\\") + "\""

class Aplayer:
    MPLAYER_DIR = 'C:\\Users\\anton\\Downloads\\mplayer-svn-38151-x86_64\\mplayer.exe'
    aplayer = None
    ctext='_'
    volume = 100
    speed = 1.0
    procInstances = 0 # to ensure everything is kill()ed
    playing=False
    songs = []
    songIndex = 0
    firstRun = True
    pos = 0
    songRunning = False
    switchToSilence = False
    errorStop = False
    args = []
    queuing = False

    # Will open a aplayer.exe
    # args is a list of additional arguments after -slave and before the fully qualified filename
    def __genProcess(FQFN, args=[]):
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

    def __loadFile(songDict: dict, queue = False, args: list=[], init=False):
        if queue == False:
            Aplayer.songs = [songDict]
            Aplayer.songIndex = 0
        else:
            Aplayer.songs.append(songDict)
            Aplayer.songs[len(Aplayer.songs) - 1] = songDict
        Aplayer.queuing = queue
        Aplayer.args = args
        if init == True:
            Aplayer.aplayer = Aplayer.__genProcess(songDict['FQFN'], args)
            Aplayer.playing = True
            threading.Thread(target=Aplayer.__playpriv).start()
        else:
            Aplayer.pwrite(
                # mplayer syntax: loadfile <file> [zero or nonzero value]
                # if it has a zero it will play immediately; queue==False as an int is 0
                'loadfile {} {}'.format(
                    genShellString(songDict['FQFN']), int(queue)
                )
            )     

    def next():

        if Aplayer.pwrite('pt_step 1 1') == True:
            Aplayer.setSpeed(Aplayer.speed)
        Aplayer.switchToSilence = len(Aplayer.songs) - Aplayer.songIndex <= 1
        Aplayer.pos = 0
    
    def prev():
        Aplayer.switchToSilence = Aplayer.songIndex <= 0
        if Aplayer.signsOfLife() == True:
            if Aplayer.songIndex >= 1:
                Aplayer.songIndex -= 1
            Aplayer.firstRun = True
            Aplayer.play(Aplayer.getSong())
            Aplayer.setSpeed(Aplayer.speed)
        Aplayer.pos = 0
        
    def play(songDict: dict, queue = False, args: list=[]):
        isInit = Aplayer.aplayer == None
        if isInit == True:
            queue = False
        Aplayer.__loadFile(songDict, queue, args, init=isInit)

    def pauseplay():
        if Aplayer.songRunning == True:
            Aplayer.playing = not Aplayer.playing
            Aplayer.pwrite('pause')

    def pwrite(text: str) -> bool:
        """Writes raw string inputs to the mplayer subprocess,
        after calling Aplayer.signsOfLife() to ensure the process
        is writable.

        Args:
            text (str): the input to pass

        Returns:
            bool: returns the result of Aplayer.signsOfLife()
        """
        ret = Aplayer.signsOfLife()
        if ret == True:
            Aplayer.aplayer.stdin.write(r"{}".format(text) + "\n") 
        return ret

    def __playpriv():
        """
        This function will ensure the playing audio keeps going normally.
        It must be threaded, and only called once, ever.
        """
        Aplayer.songRunning = True
        while (Aplayer.ctext != ''):
            Aplayer.ctext = Aplayer.aplayer.stdout.readline()
            if Aplayer.ctext.startswith('ds_fill') == True or Aplayer.errorStop==True:
                while Aplayer.aplayer.stdout.readline().startswith("ao_") == False: pass
                if Aplayer.songIndex + 1 >= len(Aplayer.songs) and Aplayer.errorStop==False: #only / last song
                    Aplayer.playing = False
                    Aplayer.aplayer.stdin.write('stop\n')
                    Aplayer.errorStop = True
                else:
                    # this branch is run EVERY time a song changes
                    if Aplayer.firstRun == True:
                        Aplayer.firstRun = False 
                    elif Aplayer.queuing == True:
                        Aplayer.songIndex += 1
                    Aplayer.aplayer = Aplayer.__genProcess(Aplayer.getSong()['FQFN'], Aplayer.args)
                    while Aplayer.aplayer.stdout.readline().startswith("Play") == False: ""
                    Aplayer.songRunning = True
                    Aplayer.playing = True
                    Aplayer.errorStop = False
            elif Aplayer.ctext.startswith('Play'):
                Aplayer.setSpeed(Aplayer.speed)         
                if Aplayer.firstRun == True:
                    Aplayer.firstRun = False 
                elif Aplayer.queuing == True:
                    Aplayer.songIndex += 1
                Aplayer.songRunning = True
                if Aplayer.switchToSilence == True and Aplayer.playing == False:
                    Aplayer.switchToSilence = False
                else:
                    Aplayer.playing = True
            elif Aplayer.ctext.startswith('A:'):
                exactPos = float(Aplayer.ctext.split()[1]) # class var in future
                Aplayer.pos = floor(exactPos)
            elif Aplayer.ctext.startswith('EOF'):
                Aplayer.songRunning = False
                Aplayer.playing = False

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
            seekString = str(seconds)
        elif type == "-":
            if Aplayer.pos == 0 and Aplayer.songIndex > 0:
                Aplayer.prev()
                return
            else:
                seekString = type + str(seconds)
        else:
            if seconds < 0:
                seekString = '0 2'
            else:
                seekString = str(seconds) + ' 2'
        Aplayer.pwrite('seek ' + seekString)

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


        
