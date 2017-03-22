import abc
import random
import string
from collections import Counter


# Abstract base class for ports
class Port(abc.ABC):
	def __init__(self, parent):
		self.value = None
		self.parent = parent


# Port for an inbound connection
class InPort(Port):
	def __init__(self, parent):
		super().__init__(parent)
		self.in_wire = None


# Port for an outbound connection
class OutPort(Port):
	def __init__(self, parent):
		super().__init__(parent)
		self.out_wire = None


# Class for the entire circuit
class Circuit(object):

	# The input ports of the circuit are OutPorts (since they have outbound connections to the gates)
	# The output ports of the circuit are InPorts (since they have inbound connections from the gates)
	def __init__(self, size):
		self.input = tuple(OutPort(self) for _ in range(size))
		self.output = tuple(InPort(self) for _ in range(size))
		self.gates = []

		self.global_id = 0
		self.cls_ids = Counter()

	def __len__(self):
		return len(self.input)

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

	# Create a wire from an OutPort to an InPort
	def add_wire(self, from_port, to_port):
		if not isinstance(from_port, OutPort):
			raise RuntimeError("Cannot add wire: Start point is not an outbound port.")
		if not isinstance(to_port, InPort):
			raise RuntimeError("Cannot add wire: End point is not an inbound port.")
		if from_port.parent not in self.gates and from_port.parent is not self:
			raise RuntimeError("Cannot add wire: Start point is not in this circuit.")
		if to_port.parent not in self.gates and to_port.parent is not self:
			raise RuntimeError("Cannot add wire: End point is not in this circuit.")

		from_port.out_wire = to_port
		to_port.in_wire = from_port

	# Helper method to create multiple wires at once
	def add_wires(self, from_ports, to_ports):
		for w1, w2 in zip(from_ports, to_ports):
			self.add_wire(w1, w2)
			
	# Helper function fot the topological sort
	def visit(self, gate):
		if gate.tempmarked:
			raise RuntimeError("Cannot sort - the circuit contains a cycle.")
		if not gate.marked:
			gate.tempmarked=True
			for gate1 in gate.out_ports:
				if gate1.out_wire.parent != self:
					self.visit(gate1.out_wire.parent)
										
			gate.marked=True
			gate.tempmarked=False
			self.ordered_gates.insert(0,gate)

	# Topological sort of the gate list
	def sort(self):
		if not self.check():
			raise RuntimeError("Cannot sort - please finish building the circuit first.")
			
		for gate in self.gates:
			if not gate.marked:
				self.visit(gate)
				
		self.gates=self.ordered_gates
		self.ordered_gates=[]

		pass

	# Check the circuit is a proper quantum circuit
	def check(self):
		return (
			all(port.out_wire is not None for port in self.input) and
			all(port.in_wire is not None for port in self.output) and
			all(port.in_wire is not None for gate in self.gates for port in gate.in_ports) and
			all(port.out_wire is not None for gate in self.gates for port in gate.out_ports)
		)
		# TODO: Check that there are no cycles - this check is a part of the topological sort
		# TODO: Possibly other checks

	# Set the input vector of the circuit and propagate the values to the first gates
	def set_input(self, in_v):
		if len(in_v) != len(self):
			raise RuntimeError("Cannot set input vector: Vector lengths do not match.")
		# TODO: check that sum(|x|^2 for x in in_v) = 1

		for i in range(len(in_v)):
			port = self.input[i]

			# Set value
			port.value = in_v[i]

			# Propagate value
			if port.out_wire is None:
				raise RuntimeError("Cannot propagate input vector: Port " + str(i) + " is not connected.")
			port.out_wire.value = in_v[i]

	# Return the output vector as computed by the last call to run (will return Nones if executed before any run calls)
	def get_output(self):
		return [port.value for port in self.output]

	# Run the circuit and return the computed output vector
	# If in_v is provided, will first set the input vector, otherwise it assumes the vector is set already
	def run(self, in_v=None):
		if in_v is not None:
			self.set_input(in_v)

		# TODO: Compute output vector using the gates' compute functions
		# for example:
		##################################################################
		self.sort() # (once sort is implemented)
		for gate in self.gates:
			gate.compute()
		##################################################################

		# The output vector will be set automatically as the gates propagate the values in their compute functions
		return self.get_output()

	# Draw a very basic, simple picture of the circuit. Assumes everything is properly set up.
	def basic_draw(self):
		# TODO (Matej): Implement
		pass


# Abstract base class for gates
class Gate(abc.ABC):
	def __init__(self, size, name=None):
		self.in_ports = tuple(InPort(self) for _ in range(size))
		self.out_ports = tuple(OutPort(self) for _ in range(size))
		self.name = name
		
		self.marked=False
		self.tempmarked=False

		self.parent = None
		self.uuid = None
		self.id = None

	def __len__(self):
		return len(self.in_ports)

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

	# Take the values that were propagated to this gate, compute the output and propagate computed values forward
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

	# Return the input values that were propagated to this gate
	def _get_input_vector(self):
		return [port.value for port in self.in_ports]

	# Set the output vector and propagate the values forward to the next gate (or circuit output)
	def _set_output_vector(self, out_v):
		if len(out_v) != len(self):
			raise RuntimeError(str(self) + ": Cannot set output vector: Vector lengths do not match.")

		for i in range(len(out_v)):
			port = self.out_ports[i]

			# Set value
			port.value = out_v[i]

			# Propagate value
			if port.out_wire is None:
				raise RuntimeError(str(self) + ": Cannot propagate output vector: Port " + str(i) + " is not connected.")
			port.out_wire.value = out_v[i]

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
