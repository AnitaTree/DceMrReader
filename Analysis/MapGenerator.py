__author__ = 'medabana'

import numpy as np

class MapGenerator():
    " Generates Maps from the dynamic series"
    def __init__(self):
        self._dynamics = None
        self._dims = None
        self._nt = None
        self._maxIntMap = None
        self._baselineMap = None
        self._numBaseline = None

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

    def getNz(self):
        """ Returns the number of slices.

        :return: int
        """
        return self._dims[0]

    def isNumBaselineSet(self):
        """ Checks whether the number of baseline timepoints (pre-contrast) is known.

        :return: bool
        True if known, False otherwise
        """
        return self._numBaseline is not None

    def maximumIntensityMap(self):
        """ Generates a map of the maximum intensity value for each voxel during the time series.

        :return: np.array
        The maximum intensity map
        """
        if self._maxIntMap is not None:
            return self._maxIntMap

        if self._dynamics is None:
            print "No data"
            return

        nz, ny, nx = self._dims
        maxMap = np.zeros([nz, nx, ny])
        for i in range(0, nz):
            startIndex = i*self._nt
            baseMap = np.mean(self._dynamics[startIndex:(startIndex+self._numBaseline), :, :], axis=0)
            baseMapAllTime = np.tile(baseMap, (self._nt-self._numBaseline, 1, 1))
            slice = self._dynamics[startIndex+self._numBaseline:(startIndex+self._nt), :, :] - baseMapAllTime
            slice = slice.clip(min=0) #remove negative values after subtraction
            maxMap[i, :, :] = np.amax(slice, axis=0)

        self._maxIntMap = maxMap
        return maxMap

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

