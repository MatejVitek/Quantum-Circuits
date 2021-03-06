from main.circuit import Circuit

from random import randint

from PyQt5.QtGui import *
from PyQt5.QtCore import *


circuit = None
in_vector = None
out_vector = None
wire_colors = None


def new_circuit(size, colors=None):
	global circuit, in_vector, out_vector, wire_colors
	circuit = Circuit(size)
	in_vector = VectorObject(size)
	out_vector = VectorObject(size)
	set_wire_colors(colors)


def set_circuit(c, colors=None):
	global circuit, in_vector, out_vector, wire_colors
	circuit = c
	in_vector = VectorObject(len(circuit))
	out_vector = VectorObject(len(circuit))
	set_wire_colors(colors)


def set_wire_colors(colors):
	global wire_colors

	# Argument None means leave colors as they are. If new circuit size is larger, pad with randoms.
	if colors is None:
		if wire_colors is not None and len(wire_colors) < len(circuit):
				wire_colors.extend(_rnd() for _ in range(len(circuit) - len(wire_colors)))

	# Argument False means don't use colors.
	elif colors is False:
		wire_colors = None

	# Argument True or empty iterable means use random colors.
	elif colors is True or not colors:
		wire_colors = [_rnd() for _ in range(len(circuit))]

	# Argument non-empty iterable means use the specified colors. Sizes must match.
	elif len(colors) != len(circuit):
		raise RuntimeError("Size of color vector does not match the size of the circuit.")

	else:
		wire_colors = list(colors)


def _rnd():
	# TODO: Implement better random color picking
	return QColor(randint(0, 200), randint(0, 200), randint(0, 200))


class VectorObject(QObject):
	changed = pyqtSignal('PyQt_PyObject', 'PyQt_PyObject', name='ioChanged')

	def __init__(self, size):
		super().__init__()
		self._vector = [0] * size

	def __str__(self):
		return "".join(map(str, self))

	def __len__(self):
		return len(self._vector)

	def __getitem__(self, i):
		return self._vector[i]

	def __setitem__(self, key, val):
		try:
			val = [int(v) for v in val]
			if any(v not in (0, 1) for v in val):
				raise ValueError("Only binary values allowed.")
		except TypeError:
			val = int(val)
			if val not in (0, 1):
				raise ValueError("Only binary values allowed.")

		self._vector[key] = val
		self.changed.emit(key, val)

	def get(self):
		return self[:]

	def set(self, v):
		self[:] = v

	def toggle(self, i):
		self[i] = 1 - self[i]
