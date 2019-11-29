import os
import re
import sys

from PyQt5 import QtCore, QtGui, QtWidgets, Qsci
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal


class TreeView(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        super(TreeView, self).__init__(parent)

        self.createContextMenu()
        self.customContextMenuRequested.connect(self.on_ContextMenuRequested)

        self.pressedFile = ''
        self.pressedFilePath = ''
        self.pressed.connect(self.on_item_pressed)

    def createContextMenu(self):
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.popupMenu = QtWidgets.QMenu(self)
        self.popupMenu.setStyleSheet('''QMenu { background-color:rgb(67,67,67); color:white; }
                                        QMenu::item { padding:4px 16px; }
                                        QMenu::item::selected { background-color: rgb(127,127,127); }
                                     ''')
        
        self.actionRun    = QtWidgets.QAction('Run', self)
        self.actionDelete = QtWidgets.QAction('Delete', self)
        self.actionRename = QtWidgets.QAction('Rename', self)
        self.actionNewdir = QtWidgets.QAction('New Folder', self)
        self.actionClosedir = QtWidgets.QAction('Close Folder', self)
        self.actionDownload = QtWidgets.QAction('Download', self)
        self.actionDownloadAndRun = QtWidgets.QAction('DownloadAndRun', self)
        
        self.popupMenu.addAction(self.actionRun)
        self.popupMenu.addAction(self.actionDelete)
        self.popupMenu.addAction(self.actionRename)
        self.popupMenu.addAction(self.actionNewdir)
        self.popupMenu.addAction(self.actionClosedir)
        self.popupMenu.addAction(self.actionDownload)
        self.popupMenu.addAction(self.actionDownloadAndRun)

    def on_ContextMenuRequested(self, point):
        self.popupMenu.clear()

        if self.pressedFile == '/flash':
            self.popupMenu.addAction(self.actionNewdir)
        elif self.pressedFile.startswith('/flash/'):
            if self.pressedFile.endswith('.py'):
                self.popupMenu.addAction(self.actionRun)
            self.popupMenu.addAction(self.actionDelete)
            self.popupMenu.addAction(self.actionRename)
        elif self.pressedFile == 'Workspace':
            self.popupMenu.addAction(self.actionNewdir)
        elif self.pressedFile.startswith('Workspace/'):
            if self.pressedFile.endswith('.py') or self.pressedFile.endswith('.mpy'):
                self.popupMenu.addAction(self.actionDownload)
                self.popupMenu.addAction(self.actionDownloadAndRun)
            self.popupMenu.addAction(self.actionDelete)
            self.popupMenu.addAction(self.actionRename)
        elif self.pressedFile.count('/') == 0:
            self.popupMenu.addAction(self.actionNewdir)
            self.popupMenu.addAction(self.actionClosedir)
        else:
            self.popupMenu.addAction(self.actionDelete)
            self.popupMenu.addAction(self.actionRename)

        self.popupMenu.exec_(self.mapToGlobal(point))

    def on_item_pressed(self, index):
        self.pressedFile = ''
        while index.data():
            self.pressedFile = '/' + index.data() + self.pressedFile
            indexPre = index
            index = index.parent()
        self.pressedFile = self.pressedFile[1:]

        if self.pressedFile == '/flash':
            self.pressedFilePath = self.ui.dirFlash
        elif self.pressedFile.startswith('/flash/'):
            self.pressedFilePath = os.path.join(self.ui.dirFlash, self.pressedFile[len('/flash/'):]).replace('\\', '/')
        elif self.pressedFile.count('/') > 0:
            self.pressedFilePath = self.model().itemFromIndex(indexPre).toolTip() + self.pressedFile[self.pressedFile.index('/'):]
        else:
            self.pressedFilePath = self.model().itemFromIndex(indexPre).toolTip()

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("text/uri-list"):
            self.dragFrom = "External"
            event.acceptProposedAction()

        elif event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            self.dragFrom = "Internal"

            index = self.indexAt(self.mapFrom(self, event.pos()))
            if not index.data():
                return

            self.on_item_pressed(index)

            if self.pressedFile.startswith('/flash'):
                self.ui.terminal.append('can only drag PC file to board')
                return

            if not os.path.isfile(self.pressedFilePath):
                self.ui.terminal.append('can only drag file, not folder')
                return

            self.dragedFilePath = self.pressedFilePath

            event.acceptProposedAction()

        else:
            event.ignore()

    def dragMoveEvent(self, event): # 必须有这个函数拖拽才能工作
        pass

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            if self.dragFrom == "External":
                for url in event.mimeData().urls():
                    filePath = url.toLocalFile().replace('\\', '/')

                    if os.path.isdir(filePath):
                        self.ui.addTreeRoot(filePath)

                    elif os.path.isfile(filePath):
                        self.dropFile(event, filePath)
                
            elif self.dragFrom=="Internal":
                self.dropFile(event, self.dragedFilePath)

        else:
            event.ignore()

    def dropFile(self, event, dragedFilePath):
        if not self.ui.ser.isOpen():
            self.ui.terminal.append('serial not opened')
            return

        index = self.indexAt(self.mapFrom(self, event.pos()))
        if not index.data():
            print('not index')
            return

        self.on_item_pressed(index)

        if not self.pressedFile.startswith('/flash'):
            self.ui.terminal.append('can only drag PC file to board')
            return

        dropDir = os.path.split(self.pressedFilePath)[-1]
        if dropDir.count('.') > 0:
            self.ui.terminal.append('can only drop to folder, no file')
            return

        self.ui.cmdQueue.put('downFile:::%s:::%s' %(dragedFilePath, self.pressedFilePath + '/' + os.path.split(dragedFilePath)[-1]))


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super(TabWidget, self).__init__(parent)

        self.tabCloseRequested.connect(self.closeTab)

        self.line = 0
        self.index = 0

    def newTab(self, filePath, text, lexer):
        editor = Qsci.QsciScintilla()
        editor.setEolMode(Qsci.QsciScintilla.EolUnix)
        editor.setLexer(lexer)
        editor.setUtf8(True)
        editor.setText(text)

        self.addTab(editor, filePath)

        editor.setContextMenuPolicy(Qt.CustomContextMenu)   # no popup menu

        editor.SendScintilla(Qsci.QsciScintilla.SCI_SETINDENTATIONGUIDES, Qsci.QsciScintilla.SC_IV_LOOKFORWARD) # Display indent guide
        editor.setIndentationsUseTabs(False)
        editor.setAutoIndent(True)
        editor.setTabWidth(4)

        editor.setAutoCompletionThreshold(2)
        editor.setAutoCompletionSource(Qsci.QsciScintilla.AcsAll)

        editor.setBraceMatching(editor.StrictBraceMatch)
        editor.setMatchedBraceBackgroundColor(QtGui.QColor(30,120,184))
        
        editor.setMarginsBackgroundColor(QtGui.QColor(39,43,48))
        editor.setMarginsForegroundColor(QtGui.QColor(255,255,255))
        
        editor.setMarginType(0, Qsci.QsciScintilla.NumberMargin)
        editor.setMarginLineNumbers(0, True)
        editor.setMarginWidth(0, 35)

        editor.setMarginType(1, Qsci.QsciScintilla.SymbolMargin)
        editor.setMarginLineNumbers(1, False)
        editor.setMarginWidth(1, 5)
        editor.setMarginSensitivity(1, False)
        editor.setMarginMarkerMask(1, 0x1FFFFFF)
        editor.markerDefine(Qsci.QsciScintilla.Background, 1)

        editor.setFolding(Qsci.QsciScintilla.PlainFoldStyle)
        editor.setFoldMarginColors(QtGui.QColor(39,43,48), QtGui.QColor(39,43,48))

        editor.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        editor.setCaretForegroundColor(QtGui.QColor(255,255,255))   # cursor color

        editor.setStyleSheet('''QWidget {font-size:20px; border: 0px solid white; border-radius:1px;}''')
        
        self.setCurrentWidget(editor)
        
        if filePath != 'untitled':
            self.ui.openedFiles.append(filePath)

        editor.textChanged.connect(self.on_textChanged)
        editor.cursorPositionChanged.connect(self.on_cursorPositionChanged)

    def closeTab(self, tabId):
        if tabId < 0:
            return

        tabToolTip = self.tabToolTip(tabId)

        self.removeTab(tabId)

        if tabToolTip in self.ui.openedFiles:
            self.ui.openedFiles.remove(tabToolTip)

    def on_textChanged(self):
        tabName = self.tabText(self.currentIndex())

        if tabName == 'untitled' or tabName.startswith('*'):
            return

        self.setTabText(self.currentIndex(), '*' + tabName)

    def on_cursorPositionChanged(self, line, index):
        self.line  = line
        self.index = index

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("text/uri-list"):                                 # External drag
            event.acceptProposedAction()
        elif event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):    # Internal drag
            event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            for url in event.mimeData().urls():
                filePath = url.toLocalFile()
            
            if os.path.isfile(filePath) and filePath not in self.ui.openedFiles:
                data = open(filePath, 'r', encoding='utf-8').read()

                self.newTab(filePath, data, self.ui.lexer)


