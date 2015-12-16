from Analysis import AcceptSeed, ThresholdInput, NumberInput
from Analysis import AnalysisInput

__author__ = 'medabana'

from PySide import QtGui, QtCore
import numpy as np

from Analysis import AifCurve
from Analysis.AIFselector import AIFselector

class AIFguiSetup(QtCore.QObject):
    """ Responsible for getting the information required for each of the analysis procedures and communicating the
    results to the main GUI. """
    maskReady = QtCore.Signal(int)
    sliceChanged = QtCore.Signal(int)

    def __init__(self, maps, parent=None):
        super(AIFguiSetup, self).__init__(parent)
        self._thresholdInput = None
        self._inputDialog = None
        self._numberInput = None
        self._aifSelector = AIFselector(maps)
        self._mapGenerator = maps
        self._latestMask = None
        self._aortaSeed = None

    def getAIFdata(self):
        return self._aifSelector.getAIFcurve()

    def getLatestMask(self):
        """ Return the last binary mask generated.

        :return: np.array(dtype = np.bool)
        """
        return self._latestMask

    def findCandidateAortaSeedAuto(self):
        self._aortaSeed, self._latestMask = self._aifSelector.findCandidateAortaSeed(3, 13)

    def findCandidateAortaSeeds(self, slice):
        """ Request the number of candidates from the user, generate a mask of the candidates and signal.

        :param slice: int
        The slice currently displayed in the main window.
        :return: bool
        True if the user wishes to continue with the process, False otherwise.
        """
        self._requestKernelSize(slice)
        self._selectCandidateAortaSeed()
        accept = self._inputDialog.exec_()

        if accept == QtGui.QDialog.Accepted:
            # self._aortaSeed, self._latestMask = self._aifSelector.getAortaSeed()
            # print self._aortaSeed
            # self.maskReady.emit()
            return True

        return False

    def findAIFvoxelsAuto(self, useKernel, fraction):
        # min = 5
        # self._latestMask = self._aifSelector.findAIFpatchBinaryChop(useKernel, min)
        if useKernel:
            self._latestMask = self._aifSelector.findAIFthreshold(useKernel, fraction)
        else:
            self._latestMask = self._aifSelector.findAIFthreshold(useKernel, fraction)

        z, x, y = np.where(self._latestMask == True)
        self.maskReady.emit(z[0]+1)
        aif, aifMeasures = self._aifSelector.getAIFcurve()
        self._displayAIF(aif)

    def findAIFvoxelsMinNumber(self, useKernel, min = 5):
        # if not useKernel:
        #     self._requestNumber()
        #     accept = self._input.exec_()
        #     if accept == QtGui.QDialog.Rejected:
        #         return
        #     else:
        #         min = self._mininumVoxelInput.spinBox.value()
        self._latestMask = self._aifSelector.findAIFpatchBinaryChop(useKernel, min)
        z, x, y = np.where(self._latestMask == True)
        self.maskReady.emit(z[0]+1)
        aif, aifMeasures = self._aifSelector.getAIFcurve()
        self._displayAIF(aif)

    def findAIFvoxelsUser(self, slice):
        """ Request the threshold from the user, generate a mask of the selected AIF voxels and signal.
        Display the AIF curve.

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
            z, x, y = np.where(self._latestMask == True)
            self.maskReady.emit(z[0]+1)
            aif, aifMeasures = self._aifSelector.getAIFcurve()
            self._displayAIF(aif)

    # def floodfillFromSeed(self, slice):
    #     """ Request the threshold from the user, generate and aorta mask and signal.
    #
    #     :param slice: int
    #     The slice displayed on the main window
    #     :return: bool
    #     True if teh user wishes to continue with the process, False otherwise
    #     """
    #     details = 'A flood fill has been performed from the aorta seed. ' \
    #               'The voxels with intensity above the threshold have been selected. ' \
    #               'Adjust the threshold until only the aorta is selected. '
    #     self._requestThreshold(self._generateAortaMaskFromThreshold, "Threshold for AortaMask", details, slice)
    #     self._generateAortaMaskFromThreshold()
    #     accept = self._inputDialog.exec_()
    #
    #     if accept == QtGui.QDialog.Accepted:
    #         self._generateAortaMaskFromThreshold()
    #         self._aifSelector.setAortaMask(self._latestMask)
    #         return True
    #
    #     return False

    def floodfillFromSeed(self, slice):

        self._latestMask = self._aifSelector.floodFillAortaToNumVoxels(self._aortaSeed)
        self._aifSelector.setAortaMask(self._latestMask)
        z, x, y = np.where(self._latestMask == True)
        sliceNum = z[z.shape[0]/2] + 1
        self.maskReady.emit(sliceNum)

        return True


    def reset(self):
        """ Reset state of object.

        :return:
        """
        self._thresholdInput = None
        self._inputDialog = None
        self._numberInput = None
        self._aifSelector.reset()
        self._mapGenerator.reset()
        self._latestMask = None
        self._aortaSeed = None

    def _displayAIF(self, aif):
        """ Display the AIF to the user.
        :param aif: np.array
        Value of the AIF at each timepoint
        :return:
        """
        self._curveWidget = QtGui.QWidget()
        self._curveDisplay = AifCurve.Ui_AifView()
        self._curveDisplay.setupUi(self._curveWidget)
        self._curveDisplay.plotWidget.plot(aif)
        g = self._curveWidget.geometry()
        g.moveTo(900, 300)
        self._curveWidget.setGeometry(g)
        self._curveWidget.show()

    def _generateAortaMaskFromThreshold(self):
        """ Get the user input threshold, floodfill from the seed, signal that new aorta mask is ready.

        :return:
        """
        threshold = self._thresholdInput.spinBox_thresh.value()
        fraction = threshold / 100.0
        self._latestMask = self._aifSelector._floodfillAorta(self._aortaSeed, fraction)
        z, x, y = np.where(self._latestMask == True)
        self.maskReady.emit(self._thresholdInput.spinBox_slice.value())

    def _requestKernelSize(self, slice):
        """ Build the dialogue that allows the user to set the number and updates the main window with the new mask

        :param slice: int
        The current slice displayed on the main window.
        :return:
        """
        map = self._mapGenerator.baselineMap()
        mapShape = map.shape
        self._inputDialog = QtGui.QDialog()
        self._numberInput = NumberInput.Ui_NumberInput()
        self._numberInput.setupUi(self._inputDialog)
        g = self._inputDialog.geometry()
        g.moveTo(900, 300)
        self._inputDialog.setGeometry(g)
        self._numberInput.slider_xKernel.valueChanged.connect(self._selectCandidateAortaSeed)
        self._numberInput.slider_yKernel.valueChanged.connect(self._selectCandidateAortaSeed)
        self._numberInput.slider_slice.setMaximum(self._mapGenerator.getNz())
        self._numberInput.slider_slice.valueChanged.connect(self._sliceChanged)
        self._numberInput.slider_slice.setValue(slice)
        self._numberInput.spinBox_slice.setValue(slice)
        self._numberInput.spinBox_slice.setMaximum(self._mapGenerator.getNz())
        self._numberInput.spinBox_xKernel.setMaximum(mapShape[2])
        self._numberInput.slider_xKernel.setMaximum(mapShape[2])
        self._numberInput.spinBox_yKernel.setMaximum(mapShape[1])
        self._numberInput.slider_yKernel.setMaximum(mapShape[1])
        self._numberInput.slider_xKernel.setValue(3)
        self._numberInput.slider_yKernel.setValue(13)
        details = 'The selected aorta seed is shown (single voxel). ' \
                  'Change the size of the kernel used to assess each voxel. ' \
                  'The Software will then flood fill the aorta from this seed.'
        self._numberInput.label_description.setText(details)

    def _requestNumber(self):
        """ Builds Dialog for requesting the minimum number of voxels

        :return:
        """
        self._input = QtGui.QDialog()
        self._mininumVoxelInput = AnalysisInput.Ui_Dialog()
        self._mininumVoxelInput.setupUi(self._input)
        g = self._input.geometry()
        g.moveTo(900, 300)
        self._input.setGeometry(g)
        self._input.setWindowTitle('Minimum number of AIF Voxels')
        self._mininumVoxelInput.spinBox.setMinimum(1)
        self._mininumVoxelInput.spinBox.setMaximum(1000)
        self._mininumVoxelInput.spinBox.setValue(5)
        self._mininumVoxelInput.label.setText("Minimum number of voxels")

    def _requestThreshold(self, changeFn, title, details, slice):
        """ Build the dialogue that allows the user to set the threshold and updates the main window with the new mask

        :param slice: int
        The current slice displayed on the main window.
        :return:
        """
        self._inputDialog = QtGui.QDialog()
        self._thresholdInput = ThresholdInput.Ui_ThresholdInput()
        self._thresholdInput.setupUi(self._inputDialog)
        g = self._inputDialog.geometry()
        g.moveTo(900, 300)
        self._inputDialog.setGeometry(g)
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
        self._latestMask = self._aifSelector._generateCandidateAIFvoxelsMask(fraction)
        z, x, y = np.where(self._latestMask == True)
        self.maskReady.emit(self._thresholdInput.spinBox_slice.value())

    def _selectCandidateAortaSeed(self):
        """ Generate a mask of of n candidate aorta seeds and signal

        :return:
        """
        kernel_x = self._numberInput.spinBox_xKernel.value()
        kernel_y = self._numberInput.spinBox_yKernel.value()
        self._aortaSeed, self._latestMask = self._aifSelector.findCandidateAortaSeed(kernel_x, kernel_y)
        z, x, y = np.where(self._latestMask == True)
        self.maskReady.emit(z[0]+1)
        # seed, mask = self._aifSelector.getAortaSeed()
        self._numberInput.slider_slice.setValue(self._aortaSeed[0]+1)
        self._numberInput.spinBox_slice.setValue(self._aortaSeed[0]+1)

    def _sliceChanged(self, slice):
        """ Emit slice changed signal.

        :param slice:
        :return:
        """
        self.sliceChanged.emit(slice)