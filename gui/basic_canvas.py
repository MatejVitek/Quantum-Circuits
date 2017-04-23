from gui import globals

from random import randint as rnd

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class Canvas(QWidget):
	def __init__(self, wire_colors, *args):
		super().__init__(*args)

		self._colors = None
		self.set_colors(wire_colors)

		self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))

		p = self.palette()
		p.setColor(self.backgroundRole(), Qt.white)
		self.setPalette(p)
		self.setAutoFillBackground(True)

	def sizeHint(self):
		return QSize(1e6, 1e6)

	def set_colors(self, colors):
		circuit = globals.circuit
		if colors is None or colors is False:
			return
		elif colors is True or not colors:
			self._colors = [QColor(rnd(0, 200), rnd(0, 200), rnd(0, 200)) for _ in range(len(circuit))]
		elif len(circuit) != len(colors):
			raise RuntimeError("Size of color vector does not match the size of the circuit.")
		else:
			self._colors = colors

	def paintEvent(self, e):
		qp = QPainter()
		qp.begin(self)
		self._draw(qp)
		qp.end()

	def _draw(self, qp):
		circuit = globals.circuit
		circuit.sort()
		size = len(circuit)
		gates = circuit.gates
		wire_ys = self.parent().get_port_ys()

		# Draw wires
		qp.setPen(QPen(Qt.black, 2, Qt.SolidLine))
		for i in range(size):
			if self._colors:
				qp.setPen(QPen(self._colors[i], 2, Qt.SolidLine))
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
		while wire.left is not globals.circuit:
			wire = wire.left.in_wires[wire.lind]
		return wire.lind

	@staticmethod
	def _follow_wire_right(wire):
		while wire.right is not globals.circuit:
			wire = wire.right.out_wires[wire.rind]
		return wire.rind
