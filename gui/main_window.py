from gui.basic_canvas import Canvas
from main.test import create_test_circuit

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt


class MainWindow(QMainWindow):
	def __init__(self, circuit=None):
		super().__init__()
		self.set_circuit(circuit or create_test_circuit())
		self.initUI()

	def set_circuit(self, c):
		self.circuit = c
		self.circuit.sort()

	def initUI(self):
		self.canvas = Canvas(self, True)
		self.setCentralWidget(self.canvas)
		self.addToolBar(Qt.BottomToolBarArea, self._create_run_panel())

		self.reset_placement()
		self.setWindowTitle("Quantum Circuits")
		self.setWindowIcon(QIcon("../Resources/Icon.png"))

		p = self.palette()
		p.setColor(self.backgroundRole(), Qt.white)
		self.setPalette(p)
		self.setAutoFillBackground(True)

	def _create_run_panel(self):
		tb = QToolBar(self)
		tb.setFloatable(False)
		tb.setMovable(False)

		w = QWidget(tb)

		self.run_button = QPushButton("Run", w)
		self.run_button.clicked.connect(self.run)
		hbox = QHBoxLayout(self)
		hbox.addStretch(1)
		hbox.addWidget(self.run_button)

		w.setAutoFillBackground(True)
		w.setLayout(hbox)
		tb.addWidget(w)
		tb.show()
		return tb

	def _create_input_panel(self, parent):
		w = QWidget(parent)
		w.resize(40, parent.height())

		class InputField(QLineEdit):
			def __init__(self, parent):
				super().__init__(parent)
				self.setInputMask('B')
				self.setAlignment(Qt.AlignCenter)
				self.setText(str(0))
				self.resize(20, 20)

		self._input = [InputField(w) for _ in range(len(self.circuit))]
		w.setAutoFillBackground(True)
		return w

	def _create_output_panel(self, parent):
		w = QWidget(parent)
		w.resize(40, parent.height())

		class OutputField(QLabel):
			def __init__(self, parent):
				super().__init__(parent)
				self.setAlignment(Qt.AlignCenter)
				self.setText(str(0))
				self.resize(20, 20)

		self._output = [OutputField(w) for _ in range(len(self.circuit))]
		w.setAutoFillBackground(True)
		return w

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

	def resizeEvent(self, *args, **kwargs):
		super().resizeEvent(*args, **kwargs)
		self.canvas.set_wire_ys()
		'''self.update_port_positions()

	def update_port_positions(self):
		for i in range(len(self.canvas.wire_ys)):
			input = self._input[i]
			input.move(input.parent().width() - input.width() - 10, self.canvas.wire_ys[i] - input.height() / 2)
			output = self._output[i]
			output.move(10, self.canvas.wire_ys[i] - output.height() / 2)
	'''
