from Analysis import AcceptSeed, ThresholdInput, NumberInput

__author__ = 'medabana'

from PySide import QtGui, QtCore
import numpy as np

from Analysis.AIFselector import AIFselector


class AIFguiSetup(QtCore.QObject):
    """ Responsible for getting the information required for each of the analysis procedures and communicating the
    results to the main GUI. """
    maskReady = QtCore.Signal()
    sliceChanged = QtCore.Signal(int)

    def __init__(self, maps, parent=None):
        super(AIFguiSetup, self).__init__(parent)
        self._thresholdInput = None
        self._inputDialog = None
        self._numberInput = None
        self._acceptSeed = None
        self._aifSelector = AIFselector(maps)
        self._mapGenerator = maps
        self._latestMask = None
        self._isFindingSeed = False
        self._aortaSeed = None
        self._refindSeed = False

    def getLatestMask(self):
        """ Return the last binary mask generated.

        :return: np.array(dtype = np.bool)
        """
        return self._latestMask

    def acceptAortaSeed(self):
        """ Display the aorta seed and ask the user to accept/reject it.

        :return accept: bool
        True if the user accepts the seed, False otherwise
        :return self._refindSeed: bool
        True if the user wishes to refind the seed, False otherwise
        """
        self._refindSeed = False
        # The '+1' to send the GUI slider number through
        self.sliceChanged.emit(self._aortaSeed[0]+1)
        self._inputDialog = QtGui.QDialog()
        self._acceptSeed = AcceptSeed.Ui_AcceptSeed()
        self._acceptSeed.setupUi(self._inputDialog)
        self._acceptSeed.pushButton_no.clicked.connect(self._setRefindSeed)
        accept = self._inputDialog.exec_()

        return accept, self._refindSeed

    def findCandidateAortaSeeds(self, slice):
        """ Request the number of candidates from the user, generate a mask of the candidates and signal.

        :param slice: int
        The slice currently displayed in the main window.
        :return: bool
        True if the user wishes to continue with the process, False otherwise.
        """
        self._requestNumber(slice)
        self._selectCandidateAortaSeeds()
        accept = self._inputDialog.exec_()

        if accept == QtGui.QDialog.Accepted:
            self._aortaSeed, self._latestMask = self._aifSelector.getAortaSeed()
            print self._aortaSeed
            self.maskReady.emit()
            return True

        return False

    def findAIFvoxels(self, slice):
        """ Request the threshold from the user, generate a mask of the selected AIF voxels and signal.

        :param slice: int
        The slice displayed on the main window
        :return:
        """
        # request the threshold for the candidate voxels from the user
        details = 'A score has been calculated for each voxel in the aorta mask using the maxInt and baseline maps. ' \
                  'The voxels with the highest score have been selected. ' \
                  'Adjust the threshold until only a small number of voxels remains. ' \
                  'The software will then choose the largest contiguous patch.'
        self._requestThreshold(self._selectCandidateAIFVoxels, "Threshold for AIF voxels", details, slice)
        self._selectCandidateAIFVoxels()
        accept = self._inputDialog.exec_()

        if accept == QtGui.QDialog.Accepted:
            # Select a patch of voxels for the AIF
            self._aifSelector.setCandidateAIFvoxelsMask(self._latestMask)
            self._latestMask = self._aifSelector.pickAIFpatch()
            self.maskReady.emit()

    def floodfillFromSeed(self, slice):
        """ Request the threshold from the user, generate and aorta mask and signal.

        :param slice: int
        The slice displayed on the main window
        :return: bool
        True if teh user wishes to continue with the process, False otherwise
        """
        details = 'A flood fill has been performed from the aorta seed. ' \
                  'The voxels with intensity above the threshold have been selected. ' \
                  'Adjust the threshold until only the aorta is selected. '
        self._requestThreshold(self._generateAortaMaskFromThreshold, "Threshold for AortaMask", details, slice)
        self._generateAortaMaskFromThreshold()
        accept = self._inputDialog.exec_()

        if accept == QtGui.QDialog.Accepted:
            self._generateAortaMaskFromThreshold()
            self._aifSelector.setAortaMask(self._latestMask)
            return True

        return False

    def _generateAortaMaskFromThreshold(self):
        """ Get the user input threshold, floodfill from the seed, signal that new aorta mask is ready.

        :return:
        """
        threshold = self._thresholdInput.spinBox_thresh.value()
        fraction = threshold / 100.0
        self._latestMask = self._aifSelector._floodfillAorta(self._aortaSeed, fraction)
        self.maskReady.emit()

    def _requestNumber(self, slice):
        """ Build the dialogue that allows the user to set the number and updates the main window with the new mask

        :param slice: int
        The current slice displayed on the main window.
        :return:
        """
        mapSize = np.size(self._mapGenerator.baselineMap());
        self._inputDialog = QtGui.QDialog()
        self._numberInput = NumberInput.Ui_NumberInput()
        self._numberInput.setupUi(self._inputDialog)
        self._numberInput.slider_thresh.valueChanged.connect(self._selectCandidateAortaSeeds)
        max = mapSize/100
        self._numberInput.slider_thresh.setMaximum(max)
        self._numberInput.spinBox_thresh.setMaximum(max)
        self._numberInput.spinBox_thresh.setValue(500)
        self._numberInput.slider_thresh.setValue(500)
        self._numberInput.slider_slice.setMaximum(self._mapGenerator.getNz())
        self._numberInput.slider_slice.valueChanged.connect(self._sliceChanged)
        self._numberInput.slider_slice.setValue(slice)
        self._numberInput.spinBox_slice.setValue(slice)
        self._numberInput.spinBox_slice.setMaximum(self._mapGenerator.getNz())
        details = 'The highest n voxels in the maxInt map have been selected. ' \
                  'Change n (the number of candidates) to ensure voxels in the aorta are selected. ' \
                  'The Software will pick out an aorta seed from these voxels.'
        self._numberInput.label_description.setText(details)

    def _requestThreshold(self, changeFn, title, details, slice):
        """ Build the dialogue that allows the user to set the threshold and updates the main window with the new mask

        :param slice: int
        The current slice displayed on the main window.
        :return:
        """
        self._inputDialog = QtGui.QDialog()
        self._thresholdInput = ThresholdInput.Ui_ThresholdInput()
        self._thresholdInput.setupUi(self._inputDialog)
        self._thresholdInput.slider_thresh.valueChanged.connect(changeFn)
        self._inputDialog.setWindowTitle(title)
        self._thresholdInput.slider_slice.setMaximum(self._mapGenerator.getNz())
        self._thresholdInput.slider_slice.valueChanged.connect(self._sliceChanged)
        self._thresholdInput.slider_slice.setValue(slice)
        self._thresholdInput.spinBox_slice.setMaximum(self._mapGenerator.getNz())
        self._thresholdInput.spinBox_slice.setValue(slice)
        self._thresholdInput.label_details.setText(details)

    def _selectCandidateAIFVoxels(self):
        """ Generate the candidate AIF voxel mask using the threshold and signal

        :return:
        """
        threshold = self._thresholdInput.spinBox_thresh.value()
        fraction = threshold / 100.0
        self._latestMask = self._aifSelector.generateCandidateAIFvoxelsMask(fraction)
        self.maskReady.emit()

    def _selectCandidateAortaSeeds(self):
        """ Generate a mask of of n candidate aorta seeds and signale

        :return:
        """
        nCandidates = self._numberInput.spinBox_thresh.value()
        self._latestMask = self._aifSelector.findCandidateAortaSeeds(nCandidates)
        self.maskReady.emit()

    def _setRefindSeed(self):
        """ Set _refindSeed to True.

        :return:
        """
        self._refindSeed = True

    def _sliceChanged(self, slice):
        """ Emit slice changed signal.

        :param slice:
        :return:
        """
        self.sliceChanged.emit(slice)