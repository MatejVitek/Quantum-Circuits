from . import glob
from .iopanel import InputPanel, OutputPanel
from main.test import create_test_circuit

import abc
import math
import random

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


UNIT = 50							# Base unit, all sizing is based on this
MIN_GAP = 0.25						# Minimum vertical gap between two gates = MIN_GAP * UNIT
WIRE_CURVE = 1.5					# Controls the wire's curvature: higher = curvier
WIRE_MIN_OFFSET = 0.5				# Minimum control point offset for short wires, should be 0 < x <= 0.5
AVOID_PORTS = False					# Should the wires avoid intersecting ports? May trade aesthetics for clarity
FONT = QFont("Courier", 10)			# The font used for gate names etc.


class Scene(QGraphicsScene):
	new_circuit = pyqtSignal(name='newCircuit')
	circuit_changed = pyqtSignal(name='circuitChanged')
	scene_changed = pyqtSignal(name='sceneChanged')

	circuit_ok = pyqtSignal(bool, name='circuitOK')

	def __init__(self, *args):
		super().__init__(*args)

		self.new_circuit.connect(self.circuit_changed)
		self.circuit_changed.connect(self.scene_changed)
		self.circuit_changed.connect(self.check_circuit)

		self.input = None
		self.output = None
		self.gates = None
		self.new(create_test_circuit(), [Qt.black, Qt.red, Qt.blue, Qt.darkGreen, Qt.magenta, Qt.darkCyan])
		self.setSceneRect(QRectF(-1e6, -1e6, 2e6, 2e6))

	def check_circuit(self):
		self.circuit_ok.emit(glob.circuit.check())

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
			self.output = OutputItem(len(circuit))
			self.addItem(self.output)

			for gate in circuit.gates:
				self.add_gate_item(gate)

			for wire in circuit.wires:
				self.add_wire_item(wire, *self._find_start_end(wire))

			#self._prettify()
			for item in self.items():
				if isinstance(item, GateItem):
					item.setPos(random.randint(0, 500), random.randint(0, 500))

		self.new_circuit.emit()

	def prettify(self):
		self._prettify()
		self.parent().view.fit_to_scene()
		self.scene_changed.emit()

	def _prettify(self):
		circuit = glob.circuit
		slices = self.slice_up(circuit)

		self.input.setPos(0, 0)

		x = 3 * UNIT
		for s in slices:
			s, pref, weights = self._slice_sorted(s)

			pos = self._layout_slice(s, pref, weights)
			for i in range(len(s)):
				gate_item = self.gates[s[i]]
				gate_item.setPos(x, pos[i])

			x += 2 * UNIT

		self.output.setPos(x, 0)

	def slice_up(self, circuit):
		remaining = set(circuit.gates)
		used = {circuit}
		slices = []
		while remaining:
			s = set(g for g in remaining if all(w.left in used for w in g.in_wires if w is not None))
			used |= s
			remaining -= s
			slices.extend(self._slice_split(s, len(circuit)))
		return slices

	def _slice_split(self, slice, size):
		split = []
		while slice:
			part = []
			while slice and self._slice_size(part) < size:
				part.append(slice.pop())
			split.append(part)
		return split

	@staticmethod
	def _slice_size(s):
		return sum(len(g) for g in s) + MIN_GAP * (len(s) - 1)

	def _slice_sorted(self, s):
		pref, weights = zip(*[self._preferred_pos(g) for g in s])
		return zip(*sorted(zip(s, pref, weights), key=lambda x: x[1]))

	def _preferred_pos(self, g):
		p = 0
		weight = len(g)

		# The preferred size and the preference strength (weight) are calculated from the gate's
		# inbound connections' connected ports, whose static positions are already known...
		for w in g.in_wires:
			if w.left is glob.circuit:
				p += self.input.ports[w.lind].center_scene_pos().y()
			else:
				p += self.gates[w.left].out_ports[w.lind].center_scene_pos().y()

		# ... and the locations of the ports on the output panel, which the gate is connected to (if any).
		for w in g.out_wires:
			if w.right is glob.circuit:
				weight += 1
				p += self.output.ports[w.rind].center_scene_pos().y()

		# The preferred position is an average of the checked port positions.
		# The weight is the number of checked ports.
		return p / weight, weight

	def _layout_slice(self, s, pref, weights):

		# A conflict is a set of gates that would clash (or require a smaller-than-minimum gap between them)
		# if they were placed at their respective preferred positions.
		# Two conflicts can then form a new conflict recursively.

		conflicts = [(g,) for g in s]
		conflict_pos = list(pref)
		conflict_weights = list(weights)

		conflict_found = True
		while conflict_found:
			conflict_found = False

			# Find a conflict and resolve it
			for i in range(len(conflicts) - 1):
				c1 = conflicts[i]
				c2 = conflicts[i+1]
				combined_size = self._slice_size(c1) + self._slice_size(c2)

				# If two single gates or previous conflicts are in a conflict
				if conflict_pos[i+1] - conflict_pos[i] < (combined_size/2 + MIN_GAP) * UNIT:
					conflict_found = True

					# Join 2 previous conflicts (or single gates) into a new conflict
					# Calculate the new conflict's overall preferred position and new weight
					w1 = conflict_weights[i]
					w2 = conflict_weights[i+1]
					new_c = c1 + c2
					new_p = (w1 * conflict_pos[i] + w2 * conflict_pos[i+1]) / (w1 + w2)
					new_w = w1 + w2

					# Remove the 2 previous conflicts (or single gates)
					del conflicts[i]
					del conflicts[i]
					del conflict_pos[i]
					del conflict_pos[i]
					del conflict_weights[i]
					del conflict_weights[i]

					# Insert the new information at that location
					conflicts.insert(i, new_c)
					conflict_pos.insert(i, new_p)
					conflict_weights.insert(i, new_w)
					break

		# Extract gate positions. Gates inside a conflict will always be as close together as possible.
		pos = []
		for c, c_pos in zip(conflicts, conflict_pos):
			y = c_pos - self._slice_size(c) / 2 * UNIT
			for g in c:
				pos.append(y)
				y += (len(g) + MIN_GAP) * UNIT

		return pos

	def add_gate_item(self, gate, pos=(0, 0)):
		g = GateItem(gate, pos)
		self.gates[gate] = g
		self.addItem(g)

	def add_wire_item(self, wire, start, end):
		w = WireItem(wire, start, end)
		self.addItem(w)

		if glob.wire_colors:
			self.circuit_changed.connect(w.determine_color)
		self.scene_changed.connect(w.update_path)

	def add_gate(self, gate_type, pos):
		gate = glob.circuit.add_gate(gate_type)
		self.add_gate_item(gate, pos)
		self.circuit_changed.emit()

	def add_wire(self, start, end):
		wire = glob.circuit.add_wire(*self._find_start_end_components_and_ports(start, end))
		self._add_wire_item(wire, start, end)
		self.circuit_changed.emit()

	def _find_start_end(self, wire):
		if wire.left is glob.circuit:
			start = self.input.ports[wire.lind]
		else:
			start = self.gates[wire.left].out_ports[wire.lind]
		if wire.right is glob.circuit:
			end = self.output.ports[wire.rind]
		else:
			end = self.gates[wire.right].in_ports[wire.rind]
		return start, end

	def _find_start_end_components_and_ports(self, start, end):
		if start.parentItem() is self.input:
			start_component = glob.circuit
			start_port = start.parentItem().ports.index(start)
		else:
			start_component = start.parentItem().gate
			start_port = start.parentItem().out_ports.index(start)
		if end.parentItem() is self.output:
			end_component = glob.circuit
			end_port = end.parentItem().ports.index(end)
		else:
			end_component = end.parentItem().gate
			end_port = end.parentItem().in_ports.index(end)
		return start_component, start_port, end_component, end_port


