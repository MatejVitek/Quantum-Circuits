import cmath
from itertools import product

#this is a helpful external function that computes the tensor product of a list of matrices
#in the order given by the list
def tensor(matrixlist):
    T=(matrixlist[0]).bintensor(matrixlist[1])
    for i in range(2,len(matrixlist)):
        T=T.bintensor(matrixlist[i])

    return T   

def matrix_product(matrixlist):
    I=Matrix.Id(len(matrixlist[0]))
    for M in matrixlist:
        I=M*I
        
    return I

class MatrixError(Exception):
    """ An exception class for Matrix """
    pass

#class for matrices
class Matrix(object):
    def __init__(self, rows):
        if rows==[]:
            raise MatrixError('Please specify the rows of the matrix.')
        for i in range(len(rows)-1):
            if len(rows[i])!=len(rows[i+1]):
                raise MatrixError('Row dimensions are not consistent.')
        self.rows = rows

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        return self.rows[i]

    def __setitem__(self, i, item):
        self.rows[i]=item

    def __str__(self):
        string=''
        for i in self.rows:
            for j in i:
                string+=str(j)+' '
            string+='\n'

        return string

    def __repr__(self):
        s=str(self.rows)
        rep="Matrix: \"%s\"" % (s)
        return rep

    def __eq__(self, M):
        return (M.rows == self.rows)

    def __mul__(self, M):
        if len(self.rows[0])!=len(M):
            raise MatrixError('Matrix dimensions must agree.')

        result = Matrix([[0]*len(M.rows[0]) for x in range(len(self))])
        for i in range(len(self)):
            for j in range(len(M.rows[0])):
                column=[k[j] for k in M.rows]
                result[i][j] = sum([item[0]*item[1] for item in zip(self.rows[i], column)])

        return result
    
    #this transforms all entries in the matrix to int. Needed to avoid numerical inaccuracies in some
    #cases but is only a temporary solution. Should make a more appropriate method
    def getInt(self):
        M=Matrix.Zero(len(self))
        for i in range(len(M)):
            for j in range(len(M.rows[0])):
                M[i][j]=int(self[i][j].real)
        return M

    def transpose(self):
        self.rows=[list(item) for item in zip(*self.rows)]
        
    def getConjugate(self):
        M=Matrix.Zero(len(self))
        for i in range(len(M)):
            for j in range(len(M.rows[0])):
                M[j][i]=(self[i][j]).conjugate()
        return M
    
    def isUnitary(self):
        if (self*(self.getConjugate())).getInt()==Matrix.Id(len(self)):
            return True
        else:
            return False
    
    #returns the tensor product of self and M. Will mostly use tensor() function for tensor products
    #this is only the basis for it
    def bintensor(self,M):
        m=len(self)
        n=len(self.rows[0])
        p=len(M)
        q=len(M.rows[0])
        
        T=Matrix.Zero(m*p,n*q)
        
        for i in range(0,m*p,p):
            for j in range(0,n*q,q):
                for k in range(p):
                    for l in range(q):
                        T[i+k][j+l]=(self[int(i/p)][int(j/q)])*(M[k][l])
                        
        return T        
    
    #"untensor" a 2**n basis vector into 2 dimensional basis vectors
    def untensor(self):
        if len(self.rows[0])!=1:
            raise MatrixError('untensor is defined for vectors (one-column matrices) only.')
        if len(self)%2 !=0:
            raise MatrixError('Vector dimensions are not as required.')
            
        states=[]
        v=[self[i][0] for i in range(len(self))]
        v2=[]
        while len(v)>2:
            v1=[]
            for i in range(0,len(v),2):
                if v[i]==1 or v[i+1]==1:
                    v2=[v[i],v[i+1]]
                    v1.append(1)
                else:
                    v1.append(0)
            v=v1
            states.insert(0,Matrix.vector(v2))
        
        states.insert(0,Matrix.vector(v))
        
        return(states)
    
    #multiplies self(vector) with a list of matrices in the order of the list
    def apply(self, matrices):
        if len(self.rows[0])>1:
            raise MatrixError("This method is reserved for vectors.")
        
        M=Matrix.vector([0 for i in range(len(self))])
        for i in range(len(M)):
            M[i][0]=self[i][0]
                
        for N in matrices:
            M=N*M
            
        return M

    #these are class methods for quickly generating the matrices needed in the project.
    #Add more if needed.
    @classmethod
    def vector(cls, column):
        M=Matrix([column])
        M.transpose()
        return M
    
    @classmethod
    def Zero(cls,nrows,ncolumns=0):
        if ncolumns==0:
            ncolumns=nrows
        rows=[[0]*ncolumns for x in range(nrows)]
        return cls(rows)
        
    @classmethod
    def Id(cls,size):
        rows=[[0]*size for x in range(size)]
        for i in range(size):
            rows[i][i]=1

        return cls(rows)
    
    @classmethod
    def H(cls, size=1):
        seznam=[]
        if size==1:
            return cls([[2**(-0.5),2**(-0.5)],[2**(-0.5),-(2**(-0.5))]])
        else:
            for i in range(size):
                seznam.append(cls([[2**(-0.5),2**(-0.5)],[2**(-0.5),-(2**(-0.5))]]))
        return tensor(seznam)
    
    @classmethod
    def X(cls):
        return cls([[0,1],[1,0]])

    @classmethod
    def Y(cls):
        return cls([[0,-1j],[0+1j,0]])

    @classmethod
    def Z(cls):
        return cls([[1,0],[0,-1]])

    @classmethod
    def PhaseShift(cls,phase):
        return cls([[1,0],[0,cmath.e**(1j*(phase))]])
    
    @classmethod
    def Permutation(cls,permutation):
        P=cls.Zero(2**(len(permutation)))
        
        for in_v1 in product(range(2),repeat=len(permutation)):
            for out1 in product(range(2),repeat=len(permutation)):
                in_v1=list(in_v1)
                out1=list(out1)
                in_v=[]
                out=[]
                for k in range(len(in_v1)):
                    in_v.append(str(in_v1[k]))
                    out.append(str(out1[k]))
                    
                x=1
                for i in range(len(permutation)):
                    if in_v[i]!=out[permutation[i]]:
                        x=0
                        break
                    
                if x==1:
                    y=int('0b'+(''.join(in_v)),2)
                    z=int('0b'+(''.join(out)),2)
                    P[y][z]=x
                     
        return P

    @classmethod
    def Cnot(cls):
        return cls([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]])

    @classmethod
    def T(cls):
        Toffoli=cls.Id(8)
        Toffoli.rows[6]=[0,0,0,0,0,0,0,1]
        Toffoli.rows[7]=[0,0,0,0,0,0,1,0]
        return Toffoli



