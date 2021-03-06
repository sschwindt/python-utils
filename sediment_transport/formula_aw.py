#!/usr/bin/python
import sys, os
import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sed_data import GrainInfo

class AW:
    # computes solid transport according to Ackers and White formula.
    def __init__(self, input_dir):
        self.grains = GrainInfo(input_dir)
        self.grains()
        self.taux = np.nan
        self.taux_cr = 0.047
        self.g = 9.81
        self.s = 2.68
        self.nu = 10 ** (-6)
        self.warnings = []
        self.hMorph = np.nan
        print(' * loaded solid transport formulae from Ackers and White (1973)')

    def check_validity(self, J, D, Q, h, Fr, k):
        warning_msg = ''
        if Fr > 0.8:
            warning_msg = 'Warning: Froude number too large.'
            print(warning_msg+' (Q = {0} m3/s, D = {1} m)'.format(Q,D))

        if self.grains.D35[k] < 0.00004 or self.grains.D35[k] > 0.004:
            warning_msg = 'Warning: D35 out of validity range.'
            print(warning_msg+' (Q = {0} m3/s)'.format(Q))
        return warning_msg

    def compute_AW(self, Di, Rh, u, J):
        nw, mw, Aw, Cw = self.get_coefficients(Di)
        ux = np.sqrt(self.g * Rh * J)

        Fgr = ux ** nw / np.sqrt((self.s - 1) * self.g * Di) * (u / (np.sqrt(32) * np.log(10 * Rh / Di))) ** (1 - nw)
        try:
            if Aw < Fgr:
                Ggr = Cw * (Fgr / Aw - 1) ** mw
                __Qsx = Ggr * Di / Rh * (u / ux) ** nw
            else:
                __Qsx = np.nan
        except:
            __Qsx = np.nan
        return __Qsx

    def compute_hmorph(self, J, iD, kst):
        # computation of the Hydraulic Radius for incipient grain motion based on Dm
        # not implemented at this point
        _qmorph = -1
        _h=0
        Di = self.grains.Dm[iD]
        nw, mw, Aw, Cw = self.get_coefficients(Di)
        try:
            while _qmorph <= 0:
                _h = _h + 0.0001
                _Rh = _h
                _ux = np.sqrt(self.g * _Rh * J)
                _u = kst * _Rh ** (2 / 3) * J ** (1 / 2)
                Fgr = _ux ** nw / np.sqrt((self.s - 1) * self.g * Di) * (_u / (np.sqrt(32) * np.log(10 * _h / Di))) ** (1 - nw)
                try:
                    Ggr = Cw * (Fgr / Aw - 1) ** mw
                except:
                    Ggr = 0.0
                _qmorph = Ggr
        except:
            _h = 0
        _hMorph = _h
        return _hMorph

    def get_coefficients(self, Di):
        Dx = (((self.s - 1) * self.g) / self.nu ** 2) ** (1 / 3) * Di

        if Dx <= 60:
            if Dx < 1:
                nw = 1.
            else:
                nw = 1 - 0.56 * np.log(Dx)
            mw = 6.83 / Dx + 1.67
            Aw = 0.23 * Dx ** (-1 / 2) + 0.14
            Cw = 10 ** (2.79 * np.log(Dx) - 0.98 * (np.log(Dx)) ** 2 - 3.46)
        else:
            nw = 0.
            mw = 1.78
            Aw = 0.17
            Cw = 0.025
        return nw, mw, Aw, Cw

    def __call__(self, J, Q, RhL, RhC, RhR, wL, wC, wR, uL, uC, uR, Fr, k):
        _Qs = np.nan
        msg = self.check_validity(J, self.grains.D35[k], Q, RhC, Fr, k)
        if not(np.isnan(self.grains.D35[k])):
            if len(msg) < 1:
                _QsxL = self.compute_AW(self.grains.D35[k], RhL, uL, J) * wL / 2
                _QsxC = self.compute_AW(self.grains.D35[k], RhC, uC, J) * wC
                _QsxR = self.compute_AW(self.grains.D35[k], RhR, uR, J) * wR / 2
                _Qs = (_QsxL + _QsxC + _QsxR) * np.sqrt(self.g * (self.s - 1) * self.grains.Dm[k] ** 3) * self.s * 1000
                if _Qs < 0:
                    _Qs = 0
        return _Qs


