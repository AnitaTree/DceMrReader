__author__ = 'medabana'

import logging
import os
import numpy as np
from PySide import QtCore, QtGui

from Analysis.MapGuiSetup import MapGuiSetup
from Analysis.AIFguiSetup import AIFguiSetup
from Analysis.AIFmethods import AIFmethods
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
        self._aifMethods = AIFmethods(self._aifGuiSetup, self._mapGuiSetup)
        self._logger = logging.getLogger(__name__)

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
        self._ui.actionDICOM.triggered.connect(self._displaySeriesNames)
        self._ui.actionNpz.triggered.connect(self._displayNpzFile)
        self._ui.actionShow_data.triggered.connect(self._displayDynamics)
        self._ui.actionSave.triggered.connect(self._saveSeries)
        self._ui.action_saveROIasRaw.triggered.connect(self._saveROIasRaw)
        self._ui.action_saveROIasNpz.triggered.connect(self._saveROIasNpz)
        self._ui.actionLoadROI_raw.triggered.connect(self._loadROI_raw)
        self._ui.actionLoadRoi_npz.triggered.connect(self._loadROI_npz)
        self._ui.label.pictureClicked.connect(self._showVoxelValue)

        # connect the analysis menu functions up
        self._ui.actionMaximum_Intensity_Map.triggered.connect(self._mapGuiSetup.getMaxIntMap)
        self._ui.actionMaximum_intensity_timepoint_map.triggered.connect(self._mapGuiSetup.getTTPMap)
        self._ui.actionMean_baseline_image.triggered.connect(self._mapGuiSetup.getMeanBaselineMap)
        self._ui.actionAorta_seed_score_map.triggered.connect(self._mapGuiSetup.displayScoreMap)
        self._ui.actionZeros_map.triggered.connect(self._mapGuiSetup.getZeroMinIntensityMap)
        self._ui.actionSelect_AIF_voxels.triggered.connect(self._selectAIFvoxelsFromMaskUser)
        self._ui.actionSelect_voxels_2.triggered.connect(self._selectAIFvoxelsGlobal)
        self._ui.actionAorta_mask_method_auto.triggered.connect(self._selectAIFvoxelsFromMaskAuto)

        #connect signals from the analysis up
        self._mapGuiSetup.timeChanged.connect(self._changeTime)
        self._mapGuiSetup.timeChanged.connect(self._ui.spinTime.setValue)
        self._mapGuiSetup.mapReady.connect(self._displayLatestMap)
        self._aifGuiSetup.maskReady.connect(self._displayLatestMask)
        self._aifGuiSetup.sliceChanged.connect(self._updateGuiSliceNum)

        # Connect the roi buttons to functions.
        self._ui.roiClear.pressed.connect(self._ui.label.clearROI)
        self._ui.roiClearSlice.pressed.connect(self._ui.label.clearSlice)
        self._ui.roiButton.pressed.connect(self._roiPressed)
        self._ui.roiFreehand.pressed.connect(self._freehandPressed)

        # self._displayNpzFile()

    def closeEvent(self, *args, **kwargs):
        """ Closes any open windows. """
        QtGui.qApp.quit()

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

    def _updateGuiSliceNum(self, num):
        """ Keep the Main GUI upto date with other windows.
        :param num: int
        Slice number
        :return:
        """
        self._currSlice = num
        self._ui.spinSlice.setValue(num)

    def _changeTime(self, num):
        """ Change the timepoint being displayed """
        if num > 0 and num <= self._nt:
            self._currTime= num
            self._mapGuiSetup.setDisplayTimepoint(num)
            self._setSlice()

    def _displayDynamics(self):
        """ Display previously loaded dynamics. """
        data = self._mapGuiSetup.getDynamics()
        self._ui.label.data = data
        nzt, self._ny, self._nx = data.shape
        self._nz = self._mapGuiSetup.getNz()
        self._nt = nzt/self._nz
        self._setGuiInfo('Dynamics')

    def _displayLatestMap(self, nt):
        """ Display the latest map produced by the analysis module. """
        self._ui.label.data = self._mapGuiSetup.latestMap
        self._nt = nt
        self._currTime = 1
        self._setGuiInfo(self._mapGuiSetup.latestMapName)

    def _displayLatestMask(self, z):
        """ Display the latest mask produced by the analysis module. """
        self._ui.label.roi = self._aifGuiSetup.latestMask
        self._updateGuiSliceNum(z)

    def _displayNpzFile(self):
        """ Load in data from a *.npz file and display it. """
        file = QtGui.QFileDialog.getOpenFileName(None, 'Select npz file', 'C:\\', "npz files (*.npz)")
        if file[0] == '':
            return
        fileName = file[0]
        npzData = np.load(fileName)
        if 'data' not in npzData or 'dims' not in npzData:
            message = "The npz file should contain the image array named \'data\' \n" \
                      "and an array [nt, nz, ny, nx] named \'dims\'"
            QtGui.QMessageBox.critical(self, "Critical", message)
            return
        data = npzData['data']
        self._ui.label.data = data
        self._nt, self._nz, self._ny, self._nx = npzData['dims']
        self._mapGuiSetup.reset()
        self._aifGuiSetup.reset()
        self._mapGuiSetup.setDynamics(data, self._nt)
        self._files = [fileName]
        seriesName = os.path.splitext(os.path.basename(fileName))[0]
        seriesName = seriesName.replace('_', ': ', 1).replace("_", " ")
        self._setGuiInfo(seriesName)
        self._dcmDir = os.path.dirname(fileName)
        self._setUpLogging()
        self._logger.info('Opening %s.' % fileName)

    def _displaySeries(self, index):
        """ Gets the data for the selected series and displays an initial image. """
        # Get the selected protocol name
        item = self.model.itemFromIndex(index)
        print "double clicked", item.text()
        seriesName = item.text()

        # get the image data and info
        data = self._seriesReader.getImageData(seriesName)
        self._ui.label.data = data
        self._files = self._seriesReader.getOrderedFileList(seriesName)
        self._nx, self._ny, self._nz, self._nt = self._seriesReader.getSequenceParameters(seriesName)
        self._mapGuiSetup.reset()
        self._aifGuiSetup.reset()
        self._mapGuiSetup.setDynamics(data, self._nt)
        print self._seriesReader.getSequenceParameters(seriesName)
        self._setGuiInfo(seriesName)

    def _displaySeriesNames(self):
        """ Request the DICOM directory from the user and displays the found protocols. """
        # Ask for the DICOM directory.
        self._dcmDir = QtGui.QFileDialog.getExistingDirectory(None, 'Select DICOM directory', 'C:\\')
        if self._dcmDir == '':
            return

        print self._dcmDir

        self._setUpLogging()
        self._logger.info('Reading DICOM directory %s' % self._dcmDir)

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
        seriesSelect.label_dcmDir.setText(self._dcmDir)
        self.scrArea.show()
        self.scrArea.activateWindow()
        self.scrArea.raise_()

    def _freehandPressed(self):
        """ Toggle roiButton """
        self._ui.roiButton.setChecked(False)
        self._ui.label.freehandMode = not self._ui.roiFreehand.isChecked()
        self._ui.label.roiMode = self._ui.roiButton.isChecked()

    def _getDirectoryReader(self):
        """ Return the correct directory reader depending on whether there is a DICOMDIR file. """
        dirName= self._dcmDir
        dirNameSearch= dirName
        if os.path.basename(dirName) == 'DICOM':
            dirNameSearch= os.path.dirname(dirName)
            dirName= dirNameSearch
        for baseDir, dirNames, files in os.walk(dirNameSearch):
            for file in files:
                if file == 'DICOMDIR':
                    return DicomDirFileReader(dirName, os.path.join(baseDir, file))
        return RecursiveDirectoryReader(dirName)

    def _loadROI_npz(self):
        """ Load in data from a *.npz file and display it. """
        file = QtGui.QFileDialog.getOpenFileName(None, 'Select npz file', self._dcmDir, "npz files (*.npz)")
        if file[0] == '':
            return
        fileName = file[0]

        npzData = np.load(fileName)
        if 'data' not in npzData or 'dims' not in npzData:
            message = "The npz file should contain the image array named \'data\' \n" \
                      "and an array [nt, nz, ny, nx] named \'dims\'"
            QtGui.QMessageBox.critical(self, "Critical", message)
            return

        self._ui.label.roi = npzData['data']

    def _loadROI_raw(self):
        firstFile = QtGui.QFileDialog.getOpenFileName(None, 'Select ROI file for first slice.', self._dcmDir)
        if firstFile == '':
            return
        fileBase = os.path.splitext(firstFile[0])[0]
        ind = fileBase.rfind('(')
        fileBase = fileBase[:ind]

        data = np.zeros([self._nz, self._ny, self._nx])

        for sliceNum in range(0, self._nz):
            fname = fileBase + '(' + str(sliceNum).zfill(3) + ',000)' + '.raw'
            if not os.path.exists(fname):
                print fname, 'expected but does not exist.'
                return
            data[self._nz-(sliceNum+1), :, :] = np.flipud(np.reshape(np.fromfile(fname, dtype='int8'), [self._ny, self._nx]))

        roi = np.zeros([self._nz, self._ny, self._nx], dtype = np.bool)
        roi[data > 0] = True
        self._ui.label.roi = roi

    def _roiPressed(self):
        """ Toggle roiFreehand button. """
        self._ui.roiFreehand.setChecked(False)
        self._ui.label.roiMode = not self._ui.roiButton.isChecked()
        self._ui.label.freehandMode = self._ui.roiFreehand.isChecked()

    def _saveROIasRaw(self, check=True, name=None):
        """ Save the ROI in a form that makes sense to PMI.
        :return:
        """
        if name == None:
            fileOut = QtGui.QFileDialog.getSaveFileName(None, 'Select output filename', self._dcmDir)
            if fileOut == '':
                return
            fileBase = os.path.splitext(fileOut[0])[0]
        else:
            roiDir = os.path.join(self._dcmDir, 'ROIs2')
            if not os.path.exists(roiDir):
                os.makedirs(roiDir)
            fileBase = os.path.join(roiDir, name)
            # fileBase = os.path.join(self._dcmDir, name)

        outFile = fileBase + '(000,000).raw'
        if check and os.path.exists(outFile):
            flags = QtGui.QMessageBox.StandardButton.Yes
            flags |= QtGui.QMessageBox.StandardButton.No
            question = "File \'" + outFile + "\' already exists. Would you like to overwrite?"
            response = QtGui.QMessageBox.warning(self, "Warning", question, flags)
            if response != QtGui.QMessageBox.Yes:
                return

        roi = self._ui.label.roi

        fnum = range(0, roi.shape[0])
        for i in fnum:
            slice = roi[i, :, :]
            slice = np.flipud(slice)
            j = roi.shape[0] - i - 1
            fname = fileBase + 'Rev(' + str(j).zfill(3) + ',000)' + '.raw'
            slice.astype('int8').tofile(fname)

    def _saveSeries(self):
        """ Save the Series currently displayed as a npz file. """
        data = self._ui.label.data
        name = self._ui.seriesLabel.text()
        name = name.replace(' ', '_').replace(":", "").replace("/", "_").replace("\\", "_")
        print name, data.shape
        outputDir = QtGui.QFileDialog.getExistingDirectory(None, 'Select output directory', self._dcmDir)
        if outputDir == '':
            return

        outFile = os.path.join(outputDir, name + '.npz')
        if os.path.exists(outFile):
            flags = QtGui.QMessageBox.StandardButton.Yes
            flags |= QtGui.QMessageBox.StandardButton.No
            question = "File \'" + outFile + "\' already exists. Would you like to overwrite?"
            response = QtGui.QMessageBox.warning(self, "Warning", question, flags)
            if response != QtGui.QMessageBox.Yes:
                return

        np.savez_compressed(outFile, data=data, dims=[self._nt, self._nz, self._ny, self._nx])
        self._dcmDir = os.path.dirname(outFile)

    def _saveROIasNpz(self):
        """ Save the ROI currently displayed as a npz file. """
        selectedFile = QtGui.QFileDialog.getSaveFileName(None, 'Select output filename', self._dcmDir)
        if selectedFile == '':
            return
        outFile = selectedFile[0]

        if os.path.exists(outFile):
            flags = QtGui.QMessageBox.StandardButton.Yes
            flags |= QtGui.QMessageBox.StandardButton.No
            question = "File \'" + outFile + "\' already exists. Would you like to overwrite?"
            response = QtGui.QMessageBox.warning(self, "Warning", question, flags)
            if response != QtGui.QMessageBox.Yes:
                return

        np.savez_compressed(outFile, data=self._ui.label.roi, dims=[self._nz, self._ny, self._nx])

    def _selectAIFvoxelsFromMaskAuto(self):
        """ Run algorithm that selects AIF voxels by generating an aorta mask,
        including requests for information from the user. """

        # fraction = [0.5, 0.75, 0.9, 0.95]
        fraction = [0.75]
        # numVoxels = [50, 20, 10, 5]


        for i in range(0, len(fraction)):
            aif, aifMeasures = self._aifMethods._selectAIFvoxelsFromMaskAuto(fraction[i], self._currSlice)
            # self._saveROI(False, 'aifFraction' + `fraction[i]`)
            aif = np.insert(aif, 0, fraction[i])
            aifMeasures = np.insert(aifMeasures, 0, fraction[i])
            if i == 0:
                aifs = aif.reshape([len(aif), 1])
                aifData = aifMeasures.reshape([1, len(aifMeasures)])
            else:
                aifs = np.append(aifs, aif.reshape([len(aif), 1]), 1)
                aifData = np.append(aifData, aifMeasures.reshape([1, len(aifMeasures)]), 0)

                # fileName = os.path.join(self._dcmDir, 'AIFcurves2.txt')
                # np.savetxt(fileName, aifs)
                # fileName = os.path.join(self._dcmDir, 'AIFmeasures2.txt')
                # np.savetxt(fileName, aifData)

                # for i in range(0, len(numVoxels)):
                #     self._aifGuiSetup.findAIFvoxelsMinNumber(False, numVoxels[i])
                #     # self._saveROI(False, 'aifNumber' + `numVoxels[i]`)
                #     aif, aifMeasures = self._aifGuiSetup.getAIFdata()
                #     aif = np.insert(aif, 0, numVoxels[i])
                #     aifMeasures = np.insert(aifMeasures, 0, numVoxels[i])
                #     if i == 0:
                #         aifs = aif.reshape([len(aif), 1])
                #         aifData = aifMeasures.reshape([1, len(aifMeasures)])
                #     else:
                #         aifs = np.append(aifs, aif.reshape([len(aif), 1]), 1)
                #         aifData = np.append(aifData, aifMeasures.reshape([1, len(aifMeasures)]), 0)

                # fileName = os.path.join(self._dcmDir, 'AIFcurvesNum2.txt')
                # np.savetxt(fileName, aifs)
                # fileName = os.path.join(self._dcmDir, 'AIFmeasuresNum2.txt')
                # np.savetxt(fileName, aifData)

    def _selectAIFvoxelsFromMaskUser(self):
        """ Run algorithm that selects AIF voxels by generating an aorta mask,
        including requests for information from the user. """
        self._aifMethods._selectAIFvoxelsFromMaskUser(self._currSlice)

    def _selectAIFvoxelsGlobal(self):
        """ Run algorithm that selects AIF voxels from the full image volume. No user input required. """
        self._aifMethods._selectAIFvoxelsGlobal()

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

    def _setUpLogging(self):
        logFile = os.path.join(self._dcmDir, 'aifSelection.log')
        logging.basicConfig(filename= logFile, filemode="w", level=logging.INFO)

    def _showVoxelValue(self, x, y, value):
        """ Show the voxel subscripts and value on the GUI """
        z = self._calculateIndex()
        self._ui.pixelVal.setText(str(x) + ', ' + str(y) + ', ' + str(z) + ": " + str(value))
