__author__ = 'medabana'

import os
import dicom

from DicomReader.PatientDirectoryReader import PatientDirectoryReader

class DicomDirFileReader(PatientDirectoryReader):
    """Responsible for reading image directories where there is a DICOMDIR file."""
    def __init__(self, dirNm, dcmdirFile):
        PatientDirectoryReader.__init__(self, dirNm)
        self._gatherSeriesFileNames(dcmdirFile)
        print "using DICOMDIR file"

    def _gatherSeriesFileNames(self, file):
        """ Read the DICOMDIR file and gather information on the image series. """
        ds= dicom.read_file(file)
        seriesRecord = None
        fileNames= []
        foundNewSeries = False
        foundImageSeries = False
        # read through the data structure and pick out the series information.
        for i, record in enumerate(ds.DirectoryRecordSequence):
            if record.DirectoryRecordType == 'SERIES':
                if foundImageSeries:
                    #found start of new series.
                    #store information on the last series now we have it all.
                    self._suidNum += 1
                    protName = str(self._suidNum) + ": " + seriesRecord.ProtocolName
                    self._suidAndTimeForProtocols[protName]= [seriesRecord.SeriesInstanceUID, seriesRecord.SeriesTime]
                    self._filesForSuid[seriesRecord.SeriesInstanceUID]= fileNames
                    self._protNamesOrdered.append(protName)
                seriesRecord= record
                fileNames= []
                foundNewSeries = True
                foundImageSeries = False
            elif foundNewSeries and record.DirectoryRecordType == 'IMAGE':
                foundImageSeries= True
                foundNewSeries = False
            if foundImageSeries and record.DirectoryRecordType == 'IMAGE':
                fileNames.append(os.path.join(*record.ReferencedFileID))
