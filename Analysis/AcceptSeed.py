# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'AcceptSeed.ui'
#
# Created: Tue Aug 11 13:53:12 2015
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_AcceptSeed(object):
    def setupUi(self, AcceptSeed):
        AcceptSeed.setObjectName("AcceptSeed")
        AcceptSeed.resize(217, 62)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(AcceptSeed.sizePolicy().hasHeightForWidth())
        AcceptSeed.setSizePolicy(sizePolicy)
        self.gridLayout = QtGui.QGridLayout(AcceptSeed)
        self.gridLayout.setObjectName("gridLayout")
        self.pushButton_cancel = QtGui.QPushButton(AcceptSeed)
        self.pushButton_cancel.setObjectName("pushButton_cancel")
        self.gridLayout.addWidget(self.pushButton_cancel, 0, 2, 1, 1)
        self.pushButton_no = QtGui.QPushButton(AcceptSeed)
        self.pushButton_no.setObjectName("pushButton_no")
        self.gridLayout.addWidget(self.pushButton_no, 0, 1, 1, 1)
        self.pushButton_yes = QtGui.QPushButton(AcceptSeed)
        self.pushButton_yes.setObjectName("pushButton_yes")
        self.gridLayout.addWidget(self.pushButton_yes, 0, 0, 1, 1)

        self.retranslateUi(AcceptSeed)
        QtCore.QObject.connect(self.pushButton_cancel, QtCore.SIGNAL("clicked()"), AcceptSeed.reject)
        QtCore.QObject.connect(self.pushButton_yes, QtCore.SIGNAL("clicked()"), AcceptSeed.accept)
        QtCore.QObject.connect(self.pushButton_no, QtCore.SIGNAL("clicked()"), AcceptSeed.close)
        QtCore.QMetaObject.connectSlotsByName(AcceptSeed)

    def retranslateUi(self, AcceptSeed):
        AcceptSeed.setWindowTitle(QtGui.QApplication.translate("AcceptSeed", "Accept aorta seed", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_cancel.setText(QtGui.QApplication.translate("AcceptSeed", "cancel", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_no.setText(QtGui.QApplication.translate("AcceptSeed", "no", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_yes.setText(QtGui.QApplication.translate("AcceptSeed", "yes", None, QtGui.QApplication.UnicodeUTF8))

