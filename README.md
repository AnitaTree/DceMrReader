# DceMrReader
Python code for reading in DICOM DCE-MRI series and selecting AIF voxels.

We would be grateful if you would reference the following abstract if you use this code:
Anita Banerji, Derek Magee, Constantina Chrysochou, Philip Kalra, David Buckley, and Steven Sourbron. "Assessment of an automated method for AIF voxel selection for renal filtration rate estimation from DCE-MRI data." Proceedings of the ISMRM (Singapore), 2016: 2865.

NOT FOR CLINICAL USE. FOR RESEARCH PURPOSES ONLY.

This code has been developed to:

(1) Read DCE-MR time series from DICOM, extended DICOM and NEMA files;

(2) Provide some analysis functionality geared towards AIF voxel selection (such as generating a maximum change from average baseline map);

(3) Select AIF voxels;

(3) Save out ROIs in raw format and npz files;

(4) Save out image series as npz files.

This is not a fully tested and complete application, but more "work in progress". 
However, I thought some of the functionality might be of use to the MR research community and no further development is currently planned so I have made it available as it is.

It relies on various Python libraries and also the QT GUI libraries through the Pyside bindingd. I used QTcreator to build the interface and pyside-uic to convert the ui file to a py file. I used Pycharm as the Python IDE and would recommend this.

Made available under the MIT license. Copyright (c) 2016 Anita Banerji, University of Leeds.

The development of this code up to May 2016 was funded by Kidney Research UK and was written by Anita Banerji whilst working at the University of Leeds. This code was made available with the approval of Kidney Research UK and the University of Leeds.
