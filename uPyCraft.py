#! python3
import os
import sys
import time
import queue
import configparser
import posixpath as xpath

import serial
from serial.tools import list_ports

from PyQt5 import QtCore, QtGui, QtWidgets

from threads import SerThread, CmdThread
from widgets import RenameDialog, NewFilDialog, NewDirDialog


from uPyCraft_UI import Ui_uPyCraft
class uPyCraft(QtWidgets.QMainWindow, Ui_uPyCraft):
    def __init__(self):
        super(uPyCraft, self).__init__()

        self.setupUi(self)

        self.tree.ui      = self
        self.terminal.ui  = self
        self.tabWidget.ui = self
        
        ''' Serial Select '''
        self.cmbSer = QtWidgets.QComboBox(self)
        for port, desc, hwid in list_ports.comports():
            self.cmbSer.addItem(f'{port} ({desc[:desc.index(" (")]})')

        self.toolBar.insertWidget(self.actionConnect, self.cmbSer)

        ''' Directory Tree '''
        self.dirFlash = '/flash'    # Flash root directory: '/flash' or '/'

        self.treeFlash = QtGui.QStandardItem(QtGui.QIcon('images/treeMenuClosed.png'), self.dirFlash)
        self.treeFlash.setData('dir', QtCore.Qt.WhatsThisRole)
        self.treeFlash.setToolTip(self.dirFlash)

        model = QtGui.QStandardItemModel(self.tree)
        model.appendRow(self.treeFlash)
        self.tree.setModel(model)

        self.tree.actionRun.triggered.connect(self.on_treeActionRun_triggered)
        self.tree.actionNewfil.triggered.connect(self.on_treeActionNewfil_triggered)
        self.tree.actionNewdir.triggered.connect(self.on_treeActionNewdir_triggered)
        self.tree.actionRename.triggered.connect(self.on_treeActionRename_triggered)
        self.tree.actionDelete.triggered.connect(self.on_treeActionDelete_triggered)
        self.tree.actionSavePC.triggered.connect(self.on_treeActionSavePC_triggered)
        
        self.initSetting()

        ''' Threads '''
        self.serQueue = queue.Queue()
        self.cmdQueue = queue.Queue()

        self.ser = serial.Serial(baudrate=115200, timeout=0.001)

        self.serThread = SerThread(self)
        self.serThread.sig_msgToTrmReceived.connect(self.terminal.on_msgToTrmReceived)

        self.cmdThread = CmdThread(self)
        self.cmdThread.sig_fileListed.connect(self.on_fileListed)
        self.cmdThread.sig_fileLoaded.connect(self.on_fileLoaded)
        self.cmdThread.sig_fileRenamed.connect(self.on_fileRenamed)
        self.cmdThread.sig_fileDeleted.connect(self.on_fileDeleted)

        ''' Dialogs '''
        self.renameDialog = RenameDialog()
        self.renameDialog.btnOK.clicked.connect(self.on_renameDialog_btnOK_clicked)

        self.newfilDialog = NewFilDialog()
        self.newfilDialog.btnOK.clicked.connect(self.on_newfilDialog_btnOK_clicked)

        self.newdirDialog = NewDirDialog()
        self.newdirDialog.btnOK.clicked.connect(self.on_newdirDialog_btnOK_clicked)

    def initSetting(self):
        if not os.path.exists('setting.ini'):
            open('setting.ini', 'w')
        
        self.conf = configparser.ConfigParser()
        self.conf.read('setting.ini')

        if not self.conf.has_section('serial'):
            self.conf.add_section('serial')
            self.conf.set('serial', 'port', 'COM0')
            self.conf.set('serial', 'baudrate', '115200')

        sel = self.cmbSer.findText(self.conf.get('serial', 'port'))
        if sel != -1:
            self.cmbSer.setCurrentIndex(sel)

        if not self.conf.has_section('window'):
            self.conf.add_section('window')
            self.conf.set('window', 'window', '(900, 600)')
            self.conf.set('window', 'hSplitter', '[200, 800]')
            self.conf.set('window', 'vSplitter', '[700, 300]')

        self.resize(*eval(self.conf.get('window', 'window')))
        self.hSplitter.setSizes(eval(self.conf.get('window', 'hSplitter')))
        self.vSplitter.setSizes(eval(self.conf.get('window', 'vSplitter')))

        if not self.conf.has_section('others'):
            self.conf.add_section('others')
            self.conf.set('others', 'PCFolder', '')

    @QtCore.pyqtSlot()
    def on_actionConnect_triggered(self):
        try:
            self.ser.port = self.cmbSer.currentText().split()[0]
            self.ser.close()
            self.ser.open()
        except Exception as e:
            self.terminal.append('serial open fail')
            return

        self.ser.write(b'\x03')
        recv = b''
        for i in range(int(2/0.01)):
            time.sleep(0.01)
            recv += self.ser.read(self.ser.in_waiting)
            if b'>>> ' in recv:
                self.terminal.removeLastLine()
                break
        else:
            self.terminal.append('connect board fail')
            return

        self.cmdThread.start()
        self.serThread.start()

        self.cmdQueue.put('importOS')

        self.cmdQueue.put(f'listFile:::{self.dirFlash}')

        self.cmbSer.setEnabled(False)

        self.terminal.setReadOnly(False)
        self.terminal.eventFilterEnable = True

        self.actionConnect.setVisible(False)
        self.actionDisconnect.setVisible(True)
        
    @QtCore.pyqtSlot()
    def on_actionDisconnect_triggered(self):
        for i in range(self.tabWidget.count()):
            index = self.tabWidget.currentIndex()
            if self.tabWidget.tabText(index).endswith('*'):
                QtWidgets.QMessageBox.warning(self, 'Unsaved File!', 'There are files not saved, deal with them first.', QtWidgets.QMessageBox.Ok)
                return

            self.tabWidget.closeTab(index)
        
        self.serQueue.put('Key:::\x03')
        self.serQueue.put('close')
        self.cmdQueue.put('close')
        while not self.cmdQueue.empty() or not self.serQueue.empty():
            time.sleep(0.100)

        self.serThread.exit()
        self.cmdThread.exit()

        self.terminal.clear()
        self.terminal.setReadOnly(True)
        self.terminal.eventFilterEnable = False

        row = self.treeFlash.rowCount()
        self.treeFlash.removeRows(0, row)

        self.actionConnect.setVisible(True)
        self.actionDisconnect.setVisible(False)

        self.ser.close()
        self.cmbSer.setEnabled(True)
    
    @QtCore.pyqtSlot()
    def on_actionRefresh_triggered(self):
        if not self.ser.is_open:
            self.terminal.append('serial not opened')
            return

        self.cmdQueue.put(f'listFile:::{self.dirFlash}')

    @QtCore.pyqtSlot()
    def on_actionDownload_triggered(self, execFile=False):
        if not self.ser.is_open:
            self.terminal.append('serial not opened')
            return False

        if self.tabWidget.currentIndex() < 0:
            self.terminal.append('no file opened')
            return False

        filePath = self.tabWidget.tabText(self.tabWidget.currentIndex())
        if filePath.endswith('*'):
            filePath = filePath[:-1]
            fileData = self.tabWidget.currentWidget().text()
            self.cmdQueue.put(f'downFile:::{filePath}:::{fileData}:::{execFile}')

            self.tabWidget.setTabText(self.tabWidget.currentIndex(), filePath)

        elif execFile:
            self.cmdQueue.put(f'execFile:::{filePath}')

    @QtCore.pyqtSlot()
    def on_actionDownloadAndRun_triggered(self):
        self.on_actionDownload_triggered(execFile=True)

    @QtCore.pyqtSlot()
    def on_actionStopExcute_triggered(self):
        if not self.ser.is_open:
            self.terminal.append('serial not opened')
            return

        self.terminal.keyPressMsg=''
        self.serQueue.put('Key:::\x03')

    @QtCore.pyqtSlot()
    def on_actionClearTerminal_triggered(self):
        self.terminal.clear()

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def on_tree_doubleClicked(self, index):
        if self.tree.pressedFileType == 'file':
            if self.tree.pressedFilePath not in self.tabWidget.openedFiles:
                self.cmdQueue.put(f'loadFile:::{self.tree.pressedFilePath}:::TabPage')

            else:               # already loaded
                index, _ = self.getFileIndex(self.tree.pressedFilePath)
                self.tabWidget.setCurrentIndex(index)
    
    def on_treeActionRun_triggered(self):
        if not self.ser.is_open:
            self.terminal.append('serial not opened')
            return

        self.cmdQueue.put(f'execFile:::{self.tree.pressedFilePath}')

    def on_treeActionNewfil_triggered(self):
        if not self.ser.is_open:
            self.terminal.append('serial not opened')
            return

        self.newfilDialog.exec()
    
    def on_newfilDialog_btnOK_clicked(self):
        name = self.newfilDialog.linName.text()
        path = xpath.join(self.tree.pressedFilePath, name)

        if self.tree.isFileExist(path, 'file'):
            self.terminal.append(f'file {path} already exists\n\n>>> ')
            return

        self.cmdQueue.put(f'createFile:::{path}')

    def on_treeActionNewdir_triggered(self):
        if not self.ser.is_open:
            self.terminal.append('serial not opened')
            return

        self.newdirDialog.exec()

    def on_newdirDialog_btnOK_clicked(self):
        name = self.newdirDialog.linName.text()
        path = xpath.join(self.tree.pressedFilePath, name)

        if self.tree.isFileExist(path, 'dir'):
            self.terminal.append(f'directory {path} already exists\n\n>>> ')
            return

        self.cmdQueue.put(f'createDir:::{path}:::True')

    def on_treeActionRename_triggered(self):
        self.renameDialog.linName.setText(os.path.basename(self.tree.pressedFilePath))
        self.renameDialog.exec()

    def on_renameDialog_btnOK_clicked(self):
        newName = self.renameDialog.linName.text()
        newPath = xpath.join(os.path.dirname(self.tree.pressedFilePath), newName)

        if self.tree.isFileExist(newPath, self.tree.pressedFileType):
            self.terminal.append(f'{newPath} already exists\n\n>>> ')
            return

        self.cmdQueue.put(f'renameFile:::{self.tree.pressedFilePath}:::{newPath}:::{self.tree.pressedFileType}')

    def on_treeActionDelete_triggered(self):
        res = QtWidgets.QMessageBox.question(self, 'confirm delete?', self.tree.pressedFilePath, QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
        if res == QtWidgets.QMessageBox.Cancel:
            return

        item = self.tree.model().itemFromIndex(self.tree.pressedIndex)
        if item.hasChildren():				# folder and not empty
            self.deleteDirContent(item)

        self.cmdQueue.put(f'deleteFile:::{self.tree.pressedFilePath}')

        self.cmdQueue.put(f'listFile:::{self.dirFlash}')

    def deleteDirContent(self, root):
        for i in range(root.rowCount()):
            item = root.child(i)
            if item.hasChildren():
                self.deleteDirContent(item)

            self.cmdQueue.put(f'deleteFile:::{self.tree.getPathAndType(item.index())[0]}')

    def on_treeActionSavePC_triggered(self):
        dirPath = QtWidgets.QFileDialog.getExistingDirectory(self, 'The folder to save to', self.conf.get('others', 'PCFolder'))
        if not dirPath:
            return

        self.conf.set('others', 'PCFolder', dirPath)

        item = self.tree.model().itemFromIndex(self.tree.pressedIndex)
        name = item.data(QtCore.Qt.DisplayRole)
        newPath = os.path.join(dirPath, 'flash' if name == '/flash' else name)
        if item.data(QtCore.Qt.WhatsThisRole) == 'dir':
            if os.path.exists(newPath) and os.path.isdir(newPath):
                self.terminal.append(f'{newPath} already exists\n\n>>> ')
                return

            os.mkdir(newPath)
            self.saveDirContent(newPath, item)

        else:
            if os.path.exists(newPath) and os.path.isfile(newPath):
                self.terminal.append(f'{newPath} already exists\n\n>>> ')
                return

            self.cmdQueue.put(f'loadFile:::{self.tree.getPathAndType(item.index())[0]}:::{newPath}')

    def saveDirContent(self, dirPath, root):
        for i in range(root.rowCount()):
            item = root.child(i)
            newPath = os.path.join(dirPath, item.data(QtCore.Qt.DisplayRole))
            if item.data(QtCore.Qt.WhatsThisRole) == 'dir':
                os.mkdir(newPath)
                self.saveDirContent(newPath, item)

            else:
                self.cmdQueue.put(f'loadFile:::{self.tree.getPathAndType(item.index())[0]}:::{newPath}')

    def on_fileListed(self, data):
        row = self.treeFlash.rowCount()
        self.treeFlash.removeRows(0, row)
        
        self.createTree(self.treeFlash, self.listBoardDir(data[self.dirFlash]))
        self.tree.expand(self.treeFlash.index())

    def createTree(self, root, msg):
        if type(msg) is str:
            item = QtGui.QStandardItem(QtGui.QIcon('images/treeFileOpen.png'), msg)
            item.setData('file', QtCore.Qt.WhatsThisRole)
            root.appendRow(item)

        elif type(msg) is list:
            for item in msg:
                self.createTree(root, item)

        elif type(msg) is dict:
            for dir in msg:
                item = QtGui.QStandardItem(QtGui.QIcon('images/treeMenuClosed.png'), os.path.split(dir)[-1])
                item.setData('dir', QtCore.Qt.WhatsThisRole)
                root.appendRow(item)

                self.createTree(item, msg[dir])

    def listBoardDir(self, items):
        files, dirs = [], []
        for item in items:
            if type(item) == str:
                files.append(item)
            elif type(item) == dict:
                dirs.append({list(item.keys())[0] : self.listBoardDir(list(item.values())[0])})

        return sorted(dirs, key=lambda dict: dict.keys()) + sorted(files)

    def on_fileLoaded(self, filePath, fileData, target):
        if target == 'TabPage':
            self.tabWidget.newTab(filePath, fileData)

            index, _ = self.getFileIndex(filePath)
            self.tabWidget.setCurrentIndex(index)

        else:
            with open(target, 'wb') as f:
                f.write(fileData.encode('latin-1'))
        
    def on_fileRenamed(self, oldPath, newPath, fileType):
        if fileType == 'file':
            if oldPath in self.tabWidget.openedFiles:
                index, changed = self.getFileIndex(oldPath)
                self.tabWidget.setTabText(index, newPath + ('*' if changed else ''))

                self.tabWidget.openedFiles[self.tabWidget.openedFiles.index(oldPath)] = newPath

        elif fileType == 'dir':
            for filePath in self.tabWidget.openedFiles:
                if filePath.startswith(oldPath):
                    index, changed = self.getFileIndex(filePath)
                    newFilePath = xpath.join(newPath, filePath[len(oldPath)+1:])
                    self.tabWidget.setTabText(index, newFilePath + ('*' if changed else ''))

                    self.tabWidget.openedFiles[self.tabWidget.openedFiles.index(filePath)] = newFilePath                    

        self.cmdQueue.put(f'listFile:::{self.dirFlash}')

    def on_fileDeleted(self, filePath):
        if filePath in self.tabWidget.openedFiles:
            index, _ = self.getFileIndex(filePath)
            self.tabWidget.removeTab(index)
            self.tabWidget.openedFiles.remove(filePath)

    def getFileIndex(self, filePath):
        for i in range(self.tabWidget.count()):
            if self.tabWidget.tabText(i) == filePath:
                return i, False

            if self.tabWidget.tabText(i) == filePath+'*':
                return i, True  # file content changed

    def closeEvent(self,event):
        self.conf.set('serial', 'port', self.cmbSer.currentText())

        if not self.isMaximized():
            self.conf.set('window', 'window', f'({self.width()}, {self.height()})')
            self.conf.set('window', 'hSplitter', f'{self.hSplitter.sizes()}')
            self.conf.set('window', 'vSplitter', f'{self.vSplitter.sizes()}')

        self.conf.write(open('setting.ini', 'w'))


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = uPyCraft()
    win.show()
    sys.exit(app.exec_())
