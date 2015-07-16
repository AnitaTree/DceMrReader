__author__ = 'medabana'

import dicom
import os
import numpy as np
from collections import Counter
from datetime import datetime


class DicomDirectoryReader(object):
    def __init__(self, dcmDir):
        self.dcmDir= dcmDir
        self.series= {}
        self.suid= {}
        self.suidInfo = {}
        self.seriesFileInfo = {}
        self.seriesFileNames = {}
        self.orderedSeries = []
        self.sequenceParameters = {}
        self.type= None
        self.suidNum= 0
        self._getSeriesInfo(dcmDir)
        self._sortSeriesListRecursive()

    def _getTimeFloat(self, fileTime):
        try:
            x = datetime.strptime(fileTime,'%H:%M:%S.%f')
            time = (x.hour * 60 + x.minute) * 60 + x.second + x.microsecond / 1000000.0
        except ValueError:
            time = float(fileTime)
        return time

    def _sortSeriesListRecursive(self):
        seriesSorted = sorted(self.suid.items(), key=lambda info: info[1])
        seriesNames= []
        suidRenumbered= {}
        for i, series in enumerate(seriesSorted):
            name= series[0]
            newName= str(i+1) + name[name.index(':'):]
            seriesNames.append(newName)
            suidRenumbered[newName]= self.suid[name]
        self.suid= suidRenumbered

    def _findDICOMDIRfile(self, dcmDir):
        if os.path.basename(dcmDir) == 'DICOM':
            dcmDir= os.path.dirname(dcmDir)
        for baseDir, dirNames, files in os.walk(dcmDir):
            for file in files:
                if file == 'DICOMDIR':
                    return os.path.join(baseDir, file)
        return None

    def _checkFileIsOfInterest(self, file):
        f = open(file, "rb")
        f.seek(0x80)
        bytes= f.read(4)
        if bytes == 'DICM':
            return True
        f.seek(0x38)
        bytes= f.read(12)
        if bytes == 'ACR-NEMA 2.0':
            return True

    def _gatherFileNamesInAllSeries(self, dirNm):
        dicomdirFile= self._findDICOMDIRfile(dirNm)
        if dicomdirFile is None:
            self._getAllFileInfoRecursive(dirNm)
            print "No DICOMDIR file"
        else:
            print "found DICOMDIR file: ", dicomdirFile
            self._getInfoFromDICOMDIRfile(dicomdirFile)

    def _getFileInfo(self, file, noData = True):
        imageData= []
        if self.type == 'DICOM' or self.type == None:
            try:
                dcm= dicom.read_file(file, stop_before_pixels=noData, force=False)
                if self.type == None:
                    if 'Enhanced' in str(dcm.SOPClassUID):
                        self.type= 'enhancedDICOM'
                    elif 'MR Image' in str(dcm.SOPClassUID):
                        self.type= 'DICOM'
            except Exception as why:
                if self.type == 'DICOM':
                    print file + " ", why
                    raise Exception
        if self.type == 'NEMA' or self.type == None:
            try:
                dcm= dicom.read_file(file, stop_before_pixels=noData, force=True)
                try:
                    #need to do this check on all files opened, as the force=True
                    #option will open all sorts of files
                    if dcm.RecognitionCode == 'ACR-NEMA 2.0':
                        if self.type == None:
                            self.type= 'NEMA'
                        #required for the pixel_array access to work
                        if not dcm.dir('SamplesPerPixel'):
                            dcm.SamplesPerPixel= 1
                except Exception:
                    raise Exception
            except Exception as why:
                    print file + " ", why
                    raise Exception
        try:
            protName = (dcm.SeriesDescription + " (" + str(dcm.Rows) + ", " + str(dcm.Columns) + ")")
            if 'AcquisitionTime' in dcm:
                acqTime = dcm.AcquisitionTime
                sliceLocation= dcm.SliceLocation
            elif 'AcquisitionDateTime' in dcm:
                acqTime= dcm.AcquisitionDateTime
                sliceLocation= 0
            elif 'ContentTime' in dcm:
                acqTime = dcm.ContentTime
                sliceLocation= dcm.SliceLocation
            if not noData:
                imageData= dcm.pixel_array
            fileInfo= [file, acqTime, sliceLocation, imageData]
        except Exception as why:
            print file + " ", why
            raise Exception
        return protName.lstrip(), fileInfo, dcm.SeriesInstanceUID

    def _getInfoFromDICOMDIRfile(self, file):
        ds= dicom.read_file(file)
        seriesRecord = None
        fileNames= []
        foundNewSeries = False
        foundImageSeries = False
        for i, record in enumerate(ds.DirectoryRecordSequence):
            if record.DirectoryRecordType == 'SERIES':
                if foundImageSeries:
                    #found start of new series.
                    #store information on the last series now we have it all.
                    self.suidNum += 1
                    protName = str(self.suidNum) + ": " + seriesRecord.ProtocolName
                    self.suidInfo[protName]= seriesRecord.SeriesInstanceUID
                    self.seriesFileNames[protName]= fileNames
                    self.orderedSeries.append(protName)
                seriesRecord= record
                print i, " ", seriesRecord.ProtocolName, " ", seriesRecord.SeriesTime
                fileNames= []
                foundNewSeries = True
                foundImageSeries = False
            elif foundNewSeries and record.DirectoryRecordType == 'IMAGE':
                foundImageSeries= True
                foundNewSeries = False
            if foundImageSeries and record.DirectoryRecordType == 'IMAGE':
                fileNames.append(os.path.join(*record.ReferencedFileID))


    def _getSeriesInfo(self, dirNm):
        dicomdirFile= self._findDICOMDIRfile(dirNm)
        if dicomdirFile is None:
            self._getAllFileInfoRecursive(dirNm)
            print "No DICOMDIR file"
        else:
            print "found DICOMDIR file: ", dicomdirFile
            self._getInfoFromDICOMDIRfile(dicomdirFile)

    def _getAllFileInfoRecursive(self, dirNm):
        files= os.listdir(dirNm)
        for file in files:
            fileNm= os.path.join(dirNm, file)
            if not os.path.isdir(fileNm):
                try:
                    protName, fileInfo, suid= self._getFileInfo(fileNm)
                    if self.type == 'NEMA':
                        suid= suid[:-3]
                except:
                    continue  # skip non-dicom file
                if suid not in self.series:
                    self.series[suid]= [fileInfo]
                    self.suidNum += 1
                    protName = str(self.suidNum) + ": " + protName
                    self.suid[protName]= [suid, self._getTimeFloat(fileInfo[1])]
                else:
                    self.series[suid].append(fileInfo)
                # print protName, ": ", fileInfo, " ", suid
            else:
                self._getAllFileInfoRecursive(fileNm)

    def _getSeriesFileInfo(self, dirNm, fileNames):
        seriesFileInfo= []
        for i, file in enumerate(fileNames):
            fileNm= os.path.join(dirNm, file)
            protName, fileInfo, suid= self._getFileInfo(fileNm)
            seriesFileInfo.append(fileInfo)
        return seriesFileInfo

    def getImageData(self, protName):
        fileList= self.getFileList(protName)
        nx, ny, nz, nt = self.getSequenceParameters(protName)
        data = np.zeros([nz*nt, nx, ny])
        for i, file in enumerate(fileList):
            dcm = dicom.read_file(file, stop_before_pixels=False, force= True)
            # this info doesn't seem present in ACR-NEMA 2.0 format
            # we need this info present for the pixel_array access to work
            if not dcm.dir('SamplesPerPixel'):
                dcm.SamplesPerPixel= 1
            if self.type == 'enhancedDICOM':
                data= dcm.pixel_array
            else:
                data[i, :, :] = dcm.pixel_array
        return data

    def getFileList(self, protName):
        if len(self.series) == 0:
            fileInfo= self._getSeriesFileInfo(self.dcmDir, self.seriesFileNames[protName])
            self.seriesFileInfo[protName]= fileInfo
        else:
            fileInfo = self.series[self.suid[protName][0]]
        if self.type != 'enhancedDICOM':
            infoSorted = sorted(fileInfo, key=lambda info: (info[2], info[1]))
        else:
            infoSorted = sorted(fileInfo, key=lambda info: info[1])
        order = ["name ", "acquisitionTime ", "sliceLocation "]
        # print order
        fileList = []
        for i, file in enumerate(infoSorted):
            # print i, ": ", file
            fileList.append(file[0])
        return fileList

    def getSequenceParameters(self, protName):
        if protName not in self.sequenceParameters:
            if len(self.series) == 0:
                fileInfo= self.seriesFileInfo[protName]
            else:
                fileInfo= self.series[self.suid[protName][0]]
            dcm = dicom.read_file(fileInfo[0][0], stop_before_pixels=False, force= True)
            acquisitionTimes= []
            sliceLocations= []
            for file in fileInfo:
                acquisitionTimes.append(file[1])
                if self.type != 'enhancedDICOM':
                    sliceLocations.append(file[2])
            if self.type != 'enhancedDICOM':
                nt = Counter(sliceLocations)[sliceLocations[0]]
                nz = Counter(acquisitionTimes)[acquisitionTimes[0]]
                # for unusual cases e.g. bold
                if nz*nt > len(fileInfo):
                    nt= len(fileInfo)/nz
            else:
                nf = dcm.NumberOfFrames - 1
                nz= dcm.PerFrameFunctionalGroupsSequence[nf].FrameContentSequence[0].DimensionIndexValues[2]
                # could get the nt from the DimensionIndexValues[3] array for a 4D image, but for a 3D image this
                # will not exist
                nt= nf / nz
            self.sequenceParameters[protName]= [dcm.Rows, dcm.Columns, nz, nt]
        return self.sequenceParameters[protName]

    def getSeriesList(self):
        if len(self.orderedSeries) == 0:
            seriesSorted = sorted(self.suid.items(), key=lambda info: info[1])
            for i, series in enumerate(seriesSorted):
                self.orderedSeries.append(series[0])
        return self.orderedSeries