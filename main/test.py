from main.circuit import *


if __name__ == '__main__':
	# This is circuit (5) from the paper
	c = Circuit(6)

	cnot1 = c.add_gate(CNot)
	x1 = c.add_gate(X)
	cnot2 = c.add_gate(CNot)
	x2 = c.add_gate(X)
	t = c.add_gate(T)
	cnot3 = c.add_gate(CNot)
	x3 = c.add_gate(X)

	c.add_wires(c, (0, 2), cnot1, ())
	c.add_wire(cnot1, 0, c, 0)
	c.add_wire(cnot1, 1, x1, 0)

	c.add_wires(c, (1, 3), cnot2, ())
	c.add_wire(cnot2, 0, c, 1)
	c.add_wire(cnot2, 1, x2, 0)

	c.add_wire(x1, 0, t, 0)
	c.add_wire(x2, 0, t, 1)
	c.add_wire(c, 4, t, 2)
	c.add_wires(t, (0, 1), c, (2, 3))

	c.add_wire(t, 2, cnot3, 0)
	c.add_wire(c, 5, cnot3, 1)
	c.add_wire(cnot3, 0, c, 4)
	c.add_wire(cnot3, 1, x3, 0)

	c.add_wire(x3, 0, c, 5)

	print(c.check())
	# Find all internal wires
	for w in c.get_internal_wires():
		print(w, end='\t')
	print()
	c.basic_draw()



	# Custom circuit to test value propagation (and Uf's computation)
	c = Circuit(3)

	cnot = c.add_gate(CNot)
	x = c.add_gate(X)
	uf = c.add_gate(Uf, lambda x: 1-x)

	c.add_wires(c, (0, 1), cnot, ())
	c.add_wire(c, 2, x, 0)
	c.add_wire(cnot, 0, c, 0)
	c.add_wire(cnot, 1, uf, 0)
	c.add_wire(x, 0, uf, 1)
	c.add_wires(uf, (), c, (1, 2))

	for v in [[0, 0, 0], [0, 0, 1], [0, 1, 0], [0, 1, 1], [1, 0, 0], [1, 0, 1], [1, 1, 0], [1, 1, 1]]:
		print(c.run(v))
