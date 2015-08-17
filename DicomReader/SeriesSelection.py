# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SeriesSelection.ui'
#
# Created: Tue Jan 20 12:04:52 2015
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_SeriesSelection(object):
    def setupUi(self, SeriesSelection):
        SeriesSelection.setObjectName("SeriesSelection")
        SeriesSelection.resize(279, 213)
        SeriesSelection.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 277, 211))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.gridLayout = QtGui.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setObjectName("gridLayout")
        self.listView = QtGui.QListView(self.scrollAreaWidgetContents)
        self.listView.setObjectName("listView")
        self.gridLayout.addWidget(self.listView, 1, 0, 1, 1)
        self.label_dcmDir = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.label_dcmDir.setText("")
        self.label_dcmDir.setObjectName("label_dcmDir")
        self.gridLayout.addWidget(self.label_dcmDir, 0, 0, 1, 1)
        SeriesSelection.setWidget(self.scrollAreaWidgetContents)

        self.retranslateUi(SeriesSelection)
        QtCore.QMetaObject.connectSlotsByName(SeriesSelection)

    def retranslateUi(self, SeriesSelection):
        SeriesSelection.setWindowTitle(QtGui.QApplication.translate("SeriesSelection", "Series Selector", None, QtGui.QApplication.UnicodeUTF8))

