"""
Copyright (C) 2012 Mara Matias

This file is part of HRFAnalyse.

    HRFAnalyse is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published
    by the Free Software Foundation, either version 3 of the License,
    or (at your option) any later version.

    HRFAnalyse is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with HRFAnalyse.  If not, see
    <http://www.gnu.org/licenses/>.

_______________________________________________________________________________

This module implements the calculation of entropy (sample and aproximate since 
after some testing these seem to be the only ones that have significant results 
for our specific purposes. Some of the functions are calls to some pyeeg 
implementation. The pyeeg module available at this time does not work for Python3.


MODULE EXTERNAL DEPENDENCIES:
pyeeg(http://code.google.com/p/pyeeg/downloads/list),
numpy(http://numpy.scipy.org/),

ENTRY POINT: entropy(input_name,function,dimension,tolerances)
             calculate_std(input_name)
"""

#comment this line if you intend to use Python3
from tools.pyeeg import samp_entropy,ap_entropy
import sys
import os
import numpy
from collections import namedtuple

#DATA TYPE DEFINITIONS
"""This is a data type defined to be used as a return for entropy; it
contains the number of points in the file, and the file's entropy"""
EntropyData = namedtuple('EntropyData','points entropy')


#ENTRY POINT FUNCTION
def entropy(input_name,function,dimension,tolerances):
    """
    (str, str, int, float) -> EntropyData
    
    Given a file or directory named input_name, calculate the desired
    entropy to all the files.

    ALGORITHM: Retrieve a complete list of all the files in the
    directory.  For every file in the list calculate the entropy using
    the user chosen function.

    NOTE: This functions last two parameters are specific for the entropy 
    calculating algorithms we are using.
    """

    method_to_call= getattr(sys.modules[__name__],function)
    entropy_dict={}
    if os.path.isdir(input_name):
        filelist = os.listdir(input_name)
        for filename in filelist:
            entropyData = method_to_call(os.path.join(input_name,filename.strip()),dimension,tolerances[filename])
            entropy_dict[filename.strip()] = entropyData
    else:
        tolerances=tolerances[list(tolerances.keys())[0]]
        entropyData = method_to_call(input_name.strip(),dimension,tolerances)
        entropy_dict[input_name.strip()] = entropyData
    return entropy_dict

def calculate_std(input_name):
    """
    Function to calculate the standard deviation for the values in a file/directory.
    This is not a conventional entry point as it does not calculate any type of 
    entropy, but since it is necessary to define tolerances, this is the best place
    for it.
    
    ARGUMENTS: String input_name name of the file/directory.
    
    RETURN: Dictionary with filenames as keys and their standard deviation as values.
    
    ALGORITHM: For each file call the implementation calculate_file_std, put the
    returned std in the dictionary.
    
    """
    files_std = {}
    if os.path.isdir(input_name):
        filelist = os.listdir(input_name)
        for filename in filelist:
            files_std[filename] = calculate_file_std(os.path.join(input_name,filename))
    else:
        files_std[input_name]=calculate_file_std(input_name)
    return files_std

#IMPLEMENTATION
def apen(filename,dimension,tolerance):
    """
    A function that uses the pyeeg implementation of aproximate entropy to 
    calculte the entropy for one file. 
    
    ARGUMENTS: String filename, int dimension, float tolerance
    
    RETURN: EntropyData type
    """
    with open(filename,"r") as file_d:
        file_data = file_d.readlines()
    file_data = list(map(float,file_data))
    return EntropyData(len(file_data),ap_entropy(file_data, dimension, tolerance))

