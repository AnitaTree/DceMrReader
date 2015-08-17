__author__ = 'medabana'

import os

from PySide import QtCore, QtGui

from Analysis.MapGuiSetup import MapGuiSetup
from Analysis.AIFguiSetup import AIFguiSetup
from DicomReader.DicomDirFileReader import DicomDirFileReader
from DicomReader.RecursiveDirectoryReader import RecursiveDirectoryReader
from DicomReader.SeriesSelection import Ui_SeriesSelection
from ImageDisplayWindow import ImageDisplay

class ControlMainWindow(QtGui.QMainWindow):
    """ Responsible for the main GUI window."""
    def __init__(self, parent=None):
        """ Set up the main window and connect buttons/sliders etc. """
        super(ControlMainWindow, self).__init__(parent)
        self._im = QtGui.QImage()
        self._currSlice = 1
        self._currTime = 1
        self._labelGeometry = [450, 450]
        self._mapGuiSetup = MapGuiSetup()
        self._aifGuiSetup = AIFguiSetup(self._mapGuiSetup.getMapGenerator())

        # Create the main window.
        self._ui = ImageDisplay.Ui_MainWindow()
        self._ui.setupUi(self)
        self._ui.spinSlice.setValue(1)
        self._ui.spinTime.setValue(1)
        self._ui.label.setGeometry(QtCore.QRect(0, 0, self._labelGeometry[0], self._labelGeometry[1]))
        self._ui.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0,0,self._labelGeometry[0],self._labelGeometry[1]))

        # Connect the image slice related buttons to functions.
        self._ui.spinSlice.valueChanged.connect(self._changeSlice)
        self._ui.spinTime.valueChanged.connect(self._changeTime)
        self._ui.actionOpen.triggered.connect(self._displaySeriesNames)
        self._ui.label.pictureClicked.connect(self._showVoxelValue)

        # connect the analysis menu functions up
        self._ui.actionMaximum_Intensity_Map.triggered.connect(self._mapGuiSetup.calcAndSignalMaxIntMap)
        self._ui.actionMean_baseline_image.triggered.connect(self._mapGuiSetup.calcAndSignalMeanBaselineMap)
        self._ui.actionSelect_AIF_voxels.triggered.connect(self._selectAIFvoxels)

        #connect signals from the analysis up
        self._mapGuiSetup.timeChanged.connect(self._changeTime)
        self._mapGuiSetup.timeChanged.connect(self._ui.spinTime.setValue)
        self._mapGuiSetup.mapReady.connect(self._displayLatestMap)
        self._aifGuiSetup.maskReady.connect(self._displayLatestMask)
        self._aifGuiSetup.sliceChanged.connect(self._changeGuiSlice)

        # Connect the roi buttons to functions.
        self._ui.roiClear.pressed.connect(self._ui.label.clearROI)
        self._ui.roiClearSlice.pressed.connect(self._ui.label.clearSlice)
        self._ui.roiButton.pressed.connect(self._roiPressed)
        self._ui.roiFreehand.pressed.connect(self._freehandPressed)

        self._displaySeriesNames()

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

    def _calculateIndex(self):
        """ Calculate the index into the data array from the subscripts.

            The '-1's are due to zero-based indexing of the data array but one-based
            indexing on the GUI.
        """
        index = (self._currSlice - 1) * self._nt + self._currTime - 1
        return index

    def _changeSlice(self, num):
        """ Change the slice being displayed """
        if num > 0 and num <= self._nz:
            self._currSlice = num
            self._setSlice()

    def _changeGuiSlice(self, num):
        self._currSlice = num
        self._ui.spinSlice.setValue(num)

    def _changeTime(self, num):
        """ Change the timepoint being displayed """
        if num > 0 and num <= self._nt:
            self._currTime= num
            self._mapGuiSetup.setDisplayTimepoint(num)
            self._setSlice()

    def _displayLatestMap(self):
        """ Display the latest map produced by the analysis module. """
        self._ui.label.setData(self._mapGuiSetup.getLatestMap())
        self._nt = 1
        self._currTime = 1
        self._setGuiInfo(self._mapGuiSetup.getLatestMapName())

    def _displayLatestMask(self):
        """ Display the latest mask produced by the analysis module. """
        self._ui.label.setROI(self._aifGuiSetup.getLatestMask())

    def _displaySeries(self, index):
        """ Gets the data for the selected series and displays an initial image. """
        # Get the selected protocol name
        item = self.model.itemFromIndex(index)
        print "double clicked", item.text()
        seriesName= item.text()

        # get the image data and info
        data= self._seriesReader.getImageData(seriesName)
        self._ui.label.setData(data)
        self._files= self._seriesReader.getOrderedFileList(seriesName)
        self._nx, self._ny, self._nz, self._nt = self._seriesReader.getSequenceParameters(seriesName)
        self._mapGuiSetup.setDynamics(data, self._nt)
        print self._seriesReader.getSequenceParameters(seriesName)
        self._setGuiInfo(seriesName)

    def _displaySeriesNames(self):
        """ Request the DICOM directory from the user and displays the found protocols. """
        # Ask for the DICOM directory.
        # self.dcmDir = QtGui.QFileDialog.getExistingDirectory(None, 'Select DICOM directory', 'D:\\renalDatabase_anon')
        # if self.dcmDir == '':
        #     return

        self.dcmDir = 'D:\\renalDatabase_anon\\NKRF\\AW27'

        # Get the appropriate type of directory reader for the data.
        # And from the reader get the protocol names.
        self._seriesReader = self._getDirectoryReader()
        seriesNames = self._seriesReader.getSeriesNames()

        # Display the protocols to the user.
        self.scrArea = QtGui.QScrollArea()
        seriesSelect = Ui_SeriesSelection()
        seriesSelect.setupUi(self.scrArea)
        self.model = QtGui.QStandardItemModel(seriesSelect.listView)
        for name in seriesNames:
            item = QtGui.QStandardItem(name)
            item.setEditable(False)
            self.model.appendRow(item)
        seriesSelect.listView.setModel(self.model)
        seriesSelect.listView.doubleClicked[QtCore.QModelIndex].connect(self._displaySeries)
        seriesSelect.label_dcmDir.setText(self.dcmDir)
        self.scrArea.show()
        self.scrArea.activateWindow()
        self.scrArea.raise_()

    def _freehandPressed(self):
        """ Toggle roiButton """
        self._ui.roiButton.setChecked(False)
        self._ui.label.setFreehandMode(not self._ui.roiFreehand.isChecked())
        self._ui.label.setROImode(self._ui.roiButton.isChecked())

    def _getDirectoryReader(self):
        """ Return the correct directory reader depending on whether there is a DICOMDIR file. """
        dirName= self.dcmDir
        dirNameSearch= dirName
        if os.path.basename(dirName) == 'DICOM':
            dirNameSearch= os.path.dirname(dirName)
            dirName= dirNameSearch
        for baseDir, dirNames, files in os.walk(dirNameSearch):
            for file in files:
                if file == 'DICOMDIR':
                    return DicomDirFileReader(dirName, os.path.join(baseDir, file))
        return RecursiveDirectoryReader(dirName)

    def _roiPressed(self):
        """ Toggle roiFreehand button. """
        self._ui.roiFreehand.setChecked(False)
        self._ui.label.setROImode(not self._ui.roiButton.isChecked())
        self._ui.label.setFreehandMode(self._ui.roiFreehand.isChecked())

    def _selectAIFvoxels(self):
        accept = self._mapGuiSetup.calcMaxIntMap()
        if accept:
            self._displayLatestMap()
            self._mapGuiSetup.calcMeanBaseline()
        findSeed = True
        accept = True
        while findSeed:
            findSeed = False
            accept = self._aifGuiSetup.findCandidateAortaSeeds(self._currSlice)
            if accept:
                accept, findSeed = self._aifGuiSetup.acceptAortaSeed()
        if accept:
            accept = self._aifGuiSetup.floodfillFromSeed(self._currSlice)
        if accept:
            self._aifGuiSetup.findAIFvoxels(self._currSlice)

    def _setGuiInfo(self, seriesName):
        """ Set up the GUI and display the series. """
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

    def _setSlice(self):
        """ Display the slice. """
        index = self._calculateIndex()
        self._ui.label.setSlice(index)

        if len(self._files) > 1:
            self._ui.fileNameLabel.setText(self._files[index])
        else:
            self._ui.fileNameLabel.setText(self._files[0] + " " + str(index))

    def _showVoxelValue(self, x, y, value):
        """ Show the voxel subscripts and value on the GUI """
        z = self._calculateIndex()
        self._ui.pixelVal.setText(str(x) + ', ' + str(y) + ', ' + str(z) + ": " + str(value))
