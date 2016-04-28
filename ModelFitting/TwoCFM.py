__author__ = 'medabana'

import numpy as np

class TwoCFM():
    def __init__(self):
        pass

    def generateCurve(self, time, aif, params):
        n = time.shape[0]
        fp = params[0]
        tp = params[1]
        ps = params[2]
        te = params[3]
        vp = fp * tp
        ve = ps * te

        ct = np.zeros(n)

        if fp == 0:
            return ct

        t = (vp + ve) / fp

        tPos = te
        tNeg = tp

        if tPos == tNeg:
            ct = fp * tPos * self._expConv(tPos, time, aif)
        else:
            ePos = (t - tNeg) / (tPos - tNeg)
            eNeg = 1 - ePos
            ct = (fp * ePos * tPos * self._expConv(tPos, time, aif)
                    + fp * eNeg * tNeg * self._expConv(tNeg, time, aif))

        return ct

    def _expConv(self, t, time, aif):
        if t == 0:
            return aif

        n = time.shape[0]
        f = np.zeros(n)
        x = (time[1:n] - time[0:n-1]) / t
        da = (aif[1:n] - aif[0:n-1]) / x

        expTerm = np.exp(-x)
        exp0 = 1 - expTerm
        exp1 = x - expTerm

        addTerm = aif[0:n-1]*exp0 + da*exp1

        for i in range(0, n-1):
            f[i+1] = expTerm[i]*f[i] + addTerm[i]

        return f