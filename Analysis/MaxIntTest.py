__author__ = 'medabana'

import unittest

import numpy as np

from Analysis.MapGenerator import Analysis


class MaxIntTest(unittest.TestCase):
    def test_simple1(self):
        a = range(0, 50*3*3)
        a = np.reshape(a, [50, 3, 3])

        xx = Analysis()
        xx.setData(a)
        mp = xx.maximumIntensityMap(3, 3, 5, 10)

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

        b = np.concatenate((a, a+1, a+2, a+3))

        xx = Analysis()
        xx.setData(b)
        mp = xx.maximumIntensityMap(3, 3, 4, 10)

        expectedDims = [4, 3, 3]

        np.testing.assert_array_equal(expectedDims, np.shape(mp))

        for i in range(0, 4):
            np.testing.assert_array_equal(i+5, mp[i, :, :])

if __name__ == "__main__":
    unittest.main()