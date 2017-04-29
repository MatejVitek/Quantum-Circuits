from . import glob
from .iopanel import InputPanel, OutputPanel
from main.test import create_test_circuit

import abc

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


UNIT = 50
FONT = QFont("Courier", 10)


class Scene(QGraphicsScene):
	new_circuit = pyqtSignal(name='newCircuit')
	circuit_changed = pyqtSignal(name='circuitChanged')
	scene_changed = pyqtSignal(name='sceneChanged')

	def __init__(self, *args):
		super().__init__(*args)

		self.new_circuit.connect(self.circuit_changed)
		self.circuit_changed.connect(self.scene_changed)
		self.scene_changed.connect(lambda: print("SCENE CHANGED"))

		self.input = None
		self.output = None
		self.gates = None
		self.new(create_test_circuit(), True)
		self.setSceneRect(QRectF(-1e6, -1e6, 2e6, 2e6))

	def new(self, circuit, colors=None):
		for item in self.items():
			del item
		self.gates = {}

		if isinstance(circuit, int):
			glob.new_circuit(circuit, colors)

		else:
			glob.set_circuit(circuit, colors)

			self.input = InputItem(len(circuit))
			self.addItem(self.input)
			self.input.xChanged.connect(self.scene_changed)
			self.input.yChanged.connect(self.scene_changed)
			self.input.zChanged.connect(self.scene_changed)

			self.output = OutputItem(len(circuit))
			self.addItem(self.output)
			self.output.xChanged.connect(self.scene_changed)
			self.output.yChanged.connect(self.scene_changed)
			self.output.zChanged.connect(self.scene_changed)

			for gate in circuit.gates:
				self._add_gate_item(gate)

			for wire in circuit.wires:
				self._add_wire_item(wire)

			self.prettify()

		self.new_circuit.emit()

	def _add_wire_item(self, wire):
		if wire.left is glob.circuit:
			start = self.input.ports[wire.lind]
		else:
			start = self.gates[wire.left.uuid].out_ports[wire.lind]
		if wire.right is glob.circuit:
			end = self.output.ports[wire.rind]
		else:
			end = self.gates[wire.right.uuid].in_ports[wire.rind]

		w = WireItem(wire, start, end)
		self.addItem(w)

		if glob.wire_colors:
			self.circuit_changed.connect(w.determine_color)
		self.scene_changed.connect(w.update_path)

	def _add_gate_item(self, gate, pos=(0, 0)):
		g = GateItem(gate, pos)
		self.gates[gate.uuid] = g
		self.addItem(g)
		g.qobj.xChanged.connect(self.scene_changed)
		g.qobj.yChanged.connect(self.scene_changed)
		g.qobj.zChanged.connect(self.scene_changed)

	def add_gate(self, gate, pos):
		g = GateItem(gate, pos)
		self.gates[gate.uuid] = g
		self.addItem(g)
		self.circuit_changed.emit()

	def add_wire(self, wire):
		self._add_wire_item(wire)
		self.circuit_changed.emit()

	def prettify(self):
		# TODO: Implement
		pass


class IOItem(QGraphicsProxyWidget, abc.ABC, metaclass=glob.AbstractWidgetMeta):
	def __init__(self, pos, width, circuit_size, panel_type, port_align, *args):
		super().__init__(*args)
		self.setZValue(1)
		self.setWidget(panel_type(circuit_size))
		self.setGeometry(QRectF(*pos, width, circuit_size * UNIT))
		rect = self.rect()

		x = 0 if port_align & Qt.AlignLeft else rect.width() if port_align & Qt.AlignRight else rect.width()/2
		ys = self.widget().get_port_ys()
		self.ports = tuple(PortItem(QPointF(x, ys[i]), self) for i in range(circuit_size))


class InputItem(IOItem):
	def __init__(self, size, pos=(0, 0), *args):
		super().__init__(pos, 60, size, InputPanel, Qt.AlignRight, *args)


class OutputItem(IOItem):
	def __init__(self, size, pos=(0, 0), *args):
		super().__init__(pos, 30, size, OutputPanel, Qt.AlignLeft, *args)


class GateItem(QGraphicsRectItem):
	def __init__(self, gate, pos=(0, 0), *args):
		super().__init__(*pos, UNIT, len(gate) * UNIT, *args)
		self.gate = gate
		self.qobj = EmptyQGraphicsObject(self)
		self.setBrush(QBrush(Qt.white))
		rect = self.rect()

		self.text = QGraphicsSimpleTextItem(str(gate), self)
		self.text.setFont(FONT)
		text_rect = self.text.boundingRect()
		self.text.setPos(rect.center().x() - text_rect.width()/2, rect.center().y() - text_rect.height()/2)

		ys = tuple((i + 0.5) * rect.height() / len(gate) for i in range(len(gate)))
		self.in_ports = tuple(PortItem(QPointF(0, ys[i]), self) for i in range(len(gate)))
		self.out_ports = tuple(PortItem(QPointF(rect.width(), ys[i]), self) for i in range(len(gate)))


class PortItem(QGraphicsEllipseItem):
	SIZE = 10

	def __init__(self, center, *args):
		super().__init__(glob.create_square(center, self.SIZE), *args)
		self.setBrush(QBrush(Qt.black))


class EmptyQGraphicsObject(QGraphicsObject):
	def boundingRect(self):
		return QRectF(0, 0, 0, 0)

	def paint(self, qp, style, widget=None):
		return


class WireItem(QGraphicsPathItem):
	def __init__(self, wire, start, end, *args):
		super().__init__(*args)
		self.wire = wire
		self.setZValue(-1)

		self.start = start
		self.end = end

		self._shape = None
		self.setPen(QPen(QBrush(Qt.black), 2.0))

	def determine_color(self):
		wire = self.wire
		visited_gates = set()
		while True:
			# Stop checking if an appropriate port was unconnected.
			if wire is None:
				self.pen().setColor(Qt.black)
				return
			# If the circuit was reached, determine the correct color.
			if wire.left is glob.circuit:
				self.pen().setColor(glob.wire_colors[wire.lind])
				return
			# Stop checking if there's a cycle (to prevent infinite loops).
			if wire.left is None or wire.left.uuid in visited_gates:
				self.pen().setColor(Qt.black)
				return
			visited_gates.add(wire.left.uuid)
			wire = wire.left.in_wires[wire.lind]

	def update_path(self):
		# TODO: Implement
		self.setPath(QPainterPath())

	def setPen(self, pen):
		self.prepareGeometryChange()
		super().setPen(pen)

	def shape(self):
		if self._shape is None:
			self._shape = self._stroke_path()
		return self._shape

	def setPath(self, path):
		self.prepareGeometryChange()
		self._shape = None
		super().setPath(path)

	def _stroke_path(self):
		pen = QPen(QBrush(Qt.black), self.pen().widthF(), Qt.SolidLine)
		stroker = QPainterPathStroker()
		stroker.setCapStyle(pen.capStyle())
		stroker.setJoinStyle(pen.joinStyle())
		stroker.setMiterLimit(pen.miterLimit())
		stroker.setWidth(pen.widthF())
		return stroker.createStroke(self.path())
