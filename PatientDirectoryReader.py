__author__ = 'medabana'

import os
import dicom
import numpy as np
from datetime import datetime
from collections import Counter

class PatientDirectoryReader(object):

    def __init__(self, dirNm):
        """ Set up storage for series information. """
        self._dirNm = dirNm
        self._fileType = None
        self._suidNum = 0
        self._filesForSuid = {}
        self._suidAndTimeForProtocols = {}
        self._fileInfoForSuid = {}
        self._protNamesOrdered = []
        self._sequenceParameters= {}
        # only keep one set of data at a time for memory purposes
        self._data = None
        self._dataSuid = None

    def _getFileType(self, dcm):
        """ Check whether the file is DICOM, multiframe DICOM or NEMA."""
        if self._fileType is None:
            if 'SOPClassUID' in dcm:
                if 'Enhanced' in str(dcm.SOPClassUID):
                    self._fileType= 'enhancedDICOM'
                elif 'MR Image' in str(dcm.SOPClassUID):
                    self._fileType= 'DICOM'
            elif 'RecognitionCode' in dcm and dcm.RecognitionCode == 'ACR-NEMA 2.0':
                self._fileType= 'NEMA'
        return self._fileType

    def _getImageTime(self, dcm):
        """ Get the acquisition time of the file. """
        if 'AcquisitionTime' in dcm:
            # DICOM
            acqTime = dcm.AcquisitionTime
        elif 'AcquisitionDateTime' in dcm:
            # DICOM enhanced
            acqTime= dcm.AcquisitionDateTime
        elif 'ContentTime' in dcm:
            # NEMA
            acqTime = dcm.ContentTime
        else:
            raise Exception
        try:
            x = datetime.strptime(acqTime,'%H:%M:%S.%f')
            time = (x.hour * 60 + x.minute) * 60 + x.second + x.microsecond / 1000000.0
        except ValueError:
            time = float(acqTime)
        return time

    def _getFileInfoAndData(self, file):
        """

        all the files should be safe to read"""
        dcm= dicom.read_file(file, stop_before_pixels=False, force=True)
        if not dcm.dir('SamplesPerPixel'):
            #required for NEMA for the pixel_array access to work
            dcm.SamplesPerPixel = 1
        if 'SliceLocation' in dcm:
            sliceLocation = dcm.SliceLocation
        else:
            sliceLocation = 0
        imageData = dcm.pixel_array
        fileInfo = [file, self._getImageTime(dcm), sliceLocation]
        return fileInfo, imageData

    def _setSeriesInfoAndData(self, suid):
        fileNames= self._filesForSuid[suid]
        seriesFileInfo= []
        # release data memory first
        self._data = None
        for i, file in enumerate(fileNames):
            fileNm= os.path.join(self._dirNm, file)
            fileInfo, fileData= self._getFileInfoAndData(fileNm)
            seriesFileInfo.append(fileInfo)
            if len(fileNames) > 1:
                if i == 0:
                    dcm= dicom.read_file(fileNm, stop_before_pixels=False, force=True)
                    if not dcm.dir('SamplesPerPixel'):
                        # required for pixel_array access
                        dcm.SamplesPerPixel = 1
                    seriesData = np.zeros([len(fileNames), dcm.Rows, dcm.Columns], dcm.pixel_array.dtype)
                seriesData[i, :, :] = fileData
            else:
                seriesData= fileData
        if len(fileNames) > 1:
            infoSortedWithIndex = sorted(enumerate(seriesFileInfo), key=lambda info: (info[1][2], info[1][1]))
            sortIndex = []
            infoSorted = []
            for info in infoSortedWithIndex:
                sortIndex.append(info[0])
                infoSorted.append(info[1])
            self._fileInfoForSuid[suid] = infoSorted
            self._data = seriesData[sortIndex, :, :]
        else:
            self._fileInfoForSuid[suid] = seriesFileInfo
            self._data = seriesData
        self._dataSuid = suid

    def getSequenceParameters(self, protName):
        if protName not in self._sequenceParameters:
            fileInfo= self._fileInfoForSuid[self._suidAndTimeForProtocols[protName][0]]
            dcm = dicom.read_file(os.path.join(self._dirNm, fileInfo[0][0]), stop_before_pixels=True, force= True)
            acquisitionTimes= []
            sliceLocations= []
            for file in fileInfo:
                acquisitionTimes.append(file[1])
                sliceLocations.append(file[2])
            if self._getFileType(dcm) != 'enhancedDICOM':
                nt = Counter(sliceLocations)[sliceLocations[0]]
                nz = Counter(acquisitionTimes)[acquisitionTimes[0]]
                # for unusual cases e.g. bold
                if nz*nt > len(fileInfo):
                    nt= len(fileInfo)/nz
            else:
                nf = dcm.NumberOfFrames
                nz= dcm.PerFrameFunctionalGroupsSequence[nf-1].FrameContentSequence[0].DimensionIndexValues[2]
                # could get the nt from the DimensionIndexValues[3] array for a 4D image, but for a 3D image this
                # will not exist
                nt= nf / nz
            self._sequenceParameters[protName]= [dcm.Rows, dcm.Columns, nz, nt]
        return self._sequenceParameters[protName]

    def getSeriesNames(self):
        return self._protNamesOrdered

    def getOrderedFileList(self, protName):
        suid= self._suidAndTimeForProtocols[protName][0]
        if suid not in self._fileInfoForSuid:
            self._setSeriesInfoAndData(suid)
        infoSorted = self._fileInfoForSuid[suid]
        fileList = []
        for i, file in enumerate(infoSorted):
            fileList.append(file[0])
        return fileList

    def getImageData(self, protName):
        suid= self._suidAndTimeForProtocols[protName][0]
        if self._dataSuid != suid:
            self._setSeriesInfoAndData(suid)
        return self._data