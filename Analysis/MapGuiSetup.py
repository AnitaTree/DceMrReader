from Analysis import AnalysisInput, MapGenerator

__author__ = 'medabana'

from PySide import QtGui, QtCore

from MapGenerator import MapGenerator

class MapGuiSetup(QtCore.QObject):
    """ Responsible for getting the information required for map generation from the dynamic data and communicating the
    results to the main GUI. """
    timeChanged = QtCore.Signal(int)
    mapReady = QtCore.Signal(int)

    def __init__(self, parent=None):
        super(MapGuiSetup, self).__init__(parent)
        self._mapGenerator = MapGenerator()
        self.reset()

    def getDynamics(self):
        """ Return the dynamic series.

        :return: np.bool double
        Dynamic series.
        """
        return self._mapGenerator.getDynamics()

    def getLatestMap(self):
        """ Return the last map generated.

        :return: np.array(np.bool)
        Boolean mask
        """
        return self._latestMap

    def getLatestMapName(self):
        """ Return the name of the last map generated

        :return: string
        map name
        """
        return self._latestMapName

    def getMapGenerator(self):
        """ Return the object used for generating the maps
        :return: MapGenerator
        """
        return self._mapGenerator

    def getMaxIntMap(self, giveSignal = True):
        """ Calculate the maximum intensity map and signal if requested.

        Request the number of pre-contrast baseline images if not already known.
        :return: bool
        True if the user wishes to continue, False otherwise.
        """
        if not self._mapGenerator.isNumBaselineSet():
            self._requestBaseline()
            accept = self._input.exec_()

            if accept == QtGui.QDialog.Accepted:
                self._mapGenerator.setNumBaseline(self._baselineNumInput.spinBox.value())
            else:
                return False

        self._latestMap = self._mapGenerator.maximumIntensityMap()
        self._latestMapName = 'Maximum Intensity Map'

        if giveSignal:
            self.mapReady.emit(1)

        return True

    def getMeanBaselineMap(self, giveSignal = True):
        """ Calculate the mean of the pre-contrast baseline images and signal if requested.

        Request the number of pre-contrast baseline images if not already known.
        :return: bool
        True if the user wishes to continue, False otherwise.
        """
        if not self._mapGenerator.isNumBaselineSet():
            self._requestBaseline()
            accept = self._input.exec_()

            if accept == QtGui.QDialog.Accepted:
                self._mapGenerator.setNumBaseline(self._baselineNumInput.spinBox.value())
            else:
                return False

        self._latestMap = self._mapGenerator.baselineMap()
        self._latestMapName = 'Mean Baseline Map'

        if giveSignal:
            self.mapReady.emit(1)

        return True

    def getNz(self):
        """ Return the number of slices.

        :return: int
        Number of slices.
        """
        return self._mapGenerator.getNz()

    def getTTPMap(self, giveSignal = True):
        """ Calculate the maximum intensity timepoint map and signal if requested.

        Request the number of pre-contrast baseline images if not already known.
        :return: bool
        True if the user wishes to continue, False otherwise.
        """
        if not self._mapGenerator.isNumBaselineSet():
            self._requestBaseline()
            accept = self._input.exec_()

            if accept == QtGui.QDialog.Accepted:
                self._mapGenerator.setNumBaseline(self._baselineNumInput.spinBox.value())
            else:
                return False

        self._latestMap = self._mapGenerator.timeToPeakMap()
        self._latestMapName = 'Maximum Intensity Timepoint Map'

        if giveSignal:
            self.mapReady.emit(1)

        return True

    def getZeroMinIntensityMap(self, giveSignal = True):
        """ Calculate a mask of voxels who have zero minimum signal intensity in their time series and signal if requested.

        :return: np.array bool
        Mask.
        """
        if not self._mapGenerator.isNumBaselineSet():
            self._requestBaseline()
            accept = self._input.exec_()

            if accept == QtGui.QDialog.Accepted:
                self._mapGenerator.setNumBaseline(self._baselineNumInput.spinBox.value())
            else:
                return False

        self._latestMap = self._mapGenerator.getZeroMinIntensityMap()
        self._latestMapName = 'Map of zeros'

        if giveSignal:
            self.mapReady.emit(1)

        return True

    def displayScoreMap(self):
        """ Display the score map generated to find the aorta seed and emit a signal.

        :return:
        """
        self._latestMap = self._mapGenerator.getScoreMap()
        self._latestMapName = 'Aorta seed score maps'
        self.mapReady.emit(1)

    def reset(self):
        """ Reset the state of the object.

        :return:
        """
        self._nt = 0
        self._currTime = 0
        self._input = None
        self._baselineNumInput = None
        self._mapGenerator.reset()
        self._latestMap = None
        self._latestMapName = None

    def setDisplayTimepoint(self, t):
        """ Set the timepoint to be used for any user dialogs

        :param t: int
        time-point
        :return:
        """
        self._currTime = t
        if self._input is not None:
            self._baselineNumInput.spinBox.setValue(t)

    def setDynamics(self, d, nt):
        """ Set the dynamic series from which to derive the maps and
        the number of timepoints.

        :param d: np.array
        3D array [nt x nz, ny, nx]
        :param nt: int
        number of timepoints
        :return:
        """
        self._mapGenerator.setDynamics(d, nt)
        self._nt = nt

    def _requestBaseline(self):
        """ Builds Dialog for requesting the number of pre-contrast images from the user

        :return:
        """
        self._input = QtGui.QDialog()
        self._baselineNumInput = AnalysisInput.Ui_Dialog()
        self._baselineNumInput.setupUi(self._input)
        g = self._input.geometry()
        g.moveTo(900, 300)
        self._input.setGeometry(g)
        self._baselineNumInput.spinBox.setMinimum(1)
        self._baselineNumInput.spinBox.setMaximum(self._nt)
        self._baselineNumInput.spinBox.setValue(self._currTime)
        self._baselineNumInput.spinBox.valueChanged.connect(self._signalTimepointChanged)

    def _signalTimepointChanged(self, t):
        """ Emits the timeChanged signal

        :param t: int
        timepoint
        :return:
        """
        self.timeChanged.emit(t)

