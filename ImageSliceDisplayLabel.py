__author__ = 'medabana'

from PySide import QtCore, QtGui
import numpy as np

class ImageSliceDisplayLabel(QtGui.QLabel):

    pictureClicked = QtCore.Signal(int, int, float)
    mouseMoved = QtCore.Signal(int, int)
    mouseReleased = QtCore.Signal(int, int)

    def __init__(self, parent=None):
        super(ImageSliceDisplayLabel, self).__init__(parent)
        self._im = QtGui.QImage(450, 450, QtGui.QImage.Format_RGB32)
        self._roiMode= False
        self._freehandMode= False

    def setData(self, imData):
        self._data= imData
        self._dims= imData.shape
        self._roiPaths= []
        for i in range(0, self._dims[0]):
            self._roiPaths.append(QtGui.QPainterPath())

    def setROImode(self, mode):
        self._roiMode= mode

    def setFreehandMode(self, mode):
        self._freehandMode= mode

    def setSlice(self, index):
      self._currSlice= index
      self._setImageSlice()
      self._displayImageSlice()

    def _setImageSlice(self):
      sliceData= self._data[self._currSlice, :, :]
      maxVal= sliceData.max()
      if maxVal == 0:
          maxVal= 1
      sliceC = np.require((sliceData*255.0)/maxVal, np.uint32, 'C')
      sliceRGB = np.zeros((self._dims[1], self._dims[2], 3), dtype=np.uint32)
      sliceRGB[:, :, 0] = sliceC
      sliceRGB[:, :, 1] = sliceC
      sliceRGB[:, :, 2] = sliceC
      self._displaySlice = (255 << 24 | sliceRGB[:,:,0] << 16 | sliceRGB[:,:,1] << 8 | sliceRGB[:,:,2])
      self._im= QtGui.QImage(self._displaySlice, self._dims[1], self._dims[2], QtGui.QImage.Format_RGB32)

    def _displayImageSlice(self):
        draw = QtGui.QPainter(self._im)
        draw.setOpacity(0.4)
        draw.setBrush(QtCore.Qt.red)
        draw.setPen(QtCore.Qt.yellow)
        draw.drawPath(self._roiPaths[self._currSlice])
        self.update()

    def mousePressEvent(self, event):
        x = event.x()
        y = event.y()
        xVox= self._dims[2] * x/self.geometry().width()
        yVox= self._dims[1] * y/self.geometry().height()
        if self._roiMode:
            self._rectPt0= [xVox, yVox]
            self.update()
        elif self._freehandMode:
            self._roiPaths[self._currSlice]= QtGui.QPainterPath(QtCore.QPoint(xVox, yVox))
            self._setImageSlice()
            self._displayImageSlice()
        else:
            value= self._data[self._currSlice, yVox, xVox]
            self.pictureClicked.emit(xVox, yVox, value)

    def mouseMoveEvent(self, event):
        xVox= self._dims[2] * event.x()/self.geometry().width()
        yVox= self._dims[1] * event.y()/self.geometry().height()
        if self._roiMode:
            if yVox > self._rectPt0[1]:
                y0= self._rectPt0[1]
                y1= yVox+1
            else:
                y0= yVox
                y1= self._rectPt0[1]+1
            if xVox > self._rectPt0[0]:
                x0= self._rectPt0[0]
                x1= xVox+1
            else:
                x0= xVox
                x1= self._rectPt0[0]+1
            self._setImageSlice()
            draw = QtGui.QPainter(self._im)
            draw.setOpacity(0.4)
            draw.setBrush(QtCore.Qt.red)
            draw.setPen(QtCore.Qt.yellow)
            path= QtGui.QPainterPath()
            path.addRect(x0, y0, x1-x0, y1-y0)
            draw.drawPath(path)
            self.update()
            self._roiPaths[self._currSlice]= path
        elif self._freehandMode:
            draw = QtGui.QPainter(self._im)
            draw.setOpacity(0.4)
            draw.setPen(QtCore.Qt.yellow)
            path= self._roiPaths[self._currSlice]
            path.lineTo(QtCore.QPoint(xVox, yVox))
            draw.drawPath(path)
            self.update()
            self._roiPaths[self._currSlice]= path

    def mouseReleaseEvent(self, event):
        if self._freehandMode:
            draw = QtGui.QPainter(self._im)
            draw.setOpacity(0.4)
            draw.setBrush(QtCore.Qt.red)
            draw.setPen(QtCore.Qt.yellow)
            path= self._roiPaths[self._currSlice]
            path.closeSubpath()
            self._roiPaths[self._currSlice]= path
            draw.drawPath(path)
            self.update()

    def paintEvent(self, event):
        super(ImageSliceDisplayLabel, self).paintEvent(event)
        scaledIm= self._im.scaledToWidth(450)
        painter = QtGui.QPainter(self)
        painter.drawImage(QtCore.QPoint(0, 0), scaledIm)

    def clearSlice(self):
        self._roiPaths[self._currSlice]= QtGui.QPainterPath()
        self._setImageSlice()
        self._displayImageSlice()

    def clearROI(self):
        for i in range(0, self._dims[0]):
            self._roiPaths[i]= QtGui.QPainterPath()
        self._setImageSlice()
        self._displayImageSlice()
