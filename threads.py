import os
import re
import time
from functools import partial

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, pyqtSignal


class SerThread(QtCore.QThread):
    sig_msgToTrmReceived = pyqtSignal(str)  # message to terminal
    sig_msgToCmdReceived = pyqtSignal(str)

    def __init__(self, parent):
        super(SerThread, self).__init__(parent)

        self.ui = parent

        self.oper = ''
        self.operargv = ''
        self.lastoper = ''
        
    def run(self):
        execOutput = ''
        while self.ui.ser.isOpen():
            if not self.ui.serQueue.empty():
                cmd = self.ui.serQueue.get()
                print(cmd)

                cmd = cmd.split(':::')
                self.oper = cmd[0]
                if len(cmd) > 1:
                    self.operargv = cmd[1] if type(cmd[1]) is bytes else cmd[1].encode('utf-8')
                else:
                    self.operargv = b''

                if self.oper == 'close':
                    break

                elif self.oper == 'UI':
                    if self.operargv == b'\x03':
                        self.lastoper = ''
                    elif self.lastoper == 'exec_':
                        self.sig_msgToTrmReceived.emit('board is running file, stop it first\r\n')
                        continue

                elif self.oper == 'Cmd':
                    if self.lastoper == 'exec_':
                        self.sig_msgToTrmReceived.emit('board is running file, stop it first\r\n')
                        self.oper = 'UI'
                        continue

                elif self.oper == 'exec_':
                    if self.lastoper == 'exec_':
                        self.sig_msgToTrmReceived.emit('board is running file, stop it first\r\n')
                        self.oper = 'UI'
                        continue

                    self.lastoper = 'exec_'

                try:
                    self.ui.ser.write(self.operargv)
                    self.ui.ser.flush()
                except Exception:
                    self.lastoper = ''
                    self.oper = ''
                    break

            if self.oper in ['', 'UI', 'exec_']:
                try:
                    data = self.ui.ser.read(1)
                except Exception as e:
                    break

                if data == b'':
                    continue

                data = data.decode(encoding='utf-8', errors='replace')
                
                if self.lastoper == 'exec_':
                    execOutput += data
                    if execOutput.find('>>> ') >= 0:    # exit from exec
                        execOutput = ''
                        self.lastoper = ''

                self.sig_msgToTrmReceived.emit(data)

            elif self.oper == 'Cmd':
                try:
                    data = self.ui.ser.read(10)
                except Exception:
                    break

                if data == b'':
                    continue

                data = data.decode(encoding='utf-8', errors='replace')
                if data:
                    self.sig_msgToCmdReceived.emit(data)           

        self.lastoper = ''
        self.exit()


