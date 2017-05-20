from main.circuit import*
from main.matrix import Matrix, tensor
from math import pi, sqrt

#Grovers algorithm finds an x for which the function f: {0,1,...,2^n -1}-->{0,1} is 1.
#It depends on the function f. We define f with the variable x, so f(13)=1 and 0 otherwise
x=13

#2^n is the size of the domain of f. n+1 is then the size of the circuit (we need 1 extra qbit)
n=6
c=Circuit(n+1)

#define the matrix that computes f
F=Matrix.Zero(2**(n+1))
for i in range(2**(n+1)):
    for j in range(2**(n+1)):
        if i==j and i!=2*x and i!=(2*x)+1:
            F[i][j]=1
        elif i==2*x and j==(2*x)+1:
            F[i][j]=1
        elif i==(2*x)+1 and j==2*x:
            F[i][j]=1
             
U=Matrix.Zero(2**(n))
for i in range(2**(n)):
    if i==0:
        U[i][i]=1
    else:
        U[i][i]=-1
         
U=tensor([U,Matrix.Id(2)])

h1=c.add_gate(H,n+1) #Haddamard gate on all qbits
c.add_wires(c, (), h1, ())

times=int((pi/4)*sqrt(2**n)) #number of times the Grover iteration will be performed
for t in range(times):
    u1=c.add(Gate(F,'f'+str(t),True))
    c.add_wires(h1, (), u1, ())
    h2=c.add(Gate(tensor([Matrix.H(n),Matrix.Id(2)]),'h1'+str(t),True))
    c.add_wires(u1, (), h2, ())
    u2=c.add(Gate(U,'u0'+str(t),True))
    c.add_wires(h2, (), u2, ())
    h3=c.add(Gate(tensor([Matrix.H(n),Matrix.Id(2)]),'h2'+str(t),True))
    c.add_wires(u2, (), h3, ())
    h1=h3

c.add_wires(h1, (), c, ())  

gatesize=0
int_wires=c.get_internal_wires()
for gate in c.gates:
    gatesize+=len(gate)
n1=len(c.gates)*(2**(len(c)+len(int_wires)))
n2=gatesize*(2/len(c))*len(c.gates)*(2**(2*len(c))) 

