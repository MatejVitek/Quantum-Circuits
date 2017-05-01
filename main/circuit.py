import abc
import random
import string
from main.matrix import Matrix, tensor
from collections import Counter
from itertools import product
from random import choices, choice, randint
from math import log, modf
<<<<<<< HEAD
from uuid import uuid4
=======
>>>>>>> parent of 262770d... Made gates' UUID an actual UUID to make gates hashable.

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

<<<<<<< HEAD
=======
        self.global_id = 0
>>>>>>> parent of 262770d... Made gates' UUID an actual UUID to make gates hashable.
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
<<<<<<< HEAD
=======
        self.global_id += 1
>>>>>>> parent of 262770d... Made gates' UUID an actual UUID to make gates hashable.
        return component

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

        return w

    # Helper method to create multiple wires at once
    # If from_ports or to_ports are empty, they default to all ports of the respective component
    def add_wires(self, from_component, from_ports, to_component, to_ports):
        if from_ports == 'all' or len(from_ports) == 0:
            from_ports = tuple(i for i in range(len(from_component)))
        if to_ports == 'all' or len(to_ports) == 0:
            to_ports = tuple(i for i in range(len(to_component)))
        if len(from_ports) != len(to_ports):
            raise RuntimeError("Cannot add wires: Number of output ports does not match number of input ports.")

        return [self.add_wire(from_component, p1, to_component, p2) for p1, p2 in zip(from_ports, to_ports)]

    def get_internal_wires(self):
        return [wire for wire in self.wires if wire.is_internal()]
    
    #this is the prefered method for implementing subcircuits. It compresses the whole circuit into
    #one matrix and returns a gate associated with it
    def get_subcircuit(self,name):
        self.sort()

        states=Matrix.Id(2**(len(self)))
                
        for g_i in range(len(self.gates)):
            gate=self.gates[g_i]
            startqbits=[self.startqbit(g_i,i) for i in range(len(gate))]
            permutation=[i for i in range(len(self))]
            permuted=[]
            for i in range(len(startqbits)):
                x=permutation[i]
                y=startqbits[i]
                if x != y and x not in permuted:
                    permutation[i]=y
                    permutation[y]=x
                    permuted.append(y)
            
            P1=Matrix.Permutation(permutation)
            P2=P1.getConjugate()
            
            if len(self)==len(gate):
                M=gate.get_matrix()
            else:
                M=tensor([gate.get_matrix(),Matrix.Id(2**(len(self)-len(gate)))])
            
            states=P2*states
            states=M*states
            states=P1*states
            
        startqbits=self.startqbits()
        P1=Matrix.Permutation(startqbits)
        P1.transpose()
        states=P1*states
            
        return Gate(states,name)

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
            
        weights=[0 for i in range(2**(len(self)))]
        int_wires=self.get_internal_wires()
        
        index=0
        for out in product(range(2),repeat=len(self)):
            Sum=0
            check=False
            
            for i in range(len(self)):
                for wire in self.input:
                    if self.output[i] == wire:
                        if wire.value != out[i]:
                            check=True
                if check:
                    break
                (self.output[i]).value=out[i]
                
            if check:
                index+=1
                continue
            
            for assign in product(range(2),repeat=len(int_wires)):
                assign=list(assign)
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
            
            weights[index]=((abs(Sum))**2)
            index+=1
            
        return weights
    
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
        weights=[]
        for i in in_v:
            if i==0:
                states.append(Matrix.vector([1,0]))
            elif i==1:
                states.append(Matrix.vector([0,1]))
        
        if len(states)>1:        
            states=tensor(states)
        else:
            states=states[0]
                
        for g_i in range(len(self.gates)):
            gate=self.gates[g_i]
            startqbits=[self.startqbit(g_i,i) for i in range(len(gate))]
            permutation=[i for i in range(len(self))]
            for i in range(len(startqbits)):
                x=permutation[i]
                y=startqbits[i]
                if x != y :
                    j=permutation.index(y)
                    permutation[i]=y
                    permutation[j]=x
            
            P1=Matrix.Permutation(permutation)
            if not P1.isUnitary():
                print("permutation matrix seems to be wrong")
            P2=P1.getConjugate()
            
            if len(self)==len(gate):
                M=gate.get_matrix()
            else:
                M=tensor([gate.get_matrix(),Matrix.Id(2**(len(self)-len(gate)))])
            
            states=P2*states
            states=M*states
            states=P1*states
            
        startqbits=self.startqbits()
        P1=Matrix.Permutation(startqbits)
        P1.transpose()
        states=P1*states

        for x in range(len(states)):
            weights.append((abs(states[x][0]))**2)
            
        return weights
    
    #this is the method that should be used for running the circuit. If the prefered method of
    #computation is not specified the faster one is automatically chosen
    def run(self,in_v,method=None):
        if not method:
            int_wires=self.get_internal_wires()
            n1=len(self.gates)*(2**(len(self)+len(int_wires)))
            n2=(3*len(self.gates))*(2**(2*len(self)))
            if n1<=n2:
                print("Running method 1...")
                method=1
            else:
                print("Running method 2...")
                method=2
        
        if method==1:
            weights=self.run_method1(in_v)
        elif method==2:
            weights=self.run_method2(in_v)
        else:
            raise RuntimeError("Please choose one of the avalible methods: 1 or 2")
            
        states=[]
        for out in product(range(2),repeat=len(self)):
            states.append(list(out))
            
        results=choices(states, weights)[0]
            
        return results
    
    #these are helper methods that give the input/output index of a given qbit
    def endqbit(self, gate_index, outwire_index):
        gate=self.gates[gate_index]
        j=outwire_index
        wire=gate.out_wires[j]
        while gate.out_wires[j].right != self:
            gate=gate.out_wires[j].right
            j=wire.rind
            wire=gate.out_wires[j]
        
        return wire.rind
    
    def startqbit(self, gate_index, inwire_index):
        gate=self.gates[gate_index]
        j=inwire_index
        wire=gate.in_wires[j]
        while gate.in_wires[j].left != self:
            gate=gate.in_wires[j].left
            j=wire.lind
            wire=gate.in_wires[j]
        
        return wire.lind
    
    def startqbits(self):
        startqbits=[]
        for i in range(len(self)):
            gate=self
            wire=self.output[i]
            while wire.left != self:
                gate=wire.left
                j=wire.lind
                wire=gate.in_wires[j]
                
            startqbits.append(wire.lind)
            
        return startqbits
    
    #returns a random quantum circuit of a specified size and number of gates. useful for testing
    @staticmethod
    def random_circuit(size=0, gates=0):
        if size==0:
            size=randint(3,6)
        if gates==0:
            n_gates=randint(1,size)
        else:
            n_gates=gates
            
        c=Circuit(size)
        av_comp=[c]
        av_in=[[i for i in range(size)]]
        for i in range(n_gates):
            gate=c.add(choice([X(1,"Gate "+str(i)),Y(1,"Gate "+str(i)),Z(1,"Gate "+str(i)),H(1,"Gate "+str(i)),CNot("Gate "+str(i)),T("Gate "+str(i))]))
            for in_wire in range(len(gate)):
                j=randint(0,len(av_comp)-1)
                component=av_comp[j]
                k=randint(0,len(av_in[j])-1)
                inputs=av_in[j][k]
                c.add_wire(component, inputs ,gate ,in_wire)
                del av_in[j][k]
                if av_in[j]==[]:
                    del av_in[j]
                    del av_comp[j]
                    
            av_comp.append(gate)
            av_in.append([i for i in range(len(gate))])
            
        for i in range(len(c)):
            j=randint(0,len(av_comp)-1)
            component=av_comp[j]
            k=randint(0,len(av_in[j])-1)
            inputs=av_in[j][k]
            c.add_wire(component, inputs ,c ,i)
            del av_in[j][k]
            if av_in[j]==[]:
                del av_in[j]
                del av_comp[j]
        
        return c

