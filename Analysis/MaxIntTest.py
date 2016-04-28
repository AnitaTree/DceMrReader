__author__ = 'medabana'

import unittest

import numpy as np

from Analysis.MapGenerator import MapGenerator

class MaxIntTest(unittest.TestCase):
    def test_simple1(self):
        a = range(0, 50*3*3)
        a = np.reshape(a, [50, 3, 3])
        a[0:41:10, :, :] = 0

        xx = MapGenerator()
        xx.setDynamics(a, 10)
        xx.numBaseline = 1
        mp = xx.maximumIntensityMap()

        expectedDims = [5, 3, 3]

        np.testing.assert_array_equal(expectedDims, np.shape(mp))

        for i in range(0, 5):
            np.testing.assert_array_equal(a[(i*10 + 9), :, :], mp[i, :, :])

    def test_simple2(self):

        a = np.zeros([10, 3, 3])
        for i in range(0, 5):
            a[i, :, :] = i + 1
        for j in range(5, 10):
            a[j, :, :] = i
            i = i - 1

        b = np.concatenate([a, a+1, a+2, a+3])
        b[0:31:10, :, :] = 0

        xx = MapGenerator()
        xx.setDynamics(b, 10)
        xx.numBaseline = 1
        mp = xx.maximumIntensityMap()

        expectedDims = [4, 3, 3]

        np.testing.assert_array_equal(expectedDims, np.shape(mp))

        for i in range(0, 4):
            np.testing.assert_array_equal(i+5, mp[i, :, :])

if __name__ == "__main__":
    unittest.main()