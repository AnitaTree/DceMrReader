__author__ = 'medabana'

import numpy as np

class ImageSeries():
    def __init__(self, data, dims):
        self._data = data
        self.nx = dims[0]
        self.ny = dims[0]
        self.nz = dims[0]
        self.nt = dims[0]

    def getTimepoint(self, i):
        return self._data[self.nz*i, :, :]