class IOItem(QGraphicsProxyWidget, abc.ABC, metaclass=glob.AbstractWidgetMeta):
	def __init__(self, pos, width, circuit_size, panel_type, port_align, *args):
		super().__init__(*args)
		self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
		self.setZValue(1)
		self.setWidget(panel_type(circuit_size))
		self.setGeometry(QRectF(*pos, width, circuit_size * UNIT))
		rect = self.rect()

		x = 0 if port_align & Qt.AlignLeft else rect.width() if port_align & Qt.AlignRight else rect.width()/2
		ys = self.widget().get_port_ys()
		self.ports = tuple(PortItem(QPointF(x, ys[i]), self) for i in range(circuit_size))

	def itemChange(self, change, value):
		if change == QGraphicsItem.ItemScenePositionHasChanged:
			self.scene().scene_changed.emit()
		return QGraphicsProxyWidget.itemChange(self, change, value)


class InputItem(IOItem):
	def __init__(self, size, pos=(0, 0), *args):
		super().__init__(pos, 60, size, InputPanel, Qt.AlignRight, *args)


class OutputItem(IOItem):
	def __init__(self, size, pos=(0, 0), *args):
		super().__init__(pos, 30, size, OutputPanel, Qt.AlignLeft, *args)


class GateItem(QGraphicsRectItem):
	def __init__(self, gate, pos=(0, 0), *args):
		super().__init__(*pos, UNIT, len(gate) * UNIT, *args)
		self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
		self.gate = gate
		self.setBrush(QBrush(Qt.white))
		rect = self.rect()

		self.text = QGraphicsSimpleTextItem(str(gate), self)
		self.text.setFont(FONT)
		text_rect = self.text.boundingRect()
		self.text.setPos(rect.center().x() - text_rect.width()/2, rect.center().y() - text_rect.height()/2)

		ys = tuple((i + 0.5) * rect.height() / len(gate) for i in range(len(gate)))
		self.in_ports = tuple(PortItem(QPointF(0, ys[i]), self) for i in range(len(gate)))
		self.out_ports = tuple(PortItem(QPointF(rect.width(), ys[i]), self) for i in range(len(gate)))

	def itemChange(self, change, value):
		if change == QGraphicsItem.ItemScenePositionHasChanged:
			self.scene().scene_changed.emit()
		return QGraphicsItem.itemChange(self, change, value)


