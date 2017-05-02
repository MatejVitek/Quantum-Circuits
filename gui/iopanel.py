from . import glob

import abc
import functools

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class IOPanel(QWidget, abc.ABC, metaclass=glob.AbstractWidgetMeta):
	def __init__(self, size, field_type, align, *args):
		super().__init__(*args)
		self.fields = [field_type(self) for _ in range(size)]

		vbox = QVBoxLayout(self)
		vbox.setContentsMargins(5, 0, 5, 0)
		for f in self.fields:
			vbox.addWidget(f, 0, align)
		self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding))

	def minimumSizeHint(self):
		return QSize(30, 0)

	def get_port_ys(self):
		return tuple(f.y() + f.height()/2 for f in self.fields)

	def __len__(self):
		return len(self.fields)

	def __getitem__(self, i):
		return int(self.fields[i].label.text())

	def __setitem__(self, key, val):
		if isinstance(key, slice):
			start = key.start or 0
			stop = key.stop or len(self.fields)
			step = key.step or 1
			for i, j in zip(range(start, stop, step), range(len(val))):
				self.fields[i].label.setText(str(val[j]))
		else:
			self.fields[key].label.setText(str(val))


class InputPanel(IOPanel):
	def __init__(self, size, *args):
		super().__init__(size, InputField, Qt.AlignRight, *args)
		glob.in_vector.changed.connect(self.__setitem__)
		for i in range(len(self)):
			self.fields[i].button.clicked.connect(functools.partial(glob.in_vector.toggle, i))


class OutputPanel(IOPanel):
	def __init__(self, size, *args):
		super().__init__(size, OutputField, Qt.AlignLeft, *args)
		glob.out_vector.changed.connect(self.__setitem__)


class InputField(QWidget):
	def __init__(self, *args):
		super().__init__(*args)

		self.label = QLabel("0", self)
		self.label.setAlignment(Qt.AlignCenter)
		self.label.setFixedSize(QSize(20, 20))
		self.label.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
		p = self.label.palette()
		p.setColor(self.label.backgroundRole(), Qt.white)
		self.label.setPalette(p)
		self.label.setAutoFillBackground(True)

		self.button = QPushButton(self)
		self.button.setFixedSize(QSize(20, 15))
		self.button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
		self.button.setStyleSheet("background-color: darkBlue; border-style: none")
		x = self.button.width()
		y = self.button.height()
		points = [QPoint(0, 0), QPoint(x/2, 0), QPoint(x, y/2), QPoint(x/2, y), QPoint(0, y)]
		self.button.setMask(QRegion(QPolygon(points)))

		hbox = QHBoxLayout(self)
		hbox.setContentsMargins(0, 0, 0, 0)
		hbox.addWidget(self.button, 0, Qt.AlignLeft)
		hbox.addWidget(self.label, 0, Qt.AlignRight)

	def set_value(self, v):
		if v not in (0, 1):
			raise RuntimeError("Only binary values allowed.")
		self.label.setText(str(v))

	def get_value(self):
		return int(self.label.text())

	def toggle_value(self):
		self.label.setText(str(1 - int(self.label.text())))


class OutputField(QWidget):
	def __init__(self, *args):
		super().__init__(*args)

		self.label = QLabel("0", self)
		self.label.setAlignment(Qt.AlignCenter)
		self.label.setFixedSize(QSize(20, 20))
		self.label.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

		p = self.label.palette()
		p.setColor(self.label.backgroundRole(), Qt.white)
		self.label.setPalette(p)
		self.label.setAutoFillBackground(True)

		hbox = QHBoxLayout(self)
		hbox.setContentsMargins(0, 0, 0, 0)
		hbox.addWidget(self.label, 0, Qt.AlignLeft)
