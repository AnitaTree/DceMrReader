__author__ = 'medabana'

import unittest

import numpy as np

from ModelFitting.TwoCFM_pmi import TwoCFM_pmi

class TwoCFMpmiTest(unittest.TestCase):
    def testA(self):
        aif_pre = np.ones(5) * 10
        aif_firstPass = np.concatenate([range(10, 51, 20), range(55, 14, -20)])
        aif_tail = np.ones(15) * 14
        aif = np.array(np.concatenate([aif_pre, aif_firstPass, aif_tail]))
        nt = aif.shape[0]
        time = np.array(range(0, 2*(nt-1), 2))
        params = [0.3, 10, 0.5, 0.3]
        model = TwoCFM_pmi()
        ct = model.generateCurve(time, aif, params)

        print ct

        # res = np.array([0., 8.64664717, 9.81684361, 9.97521248, 9.99664537,
        #                 9.999546, 28.64658573, 48.46348246, 54.45371676, 36.27942143,
        #                 16.52650369, 14.27425745, 14.03711671, 14.0050232, 14.00067982,
        #                 14.000092, 14.00001245, 14.00000169, 14.00000023, 14.00000003,
        #                 14., 14., 14., 14., 14.])
        #
        # np.testing.assert_allclose(ct, res)

if __name__ == "__main__":
    unittest.main()