# Abstract base class for gates
class Gate(abc.ABC):
    def __init__(self, mtrx, name):
        if len(mtrx)!=len(mtrx.rows[0]):
            raise RuntimeError("Gates should be represented by square matrices.")
        if not mtrx.isUnitary():
            raise RuntimeError("Gates should be represented by unitary matrices.")
        if modf(log(len(mtrx),2))[0] !=0: 
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

<<<<<<< HEAD
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.uuid == other.uuid
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self == other
        return NotImplemented

    def __hash__(self):
        return hash(self.uuid)

    # Sets the gate's parent (the circuit it belongs to) and its ID numbers
    def set_parent(self, parent):
        self.parent = parent
        self.uuid = uuid4()
        while any(g.uuid == self.uuid for g in parent.gates if g is not self):
            self.uuid = uuid4()
=======
    # Sets the gate's parent (the circuit it belongs to) and its ID numbers
    def set_parent(self, parent):
        self.parent = parent
        self.uuid = parent.global_id
>>>>>>> parent of 262770d... Made gates' UUID an actual UUID to make gates hashable.
        self.id = parent.cls_ids[self.name]
        
    def get_matrix(self):
        size=2**(len(self))
        result = Matrix([[0]*size for x in range(size)])
        for i in range(size):
            for j in range(size):
                result[i][j] = self.matrix[i][j]

        return result

class X(Gate):
    def __init__(self,size=1, name="X"):
        super().__init__(Matrix.X(size), name)

class Y(Gate):
    def __init__(self,size=1, name="Y"):
        super().__init__(Matrix.Y(size), name)

class Z(Gate):
    def __init__(self,size=1, name="Z"):
        super().__init__(Matrix.Z(size), name)

class H(Gate):
    def __init__(self,size=1, name="H"):
        super().__init__(Matrix.H(size), name)
        
class SqrtNot(Gate):
    def __init__(self,size=1, name="SqrtNot"):
        super().__init__(Matrix.SqrtNot(size), name)
        
class QFT(Gate):
    def __init__(self,size=1, name="QFT"):
        super().__init__(Matrix.QFT(size), name)

class CNot(Gate):
    def __init__(self, name="CNot"):
        super().__init__(Matrix.Cnot(), name)

class T(Gate):
    def __init__(self, name="T"):
        super().__init__(Matrix.T(), name)
