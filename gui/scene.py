UNIT = 50							# Base unit, all sizing is based on this
MIN_GAP = 0.25						# Minimum vertical gap between two gates = MIN_GAP * UNIT


from .wires import WireItem, PartialWireItem
from .nodes import GateItem, InputItem, OutputItem
from . import glob
# from main import Grover
from main.test import create_test_circuit

import pickle

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class Scene(QGraphicsScene):
	new_circuit = pyqtSignal(name='newCircuit')
	circuit_changed = pyqtSignal(name='circuitChanged')
	scene_changed = pyqtSignal(name='sceneChanged')
	circuit_ok = pyqtSignal(bool, name='circuitOK')
	status = pyqtSignal(str, name='cycle')

	def __init__(self, *args):
		super().__init__(*args)

		self.new_circuit.connect(self.circuit_changed)
		self.circuit_changed.connect(self.scene_changed)
		self.circuit_changed.connect(self.check_circuit)

		self.input = None
		self.output = None
		self.gates = None
		self.new(create_test_circuit(), [Qt.black, Qt.red, Qt.blue, Qt.darkGreen, Qt.magenta, Qt.darkCyan])
		# self.new(Grover.c, [])

		self.partial_gate = None
		self.partial_wire = None

		self.setSceneRect(QRectF(-1e6, -1e6, 2e6, 2e6))

	def new(self, circuit, colors=None):
		self.blockSignals(True)

		self.gates = {}
		self.clear()
		self.partial_wire = None

		if isinstance(circuit, int):
			glob.new_circuit(circuit, colors)
			self._add_io_items(circuit)

		else:
			glob.set_circuit(circuit, colors)
			self._add_io_items(len(circuit))

			for gate in circuit:
				self._add_gate_item(gate)

			for wire in circuit.wires:
				self._add_wire_item(wire, *self._find_start_end(wire))

			self.prettify()

		self.blockSignals(False)
		self.new_circuit.emit()

	def save(self, fname):
		with open(fname, 'wb') as f:
			pickle.dump(glob.circuit, f)
			pickle.dump(glob.in_vector.get(), f)
			pickle.dump(glob.out_vector.get(), f)
			pickle.dump(glob.wire_colors, f)
			pickle.dump(self.input.scenePos(), f)
			pickle.dump(self.output.scenePos(), f)
			pickle.dump({g: self.gates[g].scenePos() for g in glob.circuit}, f)

	def load(self, fname):
		with open(fname, 'rb') as f:
			circuit = pickle.load(f)
			in_v = pickle.load(f)
			out_v = pickle.load(f)
			colors = pickle.load(f)
			input_pos = pickle.load(f)
			output_pos = pickle.load(f)
			g_pos = pickle.load(f)

		self.new(circuit, colors if colors else False)
		glob.in_vector.set(in_v)
		glob.out_vector.set(out_v)
		self.input.setPos(input_pos)
		self.output.setPos(output_pos)
		for g in glob.circuit:
			self.gates[g].setPos(g_pos[g])
		self.scene_changed.emit()

	def check_circuit(self):
		self.circuit_ok.emit(glob.circuit.check())

	def build_gate(self, pos, gate_type=None):
		if pos is None:
			if self.partial_gate is not None:
				self.removeItem(self.partial_gate)
				self.partial_gate = None

		else:
			if self.partial_gate is None:
				height = gate_type.SIZE * UNIT if gate_type else UNIT
				self.partial_gate = QGraphicsRectItem(QRectF(0, 0, UNIT, height))
				self.partial_gate.setBrush(QBrush(Qt.white))
				self.addItem(self.partial_gate)
			pos -= QPointF(self.partial_gate.boundingRect().width(), self.partial_gate.boundingRect().height()) / 2
			self.partial_gate.setPos(pos)

	def build_wire(self, port):
		if port is None:
			if self.partial_wire is not None:
				self.removeItem(self.partial_wire)
				self.partial_wire = None

		elif self.partial_wire is None:
			self.partial_wire = PartialWireItem(port)
			if self._invalid(port, None):
				self.partial_wire.reverse = True
			self.addItem(self.partial_wire)

		else:
			start = self.partial_wire.start
			end = port
			if self.partial_wire.reverse:
				start, end = end, start
			if start is end:
				self.status.emit("Cannot connect port to itself.")
			elif self._invalid(start, end):
				self.status.emit("Connect an input port and an output port.")
			else:
				item = self.add_wire(start, end)
				if glob.circuit.contains_cycle():
					self.status.emit("Circuit should not contain cycles.")
					self.remove_wire_item(item)
			self.build_wire(None)

	def _invalid(self, start, end):
		return (
			start is not None and start.parentItem() is self.output or
			start is not None and isinstance(start.parentItem(), GateItem) and start in start.parentItem().in_ports or
			end is not None and end.parentItem() is self.input or
			end is not None and isinstance(end.parentItem(), GateItem) and end in end.parentItem().out_ports
		)

	def _add_io_items(self, size):
		self.input = InputItem(size)
		self.addItem(self.input)
		self.input.setPos(0, 0)

		self.output = OutputItem(size)
		self.addItem(self.output)
		self.output.setPos(10 * UNIT, 0)

	def _add_gate_item(self, gate):
		g = GateItem(gate)
		self.gates[gate] = g
		self.addItem(g)
		self.circuit_changed.connect(g.update_text)
		return g

	def _add_wire_item(self, wire, start, end):
		w = WireItem(wire, start, end)
		self.addItem(w)

		if glob.wire_colors:
			self.circuit_changed.connect(w.determine_color)
		self.scene_changed.connect(w.update_path)

		return w

	def remove_gate_item(self, g):
		del self.gates[g.gate]
		for port in g.in_ports + g.out_ports:
			if port.wire:
				self.remove_wire_item(port.wire)
		glob.circuit.remove_gate(g.gate)
		self.removeItem(g)
		del g

	def remove_wire_item(self, w):
		w.start.disconnect()
		w.end.disconnect()
		glob.circuit.remove_wire(w.wire)
		self.removeItem(w)
		del w

	def add_gate(self, gate_type, pos):
		gate = glob.circuit.add_gate(gate_type)
		item = self._add_gate_item(gate)
		item.setPos(pos - QPointF(item.boundingRect().width(), item.boundingRect().height()) / 2)
		self.circuit_changed.emit()
		return item

	def add_wire(self, start, end):
		wire = glob.circuit.add_wire(*self._find_start_end_components_and_ports(start, end))
		item = self._add_wire_item(wire, start, end)
		self.circuit_changed.emit()
		return item

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

	def prettify(self):
		circuit = glob.circuit
		slices = self.slice_up(circuit)

		self.input.setPos(0, 0)
		self.output.setPos((2 * len(slices) + 3) * UNIT, 0)

		x = 3 * UNIT
		for s in slices:
			s, pref, weights = self._slice_sorted(s)

			pos = self._layout_slice(s, pref, weights)
			for i in range(len(s)):
				gate_item = self.gates[s[i]]
				gate_item.setPos(x, pos[i])

			x += 2 * UNIT

		self.scene_changed.emit()

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
		weight = 0

		# The preferred size and the preference strength (weight) are calculated from the gate's
		# inbound connections' connected ports, whose static positions are already known...
		for w in g.in_wires:
			if w is None:
				continue
			weight += 1
			if w.left is glob.circuit:
				p += self.input.ports[w.lind].center_scene_pos().y()
			else:
				p += self.gates[w.left].out_ports[w.lind].center_scene_pos().y()

		# ... and the locations of the ports on the output panel, which the gate is connected to (if any).
		for w in g.out_wires:
			if w is None:
				continue
			if w.right is glob.circuit:
				weight += 1
				p += self.output.ports[w.rind].center_scene_pos().y()

		# If weight is zero, return a central preferred position and a very small weight to deal with division by 0.
		if weight == 0:
			return self.input.scenePos().y() + self.input.rect().height()/2, 1e-6

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

	def keyPressEvent(self, e):
		if e.matches(QKeySequence.Delete) and self.selectedItems():
			for item in self.selectedItems():
				if isinstance(item, GateItem):
					self.remove_gate_item(item)
				elif isinstance(item, WireItem):
					self.remove_wire_item(item)
			e.accept()
			self.circuit_changed.emit()
		elif e.matches(QKeySequence.Cancel):
			self.build_wire(None)
			e.accept()
		else:
			e.ignore()

	def mousePressEvent(self, e):
		if e.button() == Qt.RightButton and self.partial_wire:
			self.build_wire(None)
			e.accept()
		return super().mousePressEvent(e)
