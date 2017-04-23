from gui.basic_canvas import Canvas
from gui import globals

import abc

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class MainWindow(QMainWindow):
	def __init__(self, *args):
		super().__init__(*args)
		self._init_ui()

	def _init_ui(self):
		self.panel = MainPanel(self)
		self.run_panel = RunPanel(self)
		self.setCentralWidget(self.panel)
		self.addToolBar(Qt.BottomToolBarArea, self.run_panel)

		self.setWindowTitle("Quantum Circuits")
		self.setWindowIcon(QIcon("../Resources/Icon.png"))
		self.reset_placement()

	def run(self):
		pass

	def get_input(self):
		return [int(field.text()) for field in self._input]

	def set_output(self, v):
		for i in range(len(v)):
			self._output[i] = str(v[i])

	def reset_placement(self):
		g = QDesktopWidget().availableGeometry()
		self.resize(0.4 * g.width(), 0.4 * g.height())
		self.move(g.center().x() - self.width() / 2, g.center().y() - self.height() / 2)

	def minimumHeight(self):
		# TODO: Add +self.top_toolbar.height()
		# FIXME: This doesn't actually restrict resizing
		return self.run_panel.height() + len(globals.circuit) * 20


class MainPanel(QWidget):
	def __init__(self, *args):
		super().__init__(*args)

		self.canvas = Canvas(True, self)
		self.in_panel = InputPanel(self)
		self.out_panel = OutputPanel(self)

		hbox = QHBoxLayout(self)
		hbox.setContentsMargins(0, 0, 0, 0)
		hbox.addWidget(self.in_panel, 0, Qt.AlignLeft)
		hbox.addWidget(self.canvas, 0, Qt.AlignCenter)
		hbox.addWidget(self.out_panel, 0, Qt.AlignRight)

	def get_port_ys(self):
		return [f.y() + f.height() / 2 for f in self.in_panel.fields]


class IOPanel(QWidget, abc.ABC, metaclass=globals.AbstractWidgetMeta):
	def __init__(self, field_type, align, *args):
		super().__init__(*args)
		self.fields = [field_type(self) for _ in range(len(globals.circuit))]

		vbox = QVBoxLayout(self)
		vbox.setContentsMargins(5, 0, 5, 0)
		for f in self.fields:
			vbox.addWidget(f, 0, align)
		self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred))

	def minimumSizeHint(self):
		return QSize(30, 0)

	def set_vector(self, v):
		if len(v) != len(self.fields):
			raise RuntimeError("Vector dimension mismatch.")
		for i in range(len(v)):
			self.fields[i].set_value(int(v[i]))

	def get_vector(self):
		return [int(f.get_value()) for f in self.fields]


class InputPanel(IOPanel):
	def __init__(self, *args):
		super().__init__(InputField, Qt.AlignRight, *args)


class OutputPanel(IOPanel):
	def __init__(self, *args):
		super().__init__(OutputField, Qt.AlignLeft, *args)


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
		self.button.clicked.connect(self.toggle_value)
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

	def set_value(self, v):
		if v not in (0, 1):
			raise RuntimeError("Only binary values allowed.")
		self.label.setText(str(v))

	def get_value(self):
		return int(self.label.text())


class RunPanel(QToolBar):
	def __init__(self, *args):
		super().__init__(*args)
		self.setFloatable(False)
		self.setMovable(False)

		w = QWidget(self)
		self.run_button = QPushButton("Run", w)
		self.run_button.clicked.connect(self.parent().run)

		hbox = QHBoxLayout(w)
		hbox.addStretch(1)
		hbox.addWidget(self.run_button, 0, Qt.AlignRight)
		self.addWidget(w)
