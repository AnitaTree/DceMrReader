__author__ = 'medabana'

class AIFextractionParameters:
    def __init__(self, k_nx = 3, k_ny = 7, minFract = 0.9, maxStd = 3, aortaN_min = 475, aortaN_max = 525):
        self.kernel_nx = k_nx
        self.kernel_ny = k_ny
        self.minFraction = minFract
        self.maxStdev = maxStd
        self.aortaNumVoxels_min = aortaN_min
        self.aortaNumVoxels_max = aortaN_max