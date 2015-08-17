# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'NumberInput.ui'
#
# Created: Thu Aug 13 15:39:56 2015
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_NumberInput(object):
    def setupUi(self, NumberInput):
        NumberInput.setObjectName("NumberInput")
        NumberInput.resize(391, 151)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(NumberInput.sizePolicy().hasHeightForWidth())
        NumberInput.setSizePolicy(sizePolicy)
        self.layoutWidget = QtGui.QWidget(NumberInput)
        self.layoutWidget.setGeometry(QtCore.QRect(10, 10, 371, 133))
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.layoutWidget)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.scrollArea = QtGui.QScrollArea(self.layoutWidget)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 367, 69))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.gridLayout = QtGui.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setObjectName("gridLayout")
        self.label_description = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.label_description.setText("")
        self.label_description.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label_description.setWordWrap(True)
        self.label_description.setObjectName("label_description")
        self.gridLayout.addWidget(self.label_description, 0, 0, 1, 1)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_4.addWidget(self.scrollArea)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_slice = QtGui.QLabel(self.layoutWidget)
        self.label_slice.setObjectName("label_slice")
        self.verticalLayout.addWidget(self.label_slice)
        self.label = QtGui.QLabel(self.layoutWidget)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.spinBox_slice = QtGui.QSpinBox(self.layoutWidget)
        self.spinBox_slice.setMinimum(1)
        self.spinBox_slice.setObjectName("spinBox_slice")
        self.verticalLayout_2.addWidget(self.spinBox_slice)
        self.spinBox_thresh = QtGui.QSpinBox(self.layoutWidget)
        self.spinBox_thresh.setMaximum(100)
        self.spinBox_thresh.setProperty("value", 50)
        self.spinBox_thresh.setObjectName("spinBox_thresh")
        self.verticalLayout_2.addWidget(self.spinBox_thresh)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout_3 = QtGui.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.slider_slice = QtGui.QSlider(self.layoutWidget)
        self.slider_slice.setMinimum(1)
        self.slider_slice.setOrientation(QtCore.Qt.Horizontal)
        self.slider_slice.setObjectName("slider_slice")
        self.verticalLayout_3.addWidget(self.slider_slice)
        self.slider_thresh = QtGui.QSlider(self.layoutWidget)
        self.slider_thresh.setMaximum(100)
        self.slider_thresh.setProperty("value", 50)
        self.slider_thresh.setOrientation(QtCore.Qt.Horizontal)
        self.slider_thresh.setObjectName("slider_thresh")
        self.verticalLayout_3.addWidget(self.slider_thresh)
        self.horizontalLayout.addLayout(self.verticalLayout_3)
        self.buttonBox = QtGui.QDialogButtonBox(self.layoutWidget)
        self.buttonBox.setOrientation(QtCore.Qt.Vertical)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout.addWidget(self.buttonBox)
        self.verticalLayout_4.addLayout(self.horizontalLayout)

        self.retranslateUi(NumberInput)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), NumberInput.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), NumberInput.reject)
        QtCore.QObject.connect(self.spinBox_slice, QtCore.SIGNAL("valueChanged(int)"), self.slider_slice.setValue)
        QtCore.QObject.connect(self.slider_thresh, QtCore.SIGNAL("sliderMoved(int)"), self.spinBox_thresh.setValue)
        QtCore.QObject.connect(self.spinBox_thresh, QtCore.SIGNAL("valueChanged(int)"), self.slider_thresh.setValue)
        QtCore.QObject.connect(self.slider_slice, QtCore.SIGNAL("sliderMoved(int)"), self.spinBox_slice.setValue)
        QtCore.QMetaObject.connectSlotsByName(NumberInput)

    def retranslateUi(self, NumberInput):
        NumberInput.setWindowTitle(QtGui.QApplication.translate("NumberInput", "Number of candidate voxels", None, QtGui.QApplication.UnicodeUTF8))
        self.label_slice.setText(QtGui.QApplication.translate("NumberInput", "Slice", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("NumberInput", "Candidates", None, QtGui.QApplication.UnicodeUTF8))

