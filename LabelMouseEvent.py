__author__ = 'medabana'

from PySide import QtCore, QtGui
import numpy as np
from bitarray import bitarray

class LabelMouseEvent(QtGui.QLabel):

    pictureClicked = QtCore.Signal(int, int)
    mouseMoved = QtCore.Signal(int, int)
    mouseReleased = QtCore.Signal(int, int)

    def __init__(self, parent=None):
        super(LabelMouseEvent, self).__init__(parent)
        self.im = QtGui.QImage(450, 450, QtGui.QImage.Format_RGB32)

    # def mousePressEvent(self, event):
    #     x = event.x()
    #     y = event.y()
    #     self.pictureClicked.emit(x, y)

    def mouseMoveEvent(self, event):
        x = event.x()
        y = event.y()
        self.mouseMoved.emit(x, y)

    def mouseReleaseEvent(self, event):
        x = event.x()
        y = event.y()
        self.mouseReleased.emit(x, y)

    def setImageSlice(self, slice):
        self.im= slice
        self.update()

    def mousePressEvent(self, event):
        data= np.array(self.im.constBits())
        data2= data.reshape(self.im.width(), self.im.height(), 4)
        print data2[85, 65, :]

        draw = QtGui.QPainter(self.im)
        draw.setOpacity(0.4)
        draw.setBrush(QtCore.Qt.red)
        draw.setPen(QtCore.Qt.yellow)
        path= QtGui.QPainterPath()
        path.addRect(100.0, 100.0, 80.0, 60.0)
        draw.drawPath(path)

        draw.setBrush(QtCore.Qt.darkBlue)
        draw.setPen(QtCore.Qt.darkGreen)
        path2= QtGui.QPainterPath(QtCore.QPoint(10, 10))
        path2.lineTo(QtCore.QPoint(10,100))
        path2.lineTo(QtCore.QPoint(100,100))
        path2.lineTo(QtCore.QPoint(100,10))
        path2.lineTo(QtCore.QPoint(20,10))
        path2.closeSubpath()
        draw.drawPath(path2)

        # data= np.array(self.im.createMaskFromColor(QtCore.Qt.darkBlue).constBits())
        data= np.array(self.im.constBits())
        data2= data.reshape(self.im.width(), self.im.height(), 4)
        print data2[85, 65, :]
        print data.shape, data2.shape, self.im.size(), self.im.createMaskFromColor(QtCore.Qt.darkBlue).size()

        # draw.setClipPath(path)
        # maskIm = QtGui.QImage(450, 450, QtGui.QImage.Format_RGB32)
        # maskIm.fill(QtGui.qRgb(255, 0, 0))
        # draw.drawImage(0, 0, maskIm)
        # rectangle = QtCore.QRectF(100.0, 100.0, 80.0, 60.0)
        # draw.drawRect(rectangle)
        # draw.fillRect(rectangle, QtCore.Qt.red)

        self.update()

    def paintEvent(self, event):
        super(LabelMouseEvent, self).paintEvent(event)
        scaledIm= self.im.scaledToWidth(450)
        painter = QtGui.QPainter(self)
        painter.drawImage(QtCore.QPoint(0, 0), scaledIm)