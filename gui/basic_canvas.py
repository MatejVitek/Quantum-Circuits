from main.circuit import Circuit

from random import randint as rnd

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, QRect


class Canvas(QWidget):
	def __init__(self, parent, wire_colors):
		super().__init__(parent)
		self.set_colors(wire_colors)
		self.set_wire_ys()

	def set_colors(self, colors):
		circuit = self.parent().circuit
		if colors is None or colors is False:
			self.colors = None
		elif colors is True or not colors:
			self.colors = [QColor(rnd(0, 100), rnd(0, 100), rnd(0, 100)) for _ in range(len(circuit))]
		elif len(circuit) != len(colors):
			raise RuntimeError("Size of color vector does not match the size of the circuit.")
		else:
			self.colors = colors

	def set_wire_ys(self):
		size = len(self.parent().circuit)
		self.wire_ys = [(i + 0.5) * self.height() / size for i in range(size)]

	def paintEvent(self, e):
		qp = QPainter()
		qp.begin(self)
		self._draw(qp, self.parent().circuit)
		qp.end()

	def _draw(self, qp, circuit):
		size = len(circuit)
		gates = circuit.gates

		# Draw wires
		qp.setPen(QPen(Qt.black, 2, Qt.SolidLine))
		for i in range(size):
			qp.drawLine(0, self.wire_ys[i], self.width(), self.wire_ys[i])

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
			dy = self.wire_ys[0] / 2
			gate_rect = QRect(x, self.wire_ys[min_i] - dy, 0.75 * dx, self.wire_ys[max_i] - self.wire_ys[min_i] + 2*dy)
			qp.drawRect(gate_rect)
			qp.drawText(gate_rect, Qt.AlignCenter, str(gates[i]))

			# Draw the input/output ports
			qp.setPen(Qt.NoPen)
			qp.setBrush(Qt.black)
			p = 8
			for ind in in_inds:
				qp.drawEllipse(x - p/2, self.wire_ys[ind] - p/2, p, p)
			for ind in out_inds:
				qp.drawEllipse(x + 0.75 * dx - p/2, self.wire_ys[ind] - p/2, p, p)

	@staticmethod
	def _follow_wire_left(wire):
		while not isinstance(wire.left, Circuit):
			wire = wire.left.in_wires[wire.lind]
		return wire.lind

	@staticmethod
	def _follow_wire_right(wire):
		while not isinstance(wire.right, Circuit):
			wire = wire.right.out_wires[wire.rind]
		return wire.rind
