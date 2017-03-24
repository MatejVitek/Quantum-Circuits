import abc
import random
import string
from collections import Counter


# Wire class
class Wire(object):

	# Uses left and right to avoid confusion with input/output
	def __init__(self, left, right):
		self.left = left
		self.right = right
		self.value = None

	def __str__(self):
		return str(self.left) + " --> " + str(self.right)

	def is_internal(self):
		return isinstance(self.left, Gate) and isinstance(self.right, Gate)


# Class for the entire circuit
class Circuit(object):
	def __init__(self, size):
		self.input = [None] * size
		self.output = [None] * size
		self.gates = []
		self.ordered_gates = []
		self.wires = []

		self.global_id = 0
		self.cls_ids = Counter()

	def __len__(self):
		return len(self.input)

	def __str__(self):
		return "C"

	# Add component (gate or subcircuit - subcircuits are simply treated as gates everywhere else though)
	def add(self, component):
		self.gates.append(component)
		if component.parent is not None:
			raise RuntimeError("Component is already added to a circuit.")
		self.cls_ids[component.name] += 1
		component.set_parent(self)
		self.global_id += 1

	# Add gate of type t and return the gate instance. Additional arguments will be passed to the constructor.
	def add_gate(self, t, *args):
		gate = t(*args)
		self.add(gate)
		return gate

	# Create a wire from from_port-th output port of from_component to to_port-th input port of to_component
	def add_wire(self, from_component, from_port, to_component, to_port):
		# Error checking
		if from_component not in self.gates and from_component is not self:
			raise RuntimeError("Cannot add wire: Start point is not a valid component.")
		if to_component not in self.gates and to_component is not self:
			raise RuntimeError("Cannot add wire: End point is not a valid component.")
		if from_port >= len(from_component):
			raise RuntimeError("Cannot add wire: {0} does not have {1} output ports.".format(from_component, from_port+1))
		if to_port >= len(to_component):
			raise RuntimeError("Cannot add wire: {0} does not have {1} input ports.".format(to_component, to_port+1))

		# Add wire to the circuit
		w = Wire(from_component, to_component)
		self.wires.append(w)

		# Add left and right component information to the wire
		# This differs slightly depending on whether the components are gates or the main circuit
		from_ports = from_component.out_wires if isinstance(from_component, Gate) else from_component.input
		to_ports = to_component.in_wires if isinstance(to_component, Gate) else to_component.output
		from_ports[from_port] = w
		to_ports[to_port] = w

	# Helper method to create multiple wires at once
	# If from_ports or to_ports are empty, they default to all ports of the respective component
	def add_wires(self, from_component, from_ports, to_component, to_ports):
		if from_ports == 'all' or len(from_ports) == 0:
			from_ports = tuple(i for i in range(len(from_component)))
		if to_ports == 'all' or len(to_ports) == 0:
			to_ports = tuple(i for i in range(len(to_component)))
		if len(from_ports) != len(to_ports):
			raise RuntimeError("Cannot add wires: Number of output ports does not match number of input ports.")

		for p1, p2 in zip(from_ports, to_ports):
			self.add_wire(from_component, p1, to_component, p2)

	def get_internal_wires(self):
		return [wire for wire in self.wires if wire.is_internal()]
			
	# Helper function fot the topological sort
	def visit(self, gate):
		if gate.tempmarked:
			raise RuntimeError("Cannot sort - the circuit contains a cycle.")
		if not gate.marked:
			gate.tempmarked = True
			for wire in gate.out_wires:
				if wire.right is not self:
					self.visit(wire.right)

			gate.marked = True
			gate.tempmarked = False
			self.ordered_gates.insert(0, gate)

	# Topological sort of the gate list
	def sort(self):
		if not self.check():
			raise RuntimeError("Cannot sort - please finish building the circuit first.")
			
		for gate in self.gates:
			if not gate.marked:
				self.visit(gate)
				
		self.gates = self.ordered_gates
		self.ordered_gates = []

	# Check the circuit is a proper quantum circuit
	def check(self):
		return (
			all(wire is not None for wire in self.input) and
			all(wire is not None for wire in self.output) and
			all(wire is not None for gate in self.gates for wire in gate.in_wires) and
			all(wire is not None for gate in self.gates for wire in gate.out_wires)
		)
		# TODO: Possibly other checks

	# Set the input vector of the circuit
	def set_input(self, in_v):
		if len(in_v) != len(self):
			raise RuntimeError("Cannot set input vector: Vector lengths do not match.")
		# TODO: check that sum(|x|^2 for x in in_v) = 1

		for i in range(len(in_v)):
			self.input[i].value = in_v[i]

	# Return the output vector as computed by the last call to run (will return Nones if executed before any run calls)
	def get_output(self):
		return [wire.value for wire in self.output]

	# Run the circuit and return the computed output vector
	# If in_v is provided, will first set the input vector, otherwise it assumes the vector is set already
	def run(self, in_v=None):
		if in_v is not None:
			self.set_input(in_v)

		# TODO: Compute output vector using the gates' compute functions
		# for example:
		##################################################################
		self.sort()  # (once sort is implemented)
		for gate in self.gates:
			gate.compute()
		##################################################################

		return self.get_output()

	# Draw a very basic, simple picture of the circuit. Assumes everything is properly set up.
	def basic_draw(self):
		# TODO (Matej): Implement
		pass


