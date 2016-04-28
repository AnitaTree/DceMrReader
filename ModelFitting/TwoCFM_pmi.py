__author__ = 'medabana'

import numpy as np

class TwoCFM_pmi:
    def __init__(self):
        pass


    def _expConvolution(self, k, time, aif):
        n = time.shape[0]
        dt = time[1:n] - time[0:n-1]
        da = aif[1:n] - aif[0:n-1]
        z = k * dt

        expTerm = np.exp(-z)
        expTerm0 = 1 - expTerm
        expTerm1 = z - expTerm0
        expTerm2 = z**2-2*expTerm1

        il = np.array((aif[0:n-1]*expTerm0 + da*expTerm1/z) / 1)

        y = np.zeros(n)
        for i in range(0, n-1):
            y[i+1] = expTerm[i]*y[i] + il[i]

        dil = -dt*il + (aif[0:n-2]*expTerm1 + da*expTerm2/z )/(k ^ 2)
        dil = -expTerm0*dt*y + dil

        dy = np.zeros(n)

        for i in range(0, n-1):
            dy[i+1] = expTerm0[i]*dy[i] + dil[i]
            return y, dy


    def generateCurve(self, time, aif, params):
        n = time.shape[0]
        KP = params[1]/(params[0]*(1-params[2]))
        KE = params[3]*params[1]/(params[0]*params[2])
        A = 1/(1+1/params[3]-1/params[2])

        convP, dconvP = self._expConvolution(KP, time, aif)
        convE, dConvE = self._expConvolution(KE, time, aif)

        ct = params[1]*(1-A)*convP + params[1]*A*convE
        return ct

# Pro SingleInletFiltration, X, P, C, C_DER
#
# 	if n_params() eq 0 then return
#
# 	ni=X[0] & n=n_elements(X[ni+1:*])/2
# 	ti=X[1:ni] & time=X[ni+1:ni+n] & input=X[ni+n+1:*]
#
# 	KP = P[1]/(P[0]*(1-P[2]))
# 	KE = P[3]*P[1]/(P[0]*P[2])
# 	A = 1/(1+1/P[3]-1/P[2])
#
# 	convP = ExpConvolution(KP,[time,input],Der=dconvP)
# 	convE = ExpConvolution(KE,[time,input],Der=dconvE)
#
# 	C = P[1]*(1-A)*convP[ti] + P[1]*A*convE[ti]
#
# 	IF n_params() LT 4 THEN return
#
# 	;Derivatives wrt model parameters
#
# 	dKP0 = -P[1]/(P[0]^2*(1-P[2]))
# 	dKP1 = 1/(P[0]*(1-P[2]))
# 	dKP2 = P[1]/(P[0]*(1-P[2])^2)
#
# 	dKE0 = -P[3]*P[1]/(P[0]^2*P[2])
# 	dKE1 = P[3]/(P[0]*P[2])
# 	dKE2 = -P[3]*P[1]/(P[0]*P[2]^2)
# 	dKE3 = P[1]/(P[0]*P[2])
#
# 	dA2 = -(A/P[2])^2
# 	dA3 = (A/P[3])^2
#
# 	dC0 = P[1]*(1-A)*dconvP[ti]*dKP0 + P[1]*A*dconvE[ti]*dKE0
# 	dC1 = (1-A)*convP[ti] + A*convE[ti] + P[1]*(1-A)*dconvP[ti]*dKP1 + P[1]*A*dconvE[ti]*dKE1
# 	dC2 = P[1]*(1-A)*dconvP[ti]*dKP2 - P[1]*dA2*convP[ti] + P[1]*A*dconvE[ti]*dKE2 + P[1]*dA2*convE[ti]
# 	dC3 = -P[1]*dA3*convP[ti] + P[1]*A*dconvE[ti]*dKE3 + P[1]*dA3*convE[ti]
#
# 	C_DER = [[dC0],[dC1],[dC2],[dC3]]
# end

#
# function IntVector, X, Y
#
# 	n = n_elements(Y)
# 	Z = (Y[1:n-1]+Y[0:n-2]) * (X[1:n-1]-X[0:n-2]) / 2
#
# 	Int = dblarr(n)
#
# 	Int[1] = Z[0] & for i=2L,n-1 do Int[i] = Int[i-1] + Z[i-1]
#
# ;	Int[1:n-1] = total(Z,/cumulative)
#
# 	return, Int
#
#
# end
#
# function ExpConvolution, l, X, Der=DY
#
# 	n = n_elements(X)/2
# 	Y = dblarr(n)
#
# 	if finite(l) eq 0 then begin	;Bug corrected on 25/06/2012 (SPS)
# 		if arg_present(DY) then DY=Y
# 		return, Y
# 	endif
#
# 	T = X[0:n-1]
# 	A = X[n:*]
#
# 	DT = T[1:n-1]-T[0:n-2]
# 	DA = A[1:n-1]-A[0:n-2]
#
# 	Z = l*DT
#
# 	E = exp(-Z)
# 	E0 = 1-E
# 	E1 = Z-E0
#
# 	Il = (A[0:n-2]*E0 + DA*E1/Z)/l
#
# 	for i=0L,n-2 do Y[i+1] = E[i]*Y[i] + Il[i]
#
# 	if not arg_present(DY) then return, Y
#
# 	E2 = Z^2-2*E1
#
#     DIl = -DT*Il + (A[0:n-2]*E1 + DA*E2/Z )/(l^2)
#     DIl = -E*DT*Y + DIl
#
# 	DY = dblarr(n)
#
# 	for i=0L,n-2 do DY[i+1] = E[i]*DY[i] + DIl[i]
#
# 	return, Y
# end