from . import glob, utils
from .iopanel import InputPanel, OutputPanel

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class Canvas(QWidget):
	def __init__(self, *args):
		super().__init__(*args)

		self.main = Scene(self)
		self.in_panel = InputPanel(self, len(glob.circuit))
		self.out_panel = OutputPanel(self, len(glob.circuit))

		hbox = QHBoxLayout(self)
		hbox.setContentsMargins(0, 0, 0, 0)
		hbox.addWidget(self.in_panel, 0, Qt.AlignLeft)
		hbox.addWidget(self.main, 0, Qt.AlignCenter)
		hbox.addWidget(self.out_panel, 0, Qt.AlignRight)


class Scene(QWidget):
	def __init__(self, *args):
		super().__init__(*args)
		self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
		utils.set_background_color(self, Qt.white)

	def sizeHint(self):
		return QSize(1e6, 1e6)

	def paintEvent(self, e):
		qp = QPainter()
		qp.begin(self)
		self._draw(qp)
		qp.end()

	def _draw(self, qp):
		circuit = glob.circuit
		circuit.sort()
		size = len(circuit)
		gates = circuit.gates

		wire_ys = self.parent().in_panel.get_port_ys()

		# Draw wires
		qp.setPen(QPen(Qt.black, 2, Qt.SolidLine))
		for i in range(size):
			qp.drawLine(0, wire_ys[i], self.width(), wire_ys[i])

		# Draw circuit gates
		dx = self.width() / len(gates)
		for i in range(len(gates)):
			x = (i + 0.125) * dx
			in_inds = [self._follow_wire_left(wire) for wire in gates[i].in_wires]
			out_inds = [self._follow_wire_right(wire) for wire in gates[i].out_wires]
			min_i, max_i = min(in_inds + out_inds), max(in_inds + out_inds)

			# Draw the gate
			qp.setPen(QPen(Qt.black, 1, Qt.SolidLine))
			qp.setBrush(Qt.white)
			dy = wire_ys[0] / 2
			gate_rect = QRect(x, wire_ys[min_i] - dy, 0.75 * dx, wire_ys[max_i] - wire_ys[min_i] + 2*dy)
			qp.drawRect(gate_rect)
			qp.drawText(gate_rect, Qt.AlignCenter, str(gates[i]))

			# Draw the input/output ports
			qp.setPen(Qt.NoPen)
			qp.setBrush(Qt.black)
			p = 8
			for ind in in_inds:
				qp.drawEllipse(x - p/2, wire_ys[ind] - p/2, p, p)
			for ind in out_inds:
				qp.drawEllipse(x + 0.75 * dx - p/2, wire_ys[ind] - p/2, p, p)

	@staticmethod
	def _follow_wire_left(wire):
		while wire.left is not glob.circuit:
			wire = wire.left.in_wires[wire.lind]
		return wire.lind

	@staticmethod
	def _follow_wire_right(wire):
		while wire.right is not glob.circuit:
			wire = wire.right.out_wires[wire.rind]
		return wire.rind
