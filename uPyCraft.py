#! python3
import os
import sys
import time
import queue
import configparser

from PyQt5 import QtCore, QtGui, QtWidgets, Qsci
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal

import serial
import serial.tools.list_ports as listports

from widgets import RenameDialog, NewDirDialog
from threads import SerThread, CmdThread


from uPyCraft_UI import Ui_uPyCraft
class uPyCraft(QtWidgets.QMainWindow, Ui_uPyCraft):
    def __init__(self):
        super(uPyCraft, self).__init__()

        self.setupUi(self)

        self.hSplitter.setSizes([150, 750])
        self.vSplitter.setSizes([600, 300])

        ''' Serial Select '''
        self.cmbSer = QtWidgets.QComboBox(self)
        self.cmbSer.setMaximumWidth(100)
        self.cmbSer.currentTextChanged.connect(lambda txt: self.cmbSer.setToolTip(txt))

        for port, desc, hwid in listports.comports():
            self.cmbSer.addItem(f'{port} ({desc[:desc.index(" (")]})')

        self.toolBar.insertWidget(self.actionConnect, self.cmbSer)

        ''' Directory Tree '''
        self.tree.ui = self

        self.treeFlash = QtGui.QStandardItem(QtGui.QIcon('images/treeMenuClosed.png'), '/flash')

        model = QtGui.QStandardItemModel(self.tree)
        model.appendRow(self.treeFlash)
        self.tree.setModel(model)

        self.refreshPCTree()

        self.tree.actionRun.triggered.connect(self.on_treeActionRun_triggered)
        self.tree.actionDelete.triggered.connect(self.on_treeActionDelete_triggered)
        self.tree.actionRename.triggered.connect(self.on_treeActionRename_triggered)
        self.tree.actionNewdir.triggered.connect(self.on_treeActionNewdir_triggered)
        self.tree.actionClosedir.triggered.connect(self.on_treeActionClosedir_triggered)
        self.tree.actionDownload.triggered.connect(self.on_treeActionDownload_triggered)
        self.tree.actionDownloadAndRun.triggered.connect(self.on_treeActionDownloadAndRun_triggered)


        ''' TabWidget '''
        self.tabWidget.ui = self

        self.openedFiles = []


        ''' Terminal '''
        self.terminal.ui = self
        

        ''' Dialogs '''
        self.renameDialog = RenameDialog()
        self.renameDialog.btnOK.clicked.connect(self.on_renameDialog_btnOK_clicked)

        self.newdirDialog = NewDirDialog()
        self.newdirDialog.btnOK.clicked.connect(self.on_newdirDialog_btnOK_clicked)


        self.inDownloading = False
        self.isDownloadAndRun = False
        self.DownloadAndRunFile = None

        self.clipboard = QtWidgets.QApplication.clipboard()

        self.initSetting()

        self.createLexer()
        self.autoAPI = Qsci.QsciAPIs(self.lexer)

        self.ser = serial.Serial(baudrate=115200, timeout=0.001)

        self.serQueue = queue.Queue()
        self.cmdQueue = queue.Queue()

        self.serThread = SerThread(self)
        self.serThread.sig_msgToTrmReceived.connect(self.terminal.on_msgToTrmReceived)

        self.cmdThread = CmdThread(self)
        self.cmdThread.sig_boardFileDeleted.connect(self.on_boardFileDeleted)
        self.cmdThread.sig_boardFileRenamed.connect(self.on_boardFileRenamed)
        self.cmdThread.sig_boardFileLoaded.connect(self.on_boardFileLoaded)
        self.cmdThread.sig_boardFileListed.connect(self.on_boardFileListed)
        self.cmdThread.sig_messageReceived.connect(self.on_messageReceived)

    def initSetting(self):
        if not os.path.exists('setting.ini'):
            open('setting.ini', 'w')
        
        self.conf = configparser.ConfigParser()
        self.conf.read('setting.ini')

        if not self.conf.has_section('serial'):
            self.conf.add_section('serial')
            self.conf.set('serial', 'port', 'COM0')
            self.conf.set('serial', 'baudrate', '115200')

        self.cmbSer.setCurrentIndex(self.cmbSer.findText(self.conf.get('serial', 'port')))

    def createLexer(self):
        self.lexer = Qsci.QsciLexerPython()

        self.lexer.setDefaultPaper(QtGui.QColor(38,45,52))
        self.lexer.setDefaultColor(QtGui.QColor(255,255,255))

        self.lexer.setFont(QtGui.QFont(self.tr('Consolas'), 13, 1))

        self.lexer.setColor(Qt.darkGreen, Qsci.QsciLexerPython.Comment)
        self.lexer.setColor(QtGui.QColor(255,128,0), Qsci.QsciLexerPython.TripleDoubleQuotedString)

        self.lexer.setColor(QtGui.QColor(165,42,42), Qsci.QsciLexerPython.ClassName)
        self.lexer.setColor(QtGui.QColor(0,138,140), Qsci.QsciLexerPython.FunctionMethodName)

        self.lexer.setColor(Qt.green, Qsci.QsciLexerPython.Keyword)
        self.lexer.setColor(QtGui.QColor(255,0,255), Qsci.QsciLexerPython.Number)
        self.lexer.setColor(Qt.darkBlue, Qsci.QsciLexerPython.Decorator)
        self.lexer.setColor(QtGui.QColor(165,152,36), Qsci.QsciLexerPython.DoubleQuotedString)
        self.lexer.setColor(QtGui.QColor(165,152,36), Qsci.QsciLexerPython.SingleQuotedString)

    @pyqtSlot()
    def on_actionNew_triggered(self):
        self.tabWidget.newTab('untitled', '', self.lexer)

    @pyqtSlot()
    def on_actionSave_triggered(self):
        filePath = self.tabWidget.tabToolTip(self.tabWidget.currentIndex())

        if filePath != "untitled":
            open(filePath, 'w', encoding='utf-8').write(self.tabWidget.currentWidget().text())

            if self.tabWidget.tabText(self.tabWidget.currentIndex()).startswith('*'):
                self.tabWidget.setTabText(self.tabWidget.currentIndex(),
                                          self.tabWidget.tabText(self.tabWidget.currentIndex())[1:])
        else:
            filePath, _ = QtWidgets.QFileDialog.getSaveFileName(self, caption='Save File', directory=self.Workspace)
            if filePath:
                open(filePath, 'w', encoding='utf-8').write(self.tabWidget.currentWidget().text())

                self.openedFiles.remove(self.tabWidget.tabToolTip(self.tabWidget.currentIndex()))
                self.openedFiles.append(filePath)

                self.tabWidget.setTabText(self.tabWidget.currentIndex(), os.path.split(filePath)[-1])
                self.tabWidget.setTabToolTip(self.tabWidget.currentIndex(), filePath)

                self.refreshPCTree()

    @pyqtSlot()
    def on_actionUndo_triggered(self):
        if self.tabWidget.currentWidget():
            self.tabWidget.currentWidget().undo()

    @pyqtSlot()
    def on_actionRedo_triggered(self):
        if self.tabWidget.currentWidget():
            self.tabWidget.currentWidget().redo()

    @pyqtSlot()
    def on_actionConnect_triggered(self):
        self.connectBoard(self.cmbSer.currentText().split()[0])

        if self.ser.is_open:
            self.cmbSer.setEnabled(False)

    @pyqtSlot()
    def on_actionDisconnect_triggered(self):        
        self.serQueue.put('UI:::\x03')

        self.serQueue.put('close')
        self.cmdQueue.put('close')
        time.sleep(0.1)
        while not self.cmdQueue.empty(): self.cmdQueue.get()
        while not self.serQueue.empty(): self.serQueue.get()
        self.serThread.exit()
        self.cmdThread.exit()

        self.terminal.clear()
        self.terminal.setReadOnly(True)
        self.terminal.setEventFilterEnable(False)

        row = self.treeFlash.rowCount()
        self.treeFlash.removeRows(0, row)

        self.actionConnect.setVisible(True)
        self.actionDisconnect.setVisible(False)

        self.terminal.recvdata = ''
        time.sleep(0.1)

        self.ser.close()
        self.cmbSer.setEnabled(True)
    
    @pyqtSlot()
    def on_actionRefresh_triggered(self):
        if not self.ser.is_open:
            self.terminal.append('serial not opened')
            return

        self.cmdQueue.put('listFile')

    @pyqtSlot()
    def on_actionDownload_triggered(self):
        if not self.ser.is_open:
            self.terminal.append('serial not opened')
            return False

        if self.inDownloading:
            self.terminal.append('already in downloading.')
            return False

        if self.tabWidget.currentIndex() < 0:
            self.terminal.append('no file selected')
            return False
        
        filePath = self.tabWidget.tabToolTip(self.tabWidget.currentIndex())
        if filePath=='untitled':
            self.terminal.append("cannot download file 'untitled'")
            return False

        self.inDownloading = True

        self.serQueue.put('UI:::\x03')
        time.sleep(0.05)

        if filePath.startswith(self.Workspace):
            boardFilePath = filePath[len(self.Workspace):]
        else:
            boardFilePath = os.path.join(self.dirFlash, os.path.split(filePath)[-1]).replace('\\', '/')

        self.cmdQueue.put('downFile:::%s:::%s' %(filePath, boardFilePath))

        return boardFilePath

    @pyqtSlot()
    def on_actionDownloadAndRun_triggered(self):
        self.DownloadAndRunFile = self.on_actionDownload_triggered()
        if self.DownloadAndRunFile:
            self.isDownloadAndRun = True

    @pyqtSlot()
    def on_actionStopExcute_triggered(self):
        if not self.ser.is_open:
            self.terminal.append('serial not opened')
            return

        self.terminal.keyPressMsg='else'
        self.serQueue.put('UI:::\x03')
        self.inDownloading = False

    @pyqtSlot()
    def on_actionClearTerminal_triggered(self):
        self.terminal.clear()

    @pyqtSlot(QtCore.QModelIndex)
    def on_tree_doubleClicked(self, index):
        if self.tree.pressedFile.startswith('/flash/'):
            if self.tree.pressedFilePath.endswith('.py') or self.tree.pressedFilePath.endswith('.ini'):
                self.cmdQueue.put('loadFile:::%s' %self.tree.pressedFilePath)

        elif self.tree.pressedFile.count('/') > 0:
            if os.path.isfile(self.tree.pressedFilePath):
                if self.tree.pressedFilePath not in self.openedFiles:
                    data = open(self.tree.pressedFilePath, 'r', encoding='utf-8').read()

                    self.tabWidget.newTab(self.tree.pressedFilePath, data, self.lexer)
                else:
                    for i in range(len(self.openedFiles)):
                        if self.tabWidget.tabToolTip(i) == self.tree.pressedFilePath:
                            self.tabWidget.setCurrentIndex(i)
                            break

    def on_treeActionRun_triggered(self):
        if self.tree.pressedFile.startswith('/flash/') and (self.tree.pressedFile.endswith('.py') or 
                                                            self.tree.pressedFile.endswith('.mpy')):
            self.execFile(self.tree.pressedFilePath)

    def on_treeActionDelete_triggered(self):
        res = QtWidgets.QMessageBox.question(self, 'confirm delete?', self.tree.pressedFile, QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
        if res == QtWidgets.QMessageBox.Cancel:
            return

        if self.tree.pressedFile.startswith('/flash/'):
            if not self.ser.is_open:
                self.terminal.append('serial not opened')
                return

            self.cmdQueue.put('deleteFile:::%s' %self.tree.pressedFilePath)

        elif self.tree.pressedFile.count('/') > 0:
            if os.path.isfile(self.tree.pressedFilePath):
                os.remove(self.tree.pressedFilePath)

                self.closeTabPage(self.tree.pressedFilePath)

            elif os.path.isdir(self.tree.pressedFilePath):
                if len(os.listdir(self.tree.pressedFilePath)) == 0:
                    os.rmdir(self.tree.pressedFilePath)
                else:
                    self.terminal.append('dir not empty, cannot delete')

            self.refreshPCTree()

    def on_treeActionRename_triggered(self):
        self.renameDialog.exec()

    def on_renameDialog_btnOK_clicked(self):
        newName = self.renameDialog.linName.text()

        if self.tree.pressedFile.startswith('/flash/'):
            newPath = os.path.split(self.tree.pressedFilePath)[0] + '/' + newName
            self.cmdQueue.put('renameFile:::%s:::%s' %(self.tree.pressedFilePath, newPath))

        elif self.tree.pressedFile.count('/') > 0:
            os.rename(self.tree.pressedFilePath, os.path.join(os.path.split(self.tree.pressedFilePath)[0], newName))

            self.refreshPCTree()

    def on_treeActionNewdir_triggered(self):
        if self.tree.pressedFile == '/flash' and not self.ser.is_open:
            self.terminal.append('serial not opened')
            return

        self.newdirDialog.exec()

    def on_newdirDialog_btnOK_clicked(self):
        dirName = self.newdirDialog.linName.text()

        if self.tree.pressedFile == '/flash':
            self.cmdQueue.put('createDir:::%s' %os.path.join(self.dirFlash, dirName).replace('\\', '/'))

        elif self.tree.pressedFile.count('/') > 0:
            os.mkdir(os.path.join(self.tree.pressedFilePath, dirName))

            self.refreshPCTree()

    def on_treeActionClosedir_triggered(self):
        for i in range(self.tree.model().rowCount()):
            item = self.tree.model().item(i)
            if item.toolTip() == self.tree.pressedFilePath:
                self.tree.model().removeRow(item.row())
                break

    def on_treeActionDownload_triggered(self):
        if not self.ser.is_open:
            self.terminal.append('serial not opened')
            return False

        if self.inDownloading:
            self.terminal.append('already in downloading.')
            return False

        self.inDownloading = True

        self.serQueue.put('UI:::\x03')
        time.sleep(0.05)

        boardFilePath = self.tree.pressedFilePath[len(self.Workspace):]
        self.cmdQueue.put('downFile:::%s:::%s' %(self.tree.pressedFilePath, boardFilePath))

        return boardFilePath

    def on_treeActionDownloadAndRun_triggered(self):
        self.DownloadAndRunFile = self.on_treeActionDownload_triggered()
        if self.DownloadAndRunFile:
            self.isDownloadAndRun = True

    def on_boardFileDeleted(self, filePath):
        filePath = self.Workspace + filePath   # 将板上路径转换为PC上路径，如/boot.py变成<Workspace>/boot.py
        
        self.closeTabPage(filePath)
        
        self.cmdQueue.put("listFile")

    def on_boardFileRenamed(self, oldName, newName):
        self.cmdQueue.put("listFile")

    def on_boardFileLoaded(self, filePath, fileData):
        if filePath not in self.openedFiles:
            self.tabWidget.newTab(filePath, fileData, self.lexer)
        else:
            for i in range(len(self.openedFiles)):
                if self.tabWidget.tabToolTip(i) == filePath:
                    self.tabWidget.setCurrentIndex(i)
                    break

    def on_boardFileListed(self, data):
        if type(data) is not dict:
            self.terminal.append('refresh tree error.')
            self.inDownloading = False
            return

        row = self.treeFlash.rowCount()
        self.treeFlash.removeRows(0, row)
        
        self.createTree(self.treeFlash, self.listBoardDir(data[self.dirFlash]))
        self.tree.expand(self.treeFlash.index())

        if self.isDownloadAndRun:
            self.isDownloadAndRun = False
            
            self.execFile(self.DownloadAndRunFile)

        self.inDownloading = False

    def listBoardDir(self, items):
        files, dirs = [], []
        for item in items:
            if type(item) == str:
                files.append(item)
            elif type(item) == dict:
                dirs.append({list(item.keys())[0] : self.listBoardDir(list(item.values())[0])})

        return sorted(dirs, key=lambda dict: dict.keys()) + sorted(files)

    def on_messageReceived(self, msg):
        if msg in ['import os timeout', 'getcwd timeout']:
            self.terminal.append(msg)
            self.ser.close()

        elif msg == 'downFile ok':
            self.terminal.append(msg)
            self.cmdQueue.put("listFile")

        elif msg == 'downFile Fail':
            self.terminal.append(msg)
            self.inDownloading = False

        elif msg in ['deleteFile ok', 'renameFile ok', 'createDir ok']:
            self.cmdQueue.put("listFile")

        elif msg == '.':
            self.terminal.cursor.insertText(msg)
        
        else:
            self.terminal.append(msg)

    def addTreeRoot(self, path):
        if not os.path.exists(path):    # 可能文件夹已经被删除了
            return

        for i in range(self.tree.model().rowCount()):
            if self.tree.model().item(i).toolTip() == path:
                break
        else:
            treeRoot = QtGui.QStandardItem(QtGui.QIcon('images/treeMenuClosed.png'), os.path.split(path)[-1])
            treeRoot.setToolTip(path)
            self.tree.model().appendRow(treeRoot)

            self.createTree(treeRoot, self.listdir(path))

    def refreshPCTree(self):
        for i in range(self.tree.model().rowCount()):
            item = self.tree.model().item(i)
            if item.text() != '/flash':
                item.removeRows(0, item.rowCount())
                self.createTree(item, self.listdir(item.toolTip()))

    def listdir(self, path):
        files, dirs = [], []
        for item in os.listdir(path):
            itemPath = os.path.join(path, item).replace('\\', '/')
            if os.path.isfile(itemPath):
                files.append(item)
            elif os.path.isdir(itemPath):
                dirs.append({item: self.listdir(itemPath)})

        return dirs + files

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

    def connectBoard(self, port):
        try:
            self.ser.port = port
            self.ser.open()
        except Exception as e:
            self.terminal.append('serial has opened')
            return

        self.terminal.clear()
        self.ser.write(b'\x03')

        recvstr = ''
        startTime = time.time()
        while True:
            if self.ser.inWaiting() > 0:
                recvstr += self.ser.read(self.ser.inWaiting()).decode(encoding='utf-8')
                if not recvstr.find('>>> ') < 0:
                    self.terminal.append('>>> ')
                    break
            time.sleep(0.1)
            if time.time() - startTime > 3:
                self.terminal.append('connect board timeout.')
                self.ser.close()
                return

        self.cmdThread.start()
        self.serThread.start()
        time.sleep(0.01)

        self.cmdQueue.put('importOS')
        time.sleep(0.05)

        self.cmdQueue.put('getcwd')
        time.sleep(0.01)

        self.cmdQueue.put("listFile")

        self.terminal.setReadOnly(False)
        self.terminal.setEventFilterEnable(True)

        self.actionConnect.setVisible(False)
        self.actionDisconnect.setVisible(True)

    def execFile(self, filePath):
        if not self.ser.is_open:
            self.terminal.append('serial not opened')
            return

        if not filePath.endswith('.py') or filePath.endswith('.mpy'):
            self.terminal.append('only can exec py file')
            return

        self.cmdQueue.put('execFile:::%s' %filePath)

    def closeTabPage(self, filePath):
        if filePath in self.openedFiles:
            for i in range(len(self.openedFiles)):
                if self.tabWidget.tabToolTip(i) == filePath:
                    self.tabWidget.removeTab(i)
                    self.openedFiles.remove(filePath)
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
