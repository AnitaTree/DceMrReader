__author__ = 'medabana'

import numpy as np
import scipy.ndimage as ndimage


class AIFselector():
    """ Algorithms for selecting AIF voxels. """
    def __init__(self, maps):
        """
        :param maps: MapGenerator
        :return:
        """
        self._mapMaker = maps
        self._resetVariables()

    def findCandidateAortaSeed(self, kernel_nx, kernel_ny):
        """ Generates a mask of candidate aorta seeds.

        A score is calculated for the nCand voxels with highest values in the maxiIntMap.
        The score is derived from the summed value and IQR of a 1 by 5 kernel.
        :param nCand: int
        Number of candidate voxels
        :return: np.array dtype=np.bool
        A mask of the candidate aorta seed voxels
        """
        maxIntMap = self._mapMaker.maximumIntensityMap()
        ttpMap = self._mapMaker.timeToPeakMap()
        zerosMap = self._mapMaker.getZerosMap()
        maxIntMap[zerosMap == 1] = 0
        dyn = self._mapMaker.getDynamics()
        nzt, ny, nx = dyn.shape
        nz = self._mapMaker.getNz()
        nt = nzt / nz
        ttpMap[zerosMap == 1] = nt

        # nzMap, nyMap, nxMap = maxIntMap.shape
        # centreMap = np.array(abs(np.tile(np.arange(1, nxMap+1), [nzMap, nyMap, 1]) - nxMap/2)).astype('float')
        # centreScore = 1 - (centreMap / np.amax(centreMap))

        fp = np.ones([1, kernel_ny, kernel_nx])
        summedVals = ndimage.filters.convolve(maxIntMap, fp)
        q75 = ndimage.filters.percentile_filter(maxIntMap, 75, footprint=fp)
        q25 = ndimage.filters.percentile_filter(maxIntMap, 25, footprint=fp)
        iqrVals = q75 - q25
        ttpMean = ndimage.filters.uniform_filter(ttpMap, size=[1, kernel_ny, kernel_nx])
        q75_ttp = ndimage.filters.percentile_filter(ttpMap, 75, footprint=fp)
        q25_ttp = ndimage.filters.percentile_filter(ttpMap, 25, footprint=fp)
        iqrVals_ttp = q75_ttp - q25_ttp

        # Normalise the sum and iqr values and add to give a score.
        summedValsScore = summedVals / np.amax(summedVals)
        iqrValsScore = 1.0 - (iqrVals / np.amax(iqrVals))
        ttpMean[ttpMean > 10] = 10
        tpValsScore = 1.0 - (ttpMean / 10)
        iqrVals_ttpScore = 1.0 - (iqrVals_ttp / np.amax(iqrVals_ttp))
        totalScore = (summedValsScore + tpValsScore)/2  * (iqrValsScore + iqrVals_ttpScore) / 2
        # totalScore = summedValsScore * iqrValsScore * tpValsScore * iqrVals_ttpScore
        # totalScore = summedValsScore * iqrValsScore
        # totalScore[zerosMap == 1] = 0
        self._mapMaker.setScoreMap(totalScore)

        # Find the indices of the voxel with the highest score
        self._aortaSeed = np.unravel_index(np.argmax(totalScore), totalScore.shape)
        aortaSeedMask = np.zeros(maxIntMap.shape, np.bool)
        aortaSeedMask[self._aortaSeed[0], self._aortaSeed[1], self._aortaSeed[2]] = True

        print self._aortaSeed
        return self._aortaSeed, aortaSeedMask

    def findAIFpatchStepSearch(self):
        fraction = 0.5
        numVoxels = 10
        step = 0.01
        while fraction < 1 and numVoxels > 5:
            self._candidateAifVoxelsMask = self._generateCandidateAIFvoxelsMaskUsingKernel(fraction)
            mask = self.pickAIFpatch()
            numVoxels = np.count_nonzero(mask)
            fraction += step
        self._aifMask = mask
        return mask

    def findAIFthreshold(self, useKernel, fraction):
        if useKernel:
            self._candidateAifVoxelsMask = self._generateCandidateAIFvoxelsMaskUsingKernel(fraction)
            self._aifMask = self.pickAIFpatch()
            # self._aifMask = self._candidateAifVoxelsMask
        else:
            self._candidateAifVoxelsMask = self._generateCandidateAIFvoxelsMask(fraction)
            self._aifMask = self._candidateAifVoxelsMask

        print fraction, np.count_nonzero(self._aifMask)
        return self._aifMask


    def findAIFpatchBinaryChop(self, useKernel, minVoxels):
        fractionList = np.arange(0.5,1.0,0.01)
        first = 0
        last = len(fractionList)-1
        found = False

        while first <= last and not found:
            midpoint = (first + last)//2
            fraction = fractionList[midpoint]
            if useKernel:
                self._candidateAifVoxelsMask = self._generateCandidateAIFvoxelsMaskUsingKernel(fraction)
            else:
                self._candidateAifVoxelsMask = self._generateCandidateAIFvoxelsMask(fraction)
            mask1 = self.pickAIFpatch()
            numVoxels1 = np.count_nonzero(mask1)
            if useKernel:
                self._candidateAifVoxelsMask = self._generateCandidateAIFvoxelsMaskUsingKernel(fraction+0.01)
            else:
                self._candidateAifVoxelsMask = self._generateCandidateAIFvoxelsMask(fraction+0.01)
            mask2 = self.pickAIFpatch()
            numVoxels2 = np.count_nonzero(mask2)
            if numVoxels1 >= minVoxels and numVoxels2 < minVoxels:
                found = True
            else:
                if numVoxels1 < minVoxels:
                    last = midpoint-1
                else:
                    first = midpoint+1

        print fraction, np.count_nonzero(mask1)
        self._aifMask = mask1
        return mask1

    def getAIFcurve(self):
        """ Return the value of the AIF at every time point.

        :return: np.array
        """
        dyn = self._mapMaker.getDynamics()
        nzt, ny, nx = dyn.shape
        nz = self._mapMaker.getNz()
        nt = nzt / nz

        aif = np.zeros([nt])
        for i in range(0, nt):
            vol = dyn[i:nzt:nt, :, :]
            aif[i] = np.mean(vol[self._aifMask])

        nBaseline = self._mapMaker.getNumBaseline()
        aveBaseline = np.mean(aif[0:nBaseline])
        maxDiffBaseline = np.amax(aif[0:nBaseline]) - np.amin(aif[0:nBaseline])
        maxVal = np.amax(aif)

        # print aif[0:15], np.amax(aif), np.argmax(aif)
        return [aif, np.array([nBaseline, np.count_nonzero(self._aifMask), aveBaseline, maxDiffBaseline, maxVal])]

    def pickAIFpatch(self):
        """ Pick the largest contiguous patch from the candidate mask

        :return: np.array(dtype=np.bool)
        """
        kernel = np.ones([3,3,3])
        # Each label is a contiguous patch of voxels
        label, nLabels = ndimage.label(self._candidateAifVoxelsMask, kernel)
        maxIntMap = self._mapMaker.maximumIntensityMap()
        maxVoxels = 0
        maxLabel = 0
        maxAve = 0
        # Find the label with the most voxels
        for i in range(1, nLabels+1):
            nVoxels = np.size(label[label == i])
            if nVoxels > maxVoxels:
                maxVoxels = nVoxels
                maxLabel = i
                maxAve = np.sum(maxIntMap[label == i]) / np.count_nonzero(maxIntMap[label == i])
            elif nVoxels == maxVoxels:
                maxAveNew = np.sum(maxIntMap[label == i]) / np.count_nonzero(maxIntMap[label == i])
                print "pickAIFpatch found a matching size patch"
                if maxAveNew > maxAve:
                    maxVoxels = nVoxels
                    maxLabel = i
                    maxAve = maxAveNew

        mask = np.zeros(np.shape(maxIntMap), np.bool)
        mask[label == maxLabel] = True
        self._aifMask = mask
        return mask

    def reset(self):
        """ Reset state of object.

        :return:
        """
        self._mapMaker.reset()
        self._resetVariables()

    def setAortaMask(self, m):
        """ Set the aorta mask.

        :param m: np.array(dtype = bool)
        :return:
        """
        self._aortaMask = m

    def setCandidateAIFvoxelsMask(self, m):
        """ Set the mask of candidate AIF voxels.

        :param m: np.array(dtype = bool)
        :return:
        """
        self._candidateAifVoxelsMask = m

    def floodFillAortaToNumVoxels(self, voxel):

        fraction = 0.7
        step = 0.1
        found = False
        goingUp = True
        minVal = 475
        maxVal = 525

        while found is False and fraction < 1.0 and fraction > 0 and abs(step) > 0.00001 :
            mask = self._floodfillAorta(voxel, fraction)
            numVoxels = np.count_nonzero(mask)
            # print fraction, numVoxels
            if numVoxels > minVal and numVoxels < maxVal:
                found = True
            else:
                if numVoxels > maxVal and goingUp is True:
                    step = step / 2
                    goingUp = False
                elif numVoxels > maxVal and goingUp is False:
                    step = step
                elif numVoxels < minVal and goingUp is True:
                    step = step
                elif numVoxels < minVal and goingUp is False:
                    step = step / 2
                    goingUp = True
                newStep = step
                if goingUp:
                    newStep = -step
                if abs(newStep) <= 0.00001:
                    print "flood-fill step size minimum reached."
                fraction = fraction + newStep

        print "aorta mask voxels: ", numVoxels
        return mask

    def _floodfillAorta(self, voxel, fraction):
        """ Floodfill from the seed using a fraction of the seed intensity as the threshold for inclusion.

        :param voxel: [int, int, int]
        Seed for the flood fill.
        :param fraction: float
        Fraction of the aorta seed intensity to use as threshold of the floodfill.
        :return: np.array(dtype = np.bool)
        """
        maxIntMap = self._mapMaker.maximumIntensityMap()
        z, y, x = voxel
        threshold = fraction * maxIntMap[z, y, x]
        mask = np.zeros(maxIntMap.shape, np.bool)

        z, y, x = voxel
        nz, ny, nx = maxIntMap.shape

        if maxIntMap[z, y, x] >= threshold and mask[z, y, x] == False:
            mask[z, y, x] = True
            edge = [(z, y, x)]

            while edge:
                newEdge = []
                for (z, y, x) in edge:
                    nextVoxels = ((z, y, x-1), (z, y, x+1), (z, y-1, x), (z, y+1, x), (z-1, y, x), (z+1, y, x))
                    for (c, b, a) in nextVoxels:
                        if 0 <= a < nx and 0 <= b < ny and 0 <= c < nz and \
                                        maxIntMap[c, b, a] >= threshold and mask[c, b, a] == False:
                            mask[c, b, a] = True
                            newEdge.append((c, b, a))

                edge = newEdge

        # print np.count_nonzero(mask)
        return mask

    def _generateCandidateAIFvoxelsMask(self, fraction):
        """ Find candidate AIF voxels from within the set aorta mask.

        A score is calculated for each voxel within the aorta mask from the
        maxInt and baseline maps. Only voxels with a score above a fraction of the
        maximum score are included in the mask
        :param fraction: float
        Fraction of max scoring voxel to use as threshold for inclusion
        :return: np.array(np.bool)
        """
        maxIntMap = self._mapMaker.maximumIntensityMap()
        baselineMap = self._mapMaker.baselineMap()

        # if the aortaMask hasn't been set we look at all the voxels
        if self._aortaMask == None:
            print "Using all voxels"
            self._aortaMask = np.ones(maxIntMap.shape, np.bool)
        # find the voxels in the aorta mask
        maskIndices = np.where(self._aortaMask == True)
        # get the maxInt and baseline vals for these voxels and calculate the scores
        maxIntVals = maxIntMap[maskIndices]
        maxIntScores = maxIntVals / np.amax(maxIntVals)
        baselineVals = baselineMap[maskIndices]
        baselineScores = 1 - (baselineVals / np.amax(maxIntVals))
        finalScores= maxIntScores * baselineScores

        # find the voxels with scores greater than the threshold
        nCandidates = np.size(finalScores[finalScores > (fraction*np.amax(finalScores))])
        topInd = finalScores.argsort(axis=None)[-nCandidates:][::-1]

        # generate the mask
        mask = np.zeros(maxIntMap.shape, np.bool)
        mask[maskIndices[0][topInd], maskIndices[1][topInd], maskIndices[2][topInd]] = True
        # set edge slices to zero
        mask[[0, -1], :, :] = False

        return mask

    def _generateCandidateAIFvoxelsMaskUsingKernel(self, fraction):
        """ Find candidate AIF voxels from within the set aorta mask.

        A score is calculated for each voxel within the aorta mask from the
        maxInt and baseline maps. Only voxels with a score above a fraction of the
        maximum score are included in the mask
        :param fraction: float
        Fraction of max scoring voxel to use as threshold for inclusion
        :return: np.array(np.bool)
        """
        maxIntMap = self._mapMaker.maximumIntensityMap()
        baselineMap = self._mapMaker.baselineMap()
        ttpMap = self._mapMaker.timeToPeakMap()
        zerosMap = self._mapMaker.getZerosMap()
        maxIntMap[zerosMap == 1] = 0
        dyn = self._mapMaker.getDynamics()
        nzt, ny, nx = dyn.shape
        nz = self._mapMaker.getNz()
        nt = nzt / nz
        ttpMap[zerosMap == 1] = nt

        nx = 3
        ny = 7
        fp = np.ones([1, ny, nx])
        summedVals = ndimage.filters.convolve(maxIntMap, fp)
        q75 = ndimage.filters.percentile_filter(maxIntMap, 75, footprint=fp)
        q25 = ndimage.filters.percentile_filter(maxIntMap, 25, footprint=fp)
        iqrVals = q75 - q25
        ttpMean = ndimage.filters.uniform_filter(ttpMap, size=[1, ny, nx])
        q75_ttp = ndimage.filters.percentile_filter(ttpMap, 75, footprint=fp)
        q25_ttp = ndimage.filters.percentile_filter(ttpMap, 25, footprint=fp)
        iqrVals_ttp = q75_ttp - q25_ttp

        # Normalise the sum and iqr values and add to give a score.
        summedValsScore = summedVals / np.amax(summedVals)
        iqrValsScore = 1.0 - (iqrVals / np.amax(iqrVals))
        ttpMean[ttpMean > 10] = 10
        tpValsScore = 1.0 - (ttpMean / 10)
        iqrVals_ttpScore = 1.0 - (iqrVals_ttp / np.amax(iqrVals_ttp))
        tpValsScore[ttpMap == nt] = 0
        iqrVals_ttpScore[ttpMap == nt] = 0

        # totalScore = summedValsScore * iqrValsScore
        totalScore = summedValsScore * iqrValsScore * tpValsScore * iqrVals_ttpScore
        self._mapMaker.setScoreMap(totalScore)

        # look at all the voxels
        self._aortaMask = np.ones(maxIntMap.shape, np.bool)
        # find the voxels in the aorta mask
        maskIndices = np.where(self._aortaMask == True)
        # get the maxInt and baseline vals for these voxels and calculate the scores
        maxIntVals = maxIntMap[maskIndices]
        maxIntScores = maxIntVals / np.amax(maxIntVals)
        baselineVals = baselineMap[maskIndices]
        baselineScores = 1 - (baselineVals / np.amax(maxIntVals))
        kernelScores = totalScore[maskIndices]
        # zeros = zerosMap[maskIndices]
        finalScores= maxIntScores * baselineScores * kernelScores
        # finalScores[zeros == 1] = 0
        # finalScores= baselineScores * kernelScores

        # find the voxels with scores greater than the threshold
        nCandidates = np.size(finalScores[finalScores > (fraction*np.amax(finalScores))])
        topInd = finalScores.argsort(axis=None)[-nCandidates:][::-1]

        # generate the mask
        mask = np.zeros(maxIntMap.shape, np.bool)
        mask[maskIndices[0][topInd], maskIndices[1][topInd], maskIndices[2][topInd]] = True
        # set edge slices to zero
        mask[[0, -1], :, :] = False

        return mask

    def _resetVariables(self):
        """ Reset member variables.

        :return:
        """
        self._aortaMask = None
        self._aortaSeed = None
        self._candidateAifVoxelsMask = None
        self._aifMask = None