class CmdThread(QtCore.QThread):
    sig_boardFileDeleted = pyqtSignal(str)
    sig_boardFileRenamed = pyqtSignal(str, str) # oldPath, newPath
    sig_boardFileLoaded  = pyqtSignal(str, str) # filePath, fileData
    sig_boardFileListed  = pyqtSignal(dict)
    sig_messageReceived  = pyqtSignal(str)

    def __init__(self, parent):
        super(CmdThread, self).__init__(parent)

        self.ui = parent
        self.ui.serThread.sig_msgToCmdReceived.connect(self.on_msgToCmdReceived)

        self.serData = ''       # data from serial
        self.serDataBuf = ''

    def run(self):
        while True:
            msg = self.ui.cmdQueue.get().split(':::')

            if msg[0] == 'importOS':
                self.importOS()

            elif msg[0] == 'getcwd':
                self.getcwd()

            elif msg[0] == 'listFile':
                self.listFile()

            elif msg[0] == 'loadFile':
                self.loadFile(msg[1])

            elif msg[0] == 'downFile':
                self.downFile(msg[1], msg[2])

            elif msg[0] == 'execFile':
                self.execFile(msg[1])

            elif msg[0] == 'deleteFile':
                self.deleteFile(msg[1])

            elif msg[0] == 'renameFile':
                self.renameFile(msg[1], msg[2])

            elif msg[0] == 'createDir':
                self.createDir(msg[1])

            elif msg[0] == 'close':
                break

        self.exit()        

    def importOS(self):
        self.ui.serQueue.put('Cmd:::import os\r\n')
        self.waitUtilComplete('importOS')
    
    def waitUtilComplete(self, oper):
        ''' 每个self.ui.serQueue.put()调用后都要调用self.waitUtilComplete()读走板子打印的'>>>'，
            防止后面的命令错误地将前面命令的响应当作板子对自己的响应
        '''
        self.serData = ''
        startTime = time.time()
        while self.serData == '':
            time.sleep(0.005)
            if time.time() - startTime > 3:
                self.sig_messageReceived.emit('%s timeout' %oper)
                return 'timeout'

        if self.serData.find('Traceback') >= 0:
            self.sig_messageReceived.emit(self.serData)
            return 'error'

        elif self.serData.find('... ') >= 0:
            self.ui.serQueue.put('UI:::\x03')
            return 'error'
        
        return 'ok'

    def getcwd(self):
        self.ui.serQueue.put('Cmd:::os.getcwd()\r\n')
        self.waitUtilComplete('getcwd')

        dir = eval(self.serData.split('\r\n')[1])
        if dir in ['/', '/flash']:      # Flash存储器挂载点
            self.ui.dirFlash = dir
            self.ui.treeFlash.setToolTip(dir)

    def listFile(self):
        res = self.listFileDir(self.ui.dirFlash)

        self.sig_boardFileListed.emit(res)

    def listFileDir(self, dir):
        self.ui.serQueue.put("Cmd:::os.listdir('%s')\r\n" %dir)
        res = self.waitUtilComplete('listFile %s' %dir)
        if res != 'ok':
            return res

        data = {dir: []}
        for file in eval(self.serData[self.serData.find('[') : self.serData.find(']')+1]):
            self.ui.serQueue.put("Cmd:::os.stat('%s/%s')\r\n" %('' if dir == '/' else dir, file))
            res = self.waitUtilComplete('listFile stat')
            if res != 'ok':
                return res

            match = re.search(r'\((\d+), ', self.serData)
            if int(match.group(1)) == 0o40000:
                if file not in ['System Volume Information']:
                    data[dir].append(self.listFileDir('%s/%s' %('' if dir == '/' else dir, file)))
            else:
                data[dir].append(file)

        return data

    def loadFile(self, filePath):   # board file path
        self.ui.serQueue.put("Cmd:::print(open('%s', 'r', encoding='utf-8').read())\r\n" %str(filePath))
        res = self.waitUtilComplete('loadFile')
        if res != 'ok':
            return res
        
        self.serData = '\n'.join(self.serData.split('\r\n')[1:-1]).replace('\r', '\n')  # upy发送出的数据回车都是‘\r\n’

        self.sig_boardFileLoaded.emit(filePath, self.serData)

    def downFile(self, PCFilePath, boardFilePath):
        self.ui.serQueue.put('Cmd:::\x03')
        self.waitUtilComplete('downFile')
        
        self.ui.serQueue.put("Cmd:::tempfile=open('%s', 'w', encoding='utf-8')\r\n" %boardFilePath)
        res = self.waitUtilComplete('downFile open')
        if res != 'ok':
            self.sig_messageReceived.emit('downFile Fail')
            return res

        for line in iter(partial(open(PCFilePath, 'r', encoding='utf-8').read, 128), ''):
            self.sig_messageReceived.emit('.')
            self.ui.serQueue.put('Cmd:::tempfile.write(%s)\r\n' %repr(line))
            res = self.waitUtilComplete('downFile write')
            if res != 'ok':
                self.sig_messageReceived.emit('downFile Fail')
                return res

        self.ui.serQueue.put('Cmd:::tempfile.close()\r\n')
        res = self.waitUtilComplete('downFile close')
        if res != 'ok':
            self.sig_messageReceived.emit('downFile Fail')
            return 'res'

        self.sig_messageReceived.emit('downFile ok')

    def execFile(self, filePath):
        self.ui.serQueue.put("exec_:::exec(open('%s').read(), globals())\r\n" %filePath)

    def deleteFile(self, filePath):
        self.ui.serQueue.put("Cmd:::os.stat('%s')\r\n" %filePath)
        res = self.waitUtilComplete('deleteFile stat')
        if res != 'ok':
            return res

        match = re.search(r'\((\d+), ', self.serData)
        if int(match.group(1)) == 0o100000: # remove file
            self.ui.serQueue.put("Cmd:::os.remove('%s')\r\n" %filePath)
        else:                               # rmdir
            self.ui.serQueue.put("Cmd:::os.rmdir('%s')\r\n" %filePath)

        res = self.waitUtilComplete('deleteFile remove')
        if res != 'ok':
            return res
       
        self.sig_boardFileDeleted.emit(filePath)

    def renameFile(self, oldPath, newPath):
        self.ui.serQueue.put("Cmd:::os.stat('%s')\r\n" %oldPath)
        res = self.waitUtilComplete('renameFile stat')
        if res != 'ok':
            return res

        self.ui.serQueue.put("Cmd:::os.rename('%s', '%s')\r\n" %(oldPath, newPath))
        res = self.waitUtilComplete('renameFile reanme')
        if res != 'ok':
            return res

        self.sig_messageReceived.emit('renameFile ok')

    def createDir(self, path):
        self.ui.serQueue.put("Cmd:::os.mkdir('%s')\r\n" %path)
        res = self.waitUtilComplete('createDir')
        if res != 'ok':
            return res

        self.sig_messageReceived.emit('createDir ok')
    
    def on_msgToCmdReceived(self, data):
        self.serDataBuf += data
        if self.serDataBuf.find('>>> ') >= 0 or self.serDataBuf.find('... ') >= 0:
            self.serData = self.serDataBuf
            self.serDataBuf = ''
