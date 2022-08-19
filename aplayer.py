
from asyncio.subprocess import PIPE
import subprocess
from sys import stdout
import time
import threading

class Aplayer:
    MPLAYER_DIR = 'C:\\Users\\anton\\Downloads\\mplayer-svn-38151-x86_64\\mplayer.exe'
    
    # Will open a aplayer.exe
    # args is a list of additional arguments after -slave and before the fully qualified filename
    def genProcess(self, fullFileName, args=[]):
        argslist = [Aplayer.MPLAYER_DIR] + ['-slave', '-idle', '-pausing', '2'] + args + [fullFileName]
        return subprocess.Popen(
            argslist, 
            stdout=subprocess.PIPE, 
            stdin=subprocess.PIPE,
            stderr=stdout,
            universal_newlines=True, 
            bufsize=1
            )   

    def __init__(self, fullFileName=''):
        if fullFileName == '':
            self.aplayer = None
        self.fullFileName = fullFileName
        self.aplayer = self.genProcess(self.fullFileName)
        self.aplayer.stdin.write("pause\n")
        self.playing = False
        self.ctext = ''
        
        

    def clearctext(self):
        self.ctext = ''

    def signsOfLife(self) -> bool:
        time.sleep(0.01)
        ret = self.aplayer.poll() == None
        if ret == False:
            self.playing = False
        return ret

    def pwrite(self, text='') -> bool:
        sign = self.signsOfLife()
        if sign:
            self.aplayer.stdin.write(text + "\n")
        return sign
        

    def __playpriv(self):
        while self.signsOfLife():
            self.ctext += self.aplayer.stdout.readline()
        #print(self.ctext) # WILL NOT print everything to screen with vscode debugger
        #but it IS there in the ctext string
        return
             

    def pauseplay(self):
        self.pwrite('pause')
        if self.playing == True:
            self.playing = False
        else:
            self.playing = True
            t1 = threading.Thread(target=self.__playpriv)
            t1.start()
        
  
    def quit(self):
        self.playing = False
        if not self.pwrite('quit'):
            self.aplayer.terminate()
 
    def seek(self, plusMinusTime):
        self.pwrite("seek " + str(plusMinusTime))

    

