# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'AifCurve.ui'
#
# Created: Mon Sep 21 16:56:49 2015
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_AifView(object):
    def setupUi(self, AifView):
        AifView.setObjectName("AifView")
        AifView.resize(400, 300)
        self.gridLayout = QtGui.QGridLayout(AifView)
        self.gridLayout.setObjectName("gridLayout")
        self.plotWidget = PlotWidget(AifView)
        self.plotWidget.setObjectName("plotWidget")
        self.gridLayout.addWidget(self.plotWidget, 0, 0, 1, 1)

        self.retranslateUi(AifView)
        QtCore.QMetaObject.connectSlotsByName(AifView)

    def retranslateUi(self, AifView):
        AifView.setWindowTitle(QtGui.QApplication.translate("AifView", "AIF curve", None, QtGui.QApplication.UnicodeUTF8))

from pyqtgraph import PlotWidget
