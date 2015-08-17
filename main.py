__author__ = 'medabana'

import sys
from PySide import QtGui

from ControlMainWindow import ControlMainWindow

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    mySW = ControlMainWindow()
    mySW.show()
    sys.exit(app.exec_())
