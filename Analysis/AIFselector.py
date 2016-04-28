__author__ = 'medabana'

import logging
import numpy as np
import scipy.ndimage as ndimage
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt

from AIFextractionParameters import AIFextractionParameters

class AIFselector():
    """ Algorithms for selecting AIF voxels. """
    def __init__(self, maps):
        """
        :param maps: MapGenerator
        :return:
        """
        self.extractionParams = AIFextractionParameters()
        self._logger = logging.getLogger(__name__)
        self._mapMaker = maps
        self._resetVariables()

    def findAIFvoxels(self, useAortaMask):
        """ Finds the AIF voxels from the aorta mask or the full volume if useKernel is True.

        :param useAortaMask: bool
        If True voxels within the aorta mask are assessed individually. If False kernel scoring is used on the full volume.
        :param fraction:
        :return: np.array dtype = np.bool
        A mask of the selected voxels
        """
        if useAortaMask:
            self._logger.info('findAIFvoxels using aorta mask')
            self.candidateAifVoxelsMask = self._generateCandidateAIFvoxelsMask()
            # section doesn't have to be contiguous
            self._aifMask = self.candidateAifVoxelsMask
        else:
            self._logger.info('findAIFvoxels using global')
            self.candidateAifVoxelsMask = self._generateCandidateAIFvoxelsGlobal()
            # picks a contiguous section
            self._aifMask = self.pickAIFpatch()

        self._logExtractionParameters()
        print self.extractionParams.minFraction, np.count_nonzero(self._aifMask)
        return self._aifMask

    def findCandidateAortaSeed(self):
        """ Finds a single voxel in the Aorta.

        Looks for an early high enhancing voxel that is surrounded by similar voxels in a kernel.

        :return: np.array dtype=np.int
        The x, y and z indices of the aorta seed
        :return: np.array dtype=np.bool
        A mask of the candidate aorta seed voxels
        """
        totalScore = self._generateAortaSeedScoreMap()

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
        minVal = self.extractionParams.aortaNumVoxels_min
        maxVal = self.extractionParams.aortaNumVoxels_max

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
        dyn = self._mapMaker.dynamics
        nzt, ny, nx = dyn.shape
        nz = self._mapMaker.getNz()
        nt = nzt / nz

        aif = np.zeros([nt])
        for i in range(0, nt):
            vol = dyn[i:nzt:nt, :, :]
            aif[i] = np.mean(vol[self._aifMask])

        nBaseline = self._mapMaker.numBaseline
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
        label, nLabels = ndimage.label(self.candidateAifVoxelsMask, kernel)
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

    def _generateAortaSeedScoreMap(self):
        """
        Generate a map of aorta seed score for each voxel between 0 and 1.

        Applies a kernel to the maximimumIntensity and TTP maps to calculate mean value and IQR.
        :return: np.array double
        map of scores for each voxel
        """
        kernel_ny = self.extractionParams.kernel_ny
        kernel_nx = self.extractionParams.kernel_nx
        fp = np.ones([1, kernel_ny, kernel_nx])

        maxIntMap = self._mapMaker.maximumIntensityMap()
        maxInt_mean = ndimage.filters.uniform_filter(maxIntMap, size=[1, kernel_ny, kernel_nx])
        q75 = ndimage.filters.percentile_filter(maxIntMap, 75, footprint=fp)
        q25 = ndimage.filters.percentile_filter(maxIntMap, 25, footprint=fp)
        iqrVals_maxInt = q75 - q25
        # Normalise the sum and iqr values
        summedValsScore = maxInt_mean / np.amax(maxInt_mean)
        iqrValsScore = 1.0 - (iqrVals_maxInt / np.amax(iqrVals_maxInt))

        ttpMap = self._mapMaker.timeToPeakMap()
        ttpMean = ndimage.filters.uniform_filter(ttpMap, size=[1, kernel_ny, kernel_nx])
        q75_ttp = ndimage.filters.percentile_filter(ttpMap, 75, footprint=fp)
        q25_ttp = ndimage.filters.percentile_filter(ttpMap, 25, footprint=fp)
        iqrVals_ttp = q75_ttp - q25_ttp
        ttpLimit = self._mapMaker.numBaseline + 3
        ttpMean[ttpMean > ttpLimit] = ttpLimit
        tpValsScore = 1.0 - (ttpMean / ttpLimit)
        iqrVals_ttpScore = 1.0 - (iqrVals_ttp / np.amax(iqrVals_ttp))

        # currently commented out but could be used to give higher weighting to the voxels in the centre horizontally
        # nzMap, nyMap, nxMap = maxIntMap.shape
        # centreMap = np.array(abs(np.tile(np.arange(1, nxMap+1), [nzMap, nyMap, 1]) - nxMap/2)).astype('float')
        # centreScore = 1 - (centreMap / np.amax(centreMap))

        # Generate a final score. Both means are assumed to be dependent as are the both IQRs.
        # Mean and IQR are assumed to be independent of each other.
        totalScore = (summedValsScore + tpValsScore)/2 * (iqrValsScore + iqrVals_ttpScore)/2
        zerosMap = self._mapMaker.getZeroMinIntensityMap()
        totalScore[zerosMap == 1] = 0
        self._mapMaker.scoreMap = totalScore
        return totalScore

    def _generateCandidateAIFvoxelsGlobal(self):
        """ Find candidate AIF voxels from within the set aorta mask.

        A score is calculated for each voxel using a kernel on the maxInt and ttp maps.
        :param fraction: float
        Fraction of max scoring voxel to use as threshold for inclusion
        :return: np.array(np.bool)
        Mask of selected voxels
        """
        kernelScoreMap = self._generateAortaSeedScoreMap()
        fraction = self.extractionParams.minFraction
        mask = kernelScoreMap > fraction*np.amax(kernelScoreMap)
        # set edge slices to zero
        mask[[0, -1], :, :] = False

        return mask

    def _generateCandidateAIFvoxelsMask(self):
        """ Find candidate AIF voxels from within the set aorta mask.

        A score is calculated for each voxel within the aorta mask from the
        maxInt and baseline maps. Only voxels with a score above a fraction of the
        maximum score are included in the mask.
        :return: np.array(np.bool)
        Mask of the selected voxels
        """
        maxIntMap = self._mapMaker.maximumIntensityMap()
        baselineMap = self._mapMaker.baselineMap()

        # remove upper outliers from aorta mask
        maxIntValsAll = maxIntMap[self.aortaMask]
        mu = np.mean(maxIntValsAll)
        sigma = np.std(maxIntValsAll)
        upperThreshold = mu + sigma*self.extractionParams.maxStdev
        self.aortaMask[maxIntMap > upperThreshold] = False

        # find the voxels in the aorta mask
        maskIndices = np.where(self.aortaMask == True)
        # get the maxInt and baseline vals for these voxels and calculate the scores
        maxIntVals = maxIntMap[maskIndices]
        maxIntScores = maxIntVals / np.amax(maxIntVals)
        baselineVals = baselineMap[maskIndices]
        baselineScores = 1 - (baselineVals / np.amax(maxIntVals))
        finalScores= maxIntScores * baselineScores

        # find the number of voxels with scores greater than the lower threshold
        fraction = self.extractionParams.minFraction
        nCandidates = np.size(finalScores[finalScores > fraction*np.amax(finalScores)])
        # find the indices of the nCandidate greatest scores
        topInd = finalScores.argsort(axis=None)[-nCandidates:][::-1]

        # generate the mask
        mask = np.zeros(maxIntMap.shape, np.bool)
        mask[maskIndices[0][topInd], maskIndices[1][topInd], maskIndices[2][topInd]] = True
        # set edge slices to zero
        mask[[0, -1], :, :] = False

        # # the histogram of the data
        # plt.ion()
        # plt.clf()
        # n, bins, patches = plt.hist(maxIntValsAll, 50, normed=1, facecolor='red', alpha=0.75)
        # plt.hist(maxIntVals, bins, normed=1, facecolor='green', alpha=0.75)
        # # add a 'best fit' line
        # y = mlab.normpdf(bins, mu, sigma)
        # l = plt.plot(bins, y, 'r--', linewidth=1)
        # m = plt.plot([upperThreshold, upperThreshold], [0, np.max(n)], 'k--', linewidth=2)
        # plt.xlabel('Maximum Intensity Change')
        # plt.ylabel('Num Voxels')
        # plt.grid(True)

        return mask

    def _logExtractionParameters(self):
        self._logger.info('kernel_nx: %i, kernel_ny: %i' % (self.extractionParams.kernel_nx, self.extractionParams.kernel_ny))
        self._logger.info('Voxel selection. minFraction: %.2f, maxStddev: %.2f' % (self.extractionParams.minFraction, self.extractionParams.maxStdev))
        self._logger.info('Aorta mask. numVoxels_min: %i, numVoxels_max: %i' % (self.extractionParams.aortaNumVoxels_min, self.extractionParams.aortaNumVoxels_max))

    def _resetVariables(self):
        """ Reset member variables.

        :return:
        """
        self._aifMask = None
        self.aortaMask = None
        self._aortaSeed = None
        self.candidateAifVoxelsMask = None

    # def findAIFpatchBinaryChop(self, useKernel, minVoxels):
    #     """ Selects a contiguous patch of voxels from the candidate mask with atleast minVoxels using a binary chop.
    #
    #     :param useKernel: bool
    #     If true kernel scoring is used to generate the candidate mask
    #     :param minVoxels: int
    #     The minimum number of voxels in the mask
    #     :return: np.array(np.bool)
    #     Mask of the selected voxels.
    #     """
    #     fractionList = np.arange(0.5,1.0,0.01)
    #     first = 0
    #     last = len(fractionList)-1
    #     found = False
    #
    #     while first <= last and not found:
    #         midpoint = (first + last)//2
    #         fraction = fractionList[midpoint]
    #         self._candidateAifVoxelsMask = self._generateCandidateAIFvoxelsMask(fraction, useKernel, 3, 7)
    #         mask1 = self.pickAIFpatch()
    #         numVoxels1 = np.count_nonzero(mask1)
    #         self._candidateAifVoxelsMask = self._generateCandidateAIFvoxelsMask(fraction+0.01, useKernel, 3, 7)
    #         mask2 = self.pickAIFpatch()
    #         numVoxels2 = np.count_nonzero(mask2)
    #         if numVoxels1 >= minVoxels and numVoxels2 < minVoxels:
    #             found = True
    #         else:
    #             if numVoxels1 < minVoxels:
    #                 last = midpoint-1
    #             else:
    #                 first = midpoint+1
    #
    #     print fraction, np.count_nonzero(mask1)
    #     self._aifMask = mask1
    #     return mask1

# def findAIFpatchStepSearch(self):
#     """ Finds a patch of 5 or less AIF voxels by changing the fraction used to generate the candidate voxel mask.
#
#     :return: np.array dtype = np.bool
#     mask of AIF voxels
#     """
#     fraction = 0.5
#     numVoxels = 10
#     step = 0.01
#     while fraction < 1 and numVoxels > 5:
#         self._candidateAifVoxelsMask = self._generateCandidateAIFvoxelsGlobal(fraction, 3, 7)
#         mask = self.pickAIFpatch()
#         numVoxels = np.count_nonzero(mask)
#         fraction += step
#     self._aifMask = mask
#     return mask
