#! python3
import os
import sys
import time
import queue
import configparser

import serial
from serial.tools import list_ports

from PyQt5 import QtCore, QtGui, QtWidgets

from threads import SerThread, CmdThread
from widgets import RenameDialog, NewDirDialog


from uPyCraft_UI import Ui_uPyCraft
class uPyCraft(QtWidgets.QMainWindow, Ui_uPyCraft):
    def __init__(self):
        super(uPyCraft, self).__init__()

        self.setupUi(self)

        self.tree.ui      = self
        self.terminal.ui  = self
        self.tabWidget.ui = self
        
        self.hSplitter.setSizes([150, 750])
        self.vSplitter.setSizes([600, 300])

        ''' Serial Select '''
        self.cmbSer = QtWidgets.QComboBox(self)
        for port, desc, hwid in list_ports.comports():
            self.cmbSer.addItem(f'{port} ({desc[:desc.index(" (")]})')

        self.toolBar.insertWidget(self.actionConnect, self.cmbSer)

        ''' Directory Tree '''
        self.dirFlash = '/flash'    # Flash root directory: '/flash' or '/'

        self.treeFlash = QtGui.QStandardItem(QtGui.QIcon('images/treeMenuClosed.png'), self.dirFlash)
        self.treeFlash.setToolTip(self.dirFlash)

        model = QtGui.QStandardItemModel(self.tree)
        model.appendRow(self.treeFlash)
        self.tree.setModel(model)

        self.tree.actionRun.triggered.connect(self.on_treeActionRun_triggered)
        self.tree.actionDelete.triggered.connect(self.on_treeActionDelete_triggered)
        self.tree.actionRename.triggered.connect(self.on_treeActionRename_triggered)
        self.tree.actionNewfil.triggered.connect(self.on_treeActionNewfil_triggered)
        self.tree.actionNewdir.triggered.connect(self.on_treeActionNewdir_triggered)
        
        ''' Dialogs '''
        self.renameDialog = RenameDialog()
        self.renameDialog.btnOK.clicked.connect(self.on_renameDialog_btnOK_clicked)

        self.newdirDialog = NewDirDialog()
        self.newdirDialog.btnOK.clicked.connect(self.on_newdirDialog_btnOK_clicked)


        self.inDownloading = False
        self.isDownloadAndRun = False

        self.initSetting()

        self.ser = serial.Serial(baudrate=115200, timeout=0.001)

        self.serThread = SerThread(self)
        self.serThread.sig_msgToTrmReceived.connect(self.terminal.on_msgToTrmReceived)

        self.cmdQueue = queue.Queue()
        self.serQueue = queue.Queue()

        self.cmdThread = CmdThread(self)
        self.cmdThread.sig_fileLoaded.connect(self.on_fileLoaded)
        self.cmdThread.sig_fileListed.connect(self.on_fileListed)
        self.cmdThread.sig_fileRenamed.connect(self.on_fileRenamed)
        self.cmdThread.sig_fileDeleted.connect(self.on_fileDeleted)
        self.cmdThread.sig_msgReceived.connect(self.on_msgReceived)

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
        for i in range(200):
            time.sleep(0.01)
            recv += self.ser.read(self.ser.in_waiting)
            if b'>>> ' in recv:
                self.terminal.setText('>>> ')
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
        self.terminal.setEventFilterEnable(True)

        self.actionConnect.setVisible(False)
        self.actionDisconnect.setVisible(True)
        
    @QtCore.pyqtSlot()
    def on_actionDisconnect_triggered(self):        
        self.serQueue.put('UI:::\x03')
        self.serQueue.put('close')
        self.cmdQueue.put('close')
        while not self.cmdQueue.empty() or not self.serQueue.empty():
            time.sleep(0.100)

        self.serThread.exit()
        self.cmdThread.exit()

        self.terminal.setReadOnly(True)
        self.terminal.setEventFilterEnable(False)

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
    def on_actionDownload_triggered(self):
        if not self.ser.is_open:
            self.terminal.append('serial not opened')
            return False

        if self.tabWidget.currentIndex() < 0:
            self.terminal.append('no file opened')
            return False

        if self.inDownloading:
            self.terminal.append('already in downloading')
            return False

        self.serQueue.put('UI:::\x03')

        filePath = self.tabWidget.tabText(self.tabWidget.currentIndex())
        if filePath.endswith('*'):
            self.inDownloading = True

            fileData = self.tabWidget.currentWidget().text()
            self.cmdQueue.put(f'downFile:::{filePath[:-1]}:::{fileData}')

            self.tabWidget.setTabText(self.tabWidget.currentIndex(), filePath[:-1])

        return filePath

    @QtCore.pyqtSlot()
    def on_actionDownloadAndRun_triggered(self):
        filePath = self.on_actionDownload_triggered()

        if filePath:
            if filePath.endswith('*'):
                self.isDownloadAndRun = filePath[:-1]
            else:
                self.cmdQueue.put(f'execFile:::{filePath}')

    @QtCore.pyqtSlot()
    def on_actionStopExcute_triggered(self):
        if not self.ser.is_open:
            self.terminal.append('serial not opened')
            return

        self.terminal.keyPressMsg='else'
        self.serQueue.put('UI:::\x03')
        self.inDownloading = False

    @QtCore.pyqtSlot()
    def on_actionClearTerminal_triggered(self):
        self.terminal.clear()

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def on_tree_doubleClicked(self, index):
        if self.tree.pressedFilePath.endswith('.py') or self.tree.pressedFilePath.endswith('.ini'):
            self.cmdQueue.put(f'loadFile:::{self.tree.pressedFilePath}')
    
    def on_treeActionRun_triggered(self):
        if not self.ser.is_open:
            self.terminal.append('serial not opened')
            return

        self.cmdQueue.put(f'execFile:::{self.tree.pressedFilePath}')

    def on_treeActionRename_triggered(self):
        self.renameDialog.exec()

    def on_renameDialog_btnOK_clicked(self):
        newName = self.renameDialog.linName.text()

        if self.tree.pressedFile.startswith('/flash/'):
            newPath = os.path.split(self.tree.pressedFilePath)[0] + '/' + newName
            self.cmdQueue.put('renameFile:::%s:::%s' %(self.tree.pressedFilePath, newPath))

        elif self.tree.pressedFile.count('/') > 0:
            os.rename(self.tree.pressedFilePath, os.path.join(os.path.split(self.tree.pressedFilePath)[0], newName))

    def on_treeActionDelete_triggered(self):
        res = QtWidgets.QMessageBox.question(self, 'confirm delete?', self.tree.pressedFile, QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
        if res == QtWidgets.QMessageBox.Cancel:
            return

        self.cmdQueue.put('deleteFile:::%s' %self.tree.pressedFilePath)

    def on_treeActionNewfil_triggered(self):
        if not self.ser.is_open:
            self.terminal.append('serial not opened')
            return
        
    def on_treeActionNewdir_triggered(self):
        if not self.ser.is_open:
            self.terminal.append('serial not opened')
            return

        self.newdirDialog.exec()

    def on_newdirDialog_btnOK_clicked(self):
        dirName = self.newdirDialog.linName.text()

        if self.tree.pressedFile == '/flash':
            self.cmdQueue.put('createDir:::%s' %os.path.join(self.dirFlash, dirName).replace('\\', '/'))

        elif self.tree.pressedFile.count('/') > 0:
            os.mkdir(os.path.join(self.tree.pressedFilePath, dirName))

    def on_fileLoaded(self, filePath, fileData):
        if filePath not in self.tabWidget.openedFiles:
            self.tabWidget.newTab(filePath, fileData)
        else:
            for i in range(len(self.tabWidget.openedFiles)):
                if self.tabWidget.tabText(i) == filePath:
                    self.tabWidget.setCurrentIndex(i)
                    break

    def on_fileListed(self, data):
        if not isinstance(data, dict):
            self.terminal.append('refresh tree error.')
            self.inDownloading = False
            return

        row = self.treeFlash.rowCount()
        self.treeFlash.removeRows(0, row)
        
        self.createTree(self.treeFlash, self.listBoardDir(data[self.dirFlash]))
        self.tree.expand(self.treeFlash.index())

    def createTree(self, root, msg):
        if type(msg) is str:
            item = QtGui.QStandardItem(QtGui.QIcon('images/treeFileOpen.png'), msg)
            root.appendRow(item)

        elif type(msg) is list:
            for item in msg:
                self.createTree(root, item)

        elif type(msg) is dict:
            for dir in msg:
                item = QtGui.QStandardItem(QtGui.QIcon('images/treeMenuClosed.png'), os.path.split(dir)[-1])
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

    def on_fileRenamed(self, oldName, newName):
        self.cmdQueue.put(f'listFile:::{self.dirFlash}')

    def on_fileDeleted(self, filePath):
        filePath = self.Workspace + filePath   # 将板上路径转换为PC上路径，如/boot.py变成<Workspace>/boot.py
        
        self.closeTabPage(filePath)
        
        self.cmdQueue.put(f'listFile:::{self.dirFlash}')

    def on_msgReceived(self, msg):
        if msg in ['import os timeout', 'getcwd timeout']:
            self.terminal.append(msg)
            self.ser.close()

        elif msg == 'downFile ok':
            self.terminal.append(msg)
            self.inDownloading = False

            if self.isDownloadAndRun:
                self.cmdQueue.put(f'execFile:::{self.isDownloadAndRun}')

                self.isDownloadAndRun = False

        elif msg == 'downFile Fail':
            self.terminal.append(msg)
            self.inDownloading = False

        elif msg in ['deleteFile ok', 'renameFile ok', 'createDir ok']:
            self.cmdQueue.put(f'listFile:::{self.dirFlash}')

        elif msg == '.':
            self.terminal.cursor.insertText(msg)
        
        else:
            self.terminal.append(msg)

    def closeTabPage(self, filePath):
        if filePath in self.tabWidget.openedFiles:
            for i in range(len(self.tabWidget.openedFiles)):
                if self.tabWidget.tabText(i) == filePath:
                    self.tabWidget.removeTab(i)
                    self.tabWidget.openedFiles.remove(filePath)
                    break

    def closeEvent(self,event):
        self.conf.set('serial', 'port', self.cmbSer.currentText())

        self.conf.write(open('setting.ini', 'w'))


if __name__ == '__main__':
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_DontShowIconsInMenus)
    QtWidgets.QApplication.setFont(QtGui.QFont('Source Code Pro', 10))
    app = QtWidgets.QApplication(sys.argv)
    win = uPyCraft()
    win.show()
    sys.exit(app.exec_())
