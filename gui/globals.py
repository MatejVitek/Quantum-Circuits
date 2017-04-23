from PyQt5.QtCore import pyqtWrapperType
from abc import ABCMeta


circuit = None


class AbstractWidgetMeta(pyqtWrapperType, ABCMeta):
	pass
