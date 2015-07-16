__author__ = 'medabana'

from ImageDisplay import *
from SeriesSelection import *
from DirectoryReaderSelector import *

class ControlMainWindow(QtGui.QMainWindow):
    """

    """
    def __init__(self, parent=None):
        """ Set up the main window and connect buttons/sliders etc. """
        super(ControlMainWindow, self).__init__(parent)
        self._im = QtGui.QImage()
        self._currSlice = 1
        self._currTime = 1
        self._labelGeometry = [450, 450]

        # Create the main window.
        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)
        self._ui.spinSlice.setValue(1)
        self._ui.spinTime.setValue(1)
        self._ui.label.setGeometry(QtCore.QRect(0, 0, self._labelGeometry[0], self._labelGeometry[1]))
        self._ui.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0,0,self._labelGeometry[0],self._labelGeometry[1]))

        # Connect the image slice related buttons to functions.
        self._ui.spinSlice.valueChanged.connect(self._changeSlice)
        self._ui.spinTime.valueChanged.connect(self._changeTime)
        self._ui.actionOpen.triggered.connect(self._displaySeriesNames)
        self._ui.label.pictureClicked.connect(self._getVoxelValue)

        # Connect the roi buttons to functions.
        self._ui.roiClear.pressed.connect(self._ui.label.clearROI)
        # self._ui.roiTransfer.pressed.connect(self._transferROI)
        self._ui.roiClearSlice.pressed.connect(self._ui.label.clearSlice)
        self._ui.roiButton.pressed.connect(self._roiPressed)
        self._ui.roiFreehand.pressed.connect(self._freehandPressed)

    def _displaySeriesNames(self):
        """ Requests the DICOM directory and displays the found protocols. """

        # Ask for the DICOM directory.
        self.dcmDir= QtGui.QFileDialog.getExistingDirectory(None, 'Select DICOM directory', 'D:\\renalDatabase_anon')
        if self.dcmDir == '':
            return

        # Get the appropriate type of directory reader for the data.
        # And from the reader get the protocol names.
        self.seriesReader = DirectoryReaderSelector().getDirectoryReader(self.dcmDir)
        seriesNames= self.seriesReader.getSeriesNames()

        # Display the protocols to the user.
        self.scrArea= QtGui.QScrollArea()
        seriesSelect= Ui_SeriesSelection()
        seriesSelect.setupUi(self.scrArea)
        self.model = QtGui.QStandardItemModel(seriesSelect.listView)
        for name in seriesNames:
            item= QtGui.QStandardItem(name)
            item.setEditable(False)
            self.model.appendRow(item)
        seriesSelect.listView.setModel(self.model)
        seriesSelect.listView.doubleClicked[QtCore.QModelIndex].connect(self._displaySeries)
        seriesSelect.label_dcmDir.setText(self.dcmDir)
        self.scrArea.show()

    def _displaySeries(self, index):
        """ Gets the data for the selected series and displays an initial image. """

        # Get the selected protocol name
        item = self.model.itemFromIndex(index)
        print "double clicked", item.text()
        seriesName= item.text()

        # get the image data and info
        self._ui.label.setData(self.seriesReader.getImageData(seriesName))
        self.files= self.seriesReader.getOrderedFileList(seriesName)
        self._nx, self._ny, self._nz, self._nt = self.seriesReader.getSequenceParameters(seriesName)
        print self.seriesReader.getSequenceParameters(seriesName)

        # set up the info needed for the GUI
        self._ui.spinSlice.setMaximum(self._nz)
        self._ui.sliderSlice.setMaximum(self._nz)
        self._ui.spinTime.setMaximum(self._nt)
        self._ui.sliderTime.setMaximum(self._nt)

        if(self._nt <= 1):
            self._ui.spinTime.setEnabled(False)
            self._ui.sliderTime.setEnabled(False)
        else:
            self._ui.spinTime.setEnabled(True)
            self._ui.sliderTime.setEnabled(True)

        # Display the data
        self._setSlice()
        self._ui.seriesLabel.setText(seriesName)

    def _calculateIndex(self):
        """ Calculate the index into the data array from the subscripts """
        index = (self._currSlice - 1) * self._nt + self._currTime - 1
        return index

    def _changeSlice(self, num):
        """ Change the slice being displayed """
        if num > 0 and num <= self._nz:
            self._currSlice= num
            self._setSlice()

    def _changeTime(self, num):
        """ Change the timepoint being displayed """
        if num > 0 and num <= self._nt:
            self._currTime= num
            self._setSlice()

    def _setSlice(self):
        """ Display the slice. """
        index = self._calculateIndex()
        self._ui.label.setSlice(index)

        if len(self.files) > 1:
            self._ui.fileNameLabel.setText(self.files[index])
        else:
            self._ui.fileNameLabel.setText(self.files[0] + " " + str(index))

    def keyPressEvent(self, e):
        """ Move around the series images using the H, J, F, and G keys. """
        if e.key() == QtCore.Qt.Key_H:
            self._changeTime(self._currTime - 1)
            self._ui.spinTime.setValue(self._currTime)
        elif e.key() == QtCore.Qt.Key_J:
            self._changeTime(self._currTime + 1)
            self._ui.spinTime.setValue(self._currTime)
        elif e.key() == QtCore.Qt.Key_F:
            self._changeSlice(self._currSlice - 1)
            self._ui.spinSlice.setValue(self._currSlice)
        elif e.key() == QtCore.Qt.Key_G:
            self._changeSlice(self._currSlice + 1)
            self._ui.spinSlice.setValue(self._currSlice)

    def _roiPressed(self):
        """ Toggle roiFreehand button. """
        self._ui.roiFreehand.setChecked(False)
        self._ui.label.setROImode(not self._ui.roiButton.isChecked())
        self._ui.label.setFreehandMode(self._ui.roiFreehand.isChecked())

    def _freehandPressed(self):
        self._ui.roiButton.setChecked(False)
        self._ui.label.setFreehandMode(not self._ui.roiFreehand.isChecked())
        self._ui.label.setROImode(self._ui.roiButton.isChecked())

    def _getVoxelValue(self, x, y, value):
        z= self._calculateIndex()
        self._ui.pixelVal.setText(str(x) + ', ' + str(y) + ', ' + str(z) + ": " + str(value))
