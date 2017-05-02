UNIT = 50							# Base unit, all sizing is based on this
MIN_GAP = 0.25						# Minimum vertical gap between two gates = MIN_GAP * UNIT


from .wires import WireItem
from .nodes import GateItem, InputItem, OutputItem
from . import glob
from main.test import create_test_circuit

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


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

			self._prettify()

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
