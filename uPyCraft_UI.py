# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Ubuntu\uPyCraft\uPyCraft.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_uPyCraft(object):
    def setupUi(self, uPyCraft):
        uPyCraft.setObjectName("uPyCraft")
        uPyCraft.resize(902, 600)
        font = QtGui.QFont()
        font.setFamily("Consolas")
        uPyCraft.setFont(font)
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
        self.hSplitter.setHandleWidth(2)
        self.hSplitter.setChildrenCollapsible(False)
        self.hSplitter.setObjectName("hSplitter")
        self.tree = TreeView(self.hSplitter)
        self.tree.setMinimumSize(QtCore.QSize(160, 0))
        self.tree.setMaximumSize(QtCore.QSize(300, 16777215))
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
        self.vSplitter.setOpaqueResize(True)
        self.vSplitter.setHandleWidth(2)
        self.vSplitter.setChildrenCollapsible(False)
        self.vSplitter.setObjectName("vSplitter")
        self.tabWidget = TabWidget(self.vSplitter)
        self.tabWidget.setMinimumSize(QtCore.QSize(0, 100))
        self.tabWidget.setAcceptDrops(False)
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
        self.terminal.setMinimumSize(QtCore.QSize(0, 100))
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
        self.actionConnect = QtWidgets.QAction(uPyCraft)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("images/serialConnect.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.actionConnect.setIcon(icon1)
        self.actionConnect.setObjectName("actionConnect")
        self.actionDisconnect = QtWidgets.QAction(uPyCraft)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("images/serialClose.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.actionDisconnect.setIcon(icon2)
        self.actionDisconnect.setVisible(False)
        self.actionDisconnect.setObjectName("actionDisconnect")
        self.actionRefresh = QtWidgets.QAction(uPyCraft)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("images/refresh.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionRefresh.setIcon(icon3)
        self.actionRefresh.setObjectName("actionRefresh")
        self.actionDownload = QtWidgets.QAction(uPyCraft)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap("images/download.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionDownload.setIcon(icon4)
        self.actionDownload.setObjectName("actionDownload")
        self.actionDownloadAndRun = QtWidgets.QAction(uPyCraft)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap("images/downloadandrun.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.actionDownloadAndRun.setIcon(icon5)
        self.actionDownloadAndRun.setObjectName("actionDownloadAndRun")
        self.actionStopExcute = QtWidgets.QAction(uPyCraft)
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap("images/stop.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.actionStopExcute.setIcon(icon6)
        self.actionStopExcute.setObjectName("actionStopExcute")
        self.actionClearTerminal = QtWidgets.QAction(uPyCraft)
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap("images/clear.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.actionClearTerminal.setIcon(icon7)
        self.actionClearTerminal.setObjectName("actionClearTerminal")
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
        self.actionConnect.setText(_translate("uPyCraft", "Connect"))
        self.actionConnect.setToolTip(_translate("uPyCraft", "Connect"))
        self.actionDisconnect.setText(_translate("uPyCraft", "Disconnect"))
        self.actionRefresh.setText(_translate("uPyCraft", "Refresh Directory"))
        self.actionRefresh.setToolTip(_translate("uPyCraft", "Refresh Directory"))
        self.actionDownload.setText(_translate("uPyCraft", "Download (Ctrl+S)"))
        self.actionDownload.setShortcut(_translate("uPyCraft", "Ctrl+S"))
        self.actionDownloadAndRun.setText(_translate("uPyCraft", "DownloadAndRun (Ctrl+R)"))
        self.actionDownloadAndRun.setShortcut(_translate("uPyCraft", "Ctrl+R"))
        self.actionStopExcute.setText(_translate("uPyCraft", "StopExcute"))
        self.actionClearTerminal.setText(_translate("uPyCraft", "ClearTerminal"))

from widgets import TabWidget, Terminal, TreeView
