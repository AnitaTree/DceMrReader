__author__ = 'medabana'

import logging
import numpy as np

class MapGenerator():
    " Generates Maps from the dynamic series"
    def __init__(self):
        self.reset()
        self._logger = logging.getLogger(__name__)

    def baselineMap(self):
        """ Generates an map of average baseline (pre-contrast) intensity.
        :return: np.array
        The baseline map.
        """
        if self._baselineMap is not None:
            return self._baselineMap

        if self.dynamics is None:
            print "No data"
            return

        self._logger.info('generating baseline map')
        nz, ny, nx = self.dims
        map = np.zeros([nz, ny, nx])
        for i in range(0, nz):
            startIndex = i*self._nt
            map[i, :, :] = np.mean(self.dynamics[startIndex:(startIndex+self.numBaseline), :, :], axis=0)

        self._baselineMap = map
        return map

    def getNz(self):
        """ Returns the number of slices.
        :return: int
        """
        return self.dims[0]

    def getZeroMinIntensityMap(self):
        """ Return the mask of voxels who have a zero minimum signal intensity.
        :return: np.array bool
        Mask.
        """
        if self._zeroMinIntensityMap == None:
            self.minimumIntensityMap()
            nz, ny, nx = self.dims
            self._zeroMinIntensityMap = np.zeros([nz, nx, ny])
            self._zeroMinIntensityMap[self._minIntMap == 0.0] = 1
        return self._zeroMinIntensityMap

    def isNumBaselineSet(self):
        """ Checks whether the number of baseline timepoints (pre-contrast) is known.
        :return: bool
        True if known, False otherwise
        """
        return self.numBaseline is not None

    def maximumIntensityMap(self):
        """ Generate a map of the maximum intensity if required and return the map.
        :return: np.array
        The maximum intensity map
        """
        if self._maxIntMap is not None:
            return self._maxIntMap

        self._generateMaxMaps()
        return self._maxIntMap

    def minimumIntensityMap(self):
        """ Generate the minimum intensity maps from the time series.
        :return: np.array double
        """
        if self.dynamics is None:
            print "No data"
            return

        if self._minIntMap == None:
            nz, ny, nx = self.dims
            self._minIntMap = np.zeros([nz, nx, ny])
            for i in range(0, nz):
                startIndex = i*self._nt
                slice = self.dynamics[startIndex+self.numBaseline:(startIndex+self._nt), :, :]
                self._minIntMap[i, :, :] = np.amin(slice, axis=0)

    def reset(self):
        """ Reset the state of the object.
        :return:
        """
        self.dynamics = None
        self.dims = None
        self._nt = None
        self._maxIntMap = None
        self._timeToPeakMap = None
        self._baselineMap = None
        self.numBaseline = None
        self.scoreMap = None
        self._minIntMap = None
        self._zeroMinIntensityMap = None

    def setDynamics(self, dyn, nt):
        """ Sets the dynamic images.
        :param dyn: np.array
        3D data array
        :param nt: int
        number of timepoints
        :return:
        """
        self.dynamics = dyn
        [nzt, ny, nx] = dyn.shape
        self.dims = [nzt / nt, ny, nx]
        self._nt = nt

    def timeToPeakMap(self):
        """ Generate the time to peak map, if required and return the map.
        :return: np.array
        The time tp peak map
        """
        if self._timeToPeakMap is not None:
            return self._timeToPeakMap

        self._generateMaxMaps()
        return self._timeToPeakMap

    def _generateMaxMaps(self):
        """ Generate the time to peak and maximum intensity maps from the time series.
        :return:
        """
        if self.dynamics is None:
            print "No data"
            return

        nz, ny, nx = self.dims
        self._maxIntMap = np.zeros([nz, nx, ny])
        self._timeToPeakMap = np.zeros([nz, nx, ny])
        for i in range(0, nz):
            startIndex = i*self._nt
            baseMap = np.mean(self.dynamics[startIndex:(startIndex+self.numBaseline), :, :], axis=0)
            baseMapAllTime = np.tile(baseMap, (self._nt-self.numBaseline, 1, 1))
            slice = self.dynamics[startIndex+self.numBaseline:(startIndex+self._nt), :, :] - baseMapAllTime
            slice = slice.clip(min=0) #remove negative values after subtraction
            self._maxIntMap[i, :, :] = np.amax(slice, axis=0)
            ttp = np.argmax(slice, axis=0)
            self._timeToPeakMap[i, :, :] = ttp