class PortItem(QGraphicsEllipseItem):
	SIZE = 8

	def __init__(self, center, *args):
		super().__init__(glob.create_square(center, self.SIZE), *args)
		self.center = center
		self.setBrush(QBrush(Qt.black))

	def center_scene_pos(self):
		return self.parentItem().scenePos() + self.center


class WireItem(QGraphicsPathItem):
	def __init__(self, wire, start, end, *args):
		super().__init__(*args)
		self.wire = wire
		self.setZValue(-1)

		self.start = start
		self.end = end

		self._shape = None
		self.setPen(QPen(QBrush(Qt.black), 3))

	def determine_color(self):
		wire = self.wire
		visited_gates = set()
		color = Qt.black

		while True:
			# Stop if a port is unconnected.
			if wire is None:
				break

			# If the input panel was reached, determine the correct color.
			if wire.left is glob.circuit:
				color = glob.wire_colors[wire.lind]
				break

			# Stop if there's a cycle (prevent infinite loops).
			if wire.left is None or wire.left in visited_gates:
				break

			visited_gates.add(wire.left)
			wire = wire.left.in_wires[wire.lind]

		pen = self.pen()
		pen.setColor(color)
		self.setPen(pen)

	def update_path(self):
		source = self.mapFromScene(self.start.center_scene_pos())
		sink = self.mapFromScene(self.end.center_scene_pos())
		path = self._path_between(source, sink)

		if AVOID_PORTS:
			path = self._subdivide_at_intersects(source, sink, path)

		self.setPath(path)

	# Return the bezier curve (or spline) between the two points
	@classmethod
	def _path_between(cls, start, stop):
		path = QPainterPath()

		if start.x() < stop.x():
			delta = stop - start
			dist = math.sqrt(delta.x()**2 + delta.y()**2)
			offset = min(WIRE_MIN_OFFSET * dist, WIRE_CURVE * UNIT)
			path.moveTo(start)
			path.cubicTo(start + QPointF(offset, 0), stop - QPointF(offset, 0), stop)

		else:
			offset = WIRE_MIN_OFFSET * UNIT
			mid = (start + stop) / 2
			if abs(mid.y() - start.y()) < offset:
				mid.setY(start.y() + math.copysign(2 * offset, mid.y() - start.y()))

			spline = cls._spline((
				start,
				start + QPointF(offset, 0),
				QPointF(start.x() + offset, mid.y()),
				QPointF(stop.x() - offset, mid.y()),
				stop - QPointF(offset, 0),
				stop
			))

			for start, p1, p2, stop in spline:
				path.moveTo(start)
				path.cubicTo(p1, p2, stop)

		return path

	@staticmethod
	def _spline(d):
		m = len(d) - 3
		bs = [[d[0], d[1], (d[1] + d[2])/2, None]]

		for l in range(m-2):
			bs.append([None, 2/3 * d[l+2] + 1/3 * d[l+3], 1/3 * d[l+2] + 2/3 * d[l+3], None])
		bs.append([None, 1/2 * d[-3] + 1/2 * d[-2], d[-2], d[-1]])

		for l in range(m-1):
			bs[l][3] = bs[l+1][0] = 1/2 * bs[l][2] + 1/2 * bs[l+1][1]

		return bs

	def _subdivide_at_intersects(self, start, stop, path):
		p1, p2 = self._intersected_port(path)
		print("A", p1, p2, start, stop)
		if p1 or p2:
			if p1:
				p2 = p1 + QPointF(UNIT, 0)
			elif p2:
				p1 = p2 - QPointF(UNIT, 0)
			path1 = self._path_between(start, p1)
			path2 = self._path_between(p2, stop)
			print("B", start, p1)
			path = self._subdivide_at_intersects(start, p1, path1) + self._subdivide_at_intersects(p2, stop, path2)
		return path

	def _intersected_port(self, path):
		for g in self.scene().gates.values():
			for p in g.in_ports:
				if p is not self.end and path.intersects(p.rect()):
					return None, self._get_better_pos(path, p)
			for p in g.out_ports:
				if p is not self.start and path.intersects(p.rect()):
					return self._get_better_pos(path, p), None
		return None, None

	@staticmethod
	def _get_better_pos(path, port):
		offset = 0.25 * QPointF(0, UNIT)
		return port.center_scene_pos() + offset

	def setPen(self, *args):
		self.prepareGeometryChange()
		super().setPen(*args)

	def shape(self):
		if self._shape is None:
			self._shape = self._stroke_path()
		return self._shape

	def setPath(self, *args):
		self.prepareGeometryChange()
		self._shape = None
		super().setPath(*args)

	def _stroke_path(self):
		pen = QPen(QBrush(Qt.black), self.pen().widthF(), Qt.SolidLine)
		stroker = QPainterPathStroker()
		stroker.setCapStyle(pen.capStyle())
		stroker.setJoinStyle(pen.joinStyle())
		stroker.setMiterLimit(pen.miterLimit())
		stroker.setWidth(pen.widthF())
		return stroker.createStroke(self.path())