def apenv2(filename,dimension,tolerance):
    """
    An implementation of Aproximate entropy. The explanation of the algorithm is 
    a bit long because it is a little different from the original version it was 
    based on. It is still an O(mn2) worst case algorithm.
    
    ARGUMENTS: String filename, int dimension, float tolerance
    
    RETURN: EntropyData
    
    ALGORITHM: Based on the algorithm described in the book referenced bellow, 
    this implementation actualy calculates the Nm and Nm+1(Nmp) vectors directly. 
    The following description is an explanation to help you understand why we jump
    directly to building Nm.
    
    Suppose we started by directly calculating the auxilary matrix S where every
    cell S(i,j) is either 0 if the absolute distance between points i and j is 
    bigger then the tolerance or 1 otherwise. The matrix is symmetrical and the 
    diagonal is all 1's, so we would only actualy need to calculate the upper half
    of the matrix.
    
    In matrix Crm the cell value will be one if all the S(i,j)...S(i+m,j+m) cells 
    are 1. Or we can look at it the otherway arround and say that if any of the 
    values of that interval is 0 then Crm(i,j) is also 0, morover if we start at
    the S(i+m,j+m) cell and work our way back if we find a 0 we know that any Crm 
    cells diagonally above that one will also be 0(*). Looking at the description 
    it's easy to see that we could just as easily star here, if instead of verifying
    the value of auxilary matrix S is 0 we directly verify if the absolute distance
    is greater that tolerance. The Crm and Crm+1 matrixes are necessarily also 
    symmetrical and with a main diagonal filled with 1's.
    
    Nm, and Nm+1 are vectors where every index(i) is the sum of each row(i) in Crm
    and Crm+1 respectively. Since we proposed looking for 0's instead of 1 our N
    vectors start with the value assuming all the columns in the row are 1, we then
    subtract for every 0 found. Although the Cr matrixes are not actually created
    the two variables i and j in the implementation are the row and column for the
    Crm matrix. With that in mind and the fact that the Crm matrix is symmetrical,
    we can simply test the value of the distance between points i and j, if it 
    is bigger than the tolerance, Crm would have a zero in that cell and so we 
    subtract one from our Nm and Nm+1 vector at position i and j. Provided of 
    course both i and j are within the index limits.
    
    The rest of the implementation follows the description found it the book, Cm
    is the vector Nm with all cells divided by the length of Nm. Analogous for Cmp
    and Nmp. Finaly the Phi's are calculated by avaraging the Cm and Cmp vectors
    and the entropy value is the subtraction of Phi of Cm and Phi of Cmp.
    
    (*)As an implementatio boost we use this knowledge to skip some cell whose value
    we already know to be 0. This is done by creating a burned_indexes that contains 
    the columns we want to jump over in the upcoming rows. The columns are kept 
    in a dictionary so the test if a particular column is to jumped is O(1).
    
    BIBLIGRAPHICAL REFERENCE:
    Fusheng, Y., Bo, H. and Qingyu, T. (2000) Approximate Entropy and Its 
    Application to Biosignal Analysis, in Nonlinear Biomedical Signal 
    Processing: Dynamic Analysis and Modeling, Volume 2 (ed M. Akay), John Wiley
    & Sons, Inc., Hoboken, NJ, USA. doi: 10.1002/9780470545379.ch3
    
    """
    
    with open(filename,"r") as file_d:
        file_data = file_d.readlines()
    file_data = list(map(float,file_data))

    data_len = len(file_data)

    Nm = [data_len-dimension+1]*(data_len-dimension+1)
    Nmp = [data_len - dimension]*(data_len - dimension)
    burned_indexes=[{} for i in range(data_len -dimension+1)]

    for i in range(0,data_len-(dimension-1)):
        if i>0:
            burned_indexes[i-1]=None
        for j in range(i+1,data_len-(dimension-1)):
            if j in burned_indexes[i]:
                continue
            m=dimension-1
            while m >= 0:
                if abs(file_data[i+m]-file_data[j+m])>tolerance:
                    mabove=m
                    while mabove>=0:
                        if i+mabove<data_len-(dimension-1) and j+mabove<data_len-(dimension-1):
                            Nm[i+mabove]-=1
                            Nm[j+mabove]-=1
                        if i+mabove<data_len-dimension and j+mabove<data_len-dimension:
                            Nmp[i+mabove]-=1
                            Nmp[j+mabove]-=1
                        if i+mabove<data_len-dimension+1 and j+mabove<data_len-dimension+1:
                            burned_indexes[i+mabove][j+mabove]=None
                        mabove-=1
                    break
                m-=1
            if m<0 and i<data_len-dimension and j<data_len-dimension and abs(file_data[i+dimension]-file_data[j+dimension])>tolerance:
                        Nmp[i]-=1
                        Nmp[j]-=1

    Cm = [line/float(data_len-dimension+1) for line in Nm]
    Cmp = [line/float(data_len-dimension) for line in Nmp]

    Phi_m = numpy.mean([numpy.log(pos) for pos in Cm])
    Phi_mp = numpy.mean([numpy.log(pos) for pos in Cmp])
    
    Ap_En = Phi_m - Phi_mp

    return EntropyData(len(file_data),Ap_En)


