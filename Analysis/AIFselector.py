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

    def findAIFpatchBinaryChop(self, useKernel, minVoxels):
        """ Selects a contiguous patch of voxels from the candidate mask with atleast minVoxels using a binary chop.

        :param useKernel: bool
        If true kernel scoring is used to generate the candidate mask
        :param minVoxels: int
        The minimum number of voxels in the mask
        :return: np.array(np.bool)
        Mask of the selected voxels.
        """
        fractionList = np.arange(0.5,1.0,0.01)
        first = 0
        last = len(fractionList)-1
        found = False

        while first <= last and not found:
            midpoint = (first + last)//2
            fraction = fractionList[midpoint]
            self._candidateAifVoxelsMask = self._generateCandidateAIFvoxelsMask(fraction, useKernel, 3, 7)
            mask1 = self.pickAIFpatch()
            numVoxels1 = np.count_nonzero(mask1)
            self._candidateAifVoxelsMask = self._generateCandidateAIFvoxelsMask(fraction+0.01, useKernel, 3, 7)
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

    def findAIFpatchStepSearch(self):
        """ Finds a patch of 5 or less AIF voxels by changing the fraction used to generate the candidate voxel mask.

        :return: np.array dtype = np.bool
        mask of AIF voxels
        """
        fraction = 0.5
        numVoxels = 10
        step = 0.01
        while fraction < 1 and numVoxels > 5:
            self._candidateAifVoxelsMask = self._generateCandidateAIFvoxelsMask(fraction, True, 3, 7)
            mask = self.pickAIFpatch()
            numVoxels = np.count_nonzero(mask)
            fraction += step
        self._aifMask = mask
        return mask

    def findAIFvoxels(self, useKernel, fraction):
        """ Finds the AIF voxels from the aorta mask or the full volume if useKernel is True.

        :param useKernel: bool
        If True kernel scoring is used on the full volume. If false voxels within the aorta mask are assessed individually
        :param fraction:
        :return: np.array dtype = np.bool
        A mask of the selected voxels
        """
        self._candidateAifVoxelsMask = self._generateCandidateAIFvoxelsMask(fraction, useKernel, 3, 7)
        if useKernel:
            # picks a contiguous section
            self._aifMask = self.pickAIFpatch()
        else:
            # section doesn't have to be contiguous
            self._aifMask = self._candidateAifVoxelsMask

        print fraction, np.count_nonzero(self._aifMask)
        return self._aifMask

    def findCandidateAortaSeed(self, kernel_nx, kernel_ny):
        """ Finds a single voxel in the Aorta.

        Looks for an early high enhancing voxel that is surounded by similar voxels in the kernel.

        :param kernel_nx: int
        Size of kernel in x direction
        :param kernel_ny: int
        Size of kernel in y direction
        :return: np.array dtype=np.int
        The x, y and z indices of the aorta seed
        :return: np.array dtype=np.bool
        A mask of the candidate aorta seed voxels
        """
        totalScore = self._generateAortaSeedScoreMap(kernel_nx, kernel_ny)

        # Find the indices of the voxel with the highest score
        self._aortaSeed = np.unravel_index(np.argmax(totalScore), totalScore.shape)
        aortaSeedMask = np.zeros(totalScore.shape, np.bool)
        aortaSeedMask[self._aortaSeed[0], self._aortaSeed[1], self._aortaSeed[2]] = True

        print 'aorta seed ', self._aortaSeed
        return self._aortaSeed, aortaSeedMask


    def floodFillAortaToNumVoxels(self, seed):
        """ Flood fills from the seed voxels until between 475 and 525 voxels is reached by changing the threshold.

        :param seed: np.array int [x, y, z]
        x, y, z indices of the aorta seed
        :return: np.array dtype=np.bool
        mask fo the aorta
        """
        fraction = 0.7
        step = 0.1
        found = False
        goingUp = True
        minVal = 475
        maxVal = 525

        while found is False and fraction < 1.0 and fraction > 0 and abs(step) > 0.00001:
            mask = self._floodfillAorta(seed, fraction)
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

    def getAIFcurveAndMeasures(self):
        """ Return the value of the AIF at every time point and measures from the data.

        :return: np.array [np.array(double), inp.array[int, int, double, double, double]]
        AIF, [numBaseline, numVoxels, aveBaseline, maxDiff, maxVal]
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
        Mask of selected voxels.
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

    def _floodfillAorta(self, seed, fraction):
        """ Floodfill from the seed using a fraction of the seed intensity as the threshold for inclusion.

        :param seed: [int, int, int]
        Seed for the flood fill.
        :param fraction: float
        Fraction of the aorta seed intensity to use as threshold of the floodfill.
        :return: np.array(dtype = np.bool)
        """
        maxIntMap = self._mapMaker.maximumIntensityMap()
        z, y, x = seed
        threshold = fraction * maxIntMap[z, y, x]
        mask = np.zeros(maxIntMap.shape, np.bool)

        z, y, x = seed
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

    def _generateAortaSeedScoreMap(self, kernel_nx, kernel_ny):
        """
        Generate a map of aorta seed score for each voxel between 0 and 1.

        Applies a kernel to the maximimumIntensity and TTP maps to calculate mean value and IQR.
        :param kernel_nx: int
        kernel width in voxels
        :param kernel_ny:  int
        kernel height in voxels
        :return: np.array double
        map of scores for each voxel
        """
        maxIntMap = self._mapMaker.maximumIntensityMap()
        ttpMap = self._mapMaker.timeToPeakMap()
        zerosMap = self._mapMaker.getZeroMinIntensityMap()

        # currently commented out but could be used to give higher weighting to the voxels in the centre horizontally
        # nzMap, nyMap, nxMap = maxIntMap.shape
        # centreMap = np.array(abs(np.tile(np.arange(1, nxMap+1), [nzMap, nyMap, 1]) - nxMap/2)).astype('float')
        # centreScore = 1 - (centreMap / np.amax(centreMap))

        fp = np.ones([1, kernel_ny, kernel_nx])
        maxInt_mean = ndimage.filters.uniform_filter(maxIntMap, size=[1, kernel_ny, kernel_nx])
        q75 = ndimage.filters.percentile_filter(maxIntMap, 75, footprint=fp)
        q25 = ndimage.filters.percentile_filter(maxIntMap, 25, footprint=fp)
        iqrVals_maxInt = q75 - q25
        ttpMean = ndimage.filters.uniform_filter(ttpMap, size=[1, kernel_ny, kernel_nx])
        q75_ttp = ndimage.filters.percentile_filter(ttpMap, 75, footprint=fp)
        q25_ttp = ndimage.filters.percentile_filter(ttpMap, 25, footprint=fp)
        iqrVals_ttp = q75_ttp - q25_ttp

        # Normalise the sum and iqr values
        summedValsScore = maxInt_mean / np.amax(maxInt_mean)
        iqrValsScore = 1.0 - (iqrVals_maxInt / np.amax(iqrVals_maxInt))
        ttpLimit = self._mapMaker.getNumBaseline() + 3
        ttpMean[ttpMean > ttpLimit] = ttpLimit
        tpValsScore = 1.0 - (ttpMean / ttpLimit)
        iqrVals_ttpScore = 1.0 - (iqrVals_ttp / np.amax(iqrVals_ttp))

        # Generate a score. Values are assumed to be dependent as are the two IQRs. Mean and IQR are assumed to be independent.
        totalScore = (summedValsScore + tpValsScore)/2 * (iqrValsScore + iqrVals_ttpScore) / 2
        totalScore[zerosMap == 1] = 0
        self._mapMaker.setScoreMap(totalScore)
        return totalScore

    def _generateCandidateAIFvoxelsMask(self, fraction, useKernelScores = False, kernel_nx = -1, kernel_ny = -1):
        """ Find candidate AIF voxels from within the set aorta mask.

        A score is calculated for each voxel within the aorta mask from the
        maxInt and baseline maps. Only voxels with a score above a fraction of the
        maximum score are included in the mask. If useKernelScores is true, scores generated using a kernel
        on the maxInt and ttp maps are also included.
        :param fraction: float
        Fraction of max scoring voxel to use as threshold for inclusion
        :param useKernelScores: bool
        Set to True to use kernel based scores
        :param kernel_nx int
        Number of voxels of the width of the kernel
        :param kernel_ny int
        Number of voxels of the height of the kernel
        :return: np.array(np.bool)
        """
        maxIntMap = self._mapMaker.maximumIntensityMap()
        baselineMap = self._mapMaker.baselineMap()

        if useKernelScores:
            # look at all the voxels
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

        if useKernelScores:
            kernelScoreMap = self._generateAortaSeedScoreMap(kernel_nx, kernel_ny)
            kernelScores = kernelScoreMap[maskIndices]
            finalScores= finalScores * kernelScores

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
        self._aifMask = None
        self._aortaMask = None
        self._aortaSeed = None
        self._candidateAifVoxelsMask = None
