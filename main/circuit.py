import abc
import random
import string
from matrix import Matrix, tensor
from collections import Counter
from itertools import product
from random import choices
from math import log

# Wire class
class Wire(object):

    # Uses left and right to avoid confusion with input/output. lind and rind are there
    # so that the wire knows to which input/output it is attached to 
    def __init__(self, left, right, lind, rind):
        self.left = left
        self.right = right
        self.lind=lind
        self.rind=rind
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
        w = Wire(from_component, to_component, from_port, to_port)
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
        for gate in self.gates:
            gate.marked=False
            gate.tempmarked=False

    # Check the circuit is a proper quantum circuit
    def check(self):
        return (
            all(wire is not None for wire in self.input) and
            all(wire is not None for wire in self.output) and
            all(wire is not None for gate in self.gates for wire in gate.in_wires) and
            all(wire is not None for gate in self.gates for wire in gate.out_wires)
        )
        # TODO: Possibly other checks

    # Run the circuit and return the computed output vector
    #method1 is the Feynman approach
    def run_method1(self, in_v):
        if len(in_v) != len(self):
            raise RuntimeError("Input length does not match the size of the circuit.")
        for i in in_v:
            if i==0 or i==1:
                pass
            else:
                raise RuntimeError("Invalid input - values must be 0 or 1.")
                
        for i in range(len(self)):
            (self.input[i]).value=in_v[i]
            
        states=[]
        weights=[]
        int_wires=self.get_internal_wires()
            
        for out in product(range(2),repeat=len(self)):
            Sum=0
            
            for i in range(len(self)):
                (self.output[i]).value=out[i]
            
            for assign in product(range(2),repeat=len(int_wires)):
                for i in range(len(int_wires)):
                    (int_wires[i]).value=assign[i]
                
                prod=1
                for gate in self.gates:
                    endqbits=[str(wire.value) for wire in gate.out_wires]
                    startqbits=[str(wire.value) for wire in gate.in_wires]
                    i=int('0b'+(''.join(startqbits)),2)
                    j=int('0b'+(''.join(endqbits)),2)
                    prod=prod*(gate.matrix[i][j])
                    
                Sum+=prod
                
            weights.append(abs(Sum))
            states.append(list(out))
 
        return choices(states, weights)[0]
    
    #method2 is the matrix multiplication approach
    def run_method2(self, in_v):
        self.sort()
        
        if len(in_v) != len(self):
            raise RuntimeError("Input length does not match the size of the circuit.")
        for i in in_v:
            if i==0 or i==1:
                pass
            else:
                raise RuntimeError("Invalid input - values must be 0 or 1.")
            
        states=[]
        for i in in_v:
            if i==0:
                states.append(Matrix.vector([1,0]))
            elif i==1:
                states.append(Matrix.vector([0,1]))
        
        if len(states)>1:        
            states=tensor(states)
        else:
            states=states[0]
                
        for gate in self.gates:
            startqbits=[self.startqbit(gate,i) for i in range(len(gate))]
            matrices=[]
            tempmatrices=[]
            result=Matrix.Id(2**(len(self)))
            for i, j in zip(range(len(gate)),startqbits):
                if i!=j:
                    matrices.insert(0,Matrix.Swap(i,j,len(self)))
                    tempmatrices.append(Matrix.Swap(i,j,len(self)))

            if len(self)-len(gate)==0:
                matrices.insert(0,gate.matrix)
            else:
                matrices.insert(0,tensor([gate.matrix,Matrix.Id(2**(len(self)-len(gate)))]))
            matrices=tempmatrices+matrices 
            for M in matrices:
                result=result*M

            states=result*states        
              
        measured=states.untensor()
        output=[]
        for x in measured:
            if x==Matrix.vector([1,0]):
                output.append(0)
            elif x==Matrix.vector([0,1]):
                output.append(1)

        return output
    
    #these are helper methods that give the input/output index of a given qbit
    def endqbit(self, gate, outwire_index):
        j=outwire_index
        wire=gate.out_wires[j]
        while gate.out_wires[j].right != self:
            gate=gate.out_wires[j].right
            j=wire.rind
            wire=gate.out_wires[j]
        
        return wire.rind
    
    def startqbit(self, gate, inwire_index):
        j=inwire_index
        wire=gate.in_wires[j]
        while gate.in_wires[j].left != self:
            gate=gate.in_wires[j].left
            j=wire.lind
            wire=gate.in_wires[j]
        
        return wire.lind

    # Draw a very basic, simple picture of the circuit. Assumes everything is properly set up.
    def basic_draw(self):
        # TODO (Matej): Implement
        pass


# Abstract base class for gates
class Gate(abc.ABC):
    def __init__(self, mtrx, name):
        if len(mtrx)!=len(mtrx.rows[0]):
            raise RuntimeError("Gates should be represented by square matrices.")
        if not mtrx.isUnitary():
            raise RuntimeError("Gates should be represented by unitary matrices.")
        if len(mtrx)%2 !=0: #this should be changed into a statement involving logarithms
            raise RuntimeError("Invalid gate dimension.")
        size=int(log(len(mtrx),2))

        self.matrix=mtrx
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

    def draw(self):
        # TODO (Matej): implement
        # draw_box(self.name)
        pass


class X(Gate):
    def __init__(self):
        super().__init__(Matrix.X(), "X")

class Y(Gate):
    def __init__(self):
        super().__init__(Matrix.Y(), "Y")

class Z(Gate):
    def __init__(self):
        super().__init__(Matrix.Z(), "Z")

class H(Gate):
    def __init__(self):
        super().__init__(Matrix.H(), "H")

class CNot(Gate):
    def __init__(self):
        super().__init__(Matrix.Cnot(), "CNot")

    def draw(self):
        # TODO (Matej): Implement
        # Special draw
        pass


class T(Gate):
    def __init__(self):
        super().__init__(Matrix.T(), "T")

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
