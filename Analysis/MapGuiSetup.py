from Analysis import AnalysisInput, MapGenerator

__author__ = 'medabana'

from PySide import QtGui, QtCore

from MapGenerator import MapGenerator

class MapGuiSetup(QtCore.QObject):
    """ Responsible for getting the information required for map generation from the dynamic data and communicating the
    results to the main GUI. """
    timeChanged = QtCore.Signal(int)
    mapReady = QtCore.Signal()

    def __init__(self, parent=None):
        super(MapGuiSetup, self).__init__(parent)
        self._nt = 0
        self._currTime = 0
        self._input = None
        self._baselineNumInput = None
        self._mapGenerator = MapGenerator()
        self._latestMap = None
        self._latestMapName = None

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

    def calcMaxIntMap(self):
        """ Calculate the maximum intensity map.

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
        return True

    def calcMeanBaseline(self):
        """ Calculate the mean of the pre-contrast baseline images

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
        return True

    def calcAndSignalMaxIntMap(self):
        """ Calculates the maximum intensity map and signals when it is ready.

        :return:
        """
        isMap = self.calcMaxIntMap()

        if isMap:
            self.mapReady.emit()

    def calcAndSignalMeanBaselineMap(self):
        """ Calculates the baseline map and signals when it is ready.

        :return:
        """
        isMap = self.calcMeanBaseline()

        if isMap:
            self.mapReady.emit()

    def _requestBaseline(self):
        """ Builds Dialog for requesting the number of pre-contrast images from the user

        :return:
        """
        self._input = QtGui.QDialog()
        self._baselineNumInput = AnalysisInput.Ui_Dialog()
        self._baselineNumInput.setupUi(self._input)
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

