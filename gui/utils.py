from abc import ABCMeta
from numbers import Real
from operator import mul, truediv
from re import findall

from PyQt5.QtCore import *


class AbstractWidgetMeta(pyqtWrapperType, ABCMeta):
	pass


def set_background_color(widget, color):
	p = widget.palette()
	p.setColor(widget.backgroundRole(), color)
	widget.setPalette(p)
	widget.setAutoFillBackground(True)


def create_square(center, size):
	return QRectF(center - QPointF(size/2, size/2), QSizeF(size, size))


def shorten(s, n=5):
	while len(s) > n:
		number = "".join(c for c in s if c.isdigit())
		words = findall('[a-zA-Z][^A-Z0-9]*', s)
		if len(words) == 0:
			s = number
			break
		words = list(reversed(words))
		i = words.index(max(words, key=len)) if any(len(w) > 1 for w in words) else len(words)-1
		words[i] = words[i][:-2] + words[i][-1] if len(words[i]) > 2 else words[i][:-1]
		s = "".join(reversed(words)) + number
	return s


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
