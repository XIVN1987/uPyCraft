import os
import re
import time
import posixpath as xpath

from PyQt5 import QtCore, QtGui


class SerThread(QtCore.QThread):
    keyRespAvailable = QtCore.pyqtSignal(str)
    cmdRespAvailable = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super(SerThread, self).__init__(parent)

        self.ser      = parent.ser
        self.serQueue = parent.serQueue
        
    def run(self):
        while self.ser.isOpen():
            if not self.serQueue.empty():
                cmd = self.serQueue.get()
                print(cmd)

                if cmd == 'close':
                    break

                self.type, self.oper = cmd.split(':::')
                try:
                    self.ser.write(self.oper.encode('utf-8'))
                    self.ser.flush()
                except Exception:
                    break

            try:
                data = self.ser.read(self.ser.in_waiting).decode(encoding='utf-8', errors='replace')
            except Exception as e:
                break
            
            if data == '':
                time.sleep(0.001)
                continue

            if self.type == 'Cmd' and not self.oper.startswith('exec'):
                self.cmdRespAvailable.emit(data)
            else:
                self.keyRespAvailable.emit(data)

        self.exit()


class CmdThread(QtCore.QThread):
    ''' Operation below will affect UI, UI change can only be done in UI thread '''
    sig_fileListed  = QtCore.pyqtSignal(dict)
    sig_fileLoaded  = QtCore.pyqtSignal(str, str, str)  # filePath, fileData, target
    sig_fileRenamed = QtCore.pyqtSignal(str, str, str)  # oldPath,  newPath,  fileType
    sig_fileDeleted = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super(CmdThread, self).__init__(parent)

        self.ui = parent

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
                self.loadFile(msg[1], msg[2])

            elif msg[0] == 'downFile':
                self.downFile(msg[1], msg[2], msg[3] == 'True', msg[4] == 'True')

            elif msg[0] == 'execFile':
                self.execFile(msg[1])

            elif msg[0] == 'createDir':
                self.createDir(msg[1], msg[2] == 'True')

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
        self.waitComplete()

        self.ui.serQueue.put('Cmd:::import binascii\r\n')
        self.waitComplete()
    
    def waitComplete(self, second=2):
        ''' 每个self.ui.serQueue.put()调用后都要调用self.waitComplete()读走板子打印的'>>>'，
            防止后面的命令错误地将前面命令的响应当作板子对自己的响应
        '''
        self.serRecv = ''
        for i in range(int(second/0.01)):
            time.sleep(0.01)
            if self.serRecv:
                break
        else:
            return 'Timeout'
        
        if self.serRecv.find('... ') >= 0:
            self.ui.serQueue.put('Key:::\x03')
            return 'IOError'

        if self.serRecv.find('Traceback') >= 0:
            return self.serRecv
        
        return None

    def listFile(self, path):
        data = self.listFileDir(path)

        if not isinstance(data, dict):
            self.info(f'list {path} fail')
            return

        self.sig_fileListed.emit(data)
    
    def listFileDir(self, path):
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
                    data[path].append(self.listFileDir(xpath.join(path, file)))
            else:
                data[path].append(file)

        return data

    def loadFile(self, filePath, target):
        self.ui.serQueue.put(f'Cmd:::print(open({filePath!r}, "r").read())\r\n')
        err = self.waitComplete(second=5)
        if err:
            self.info(f'load {filePath} fail')
            return
        
        fileData = '\n'.join(self.serRecv.split('\r\n')[1:-1])  # upy发送出的数据回车都是‘\r\n’

        self.sig_fileLoaded.emit(filePath, fileData, target)

    def downFile(self, filePath, fileData, binFile, execFile):
        self.ui.serQueue.put(f'Cmd:::tempfile=open({filePath!r}, {repr("wb" if binFile else "w")})\r\n')
        err = self.waitComplete()
        if err:
            self.info(f'down {filePath} fail')
            return

        for i in range(0, len(fileData), 128):
            self.ui.terminal.cursor.insertText('.')
            if binFile:
                self.ui.serQueue.put(f'Cmd:::tempfile.write(binascii.unhexlify({fileData[i:i+128]!r}))\r\n')
            else:
                self.ui.serQueue.put(f'Cmd:::tempfile.write({fileData[i:i+128]!r})\r\n')
            err = self.waitComplete()
            if err:
                self.info(f'down {filePath} fail')
                return

        self.ui.serQueue.put('Cmd:::tempfile.close()\r\n')
        err = self.waitComplete()
        if err:
            self.info(f'down {filePath} fail')
            return

        self.info(f'down {filePath} success')

        if execFile:
            self.ui.cmdQueue.put(f'execFile:::{filePath}')

    def execFile(self, filePath):
        self.ui.serQueue.put(f'Cmd:::exec(open({filePath!r}).read(), globals())\r\n')
        self.waitComplete(second=0.5)   # no check, may exec for long time

    def createDir(self, path, refresh):
        self.ui.serQueue.put(f'Cmd:::os.mkdir({path!r})\r\n')
        err = self.waitComplete()
        if err:
            self.info(f'create {path} fail')
            return

        if refresh:
            self.ui.cmdQueue.put(f'listFile:::/')

    def createFile(self, path):
        self.ui.serQueue.put(f'Cmd:::open({path!r}, "w")\r\n')
        err = self.waitComplete()
        if err:
            self.info(f'create {path} fail')
            return

        self.ui.cmdQueue.put(f'listFile:::/')

    def renameFile(self, oldPath, newPath, fileType):
        self.ui.serQueue.put(f'Cmd:::os.rename({oldPath!r}, {newPath!r})\r\n')
        err = self.waitComplete()
        if err:
            self.info(f'rename {oldPath} fial')
            return

        self.sig_fileRenamed.emit(oldPath, newPath, fileType)

    def deleteFile(self, path):
        self.ui.serQueue.put(f'Cmd:::os.stat({path!r})\r\n')
        err = self.waitComplete()
        if err:
            self.info(f'delete {path} fail')
            return

        match = re.search(r'\((\d+), ', self.serRecv)
        if int(match.group(1)) == 0o100000: # remove file
            self.ui.serQueue.put(f'Cmd:::os.remove({path!r})\r\n')
        else:                               # rmdir
            self.ui.serQueue.put(f'Cmd:::os.rmdir({path!r})\r\n')

        err = self.waitComplete()
        if err:
            self.info(f'delete {path} fail')
            return
            
        self.sig_fileDeleted.emit(path)
    
    def on_cmdRespAvailable(self, data):
        self.serRecvBuf += data
        if self.serRecvBuf.find('>>> ') >= 0 or self.serRecvBuf.find('... ') >= 0:
            self.serRecv = self.serRecvBuf
            self.serRecvBuf = ''

    def info(self, msg):
        self.ui.terminal.append(f'{msg}\n\n>>> ')