class Terminal(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super(Terminal, self).__init__(parent)

        self.setContextMenuPolicy(Qt.CustomContextMenu)   # no popup menu

        self.cursor = self.textCursor()

        self.eventFilterEnable = False
        self.installEventFilter(self)
        
        self.keyPressMsg = ''
        self.recvbuff = ''
    
    def setEventFilterEnable(self, enable):
        self.eventFilterEnable = enable

    def eventFilter(self, watch, event):
        if not self.eventFilterEnable:
            return QtWidgets.QMainWindow.eventFilter(self, watch, event)

        if event.type() == QtCore.QEvent.KeyPress:                
            if event.key() == Qt.Key_Backspace:
                self.keyPressMsg = '\x08'
                self.ui.serQueue.put('UI:::%s' %self.keyPressMsg)

            elif event.key() == Qt.Key_Tab:
                self.keyPressMsg = '\x09'
                self.ui.serQueue.put('UI:::%s' %self.keyPressMsg)

            elif event.key() == Qt.Key_Delete:
                self.keyPressMsg = '\x1b\x5b\x33\x7e'
                self.ui.serQueue.put('UI:::%s' %self.keyPressMsg)

            elif event.key() == Qt.Key_Up:
                self.keyPressMsg = '\x1b\x5b\x41'
                self.ui.serQueue.put('UI:::%s' %self.keyPressMsg)

            elif event.key() == Qt.Key_Down:
                self.keyPressMsg = '\x1b\x5b\x42'
                self.ui.serQueue.put('UI:::%s' %self.keyPressMsg)

            elif event.key() == Qt.Key_Right:
                self.keyPressMsg = '\x1b\x5b\x43'
                self.ui.serQueue.put('UI:::%s' %self.keyPressMsg)

            elif event.key() == Qt.Key_Left:
                self.keyPressMsg = '\x1b\x5b\x44'
                self.ui.serQueue.put('UI:::%s' %self.keyPressMsg)
                
            else:
                self.keyPressMsg = 'else'
                if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
                    self.cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
                    self.moveCursor(QtGui.QTextCursor.End)

                self.ui.serQueue.put('UI:::%s' %event.text())

            return True

        elif event.type() == QtCore.QEvent.InputMethod:
            self.ui.serQueue.put('UI:::%s' %QtGui.QInputMethodEvent(event).commitString())

            return True

        else:
            return QtWidgets.QMainWindow.eventFilter(self, watch, event)            

    def on_msgToTrmReceived(self, data):
        if self.keyPressMsg == '\x08':  # Backspace
            self.recvbuff += data

            if self.cursor.atEnd():
                if self.recvbuff.count('\x08\x1b\x5b\x4b') > 0:
                    cursor = self.textCursor()
                    cursor.deletePreviousChar()
                    self.recvbuff = ''
            
            else:
                if self.recvbuff.count('\x08\x1b\x5b\x4b') > 0 and self.recvbuff[-1] == '\x08':
                    cursor = self.textCursor()
                    cursor.deletePreviousChar()
                    self.recvbuff = ''

                elif re.search('\x08\x1b\[K[\s\S]+?\x1b\[\d+D', self.recvbuff):
                    cursor = self.textCursor()
                    cursor.deletePreviousChar()
                    self.recvbuff = ''
        
        elif self.keyPressMsg == '\x09' and not self.cursor.atEnd():    # Tab
            pass

        elif self.keyPressMsg == '\x1b\x5b\x33\x7e' and not self.cursor.atEnd(): # Delete
            self.recvbuff += data
            lastLine = self.toPlainText().split('\n')[-1]
            lastLineCursorPos = self.cursor.columnNumber()

            if self.recvbuff == '\x1b\x5b\x4b' and len(lastLine) - lastLineCursorPos == 1:  #光标前只有一个字符
                self.cursor.deleteChar()
                self.recvbuff = ''

            elif self.recvbuff.count('\x1b\x5b\x4b') and self.recvbuff[-1] == '\x08':
                self.cursor.deleteChar()
                self.recvbuff = ''

            elif re.search('\x1b\[K[\s\S]+?\x1b\[\d+D', self.recvbuff):
                self.cursor.deleteChar()
                self.recvbuff = ''

            elif self.recvbuff == '\x08':  # 可能会有多余的'\x08'
                self.recvbuff = ''

        elif self.keyPressMsg == '\x1b\x5b\x44':  # Key_Left
            if data == '\x08':
                self.moveCursor(QtGui.QTextCursor.Left,QtGui.QTextCursor.MoveAnchor)
                self.cursor = self.textCursor()

        elif self.keyPressMsg == '\x1b\x5b\x43':  # Key_Right
            self.moveCursor(QtGui.QTextCursor.Right, QtGui.QTextCursor.MoveAnchor)
            self.cursor = self.textCursor()

        elif self.keyPressMsg=='\x1b\x5b\x41':  # Key_Up
            if data == '\x08':
                self.removeLastLine()

            elif data == '\x1b' or self.recvbuff.count('\x1b'):
                self.recvbuff += data

                if self.recvbuff.count('[K') or self.recvbuff.count('D'):
                    self.recvbuff = ''

                    self.removeLastLine()

            else:
                self.cursor.insertText(data)

        elif self.keyPressMsg=='\x1b\x5b\x42':  # Key_Down
            if data == '\x08':
                self.removeLastLine()

            elif data == '\x1b' or self.recvbuff.count('\x1b'):
                self.recvbuff += data

                if self.recvbuff.count('[K') or self.recvbuff.count('D'):
                    self.recvbuff = ''

                    self.removeLastLine()
            else:
                self.cursor.insertText(data)

        else:
            if self.cursor.atEnd():
                if data != '\n':
                    self.insertPlainText(data)
                self.ensureCursorVisible()

            else:                   # 在内容中间输入
                self.recvbuff+=data
                
                if len(self.recvbuff) > 1 and self.recvbuff[-1] == '\x08':
                    self.cursor.insertText(self.recvbuff[0])
                    self.recvbuff = ''

                elif self.recvbuff == '\x08':   # 除上面那种情况，其他'\x08'丢掉
                    self.recvbuff = ''

                elif re.search('[\s\S]+?\x1b\[\d+D', self.recvbuff):
                    self.cursor.insertText(self.recvbuff[0])
                    self.recvbuff = ''

    def removeLastLine(self):
        plainMsg = self.toPlainText()
        if plainMsg.count('\n') == 0:
            plainMsg = '>>> '
        else:
            plainMsg = plainMsg[:plainMsg.rindex('\n')] + '\n>>> '
        self.setPlainText(plainMsg)

        self.cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
        self.moveCursor(QtGui.QTextCursor.End)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            cursor = self.cursorForPosition(event.pos())
            self.selectStartPos = cursor.position()

        elif event.button() == Qt.RightButton:
            if self.ui.ser.isOpen():
                self.keyPressMsg = ''
                for char in QtWidgets.QApplication.clipboard().text():
                    if char == '\n':
                        char = '\r\n'
                    self.ui.serQueue.put('UI:::%s' %char)

    def mouseMoveEvent(self, event):
        if event.button() == Qt.NoButton:
            cursor = self.cursorForPosition(event.pos())
            selectEndPos = cursor.position()

            cursor.setPosition(self.selectStartPos)
            cursor.setPosition(selectEndPos, QtGui.QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)

            cursor.select(QtGui.QTextCursor.WordUnderCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:         # Ctrl+C 是upy的终止信号，因此用鼠标释放触发赋值
            if self.textCursor() != self.cursor:    # 有内容被选中
                self.copy()
                self.setTextCursor(self.cursor)


class RenameDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(RenameDialog, self).__init__(parent)

        self.setWindowFlags(Qt.WindowCloseButtonHint)
        self.setWindowTitle('Rename as')
        self.setWindowIcon(QtGui.QIcon('images/logo.png'))
        self.setStyleSheet('''QDialog { background-color: rgb(236, 236, 236); color: black; }
                              QPushButton { background-color: rgb(253,97,72); color: white; }
                           ''')

        self.lblName = QtWidgets.QLabel('new name:')
        self.linName = QtWidgets.QLineEdit()

        self.btnOK = QtWidgets.QPushButton('Ok')
        self.btnOK.clicked.connect(self.on_btnOK_clicked)

        self.btnCancel = QtWidgets.QPushButton('Cancel')
        self.btnCancel.clicked.connect(self.on_btnCancel_clicked)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.lblName,   0, 0)
        layout.addWidget(self.linName,   0, 1)
        layout.addWidget(self.btnOK,     1, 0)
        layout.addWidget(self.btnCancel, 1, 1)
        self.setLayout(layout)

    def on_btnOK_clicked(self):
        self.close()

    def on_btnCancel_clicked(self):
        self.close()


class NewDirDialog(RenameDialog):
    def __init__(self, parent=None):
        super(NewDirDialog, self).__init__(parent)

        self.setWindowTitle('New Dir')

        self.lblName.setText('dir name:')
