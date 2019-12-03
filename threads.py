import os
import re
import time
import posixpath as xpath

from PyQt5 import QtCore, QtGui


class SerThread(QtCore.QThread):
    sig_msgToTrmReceived = QtCore.pyqtSignal(str)  # message to terminal
    sig_msgToCmdReceived = QtCore.pyqtSignal(str)

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
    ''' Operation below will affect UI, UI change can only be done in UI thread '''
    sig_fileListed  = QtCore.pyqtSignal(dict)
    sig_fileLoaded  = QtCore.pyqtSignal(str, str)       # filePath, fileData
    sig_fileRenamed = QtCore.pyqtSignal(str, str, str)  # oldPath,  newPath, fileType
    sig_fileDeleted = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super(CmdThread, self).__init__(parent)

        self.ui = parent
        self.ui.serThread.sig_msgToCmdReceived.connect(self.on_msgToCmdReceived)

        self.serRecv = ''       # data from serial
        self.serRecvBuf = ''

    def run(self):
        while True:
            msg = self.ui.cmdQueue.get().split(':::')

            if msg[0] == 'importOS':
                self.importOS()

            elif msg[0] == 'listFile':
                self.listFile(msg[1])

            elif msg[0] == 'loadFile':
                self.loadFile(msg[1])

            elif msg[0] == 'downFile':
                self.downFile(msg[1], msg[2])
                self.ui.inDownloading = False

            elif msg[0] == 'execFile':
                self.execFile(msg[1])

            elif msg[0] == 'createDir':
                self.createDir(msg[1])

            elif msg[0] == 'createFile':
                self.createFile(msg[1])

            elif msg[0] == 'renameFile':
                self.renameFile(msg[1], msg[2], msg[3])

            elif msg[0] == 'deleteFile':
                self.deleteFile(msg[1])

            elif msg[0] == 'close':
                break

        self.exit()        

    def importOS(self):
        self.ui.serQueue.put('Cmd:::import os\r\n')
        err = self.waitComplete()
        if err:
            return
    
    def waitComplete(self):
        ''' 每个self.ui.serQueue.put()调用后都要调用self.waitComplete()读走板子打印的'>>>'，
            防止后面的命令错误地将前面命令的响应当作板子对自己的响应
        '''
        self.serRecv = ''
        for i in range(int(2/0.01)):
            time.sleep(0.01)
            if self.serRecv:
                break
        else:
            return 'Timeout'
        
        if self.serRecv.find('Traceback') >= 0:
            return self.serRecv

        elif self.serRecv.find('... ') >= 0:
            self.ui.serQueue.put('UI:::\x03')
            return 'IOError'
        
        return None

    def listFile(self, path):
        data = self.listFileSub(path)

        if path == '/flash' and not isinstance(data, dict):
            self.ui.dirFlash = '/'
            self.ui.treeFlash.setToolTip(self.ui.dirFlash)

            data = self.listFileSub(self.ui.dirFlash)

        if isinstance(data, dict):
            self.sig_fileListed.emit(data)
        else:
            self.ui.terminal.append('refresh tree error.')

    def listFileSub(self, path):
        self.ui.serQueue.put(f'Cmd:::os.listdir({path!r})\r\n')
        err = self.waitComplete()
        if err:
            return

        data = {path: []}
        for file in eval(self.serRecv[self.serRecv.find('[') : self.serRecv.find(']')+1]):
            self.ui.serQueue.put(f'Cmd:::os.stat({xpath.join(path, file)!r})\r\n')
            err = self.waitComplete()
            if err:
                return

            match = re.search(r'\((\d+), ', self.serRecv)
            if int(match.group(1)) == 0o40000:
                if file not in ['System Volume Information']:
                    data[path].append(self.listFileSub(xpath.join(path, file)))
            else:
                data[path].append(file)

        return data

    def loadFile(self, filePath):
        self.ui.serQueue.put(f'Cmd:::print(open({filePath!r}, "r").read())\r\n')
        err = self.waitComplete()
        if err:
            return
        
        fileData = '\n'.join(self.serRecv.split('\r\n')[1:-1])  # upy发送出的数据回车都是‘\r\n’

        self.sig_fileLoaded.emit(filePath, fileData)

    def downFile(self, filePath, fileData):
        self.ui.serQueue.put(f'Cmd:::tempfile=open({filePath!r}, "w")\r\n')
        err = self.waitComplete()
        if err:
            return

        for i in range(0, len(fileData), 128):
            self.ui.terminal.cursor.insertText('.')
            self.ui.serQueue.put(f'Cmd:::tempfile.write({fileData[i:i+128]!r})\r\n')
            err = self.waitComplete()
            if err:
                return

        self.ui.serQueue.put('Cmd:::tempfile.close()\r\n')
        err = self.waitComplete()
        if err:
            return

        self.ui.terminal.append(f'{filePath} download successful\n\n>>> ')

        if self.ui.isDownloadAndRun:
            self.ui.cmdQueue.put(f'execFile:::{self.ui.isDownloadAndRun}')

            self.ui.isDownloadAndRun = False

    def execFile(self, filePath):
        self.ui.serQueue.put(f'exec_:::exec(open({filePath!r}).read(), globals())\r\n')
        err = self.waitComplete()
        if err:
            return

    def createDir(self, path):
        self.ui.serQueue.put(f'Cmd:::os.mkdir({path!r})\r\n')
        err = self.waitComplete()
        if err:
            return

        self.ui.cmdQueue.put(f'listFile:::{self.ui.dirFlash}')

    def createFile(self, path):
        self.ui.serQueue.put(f'Cmd:::open({path!r}, "w")\r\n')
        err = self.waitComplete()
        if err:
            return

        self.ui.cmdQueue.put(f'listFile:::{self.ui.dirFlash}')

    def renameFile(self, oldPath, newPath, fileType):
        self.ui.serQueue.put(f'Cmd:::os.rename({oldPath!r}, {newPath!r})\r\n')
        err = self.waitComplete()
        if err:
            return

        self.sig_fileRenamed.emit(oldPath, newPath, fileType)

    def deleteFile(self, path):
        self.ui.serQueue.put(f'Cmd:::os.stat({path!r})\r\n')
        err = self.waitComplete()
        if err:
            return

        match = re.search(r'\((\d+), ', self.serRecv)
        if int(match.group(1)) == 0o100000: # remove file
            self.ui.serQueue.put(f'Cmd:::os.remove({path!r})\r\n')
        else:                               # rmdir
            self.ui.serQueue.put(f'Cmd:::os.rmdir({path!r})\r\n')

        err = self.waitComplete()
        if err:
            return
       
        self.sig_fileDeleted.emit(path)
    
    def on_msgToCmdReceived(self, data):
        self.serRecvBuf += data
        if self.serRecvBuf.find('>>> ') >= 0 or self.serRecvBuf.find('... ') >= 0:
            self.serRecv = self.serRecvBuf
            self.serRecvBuf = ''
