from .view import View
from .scene import Scene

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class Canvas(QWidget):
	def __init__(self, *args):
		super().__init__(*args)

		self.scene = Scene(self)
		self.view = View(self.scene, self)

		vbox = QVBoxLayout(self)
		vbox.setContentsMargins(0, 0, 0, 0)
		vbox.addWidget(self.view, Qt.AlignCenter)

	# TODO: Add I/O panels when I/O Graphics Items are out of view
