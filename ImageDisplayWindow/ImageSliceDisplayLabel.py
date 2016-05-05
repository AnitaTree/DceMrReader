__author__ = 'medabana'

from PySide import QtCore, QtGui
import numpy as np

class ImageSliceDisplayLabel(QtGui.QLabel):
    """ Responsible for the Image display area. """
    pictureClicked = QtCore.Signal(int, int, float)
    mouseMoved = QtCore.Signal(int, int)
    mouseReleased = QtCore.Signal(int, int)

    def __init__(self, parent=None):
        """ Set up QImage and roi modes. """
        super(ImageSliceDisplayLabel, self).__init__(parent)
        self._data = None
        self._freehandMode = False
        self._roiMode = False
        self._roi = None
        self._currSlice = None
        self._currPath = 0
        self._qIm = QtGui.QImage(450, 450, QtGui.QImage.Format_RGB32)

    def clearROI(self):
        """ Clear the whole ROI. """
        if self._roi is not None:
            self._roi[:, :, :] = False
        self._setImageSlice()
        self._displayImageSlice()

    def clearSlice(self):
        """ Clear the current ROI slice. """
        self._roi[self._currSlice, :, :] = False
        self._setImageSlice()
        self._displayImageSlice()

    @property
    def data(self):
        """ Return the currently displayed data

        :return: np.array
        3D array [nt x nz, ny, nx]
        """
        return self._data

    @data.setter
    def data(self, imData):
        """ Set the data for the image and a new clear ROI. """
        self._data = imData
        self._dims = imData.shape
        print self._dims
        self._maxVal = np.amax(imData)
        if self._maxVal == 0:
            self._maxVal = 1
        self._roi = np.zeros(self._dims, np.bool)

    def highlightVoxel(self, voxel):
        """ Draw box around the given voxel. """
        path = QtGui.QPainterPath(QtCore.QPoint())
        path.addRect(voxel[2]-1, voxel[1]-1, 2, 2)
        self._currPath = path
        self.update()

    @property
    def roi(self):
        return self._roi

    @roi.setter
    def roi(self, region):
        """ Set the ROI to region. """
        if region.shape == self._roi.shape:
            self._roi = region
            self._setImageSlice()
            self.update()
        else:
            print "Region is not the correct shape."

    def setSlice(self, index):
        """ Change and display the slice. """
        self._currSlice = index
        self._currPath = QtGui.QPainterPath()
        self._setImageSlice()
        self._displayImageSlice()

    def mouseMoveEvent(self, event):
        """ Draw the ROI as required by the ROI mode.

        Do nothing if none of the ROI modes are set.
        """
        #Sometimes the label is a different height to the pixmap so set both to width
        xVox = self._dims[2] * event.x()/self.width()
        yVox = self._dims[1] * event.y()/self.width()
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
            draw = QtGui.QPainter(self._qIm)
            draw.setOpacity(0.4)
            draw.setBrush(QtCore.Qt.red)
            draw.setPen(QtCore.Qt.yellow)
            path = QtGui.QPainterPath()
            path.addRect(x0, y0, x1-x0, y1-y0)
            draw.drawPath(path)
            self.update()
            self._currPath = path
        elif self._freehandMode:
            draw = QtGui.QPainter(self._qIm)
            draw.setOpacity(0.4)
            draw.setPen(QtCore.Qt.yellow)
            self._currPath.lineTo(QtCore.QPoint(xVox, yVox))
            draw.drawPath(self._currPath)
            self.update()

    def mousePressEvent(self, event):
        """  Start a new ROI section or display the voxel value. """
        self._roi[self._currSlice, :, :] = False
        self.update()
        x = event.x()
        y = event.y()
        #Sometimes the label is a different height to the pixmap so both are set to the width
        xVox = self._dims[2] * x/self.width()
        yVox = self._dims[1] * y/self.width()
        if self._roiMode:
            self._rectPt0 = [xVox, yVox]
            self.update()
        elif self._freehandMode:
            self._currPath= QtGui.QPainterPath(QtCore.QPoint(xVox, yVox))
            self._setImageSlice()
            self._displayImageSlice()
        else:
            value = self._data[self._currSlice, yVox, xVox]
            self.pictureClicked.emit(xVox, yVox, value)

    def mouseReleaseEvent(self, event):
        """ If drawing a freehand ROI, close the ROI. """
        if self._freehandMode:
            draw = QtGui.QPainter(self._qIm)
            draw.setOpacity(0.4)
            draw.setBrush(QtCore.Qt.red)
            draw.setPen(QtCore.Qt.yellow)
            self._currPath.closeSubpath()
            draw.drawPath(self._currPath)
            del draw
        if self._freehandMode or self._roiMode:
            self._setPathInROI()
            self._currPath = QtGui.QPainterPath()
            self._setImageSlice()
            self.update()

    def paintEvent(self, event):
        """ Repaint the current image. """
        super(ImageSliceDisplayLabel, self).paintEvent(event)
        scaledIm = self._qIm.scaledToWidth(self.width())
        painter = QtGui.QPainter(self)
        painter.drawImage(QtCore.QPoint(0, 0), scaledIm)

    def _displayImageSlice(self):
        """ Paint the current slice and ROI. """
        draw = QtGui.QPainter(self._qIm)
        draw.setOpacity(0.5)
        draw.setBrush(QtCore.Qt.red)
        draw.setPen(QtCore.Qt.yellow)
        draw.drawPath(self._currPath)
        self.update()

    def _setImageSlice(self):
        """ Set the QImage for the current slice. """
        sliceData = self._data[self._currSlice, :, :]
        sliceC = np.require((sliceData*255.0)/self._maxVal, np.uint32, 'C')
        sliceRGB = np.zeros((self._dims[1], self._dims[2], 3), dtype=np.uint32)
        sliceR = sliceC.copy()
        sliceG = sliceC.copy()
        sliceB = sliceC.copy()
        # Set any True ROI voxels to red
        sliceR[self._roi[self._currSlice, :, :]] = 255.0
        sliceG[self._roi[self._currSlice, :, :]] = 0.0
        sliceB[self._roi[self._currSlice, :, :]] = 0.0
        sliceRGB[:, :, 0] = sliceR
        sliceRGB[:, :, 1] = sliceG
        sliceRGB[:, :, 2] = sliceB
        self._displaySlice = (255 << 24 | sliceRGB[:,:,0] << 16 | sliceRGB[:,:,1] << 8 | sliceRGB[:,:,2])
        self._qIm = QtGui.QImage(self._displaySlice, self._dims[1], self._dims[2], QtGui.QImage.Format_RGB32)

    def _setPathInROI(self):
        # create a blank image
        im = QtGui.QImage(self._dims[1], self._dims[2], QtGui.QImage.Format_RGB32)
        im.fill(0)
        # create a drawing tool
        draw = QtGui.QPainter(im)
        draw.setBrush(QtCore.Qt.darkBlue)
        draw.setPen(QtCore.Qt.darkGreen)
        # draw on the path
        path = self._currPath
        draw.drawPath(path)
        del draw
        # get the data out of the image
        data = np.array(im.constBits()).reshape(im.height(), im.width(), 4)
        # get the indices of any filled voxels and set in the roi
        indices = np.where((data[:, :, 2] > 0) | (data[:, :, 1] > 0) | (data[:, :, 0] > 0))
        self._roi[self._currSlice, indices[0], indices[1]] = True