def transform_to_space(m,data):
    pointArray=[]
    for index in range(len(data)):
        pointArray[index]=[axis for axis in data[i:i+m]]
    return pointArray
        

#def fast_apen(filename,args):
#    """Try the implementation described in this article 
#    http://www.sciencedirect.com/science/article/pii/S0169260710002956"""
#
#    with open(filename,"r") as file_d:
#        file_data = file_d.readlines()
#    file_data = list(map(float,file_data))
#
#    data_len = len(file_data)
#
#    pointArray = transform_to_space(m,file_data)
#    
#    pointArray.sort()

def sampen(filename,dimension,tolerance):
    """
    A function that uses the pyeeg implementation of sample entropy to 
    calculte the entropy for one file. 
    
    ARGUMENTS: String filename, int dimension, float tolerance
    
    RETURN: EntropyData type
    """
    with open(filename,'r') as file_d:
        file_data= file_d.readlines()
    file_data=list(map(float,file_data))
    return EntropyData(len(file_data),samp_entropy(file_data,dimension,tolerance))

def calculate_file_std(filename):
    """
    Function to calculate the standard deviation of the values in a single file.
    
    ARGUMENTS: String filename.
    
    RETURN: float standard deviation of file data.
    """
    with open(filename,"rU") as fdin:
        file_data = fdin.readlines()
    file_data = list(map(float,file_data))
    return numpy.std(file_data)

#AUXILIARY FUNCTIONS

def add_parser_options(parser):
    """
    !!!Auxiliary function!!!  These are arguments for an argparse
    parser or subparser, and are the optional arguments for
    the entry function in this module

    Arguments: The parser to which you want the arguments added to.
    
    Return:None
    """
    entropy_parsers = parser.add_subparsers(help='Diferent methods for calculating entropy', dest="entropy")

    samp_en = entropy_parsers.add_parser('sampen', help="Sample Entropy")
    samp_en.add_argument('-t','--tolerance',dest="tolerance",type=float,action="store",metavar="TOLERANCE",help="Tolerance level to be used when calculating sample entropy. [default:%(default)s]",default=0.1)
    samp_en.add_argument('-d','--dimension',dest="dimension",type=int,action="store",metavar="MATRIX DIMENSION",help="Matrix Dimension. [default:%(default)s]",default=2)

    ap_en = entropy_parsers.add_parser('apen', help="Aproximate Entropy")
    ap_en.add_argument('-t','--tolerance',dest="tolerance",type=float,action="store",metavar="TOLERANCE",help="Tolerance level to be used when calculating aproximate entropy. [default:%(default)s]",default=0.1)
    ap_en.add_argument('-d','--dimension',dest="dimension",type=int,action="store",metavar="MATRIX DIMENSION",help="Matrix Dimension. [default:%(default)s]",default=2)

    ap_en_v2 = entropy_parsers.add_parser('apenv2', help="Aproximate Entropy version 2")
    ap_en_v2.add_argument('-t','--tolerance',dest="tolerance",type=float,action="store",metavar="TOLERANCE",help="Tolerance level to be used when calculating aproximate entropy. [default:%(default)s]",default=0.1)
    ap_en_v2.add_argument('-d','--dimension',dest="dimension",type=int,action="store",metavar="MATRIX DIMENSION",help="Matrix Dimension. [default:%(default)s]",default=2)