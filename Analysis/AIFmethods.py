__author__ = 'medabana'

import logging

from Analysis.MapGuiSetup import MapGuiSetup
from Analysis.AIFguiSetup import AIFguiSetup

class AIFmethods():
    def __init__(self, aifGui, mapGui):
        """ Initialize variables.
        :param aifGui: AIFGuiSetup
        :param mapGui: MapGuiSetup
        :return:
        """
        self._logger = logging.getLogger(__name__)
        self._aifGuiSetup = aifGui
        self._mapGuiSetup = mapGui

    def _selectAIFvoxelsFromMaskAuto(self, fraction, currSlice):
        """ Select AIF voxels automatically (without user input) by finding an aorta seed, generating an aorta mask
        and then selecting a percentage of that mask.
        :param fraction: double
        Voxels with a maximum signal intensity change greater than this fraction of the maximum change in the aorta mask
        are selected.
        :param currSlice: int
        The slice currently being displayed.
        :return:
        """
        self._logger.info('_selectAIFvoxelsFromMaskAuto')
        accept = self._mapGuiSetup.getMaxIntMap()
        if not accept:
            return
        self._mapGuiSetup.getMeanBaselineMap(False)
        self._aifGuiSetup.floodfillFromSeed(currSlice)
        self._aifGuiSetup.findAIFvoxelsAuto(True)
        aif, aifMeasures = self._aifGuiSetup.getAIFdata()

        return [aif, aifMeasures]


    def _selectAIFvoxelsFromMaskUser(self, currSlice):
        """ Select AIF voxels, requesting input from the user, by finding an aorta seed, generating an aorta mask
        and then selecting a percentage of that mask.
        :param currSlice: int
        The slice currently being displayed.
        :return:
        """
        accept = self._mapGuiSetup.getMaxIntMap()
        if not accept:
            return
        self._mapGuiSetup.getMeanBaselineMap(False)
        accept = self._aifGuiSetup.findCandidateAortaSeedUser(currSlice)
        if accept:
            sliceNum = self._aifGuiSetup.floodfillFromSeed(currSlice)
            self._aifGuiSetup.findAIFvoxelsUser(sliceNum)
            # self._aifGuiSetup.findAIFvoxelsMinNumber(False)

    def _selectAIFvoxelsGlobal(self):
        """ Select AIF voxels automatically (without user input) by applying kernel based scoring to the full image volume.
        :return:
        """
        accept = self._mapGuiSetup.getMaxIntMap()
        if not accept:
            return
        self._mapGuiSetup.getMeanBaselineMap(False)
        # self._aifGuiSetup.findAIFvoxelsMinNumber(True)
        self._aifGuiSetup.findAIFvoxelsAuto(False)
