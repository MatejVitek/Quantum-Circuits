import cmath

#this is a helpful external function that computes the tensor product of a list of matrices
#in the order given by the list
def tensor(matrixlist):
    T=(matrixlist[0]).bintensor(matrixlist[1])
    for i in range(2,len(matrixlist)):
        T=T.bintensor(matrixlist[i])

    return T   

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
    def H(cls):
        return cls([[2**(-0.5),2**(-0.5)],[2**(-0.5),-(2**(-0.5))]])
    
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

    #The matrix that swaps qbits qbit1 and qbit2
    @classmethod
    def Swap(cls,qbit1,qbit2,circuitsize):
        if qbit1>qbit2:
            q=qbit2
            qbit2=qbit1
            qbit1=q
            
        if qbit2>=circuitsize:
            raise MatrixError("Qbit indices exceed circuit size.")
        
        ran=(qbit2-qbit1)
        T=cls.Id(2**circuitsize)
        for i in range(ran):
            A1=cls.Id(2**(qbit2-1))
            A2=cls([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]])
            A3=cls.Id(2**(circuitsize-qbit2-1))
            T=T*tensor([A1,A2,A3])
            qbit1+=-1
            qbit2+=-1
            
        for i in range(ran-1):
            qbit1+=1
            qbit2+=1
            A1=cls.Id(2**(qbit2-1))
            A2=cls([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]])
            A3=cls.Id(2**(circuitsize-qbit2-1))
            T=T*tensor([A1,A2,A3])
            
        return T

    @classmethod
    def Cnot(cls):
        return cls([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]])

    @classmethod
    def T(cls):
        Toffoli=cls.Id(8)
        Toffoli.rows[6]=[0,0,0,0,0,0,0,1]
        Toffoli.rows[7]=[0,0,0,0,0,0,1,0]
        return Toffoli



