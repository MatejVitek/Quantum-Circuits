from . import canvas, glob

import abc

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class MainWindow(QMainWindow):
	def __init__(self, *args):
		super().__init__(*args)
		self._init_ui()

	def _init_ui(self):
		#self.basic_canvas = basic_canvas.Canvas(self)
		self.canvas = canvas.Canvas(self)
		self.setCentralWidget(self.canvas)

		self.run_panel = RunToolBar(self)
		self.addToolBar(Qt.BottomToolBarArea, self.run_panel)
		self.input_panel = IOToolBar(self)
		self.canvas.scene.new_circuit.connect(self.input_panel.new)
		self.addToolBar(Qt.LeftToolBarArea, self.input_panel)
		self.output_panel = IOToolBar(self)
		self.addToolBar(Qt.RightToolBarArea, self.output_panel)
		self.canvas.scene.new_circuit.connect(self.output_panel.new)
		self.set_visible(Qt.LeftToolBarArea | Qt.RightToolBarArea, True)

		self.menu_bar = MenuBar(self)
		self.setMenuBar(self.menu_bar)

		self.setWindowTitle("Quantum Circuits")
		self.setWindowIcon(QIcon("../Resources/Icon.png"))
		self.reset_placement()

	def set_visible(self, panel, visible):
		if panel & Qt.LeftToolBarArea:
			self.input_panel.setVisible(visible)
		if panel & Qt.RightToolBarArea:
			self.output_panel.setVisible(visible)

	def run(self):
		pass

	def reset_placement(self):
		g = QDesktopWidget().availableGeometry()
		self.resize(0.4 * g.width(), 0.4 * g.height())
		self.move(g.center().x() - self.width()/2, g.center().y() - self.height()/2)

	def closeEvent(self, *args, **kwargs):
		self.deleteLater()
		super().closeEvent(*args, **kwargs)


class PanelToolBar(QToolBar, abc.ABC, metaclass=glob.AbstractWidgetMeta):
	def __init__(self, *args):
		super().__init__(*args)
		self.setFloatable(False)
		self.setMovable(False)


class RunToolBar(PanelToolBar):
	def __init__(self, *args):
		super().__init__(*args)

		w = QWidget(self)
		self.run_button = QPushButton("Run", w)
		self.run_button.clicked.connect(self.parent().run)

		hbox = QHBoxLayout(w)
		hbox.addStretch(1)
		hbox.addWidget(self.run_button, 0, Qt.AlignRight)
		self.addWidget(w)


class IOToolBar(PanelToolBar):
	def __init__(self, panel_type, *args):
		super().__init__(*args)
		self.panel_type = panel_type
		self.panel = None

	def new(self):
		if self.panel is not None:
			del self.panel
		self.addWidget(self.panel_type(len(glob.circuit)))


class MenuBar(QMenuBar):
	def __init__(self, *args):
		super().__init__(*args)

		self.exit = QAction("Exit", self)
		self.exit.setShortcut('Ctrl+Q')
		self.exit.setToolTip("Exit application")
		self.exit.triggered.connect(qApp.quit)

		self.file = self.addMenu("File")
		self.file.addAction(self.exit)

		self.fit = QAction("Fit to Scene", self)
		self.fit.setShortcut('Ctrl+F')
		self.fit.setToolTip("Fit the viewport to the circuit's bounding rectangle")
		self.fit.triggered.connect(self.parent().canvas.view.fit_to_scene)

		self.view = self.addMenu("View")
		self.view.addAction(self.fit)
