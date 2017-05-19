from .iopanel import InputPanel, OutputPanel
from . import canvas, glob, utils
from main.circuit import Gate

import abc
import inspect
import pickle
import sys

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

		scene = self.canvas.scene
		self.in_panel = None
		self.out_panel = None
		scene.new_circuit.connect(self.refresh)

		self.menu_bar = MenuBar(self)
		self.setMenuBar(self.menu_bar)

		scene.circuit_changed.connect(self.statusBar().clearMessage)
		scene.status.connect(self.statusBar().showMessage)

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


class PanelToolBar(QToolBar, abc.ABC, metaclass=utils.AbstractWidgetMeta):
	def __init__(self, *args):
		super().__init__(*args)
		self.setFloatable(False)
		self.setMovable(False)


class RunToolBar(PanelToolBar):
	def __init__(self, *args):
		super().__init__(*args)

		w = QWidget(self)
		self.run_button = QPushButton("Run", w)
		self.run_button.setFont(QFont('Arial', 12, QFont.Bold))
		self.run_button.setMinimumHeight(40)
		self.run_button.clicked.connect(self.parent().run)

		hbox = QHBoxLayout(w)
		hbox.setContentsMargins(0, 5, 5, 0)
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
		self.new.setShortcut(QKeySequence.New)
		self.new.setToolTip("Open a new blank circuit")
		self.new.triggered.connect(self.new_dialog)

		self.save = QAction("Save", self)
		self.save.setShortcut(QKeySequence.Save)
		self.save.setToolTip("Save current circuit")
		self.save.triggered.connect(self.save_dialog)

		self.open = QAction("Open", self)
		self.open.setShortcut(QKeySequence.Open)
		self.open.setToolTip("Open circuit file")
		self.open.triggered.connect(self.open_dialog)

		self.exit = QAction("Exit", self)
		self.exit.setShortcut(QKeySequence.Quit)
		self.exit.setToolTip("Exit application")
		self.exit.triggered.connect(qApp.quit)

		self.file = self.addMenu("File")
		self.file.addAction(self.new)
		self.file.addSeparator()
		self.file.addAction(self.save)
		self.file.addAction(self.open)
		self.file.addSeparator()
		self.file.addAction(self.exit)

		self.fit = QAction("Fit View", self)
		self.fit.setShortcut(Qt.CTRL | Qt.Key_F)
		self.fit.setToolTip("Fit the viewport to the circuit's bounding rectangle")
		self.fit.triggered.connect(self.parent().canvas.view.fit_to_scene)

		self.prettify = QAction("Prettify", self)
		self.prettify.setShortcut(Qt.CTRL | Qt.Key_P)
		self.prettify.setToolTip("Lay the circuit out automatically in a nice way")
		self.prettify.triggered.connect(self.parent().canvas.scene.prettify)

		self.set_input = QAction("Set Input", self)
		self.set_input.setShortcuts((Qt.Key_Insert, Qt.CTRL | Qt.Key_I))
		self.set_input.setToolTip("Set the input vector")
		self.set_input.triggered.connect(self.input_dialog)

		self.circuit = self.addMenu("Circuit")
		self.circuit.addAction(self.fit)
		self.circuit.addAction(self.prettify)
		self.circuit.addSeparator()
		self.circuit.addAction(self.set_input)

	def new_dialog(self):
		size, ok = QInputDialog.getInt(self.parent(), "Size", "Set circuit size", len(glob.circuit), 1)
		if ok:
			self.parent().canvas.scene.new(size)

	def input_dialog(self):
		while True:
			text, ok = QInputDialog.getText(self.parent(), "Set Input", "Input vector:", text=str(glob.in_vector))
			if not ok:
				break
			if len(text) != len(glob.circuit):
				QMessageBox.warning(self, "Length Mismatch", "Input length does not match circuit size.")
			else:
				try:
					glob.in_vector.set(text)
					break
				except ValueError:
					QMessageBox.warning(self, "Illegal Value", "Only binary values are allowed.")

	def save_dialog(self):
		fname, _ = QFileDialog.getSaveFileName(self.parent(), "Save", "../Resources/Saved/", "Circuits (*.cir)")
		if fname:
			self.parent().canvas.scene.save(fname)

	def open_dialog(self):
		fname, _ = QFileDialog.getOpenFileName(self.parent(), "Open", "../Resources/Saved/", "Circuits (*.cir)")
		if fname:
			self.parent().canvas.scene.load(fname)


class BuildToolBar(PanelToolBar):
	def __init__(self, *args):
		super().__init__(*args)

		w = QWidget(self)
		hbox = QHBoxLayout(w)
		hbox.setContentsMargins(100, 10, 100, 10)
		hbox.setSpacing(20)

		gate_check = lambda t: inspect.isclass(t) and issubclass(t, Gate) and t is not Gate
		gates = [g for _, g in inspect.getmembers(sys.modules['main.circuit'], gate_check)]
		gates.sort(key=lambda g: (g.SIZE, len(g.__name__), g.__name__))
		for g in gates:
			hbox.addWidget(GateLabel(g, w), 0, Qt.AlignLeft)

		self.addWidget(w)


class GateLabel(QLabel):
	def __init__(self, gate_type, *args):
		super().__init__(utils.shorten(gate_type.__name__), *args)
		self.type = gate_type

		self.setAlignment(Qt.AlignCenter)
		self.setFixedSize(40, 40)
		self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
		utils.set_background_color(self, Qt.white)

	def mouseMoveEvent(self, e):
		if e.buttons() == Qt.LeftButton:
			mime = QMimeData()
			mime.setData('application/gate-type', pickle.dumps(self.type))
			drag = QDrag(self)
			drag.setMimeData(mime)
			drag.setHotSpot(e.pos() - self.rect().center())
			drop_action = drag.exec_(Qt.CopyAction)
			if not drop_action:
				self.parent().parent().parent().canvas.scene.build_gate(None)
			e.accept()
		else:
			e.ignore()
			super().mouseMoveEvent(e)

	def paintEvent(self, *args):
		qp = QPainter()
		qp.begin(self)
		self._draw(qp)
		qp.end()
		super().paintEvent(*args)

	def _draw(self, qp):
		qp.setPen(QPen(Qt.black, 2))
		qp.setBrush(QBrush(Qt.NoBrush))
		qp.drawRect(self.rect())
