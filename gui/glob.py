from main.circuit import Circuit

from abc import ABCMeta
from numbers import Real
from operator import mul, truediv
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

	# Argument None means leave colors as they are. If sizes don't match, pad or delete extras.
	if colors is None:
		if wire_colors is not None:
			if len(wire_colors) > len(circuit):
				wire_colors = wire_colors[:len(circuit)]
			elif len(wire_colors) < len(circuit):
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
		return "".join(str(i) for i in self)

	def __len__(self):
		return len(self._vector)

	def __getitem__(self, i):
		return self._vector[i]

	def __setitem__(self, key, val):
		try:
			map(int, val)
			if any(v not in (0, 1) for v in val):
				raise RuntimeError("Only binary values allowed.")
		except TypeError:
			val = int(val)
			if val not in (0, 1):
				raise RuntimeError("Only binary values allowed.")

		self._vector[key] = val
		self.changed.emit(key, val)

	def get(self):
		return self[:]

	def set(self, v):
		self[:] = v

	def toggle(self, i):
		self[i] = 1 - self[i]


class AbstractWidgetMeta(pyqtWrapperType, ABCMeta):
	pass


def set_background_color(widget, color):
	p = widget.palette()
	p.setColor(widget.backgroundRole(), color)
	widget.setPalette(p)
	widget.setAutoFillBackground(True)


def create_square(center, size):
	return QRectF(center - QPointF(size/2, size/2), QSizeF(size, size))


def _op(self, f, op):
	if isinstance(f, Real):
		return type(self)(op(self.x(), f), op(self.y(), f))
	raise NotImplementedError


QPointF.__mul__ = lambda self, f: _op(self, f, mul)
QPointF.__rmul__ = lambda self, f: _op(self, f, mul)
QPointF.__truediv__ = lambda self, f: _op(self, f, truediv)
QPointF.__rtruediv__ = lambda self, f: _op(self, f, truediv)
QPoint.__mul__ = lambda self, f: _op(self, f, mul)
QPoint.__rmul__ = lambda self, f: _op(self, f, mul)
QPoint.__truediv__ = lambda self, f: _op(self, f, truediv)
QPoint.__rtruediv__ = lambda self, f: _op(self, f, truediv)
