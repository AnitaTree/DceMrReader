__author__ = 'medabana'

import numpy as np

class MapGenerator():
    " Generates Maps from the dynamic series"
    def __init__(self):
        self.reset()

    def baselineMap(self):
        """ Generates an map of average baseline (pre-contrast) intensity.

        :return: np.array
        The baseline map.
        """
        if self._baselineMap is not None:
            return self._baselineMap

        if self._dynamics is None:
            print "No data"
            return

        nz, ny, nx = self._dims
        map = np.zeros([nz, ny, nx])
        for i in range(0, nz):
            startIndex = i*self._nt
            map[i, :, :] = np.mean(self._dynamics[startIndex:(startIndex+self._numBaseline), :, :], axis=0)

        self._baselineMap = map
        return map

    def getNumBaseline(self):
        return self._numBaseline

    def getNz(self):
        """ Returns the number of slices.

        :return: int
        """
        return self._dims[0]

    def getDynamics(self):
        return self._dynamics

    def isNumBaselineSet(self):
        """ Checks whether the number of baseline timepoints (pre-contrast) is known.

        :return: bool
        True if known, False otherwise
        """
        return self._numBaseline is not None

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

        :return:
        """
        if self._dynamics is None:
            print "No data"
            return

        if self._minIntMap == None:
            nz, ny, nx = self._dims
            self._minIntMap = np.zeros([nz, nx, ny])
            for i in range(0, nz):
                startIndex = i*self._nt
                slice = self._dynamics[startIndex+self._numBaseline:(startIndex+self._nt), :, :]
                self._minIntMap[i, :, :] = np.amin(slice, axis=0)

    def reset(self):
        """ Reset the state of the object.

        :return:
        """
        self._dynamics = None
        self._dims = None
        self._nt = None
        self._maxIntMap = None
        self._timeToPeakMap = None
        self._baselineMap = None
        self._numBaseline = None
        self._scoreMap = None
        self._minIntMap = None
        self._zerosMap = None

    def scoreMap(self):
        return self._scoreMap

    def setDynamics(self, dyn, nt):
        """ Sets the dynamic images.

        :param dyn: np.array
        3D data array
        :param nt: int
        number of timepoints
        :return:
        """
        self._dynamics = dyn
        [nzt, ny, nx] = dyn.shape
        self._dims = [nzt / nt, ny, nx]
        self._nt = nt

    def setNumBaseline(self, base):
        """ Sets the number of baseline images.

        :param base: int
        The number od pre-contrast images
        :return:
        """
        self._numBaseline = base

    def setScoreMap(self, map):
        self._scoreMap = map

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
        """ Generate the time to peak and maximum intensity maps from the time series

        :return:
        """
        if self._dynamics is None:
            print "No data"
            return

        nz, ny, nx = self._dims
        self._maxIntMap = np.zeros([nz, nx, ny])
        self._timeToPeakMap = np.zeros([nz, nx, ny])
        for i in range(0, nz):
            startIndex = i*self._nt
            baseMap = np.mean(self._dynamics[startIndex:(startIndex+self._numBaseline), :, :], axis=0)
            baseMapAllTime = np.tile(baseMap, (self._nt-self._numBaseline, 1, 1))
            slice = self._dynamics[startIndex+self._numBaseline:(startIndex+self._nt), :, :] - baseMapAllTime
            # slicePre = self._dynamics[startIndex:startIndex+self._numBaseline, :, :] - np.tile(baseMap, (self._numBaseline, 1, 1))
            slice = slice.clip(min=0) #remove negative values after subtraction
            # slicePre = slicePre.clip(min=0) #remove negative values after subtraction
            self._maxIntMap[i, :, :] = np.amax(slice, axis=0)
            ttp = np.argmax(slice, axis=0)
            # ttp[np.amax(slicePre, axis=0) > np.amax(slice, axis=0)*0.33] = self._nt
            self._timeToPeakMap[i, :, :] = ttp
            # print np.count_nonzero(ttp == self._nt)
        # maxInt = np.amax(self._maxIntMap)
        # self.minimumIntensityMap()
        # self._maxIntMap[self._minIntMap == 0.0] = 0
        # self._maxIntMap[np.logical_and(self._minIntMap == 0.0, self._maxIntMap > maxInt*0.75)] = 0

    def getZerosMap(self):
        if self._zerosMap == None:
            self.minimumIntensityMap()
            nz, ny, nx = self._dims
            self._zerosMap = np.zeros([nz, nx, ny])
            self._zerosMap[self._minIntMap == 0.0] = 1
        return self._zerosMap