# Abstract base class for gates
class Gate(abc.ABC):
	def __init__(self, size, name):
		self.in_wires = [None] * size
		self.out_wires = [None] * size
		self.name = name
		
		self.marked=False
		self.tempmarked=False

		self.parent = None
		self.uuid = None
		self.id = None

	def __len__(self):
		return len(self.in_wires)

	def __str__(self):
		s = self.name
		if self.parent is not None and self.parent.cls_ids[self.name] > 1:
			s += str(self.id)
		return s

	# Sets the gate's parent (the circuit it belongs to) and its ID numbers
	def set_parent(self, parent):
		self.parent = parent
		self.uuid = parent.global_id
		self.id = parent.cls_ids[self.name]

	# Take the values on the input wires, compute the output and set the output wires to the computed values
	def compute(self):
		in_v = self._get_input_vector()
		if any(i is None for i in in_v):
			raise RuntimeError(str(self) + ": Cannot compute: Inputs not set.")
		out_v = self._compute_output_vector(in_v)
		self._set_output_vector(out_v)

	# This method is where the output vector is computed - all subclasses need to implement this
	@abc.abstractmethod
	def _compute_output_vector(self, in_v):
		raise NotImplementedError("Gate._compute_output_vector()")

	# Return the vector of values on input wires
	def _get_input_vector(self):
		return [wire.value for wire in self.in_wires]

	# Set the output wires to the values of out_v
	def _set_output_vector(self, out_v):
		if len(out_v) != len(self):
			raise RuntimeError(str(self) + ": Cannot set output vector: Vector lengths do not match.")

		for i in range(len(out_v)):
			self.out_wires[i].value = out_v[i]

	def draw(self):
		# TODO (Matej): implement
		# draw_box(self.name)
		pass


class X(Gate):
	def __init__(self):
		super().__init__(1, "X")

	def _compute_output_vector(self, in_v):
		# TODO: compute output vector
		out_v = in_v
		return out_v


class Y(Gate):
	def __init__(self):
		super().__init__(1, "Y")

	def _compute_output_vector(self, in_v):
		# TODO: compute output vector
		out_v = in_v
		return out_v


class Z(Gate):
	def __init__(self):
		super().__init__(1, "Z")

	def _compute_output_vector(self, in_v):
		# TODO: compute output vector
		out_v = in_v
		return out_v


class H(Gate):
	def __init__(self):
		super().__init__(1, "H")

	def _compute_output_vector(self, in_v):
		# TODO: compute output vector
		out_v = in_v
		return out_v


class CNot(Gate):
	def __init__(self):
		super().__init__(2, "CNot")

	def _compute_output_vector(self, in_v):
		# TODO: compute output vector
		out_v = in_v
		return out_v

	def draw(self):
		# TODO (Matej): Implement
		# Special draw
		pass


class T(Gate):
	def __init__(self):
		super().__init__(3, "T")

	def _compute_output_vector(self, in_v):
		# TODO: compute output vector
		out_v = in_v
		return out_v

	def draw(self):
		# TODO (Matej): Implement
		# Special draw
		pass


# This class is magic, probably doesn't work yet
class SubCircuit(Gate, Circuit):
	def __init__(self, size, name=None):
		if name is None:
			name = ''.join(random.choices(string.ascii_uppercase, k=3))
		Gate.__init__(self, size, name)
		Circuit.__init__(self, size)

	@classmethod
	def from_circuit(cls, circuit, name):
		self = cls(len(circuit), name)
		self.__dict__.update(circuit.__dict__)
		return self

	def _compute_output_vector(self, in_v):
		return self.run(in_v)


# Example
# Because we don't know how to construct Uf as a SubCircuit (i.e. with a gate configuration), implement it as a new gate
class Uf(Gate):
	def __init__(self, f):
		super().__init__(2, "Uf")
		self.f = f

	# This probably won't work once we work with proper quantum values
	def _compute_output_vector(self, in_v):
		return [in_v[0], (in_v[1] + self.f(in_v[0])) % 2]
