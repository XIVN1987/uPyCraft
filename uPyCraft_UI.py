# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Program\Ubuntu\uPyCraft\uPyCraft.ui'
#
# Created by: PyQt5 UI code generator 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_uPyCraft(object):
    def setupUi(self, uPyCraft):
        uPyCraft.setObjectName("uPyCraft")
        uPyCraft.resize(902, 600)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("images/logo.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        uPyCraft.setWindowIcon(icon)
        uPyCraft.setIconSize(QtCore.QSize(32, 32))
        self.centralwidget = QtWidgets.QWidget(uPyCraft)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setContentsMargins(1, 1, 1, 2)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.hSplitter = QtWidgets.QSplitter(self.centralwidget)
        self.hSplitter.setStyleSheet("background-color: rgb(236, 236, 236);\n"
"QSplitter::handle { \n"
"    background-color: rgb(236, 236, 236);\n"
"}")
        self.hSplitter.setOrientation(QtCore.Qt.Horizontal)
        self.hSplitter.setHandleWidth(1)
        self.hSplitter.setObjectName("hSplitter")
        self.tree = TreeView(self.hSplitter)
        self.tree.setAcceptDrops(True)
        self.tree.setStyleSheet("QTreeView {\n"
"    background-color: qlineargradient(y1: 0, y2: 1,stop: 0 #0D0B0B, stop: 1 #5D5C5C);\n"
"    border-width: 1px;\n"
"    border-color: #888888;\n"
"    border-style: solid;\n"
"    color: white;\n"
"}\n"
"\n"
"QTreeView::branch:closed:has-children {\n"
"    border-image: none;\n"
"    image: url(\'images/treeBranchOpen.png\');\n"
"}\n"
"\n"
"QTreeView::branch:open:has-children {\n"
"    border-image: none;\n"
"    image: url(\'images/treeBranchClose.png\');\n"
"}")
        self.tree.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tree.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.tree.setObjectName("tree")
        self.tree.header().setVisible(False)
        self.vSplitter = QtWidgets.QSplitter(self.hSplitter)
        self.vSplitter.setStyleSheet("QSplitter {\n"
"    background-color: qlineargradient(x1: 0, x2: 1,stop: 0 #646464, stop: 1 #171717);\n"
"}\n"
"QTabBar::tab {\n"
"    border-top-left-radius: 3px; \n"
"    border-top-right-radius: 5px;\n"
"    min-width: 120px;\n"
"    min-height: 25px; \n"
"    border: 0px solid rgb(255,0,0); \n"
"    border-bottom: none;  \n"
"    margin-top: 3; \n"
"    color: rgb(255,255,255);\n"
"}\n"
"QTabWidget::pane {\n"
"    border-width: 0px;\n"
"    border-color: rgb(161,161,161);    \n"
"    border-style: inset;\n"
"    background-color: rgb(64, 64, 64);\n"
"}\n"
"QTabBar::tab::selected {\n"
"    background-color: rgb(38,45,52);\n"
"    border-bottom: 2px solid rgb(254,152,77);\n"
"}\n"
"QTabBar::tab::!selected {\n"
"    background-color:rgb(64,64,64);\n"
"}\n"
"QTabBar::close-button {\n"
"    subcontrol-position: right;\n"
"    image: url(images/tabClose.png)  \n"
"}\n"
"QTabBar::close-button:hover {\n"
"    subcontrol-position: right;\n"
"    image: url(images/tabCloseHover.png)  \n"
"}\n"
"")
        self.vSplitter.setOrientation(QtCore.Qt.Vertical)
        self.vSplitter.setOpaqueResize(False)
        self.vSplitter.setHandleWidth(1)
        self.vSplitter.setObjectName("vSplitter")
        self.tabWidget = TabWidget(self.vSplitter)
        self.tabWidget.setAcceptDrops(True)
        self.tabWidget.setStyleSheet("QWidget {\n"
"    background-color: qlineargradient(x1: 0, x2: 1, stop: 0 #262D34, stop: 1 #222529);\n"
"    border-width: 0px;\n"
"    border-color: #666666;\n"
"    border-style: none;\n"
"    color: white;\n"
"}\n"
"QScrollBar:vertical {\n"
"    background-color: rgb(94,98,102);\n"
"    border: 0px;\n"
"    width:  15px;\n"
"    margin: 0px 0px 0px 0px;\n"
"}\n"
"QScrollBar::add-page:vertical {\n"
"    background-color: rgb(61,62,64);\n"
"    width:  15px;\n"
"    margin: 0px 0px 0px 0px;\n"
"}\n"
"QScrollBar::sub-page:vertical {\n"
"    background-color: rgb(61,62,64);\n"
"    width:  15px;\n"
"    margin: 0px 0px 0px 0px;\n"
"}")
        self.tabWidget.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.tabWidget.setElideMode(QtCore.Qt.ElideRight)
        self.tabWidget.setTabsClosable(True)
        self.tabWidget.setMovable(True)
        self.tabWidget.setObjectName("tabWidget")
        self.terminal = Terminal(self.vSplitter)
        self.terminal.setAcceptDrops(False)
        self.terminal.setStyleSheet("QTextEdit {\n"
"    background-color: qlineargradient(x1: 0, x2: 1, stop: 0 #262D34, stop: 1 #222529);\n"
"    border-style: none;\n"
"    color: white;\n"
"}\n"
"QScrollBar:vertical {\n"
"    background-color: rgb(94,98,102);\n"
"    border: 0px;\n"
"    width: 15px;\n"
"    margin: 0px 0px 0px 0px;\n"
"}\n"
"QScrollBar::add-page:vertical {\n"
"    background-color: rgb(61,62,64);\n"
"    width: 15px;\n"
"    margin: 0px 0px 0px 0px;\n"
"}\n"
"QScrollBar::sub-page:vertical {\n"
"    background-color: rgb(61,62,64);\n"
"    width: 15px;\n"
"    margin: 0px 0px 0px 0px;\n"
"}")
        self.terminal.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.terminal.setObjectName("terminal")
        self.horizontalLayout.addWidget(self.hSplitter)
        uPyCraft.setCentralWidget(self.centralwidget)
        self.toolBar = QtWidgets.QToolBar(uPyCraft)
        self.toolBar.setStyleSheet("QToolBar {\n"
"    background-color: qlineargradient( y1: 0,  y2: 1,stop: 0 #FF4E50, stop: 1 #FFBE2B);\n"
"    spacing: 8px;\n"
"}")
        self.toolBar.setObjectName("toolBar")
        uPyCraft.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.actionNew = QtWidgets.QAction(uPyCraft)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("images/newfile.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.actionNew.setIcon(icon1)
        self.actionNew.setObjectName("actionNew")
        self.actionOpen = QtWidgets.QAction(uPyCraft)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("images/fileopen.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.actionOpen.setIcon(icon2)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QtWidgets.QAction(uPyCraft)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("images/save.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.actionSave.setIcon(icon3)
        self.actionSave.setObjectName("actionSave")
        self.actionSaveAs = QtWidgets.QAction(uPyCraft)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap("images/saveas.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionSaveAs.setIcon(icon4)
        self.actionSaveAs.setObjectName("actionSaveAs")
        self.actionExit = QtWidgets.QAction(uPyCraft)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap("images/exit.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionExit.setIcon(icon5)
        self.actionExit.setObjectName("actionExit")
        self.actionCut = QtWidgets.QAction(uPyCraft)
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap("images/cut.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionCut.setIcon(icon6)
        self.actionCut.setObjectName("actionCut")
        self.actionCopy = QtWidgets.QAction(uPyCraft)
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap("images/copy.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionCopy.setIcon(icon7)
        self.actionCopy.setObjectName("actionCopy")
        self.actionPaste = QtWidgets.QAction(uPyCraft)
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap("images/paste.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionPaste.setIcon(icon8)
        self.actionPaste.setObjectName("actionPaste")
        self.actionUndo = QtWidgets.QAction(uPyCraft)
        icon9 = QtGui.QIcon()
        icon9.addPixmap(QtGui.QPixmap("images/undo.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.actionUndo.setIcon(icon9)
        self.actionUndo.setObjectName("actionUndo")
        self.actionRedo = QtWidgets.QAction(uPyCraft)
        icon10 = QtGui.QIcon()
        icon10.addPixmap(QtGui.QPixmap("images/redo.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.actionRedo.setIcon(icon10)
        self.actionRedo.setObjectName("actionRedo")
        self.actionConnect = QtWidgets.QAction(uPyCraft)
        icon11 = QtGui.QIcon()
        icon11.addPixmap(QtGui.QPixmap("images/serialConnect.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.actionConnect.setIcon(icon11)
        self.actionConnect.setObjectName("actionConnect")
        self.actionDisconnect = QtWidgets.QAction(uPyCraft)
        icon12 = QtGui.QIcon()
        icon12.addPixmap(QtGui.QPixmap("images/serialClose.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.actionDisconnect.setIcon(icon12)
        self.actionDisconnect.setVisible(False)
        self.actionDisconnect.setObjectName("actionDisconnect")
        self.actionRefresh = QtWidgets.QAction(uPyCraft)
        icon13 = QtGui.QIcon()
        icon13.addPixmap(QtGui.QPixmap("images/refresh.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionRefresh.setIcon(icon13)
        self.actionRefresh.setObjectName("actionRefresh")
        self.actionDownload = QtWidgets.QAction(uPyCraft)
        icon14 = QtGui.QIcon()
        icon14.addPixmap(QtGui.QPixmap("images/download.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionDownload.setIcon(icon14)
        self.actionDownload.setObjectName("actionDownload")
        self.actionDownloadAndRun = QtWidgets.QAction(uPyCraft)
        icon15 = QtGui.QIcon()
        icon15.addPixmap(QtGui.QPixmap("images/downloadandrun.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.actionDownloadAndRun.setIcon(icon15)
        self.actionDownloadAndRun.setObjectName("actionDownloadAndRun")
        self.actionStopExcute = QtWidgets.QAction(uPyCraft)
        icon16 = QtGui.QIcon()
        icon16.addPixmap(QtGui.QPixmap("images/stop.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.actionStopExcute.setIcon(icon16)
        self.actionStopExcute.setObjectName("actionStopExcute")
        self.actionClearTerminal = QtWidgets.QAction(uPyCraft)
        icon17 = QtGui.QIcon()
        icon17.addPixmap(QtGui.QPixmap("images/clear.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.actionClearTerminal.setIcon(icon17)
        self.actionClearTerminal.setObjectName("actionClearTerminal")
        self.actionPreference = QtWidgets.QAction(uPyCraft)
        self.actionPreference.setObjectName("actionPreference")
        self.actionTutorial = QtWidgets.QAction(uPyCraft)
        self.actionTutorial.setObjectName("actionTutorial")
        self.toolBar.addAction(self.actionNew)
        self.toolBar.addAction(self.actionSave)
        self.toolBar.addAction(self.actionUndo)
        self.toolBar.addAction(self.actionRedo)
        self.toolBar.addAction(self.actionConnect)
        self.toolBar.addAction(self.actionDisconnect)
        self.toolBar.addAction(self.actionRefresh)
        self.toolBar.addAction(self.actionDownload)
        self.toolBar.addAction(self.actionDownloadAndRun)
        self.toolBar.addAction(self.actionStopExcute)
        self.toolBar.addAction(self.actionClearTerminal)

        self.retranslateUi(uPyCraft)
        self.tabWidget.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(uPyCraft)

    def retranslateUi(self, uPyCraft):
        _translate = QtCore.QCoreApplication.translate
        uPyCraft.setWindowTitle(_translate("uPyCraft", "uPyCraft"))
        self.toolBar.setWindowTitle(_translate("uPyCraft", "toolBar"))
        self.actionNew.setText(_translate("uPyCraft", "New"))
        self.actionNew.setShortcut(_translate("uPyCraft", "Ctrl+N"))
        self.actionOpen.setText(_translate("uPyCraft", "Open"))
        self.actionOpen.setShortcut(_translate("uPyCraft", "Ctrl+O"))
        self.actionSave.setText(_translate("uPyCraft", "Save"))
        self.actionSave.setShortcut(_translate("uPyCraft", "Ctrl+S"))
        self.actionSaveAs.setText(_translate("uPyCraft", "SaveAs"))
        self.actionExit.setText(_translate("uPyCraft", "Exit"))
        self.actionExit.setShortcut(_translate("uPyCraft", "Ctrl+Q"))
        self.actionCut.setText(_translate("uPyCraft", "Cut"))
        self.actionCut.setShortcut(_translate("uPyCraft", "Ctrl+X"))
        self.actionCopy.setText(_translate("uPyCraft", "Copy"))
        self.actionCopy.setShortcut(_translate("uPyCraft", "Ctrl+C"))
        self.actionPaste.setText(_translate("uPyCraft", "Paste"))
        self.actionPaste.setShortcut(_translate("uPyCraft", "Ctrl+P"))
        self.actionUndo.setText(_translate("uPyCraft", "Undo"))
        self.actionUndo.setShortcut(_translate("uPyCraft", "Ctrl+Z"))
        self.actionRedo.setText(_translate("uPyCraft", "Redo"))
        self.actionRedo.setToolTip(_translate("uPyCraft", "Redo"))
        self.actionRedo.setShortcut(_translate("uPyCraft", "Ctrl+Y"))
        self.actionConnect.setText(_translate("uPyCraft", "Connect"))
        self.actionConnect.setToolTip(_translate("uPyCraft", "Connect"))
        self.actionDisconnect.setText(_translate("uPyCraft", "Disconnect"))
        self.actionRefresh.setText(_translate("uPyCraft", "Refresh Directory"))
        self.actionRefresh.setToolTip(_translate("uPyCraft", "Refresh Directory"))
        self.actionDownload.setText(_translate("uPyCraft", "Download"))
        self.actionDownloadAndRun.setText(_translate("uPyCraft", "DownloadAndRun"))
        self.actionDownloadAndRun.setShortcut(_translate("uPyCraft", "F5"))
        self.actionStopExcute.setText(_translate("uPyCraft", "StopExcute"))
        self.actionClearTerminal.setText(_translate("uPyCraft", "ClearTerminal"))
        self.actionPreference.setText(_translate("uPyCraft", "Preference"))
        self.actionPreference.setToolTip(_translate("uPyCraft", "Preference"))
        self.actionTutorial.setText(_translate("uPyCraft", "Tutorial"))

from widgets import TabWidget, Terminal, TreeView
