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

This module mostly reads the data from the files to a python list and
calls the function with the same name implemented in pyeeg, with the
exception of sample entropy wich is a command line call to an
executable, the executable is included in the tool directory for ease
of use, but you can download the code or just get to know the
implementation details from the project page cited below.

For all other function's documentation look at the pyeeg project page.

MODULE DEPENDENCIES:
pyeeg(http://code.google.com/p/pyeeg/downloads/list),
numpy(http://numpy.scipy.org/),
sampen(http://www.physionet.org/physiotools/sampen/)

This module's entry point function is entropy(...)
"""

import pyeeg
import sys
import os
import numpy

#ENTRY POINT FUNCTION

def entropy(input_name,function,*function_args):
    """
    Given a file or directory named input_name, calculate the desired
    entropy to all the files.

    Arguments: name of the directory/file where entropy should be
    calculated, entropy function to use, and the arguments to the
    selected entropy function.
    
    Return: Dictionary, where filenames are the keys and the values
    are tuples with the number of points in the files and entropy
    value.

    Algorithm: Retrieve a complete list of all the files in the
    directory.  For every file in the list calculate the entropy using
    the user chosen function.

    Note: The * in the last variable is so I can get a variable amount
    of argments to pass to the entropy calculating functions, if you
    look at those function's arguments you'll notice different numbers
    and types of arguments.
    """

    method_to_call= getattr(sys.modules[__name__],function)
    entropy_dict={}
    if os.path.isdir(input_name):
        filelist = os.listdir(input_name)
        for filename in filelist:
            file_points,file_entropy = method_to_call(os.path.join(input_name,filename.strip()),function_args)
            entropy_dict[filename.strip()] = (file_points,file_entropy)
    else:
        file_points,file_entropy = method_to_call(input_name.strip(),function_args)
        entropy_dict[input_name.strip()] = (file_points,file_entropy)
    return entropy_dict


#IMPLEMENTATION

def apen(filename,args):
    file_d = open(filename,"r")
    file_data = []
    for line in file_d:
        if len(line.split())==2:
            time, hrf = line.split()
        else:
            hrf = line
        file_data.append(float(hrf))
    try:
        dim, tolerance = args
    except:
        print "Error: Insuficient arguments to apply ap entropy"
        exit
    tolerance = tolerance*numpy.std(file_data)
    return len(file_data),pyeeg.ap_entropy(file_data, dim, tolerance)

# TODO
# def fast_apen(filename,args):
#    Try the implementation described in this article http://www.sciencedirect.com/science/article/pii/S0169260710002956
#

def sampen(filename,args):
    try:
        dim, tolerance = args
    except:
        print "Error: Insuficient arguments to apply sample entropy"
        exit
    with open(filename,'r') as file_d:
        file_data= file_d.readlines()
    if len(file_data)==0:
        return (0,0)
    result = os.popen('%s -r %f -m %d "%s"'%(os.path.join('tools','sampen'),tolerance,dim,filename))
    result = result.readlines()
    result = result[dim].split('=')[1]
    return len(file_data),result.strip()


def specen(filename,args):
    file_d = open(filename,"r")
    file_data = []
    for line in file_d:
        if len(line.split())==2:
            time, hrf = line.split()
        else:
            hrf = line
        file_data.append(float(hrf))
    try:
        Band, Fs = args
    except:
        print "Error: Insuficient arguments to apply spectral entropy"
        exit
    return len(file_data),pyeeg.spectral_entropy(file_data, Band, Fs)

def hurst(filename,args):
    file_d = open(filename,"r")
    file_data = []
    for line in file_d:
        if len(line.split())==2:
            time, hrf = line.split()
        else:
            hrf = line
        file_data.append(float(hrf))
    return len(file_data),pyeeg.hurst(file_data)

def dfa(filename,args):
    file_d = open(filename,"r")
    file_data = []
    for line in file_d:
        if len(line.split())==2:
            time, hrf = line.split()
        else:
            hrf = line
        file_data.append(float(hrf))
    return len(file_data),pyeeg.dfa(file_data)


def hjorth(filename,args):
    file_d = open(filename,"r")
    file_data = []
    for line in file_d:
        if len(line.split())==2:
            time, hrf = line.split()
        else:
            hrf = line
        file_data.append(float(hrf))
    return len(file_data),pyeeg.hjorth(file_data)

def pfd(filename,args):
    file_d = open(filename,"r")
    file_data = []
    for line in file_d:
        if len(line.split())==2:
            time, hrf = line.split()
        else:
            hrf = line
        file_data.append(float(hrf))
    return len(file_data),pyeeg.pfd(file_data)

def hfd(filename,args):
    try:
        kmax = args[0]
    except:
        print "Error: Insuficient arguments to apply hfd"
        exit
    file_d = open(filename,"r")
    file_data = []
    for line in file_d:
        if len(line.split())==2:
            time, hrf = line.split()
        else:
            hrf = line
        file_data.append(float(hrf))
    return len(file_data),pyeeg.hfd(file_data,kmax)


def fi(filename,args):
    try:
        dim,tau = args
    except:
        print "Error: Insuficient arguments to apply fi"
        exit
    file_d = open(filename,"r")
    file_data = []
    for line in file_d:
        if len(line.split())==2:
            time, hrf = line.split()
        else:
            hrf = line
        file_data.append(float(hrf))
    seq = pyeeg.embed_seq(file_data, tau, dim)
    w = numpy.linalg.svd(seq, compute_uv=0)
    w /= sum(w)
    return len(file_data),pyeeg.fisher_info(file_data, tau, dim, w)

def svden(filename,args):
    try:
        dim,tau = args
    except:
        print "Error: Insuficient arguments to apply fi"
        exit
    file_d = open(filename,"r")
    file_data = []
    for line in file_d:
        if len(line.split())==2:
            time, hrf = line.split()
        else:
            hrf = line
        file_data.append(float(hrf))
    seq = pyeeg.embed_seq(file_data, tau, dim)
    w = numpy.linalg.svd(seq, compute_uv=0)
    w /= sum(w)
    return len(file_data),pyeeg.svd_entropy(file_data, tau, dim, w)


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

    spec_en = entropy_parsers.add_parser('specen', help="Spectral Entropy")

    hurst_en = entropy_parsers.add_parser('hurst', help="Hurst Exponent")

    dfa_en = entropy_parsers.add_parser('dfa', help="Detrended Fluctuation Analysis")

    hjorth_en = entropy_parsers.add_parser('hjorth', help="Hjorth Mobility and Complexity")
    
    pfd_en = entropy_parsers.add_parser('pfd', help="Petrosian Fractal Dimension")

    hfd_en = entropy_parsers.add_parser('hfd', help="Higuchi Fractal Dimension")
    hfd_en.add_argument('-k','--kmax',dest="kmax",type=int,action="store",metavar="KMAX",help="Value of Kmax. [default:%(default)s]",default=5)

    fi_en = entropy_parsers.add_parser('fi', help="Fisher Information")
    fi_en.add_argument('-t','--tau',dest="tau",type=int,action="store",metavar="TAU",help="Value of Tau. [default:%(default)s]",default=4)
    fi_en.add_argument('-d','--dimension',dest="dimension",type=int,action="store",metavar="DIMENSION",help="Dimension. [default:%(default)s]",default=10)

    svd_en = entropy_parsers.add_parser('svden', help="Singular Value Decomposition Entropy")
    svd_en.add_argument('-d','--dimension',dest="dimension",type=int,action="store",metavar="DIMENSION",help="Dimension. [default:%(default)s]",default=10)
    svd_en.add_argument('-t','--tau',dest="tau",type=int,action="store",metavar="TAU",help="Value of Tau. [default:%(default)s]",default=4)
    
