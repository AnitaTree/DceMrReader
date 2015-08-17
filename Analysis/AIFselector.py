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
        self._aortaMask = None
        self._aortaSeed = None
        self._candidateAifVoxelsMask = None
        self._dims = None

    def findCandidateAortaSeeds(self, nCand):
        """ Generates a mask of candidate aorta seeds.

        A score is calculated for the nCand voxels with highest values in the maxiIntMap.
        The score is derived from the summed value and IQR of a 1 by 5 kernel.
        :param nCand: int
        Number of candidate voxels
        :return: np.array dtype=np.bool
        A mask of the candidate aorta seed voxels
        """
        # Get the nCand voxel indices with the highest values in the maxInt map
        maxIntMap = self._mapMaker.maximumIntensityMap()
        self._dims = maxIntMap.shape
        nCandidates = min([nCand, np.prod(self._dims)])
        [z, y, x] = np.unravel_index(maxIntMap.argsort(axis=None)[-nCandidates:][::-1], self._dims)

        summedVals = np.zeros(z.size, maxIntMap.dtype)
        iqrVals = np.zeros(z.size, maxIntMap.dtype)
        candidateMask = np.zeros(maxIntMap.shape, np.bool)

        # Calculate the sum and IQR for a 1x5 kernel for each voxel
        for i in range(0, z.size):
            ny = 5
            nx = 1
            yUnder = np.max([0, y[i]-ny])
            yAbove = np.min([y[i]+ny+1, self._dims[1]])
            xUnder = np.max([0, x[i]-nx])
            xAbove = np.min([x[i]+nx+1, self._dims[2]])
            vals = maxIntMap[z[i], yUnder:yAbove, xUnder:xAbove]
            summedVals[i] = vals.sum()
            q75, q25 = np.percentile(vals, [75 ,25])
            iqr = q75 - q25
            iqrVals[i] = iqr
            candidateMask[z[i], y[i], x[i]]= True

        # Normalise the sum and iqr values and add to give a score.
        summedValsScore = summedVals / np.amax(summedVals)
        iqrValsScore = 1.0 - (iqrVals / np.amax(iqrVals))
        totalScore = summedValsScore + iqrValsScore

        # Find the indices of the voxel with the highest score
        topVoxel = np.argmax(totalScore)
        self._aortaSeed = [z[topVoxel], y[topVoxel], x[topVoxel]]

        return candidateMask

    def generateCandidateAIFvoxelsMask(self, fraction):
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

        # find the voxels in the aorta mask
        maskIndices = np.where(self._aortaMask == True)
        # get the maxInt and baseline vals for these voxels and calculate the scores
        maxIntVals = maxIntMap[maskIndices]
        maxIntScores = maxIntVals / np.amax(maxIntVals)
        baselineVals = baselineMap[maskIndices]
        baselineScores = 1 - (baselineVals / np.amax(maxIntVals))
        finalScores= maxIntScores + baselineScores

        # find the voxels with scores greater than the threshold
        nCandidates = np.size(finalScores[finalScores > (fraction*np.amax(finalScores))])
        topInd = finalScores.argsort(axis=None)[-nCandidates:][::-1]

        # generate the mask
        mask = np.zeros(maxIntMap.shape, np.bool)
        mask[maskIndices[0][topInd], maskIndices[1][topInd], maskIndices[2][topInd]] = True

        return mask

    def getAortaSeed(self):
        """ Return the aorta seed voxel and a mask of the voxel.

        :return: [int, int, int], np.array(dtype = np.bool)
        The [z, y, x] subscripts of the aorta seed and a binary map of the seed.
        """
        seedMap = np.zeros(self._dims, np.bool)
        seedMap[self._aortaSeed[0], self._aortaSeed[1], self._aortaSeed[2]] = True
        return self._aortaSeed, seedMap

    def pickAIFpatch(self):
        """ Pick the largest contiguous patch from the candidate mask

        :return: np.array(dtype=np.bool)
        """
        kernel = np.ones([3,3,3])
        # Each label is a contiguous patch of voxels
        label, nLabels = ndimage.label(self._candidateAifVoxelsMask, kernel)
        maxVoxels = 0
        maxLabel = 0
        # Find the label with the most voxels
        for i in range(1, nLabels+1):
            nVoxels = np.size(label[label == i])
            if nVoxels > maxVoxels:
                maxVoxels = nVoxels
                maxLabel = i
        mask = np.zeros(np.shape(self._mapMaker.maximumIntensityMap()), np.bool)
        mask[label == maxLabel] = True
        return mask

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
                        if  0 <= a < nx and 0 <= b < ny and 0 <= c < nz and \
                            maxIntMap[c, b, a] >= threshold and mask[c, b, a] == False:
                            mask[c, b, a] = True
                            newEdge.append((c, b, a))

                edge = newEdge

        return mask
