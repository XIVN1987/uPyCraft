import os
import re
import sys
import posixpath as xpath

from PyQt5 import QtCore, QtGui, QtWidgets, Qsci


class TreeView(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        super(TreeView, self).__init__(parent)

        self.createContextMenu()
        self.customContextMenuRequested.connect(self.on_ContextMenuRequested)

        self.pressedIndex = None
        self.pressedFilePath = ''
        self.pressedFileType = ''
        self.pressed.connect(self.on_item_pressed)

    def createContextMenu(self):
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.popupMenu = QtWidgets.QMenu(self)
        self.popupMenu.setStyleSheet('''QMenu { background-color:rgb(67,67,67); color:white; }
                                        QMenu::item { padding:4px 16px; }
                                        QMenu::item::selected { background-color: rgb(127,127,127); }
                                     ''')
        
        self.actionRun    = QtWidgets.QAction('Run',        self)
        self.actionDelete = QtWidgets.QAction('Delete',     self)
        self.actionRename = QtWidgets.QAction('Rename',     self)
        self.actionNewfil = QtWidgets.QAction('New File',   self)
        self.actionNewdir = QtWidgets.QAction('New Folder', self)
        self.actionSavePC = QtWidgets.QAction('Save to PC', self)
    
    def on_ContextMenuRequested(self, point):
        self.popupMenu.clear()

        if self.indexAt(point).row() == -1:
            return

        if self.pressedFilePath == self.ui.dirFlash:
            self.popupMenu.addAction(self.actionNewfil)
            self.popupMenu.addAction(self.actionNewdir)
        elif self.pressedFileType == 'dir':
            self.popupMenu.addAction(self.actionNewfil)
            self.popupMenu.addAction(self.actionNewdir)
            self.popupMenu.addAction(self.actionRename)
            self.popupMenu.addAction(self.actionDelete)
        else:
            if self.pressedFilePath.endswith('.py'):
                self.popupMenu.addAction(self.actionRun)
            self.popupMenu.addAction(self.actionRename)
            self.popupMenu.addAction(self.actionDelete)

        self.popupMenu.addAction(self.actionSavePC)

        self.popupMenu.exec_(self.mapToGlobal(point))

    def on_item_pressed(self, index):
        self.pressedIndex = index
        self.pressedFilePath, self.pressedFileType = self.getPathAndType(index)

    def getPathAndType(self, index):
        fileType = index.data(QtCore.Qt.WhatsThisRole)

        filePath = ''
        while index.data():
            filePath = index.data() + '/' + filePath
            index = index.parent()
        filePath = filePath[:-1]

        if self.ui.dirFlash == '/':
            filePath = filePath[len('/flash'):] or '/'  # '/flash' will become ''

        return filePath, fileType

    def isFileExist(self, path, type):  # type: 'dir', 'file'
        if self.ui.dirFlash == '/':
            path = path[len('/'):]
        elif self.ui.dirFlash == '/flash':
            path = path[len('/flash/'):]
        
        *nameM, nameL = path.split('/') # Middle names, Last name
        
        root = self.ui.treeFlash
        for name in nameM:
            for i in range(root.rowCount()):
                item = root.child(i)
                if item.data(QtCore.Qt.DisplayRole) == name and item.data(QtCore.Qt.WhatsThisRole) == 'dir':
                    root = item
                    break

            else:   # dir 'name' not found
                return False

        for i in range(root.rowCount()):
            item = root.child(i)
            if item.data(QtCore.Qt.DisplayRole) == nameL and item.data(QtCore.Qt.WhatsThisRole) == type:
                return True

        return False

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("text/uri-list"):
            self.dragFrom = "External"

            event.acceptProposedAction()

        elif event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            self.dragFrom = "Internal"

            event.acceptProposedAction()

    def dragMoveEvent(self, event): # for drag work
        index = self.indexAt(event.pos())
        if not index.data() or index.data(QtCore.Qt.WhatsThisRole) != 'dir':
            event.ignore()
        else:
            event.acceptProposedAction()

    def dropEvent(self, event):
        if not self.ui.ser.isOpen():
            self.ui.terminal.append('serial not opened')
            return

        index = self.indexAt(event.pos())
        if not index.data() or index.data(QtCore.Qt.WhatsThisRole) != 'dir':
            return

        dropDir, _ = self.getPathAndType(index)

        if self.dragFrom == "Internal":
            newPath = xpath.join(dropDir, os.path.basename(self.pressedFilePath))
            if self.isFileExist(newPath, self.pressedFileType):
                self.ui.terminal.append(f'file {newPath} already exists\n\n>>> ')
                return

            self.ui.cmdQueue.put(f'renameFile:::{self.pressedFilePath}:::{newPath}:::{self.pressedFileType}')

        elif self.dragFrom == "External":
            for url in event.mimeData().urls():
                pcFile = url.toLocalFile()

                if os.path.isfile(pcFile):
                    filePath = xpath.join(dropDir, os.path.basename(pcFile))
                    if self.isFileExist(filePath, 'file'):
                        self.ui.terminal.append(f'file {filePath} already exists\n\n>>> ')
                        return

                    fileData = open(pcFile, 'rb').read().decode('latin-1')
                    self.ui.cmdQueue.put(f'downFile:::{filePath}:::{fileData}:::False')

                elif os.path.isdir(pcFile):
                    dirPath = xpath.join(dropDir, os.path.basename(pcFile))
                    if self.isFileExist(dirPath, 'dir'):
                        self.ui.terminal.append(f'directory {dirPath} already exists\n\n>>> ')
                        return

                    self.ui.cmdQueue.put(f'createDir:::{dirPath}:::False')

                    for root, dirs, files in os.walk(pcFile):
                        middle = root[len(os.path.dirname(pcFile)) + 1:].replace('\\', '/')
                        for dir in dirs:
                            dirPath = xpath.join(dropDir, middle, dir)
                            self.ui.cmdQueue.put(f'createDir:::{dirPath}:::False')

                        for file in files:
                            filePath = xpath.join(dropDir, middle, file)
                            fileData = open(os.path.join(root, file), 'rb').read().decode('latin-1')
                            self.ui.cmdQueue.put(f'downFile:::{filePath}:::{fileData}:::False')

            self.ui.cmdQueue.put(f'listFile:::{self.ui.dirFlash}')


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super(TabWidget, self).__init__(parent)

        self.createLexer()

        self.openedFiles = []

        self.tabCloseRequested.connect(self.closeTab)

    def newTab(self, filePath, text):
        editor = Qsci.QsciScintilla()
        editor.setEolMode(Qsci.QsciScintilla.EolUnix)
        editor.setLexer(self.lexer if filePath.endswith('.py') else None)
        editor.setUtf8(True)
        editor.setText(text)

        editor.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)   # no popup menu

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

        editor.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        editor.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        editor.setCaretForegroundColor(QtGui.QColor(255,255,255))   # cursor color

        editor.setStyleSheet('''QWidget {font-size:20px; border: 0px solid white; border-radius:1px;}''')
        
        editor.textChanged.connect(self.on_textChanged)

        self.setCurrentWidget(editor)
        
        self.addTab(editor, filePath)

        self.openedFiles.append(filePath)

    def closeTab(self, index):
        filePath = self.tabText(index)
        
        if filePath.endswith('*'):
            res = QtWidgets.QMessageBox.question(None, 'save before close?', f'The file {filePath[:-1]} has been changed, do you like to save it before close?',
                                                 QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No|QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
            if res == QtWidgets.QMessageBox.Cancel:
                return

            else:
                if res == QtWidgets.QMessageBox.Yes:
                    self.ui.on_actionDownload_triggered()

                filePath = filePath[:-1]

        self.removeTab(index)

        if filePath in self.openedFiles:
            self.openedFiles.remove(filePath)

    def createLexer(self):
        self.lexer = Qsci.QsciLexerPython()

        self.lexer.setDefaultPaper(QtGui.QColor(38,45,52))
        self.lexer.setDefaultColor(QtGui.QColor(255,255,255))

        self.lexer.setFont(QtGui.QFont(self.tr('Consolas'), 13, 1))

        self.lexer.setColor(QtCore.Qt.darkGreen, Qsci.QsciLexerPython.Comment)
        self.lexer.setColor(QtGui.QColor(255,128,0), Qsci.QsciLexerPython.TripleDoubleQuotedString)

        self.lexer.setColor(QtGui.QColor(165,42,42), Qsci.QsciLexerPython.ClassName)
        self.lexer.setColor(QtGui.QColor(0,138,140), Qsci.QsciLexerPython.FunctionMethodName)

        self.lexer.setColor(QtCore.Qt.green, Qsci.QsciLexerPython.Keyword)
        self.lexer.setColor(QtGui.QColor(255,0,255), Qsci.QsciLexerPython.Number)
        self.lexer.setColor(QtCore.Qt.darkBlue, Qsci.QsciLexerPython.Decorator)
        self.lexer.setColor(QtGui.QColor(165,152,36), Qsci.QsciLexerPython.DoubleQuotedString)
        self.lexer.setColor(QtGui.QColor(165,152,36), Qsci.QsciLexerPython.SingleQuotedString)

    def on_textChanged(self):
        tabName = self.tabText(self.currentIndex())

        if tabName.endswith('*'):
            return

        self.setTabText(self.currentIndex(), tabName + '*')


class Terminal(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super(Terminal, self).__init__(parent)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)   # no popup menu

        self.cursor = self.textCursor()

        self.eventFilterEnable = False
        self.installEventFilter(self)
        
        self.keyPressMsg = ''
        self.recvbuff = ''

    def eventFilter(self, watch, event):
        if not self.eventFilterEnable:
            return QtWidgets.QMainWindow.eventFilter(self, watch, event)

        if event.type() == QtCore.QEvent.KeyPress:
            self.keyPressMsg = ''

            if event.key() == QtCore.Qt.Key_Backspace:
                self.keyPressMsg = '\x08'
                
            elif event.key() == QtCore.Qt.Key_Tab:
                self.keyPressMsg = '\x09'

            elif event.key() == QtCore.Qt.Key_Delete:
                self.keyPressMsg = '\x1b\x5b\x33\x7e'

            elif event.key() == QtCore.Qt.Key_Up:
                self.keyPressMsg = '\x1b\x5b\x41'

            elif event.key() == QtCore.Qt.Key_Down:
                self.keyPressMsg = '\x1b\x5b\x42'

            elif event.key() == QtCore.Qt.Key_Right:
                self.keyPressMsg = '\x1b\x5b\x43'

            elif event.key() == QtCore.Qt.Key_Left:
                self.keyPressMsg = '\x1b\x5b\x44'
            
            if self.keyPressMsg:
                self.ui.serQueue.put(f'Key:::{self.keyPressMsg}')

            else:
                if event.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
                    self.cursorToEnd()

                self.ui.serQueue.put(f'Key:::{event.text()}')

            return True

        elif event.type() == QtCore.QEvent.InputMethod:
            self.ui.serQueue.put(f'Key:::{QtGui.QInputMethodEvent(event).commitString()}')

            return True

        else:
            return QtWidgets.QMainWindow.eventFilter(self, watch, event)            

    def on_keyRespAvailable(self, data):
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
                self.cursor.movePosition(QtGui.QTextCursor.Left, QtGui.QTextCursor.MoveAnchor)
                self.setTextCursor(self.cursor)

        elif self.keyPressMsg == '\x1b\x5b\x43':  # Key_Right
            self.cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.MoveAnchor)
            self.setTextCursor(self.cursor)

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

        self.cursorToEnd()

    def cursorToEnd(self):
        self.cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
        self.setTextCursor(self.cursor)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            cursor = self.cursorForPosition(event.pos())
            self.selectStartPos = cursor.position()

        elif event.button() == QtCore.Qt.RightButton:
            if self.ui.ser.isOpen():
                self.keyPressMsg = ''
                for char in QtWidgets.QApplication.clipboard().text():
                    if char == '\n':
                        char = '\r\n'
                    self.ui.serQueue.put(f'Key:::{char}')

    def mouseMoveEvent(self, event):
        if event.button() == QtCore.Qt.NoButton:
            cursor = self.cursorForPosition(event.pos())
            selectEndPos = cursor.position()

            cursor.setPosition(self.selectStartPos)
            cursor.setPosition(selectEndPos, QtGui.QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)

            cursor.select(QtGui.QTextCursor.WordUnderCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:         # Ctrl+C 是upy的终止信号，因此用鼠标释放触发赋值
            if self.textCursor() != self.cursor:    # 有内容被选中
                self.copy()
                self.setTextCursor(self.cursor)


class RenameDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(RenameDialog, self).__init__(parent)

        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
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


class NewFilDialog(RenameDialog):
    def __init__(self, parent=None):
        super(NewFilDialog, self).__init__(parent)

        self.setWindowTitle('New File')

        self.lblName.setText('file name:')


class NewDirDialog(RenameDialog):
    def __init__(self, parent=None):
        super(NewDirDialog, self).__init__(parent)

        self.setWindowTitle('New Dir')

        self.lblName.setText('dir name:')
