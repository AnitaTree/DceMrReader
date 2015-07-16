__author__ = 'medabana'

from RecursiveDirectoryReader import RecursiveDirectoryReader
from DicomDirFileReader import DicomDirFileReader
import os

class DirectoryReaderSelector(object):

    def getDirectoryReader(self, dirName):
        dirNameSearch= dirName
        if os.path.basename(dirName) == 'DICOM':
            dirNameSearch= os.path.dirname(dirName)
            dirName= dirNameSearch
        for baseDir, dirNames, files in os.walk(dirNameSearch):
            for file in files:
                if file == 'DICOMDIR':
                    return DicomDirFileReader(dirName, os.path.join(baseDir, file))
        return RecursiveDirectoryReader(dirName)