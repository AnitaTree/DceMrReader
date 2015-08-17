__author__ = 'medabana'

import unittest

import numpy as np

from Analysis.MapGenerator import Analysis


class FloodFillTest(unittest.TestCase):
    def test_simple1(self):
        a = range(0, 5*3*3)
        a = np.reshape(a, [5, 3, 3])

        xx = Analysis()
        xx.setData(a)
        mask= np.zeros([5, 3, 3])
        xx._floodfillMask([4, 1, 1], 30, mask)

        print a
        print mask


    def test_simple2(self):
        a = np.zeros([6, 4, 4])
        for i in range(0, 3):
            a[i, 2:4, 2:4] = i + 1
        for j in range(3, 6):
            a[j, 2:4, 2:4] = i
            i -= 1

        xx = Analysis()
        xx.setData(a)
        mask= np.zeros(a.shape)
        xx._floodfillMask([1, 2, 2], 2, mask)

        print a
        print mask

if __name__ == "__main__":
    unittest.main()