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

This module contains functions to calculates the distance between the
information in two files. The distance can be symmetrical or
asymmetrical depending if the value of the compression/entropy for the
concatenation of two files f1, f2 is the same whether you have f1.f2
or f2.f1.

Simetrical Distances:
Normalized Information Distance (compression)

Assymetrical Distances:
CrossEntropy (entropy): NOT IMPLEMENTED


This module's entry point function is distance(...)
"""


import sys
import os
import entropy
import compress
import tempfile

#ENTRY POINT FUNCTION
def distance(filename1,filename2,distance_definition,function,function_args):
    """Calculate the distance between two files using some defenition of distance.

    Arguments: Both files names,distance definition (one of the
    implemente definitions in this module), function is the particular
    function to be used (ex:paq8l,hdf,sampen,etc.), function_arg are
    arguments to be passed to the called function (ex:level for
    compressor and matrix and tolerance for sampen).

    Return: A float that represents the distance between the two files.
    """
    method_to_call = getattr(sys.modules[__name__],distance_defenition)
    return method_to_call(filename1,filename2,function,function_args)


#IMPLEMENTATION
def normalized_information_distance(filename1,filename2,compressor,level):
    """
    Use the compressor to calculate respectively c(f1f2),c(f1) and
    c(f2) and calculate the distance acording to the definition of
    normalized information distance:

    d(f1,f2) = (c(f1.f2)-min{c(f1),c(f2)})/max{c(f1),c(f2)},

    where c is the chosen compressor,and an application of c to a file
    is the size of that file compressed (This formula is based on
    Kolmogorov complexity concepts).
    

    Arguments: filename for both files, compressor, level of compression.
    
    Return: A float that represents the distance between the two
    files.

    Algorithm: Both files are opened and their content concatenated in
    a temporary file. Compression is then calculated for each file
    including the concatenation file, and the formula is applied.
    """
    file_total_data = []
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    with open(filename1,"r") as file1:
        file_total_data += file1.readlines()
    with open(filename2,"r") as file2:
        file_total_data += file2.readlines()
    for line in file_total_data:
        temp_file.write(line)
    (size_file1,size_file1_compressed) = compress.compress(filename1,compressor,level)[0]
    (size_file2,size_file2_compressed) = compress.compress(filename2,compressor,level)[0]
    (size_files_total,size_files_total_compressed) = compress.compress(temp_file.name,compressor,level)[0]
    print filename1,filename2,size_files_total_compressed
    dist = (size_files_total_compressed - min(size_file1_compressed,size_file2_compressed))/float(max(size_file1_compressed,size_file2_compressed))
    temp_file.close()
    os.unlink(temp_file.name)
    return dist
    

#AUXILIARY FUNCTION

def add_parser_options(parser):
    """
    !!!Auxiliary function!!!  These are arguments for an argparse
    parser or subparser, and are the optional arguments for
    the entry function in this module

    Arguments: The parser to which you want the arguments added to.
    
    Return:None
    """
    distance_parsers = parser.add_subparsers(help='Diferent Distance Definitions', dest="distance")
    
    nid = distance_parsers.add_parser('nid', help="Normalized Information Distance")
    compress.add_parser_options(nid)
