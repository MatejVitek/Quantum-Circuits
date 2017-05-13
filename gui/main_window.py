from .iopanel import InputPanel, OutputPanel
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
		# Deprecated canvas: self.basic_canvas = basic_canvas.Canvas(self)
		self.canvas = canvas.Canvas(self)
		self.setCentralWidget(self.canvas)

		self.build_panel = BuildToolBar(self)
		self.addToolBar(Qt.TopToolBarArea, self.build_panel)

		self.run_panel = RunToolBar(self)
		self.canvas.scene.circuit_ok.connect(self.run_panel.run_button.setEnabled)
		self.canvas.scene.check_circuit()
		self.addToolBar(Qt.BottomToolBarArea, self.run_panel)

		self.in_panel = None
		self.out_panel = None
		self.canvas.scene.new_circuit.connect(self.refresh)

		self.menu_bar = MenuBar(self)
		self.setMenuBar(self.menu_bar)

		self.setWindowTitle("Quantum Circuits")
		self.setWindowIcon(QIcon("../Resources/Icon.png"))
		self.reset_placement()

	def set_visible(self, panel, visible):
		if panel & Qt.LeftToolBarArea:
			if visible and not self.in_panel:
				self.in_panel = IOToolBar(InputPanel, self)
				self.addToolBar(self.in_panel, Qt.LeftToolBarArea)
			elif not visible and self.in_panel:
				self.removeToolBar(self.in_panel)
				self.in_panel.deleteLater()
				self.in_panel = None

		if panel & Qt.RightToolBarArea:
			if visible and not self.out_panel:
				self.out_panel = IOToolBar(OutputPanel, self)
				self.addToolBar(self.out_panel, Qt.RightToolBarArea)
			elif not visible and self.out_panel:
				self.removeToolBar(self.out_panel)
				self.out_panel.deleteLater()
				self.out_panel = None

	def refresh(self):
		panels = Qt.LeftToolBarArea if self.in_panel else 0
		panels |= Qt.RightToolBarArea if self.out_panel else 0
		self.set_visible(Qt.LeftToolBarArea | Qt.RightToolBarArea, False)
		self.set_visible(panels, True)

	def run(self):
		in_v = glob.in_vector.get()
		out_v = glob.circuit.run(in_v)
		glob.out_vector.set(out_v)

	def reset_placement(self):
		g = QDesktopWidget().availableGeometry()
		self.resize(0.6 * g.width(), 0.6 * g.height())
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
		self.panel = self.panel_type(len(glob.circuit))
		self.addWidget(self.panel)


class MenuBar(QMenuBar):
	def __init__(self, *args):
		super().__init__(*args)

		self.new = QAction("New", self)
		self.new.setShortcut('Ctrl+N')
		self.new.setToolTip("Open a new blank circuit")
		self.new.triggered.connect(self.new_dialog)

		self.exit = QAction("Exit", self)
		self.exit.setShortcut('Ctrl+Q')
		self.exit.setToolTip("Exit application")
		self.exit.triggered.connect(qApp.quit)

		self.file = self.addMenu("File")
		self.file.addAction(self.new)
		self.file.addSeparator()
		self.file.addAction(self.exit)

		self.fit = QAction("Fit View", self)
		self.fit.setShortcut('Ctrl+F')
		self.fit.setToolTip("Fit the viewport to the circuit's bounding rectangle")
		self.fit.triggered.connect(self.parent().canvas.view.fit_to_scene)

		self.prettify = QAction("Prettify", self)
		self.prettify.setShortcut('Ctrl+P')
		self.prettify.setToolTip("Lay the circuit out automatically in a nice way")
		self.prettify.triggered.connect(self.parent().canvas.scene.prettify)

		self.set_input = QAction("Set Input", self)
		self.set_input.setShortcut('Ins')
		self.set_input.setToolTip("Set the input vector")
		self.set_input.triggered.connect(self.input_dialog)

		self.circuit = self.addMenu("Circuit")
		self.circuit.addAction(self.fit)
		self.circuit.addAction(self.prettify)
		self.circuit.addSeparator()
		self.circuit.addAction(self.set_input)

	def new_dialog(self):
		size, ok = QInputDialog.getInt(self, "Size", "Set circuit size", len(glob.circuit), 1)
		if ok:
			self.parent().canvas.scene.new(size)

	def input_dialog(self):
		successful = False
		while not successful:
			text, ok = QInputDialog.getText(self, "Set Input", "Input vector:", text=str(glob.in_vector))
			if ok:
				if len(text) != len(glob.circuit):
					QMessageBox.warning(self, "Length Mismatch", "Input length does not match circuit size.")
				else:
					try:
						glob.in_vector.set(text)
						successful = True
					except ValueError:
						QMessageBox.warning(self, "Illegal Value", "Only binary values are allowed.")


class BuildToolBar(PanelToolBar):
	def __init__(self, *args):
		super().__init__(*args)

		w = QWidget(self)

		hbox = QHBoxLayout(w)
		self.addWidget(w)
