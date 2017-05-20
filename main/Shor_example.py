from main.circuit import *
from main.Shor import binary

N=21
a=17

q=(len(bin(N))-2)*2
                    
c=Circuit(q)

U=Matrix.Zero(2**q)
for i in range(0,2**q):
    for j in range(0,2**q):
        i1=binary(i,0,q//2,q)
        i2=binary(i,q//2,q,q)
        j1=binary(j,0,q//2,q)
        j2=binary(j,q//2,q,q)
        check=True

        if int(i2,2)==0 and i1==j1 and a**(int(i1,2)) % N==int(j2,2):                
            U[i][j]=1 
            U[j][i]=1
            break
        elif i2=='1'*(q//2) and i1==j1:
            l=binary(a**(int(i1,2)) % N,0,q//2,q//2)
            for k in range(0,len(l)):
                if l[k]==j2[k]:
                    check=False
                    break
            if check:
                U[i][j]=1  
                U[j][i]=1
                break
count=0
for row in U.rows:
    if row==[0]*(2**q):
        U[count][count]=1
        count+=1
        continue
    count+=1      
    
h=c.add_gate(H,q//2) 
c.add_wires(c, [i for i in range(0,q//2)], h, [i for i in range(0,q//2)])
u=c.add(Gate(U,'U',True))
c.add_wires(h, [i for i in range(0,q//2)], u, [i for i in range(0,q//2)]) 
c.add_wires(c, [i for i in range(q//2,q)], u, [i for i in range(q//2,q)])
c.add_wires(u, [i for i in range(q//2,q)], c, [i for i in range(q//2,q)])
QFT=Matrix.QFT(q//2)
qft=c.add(Gate(QFT,'QFT', True))
c.add_wires(u, [i for i in range(0,q//2)], qft, [i for i in range(0,q//2)])
c.add_wires(qft, [i for i in range(0,q//2)], c, [i for i in range(0,q//2)])