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

COMPRESSORS AVAILABLE: zlib, paq8l, lzma, gzip, zip, bzip2, ppmd, spbio.

Not all the compressor have an outpufile parameter, wich means they
   produce a compressed file with the exact same name as the original
   but with some extra prefix. To mantain some coherence troughout the
   code I opted to force the same behavior in all the
   compressors. This however means the same directory/file cannot be
   compressed concurrently in the same machine since one of the
   processes could delete the temporary file before the other was
   finished using it.

MODULE DEPENDENCIES: 
                     Zlib module for python.
                     This modules uses system installed compressors. 

This module's entry point function is compress(...)

"""

import os
import subprocess
import sys
import zlib
import bz2
try:
    import lzma
    lzma_available=True
except ImportError:
    try:
        import pylzma as lzma
        lzma_available=True
    except ImportError:
        lzma_available=False
        
import timeit

from collections import namedtuple
#from memoize import Memoize

#DEFINITIONS

CompressionData = namedtuple('CompressionData','original compressed time')

#ENTRY POINT FUNCTION
#@Memoize
def compress(input_name,compression_algorithm,level,decompress=False):
    """Given a file or directory named input_name, apply the desired
    compression algorithm to all the files.

    Arguments: name of the directory/file where compression should be
    applied, compression algorithm to use, level of compression.
    
    Return: Dictionary, where filenames are the keys and the values
    are tuples with the files original size and compressed size.

    Algorithm: Retrieve a complete list of all the files in the
    directory, since at each step we will be creatig temporary files
    in the same directory we use .readlines() to make sure the list is
    static.  For every file in the list apply the chosen compression
    algorithm by querying the module attributes

    Implementation Note: sys.modules[__name__] gives you the current
    module, get arg fetches the function that will be used wich should
    be a concatenation of the ahgorithm being used with _compress

    """

    compressed ={}
    method_to_call= getattr(sys.modules[__name__],compression_algorithm+'_compress')
    
    if level>AVAILABLE_COMPRESSORS[compression_algorithm][1]: 
        level=str(AVAILABLE_COMPRESSORS[compression_algorithm][1])
    elif level<AVAILABLE_COMPRESSORS[compression_algorithm][0]: 
        level=str(AVAILABLE_COMPRESSORS[compression_algorithm][0])
    else:
        level=str(level)


    if os.path.isdir(input_name):
        filelist = os.listdir(input_name)
        for filename in filelist:
            filename = filename.strip()#removes the tailing \n
            compression_data = method_to_call(os.path.join(input_name,filename),level,decompress)
            compressed[filename.strip()]= compression_data
    else:
        compression_data = method_to_call(input_name.strip(),level,decompress)
        compressed[input_name.strip()]= compression_data
    return compressed


#IMPLEMENTATION

def gzip_compress(inputfile,level,decompress): 

    """ 
    Compresses one file using the python implementation of zlib, the
    size is determined by quering a temporary file created from the
    resulting string, this temporary file is removed when the
    process is over.

    Arguments: name of the file to be compressed,level of compression,
    whether or not decompression time should be calculated.

    Return: CompressionData object.

    Algorithm: The input file is opened and it's content extracted
    to a string, the compress function from the zlib module is
    called with that string as an argument. The string returned by
    the compress method is then writen to a temporary file.  A query
    is made on the system to find the size of the generated file.
    The temporary file generated is deleted.

    NOTE: Although this uses the name gzip the actual tool being used
    is python's zlib wich is the actual implementation of the the
    deflate compression algorithm.
    """
    
    original_size= int(os.stat(inputfile).st_size)
    with open(inputfile,"rU") as fdorig:
        origlines=fdorig.read()
    origtext = memoryview(bytearray(origlines,"utf8"))
    compressedtext = bytearray(zlib.compress(origtext.tobytes(),int(level)))
    with open(inputfile+".gz","wb") as fdout:
        fdout.write(compressedtext)
    compressed_size = int(os.stat(inputfile+'.gz').st_size)

    decompress_time=None
    if decompress:
        decompress_time = min(timeit.repeat(lambda: zlib.decompress(compressedtext),number=10,repeat=3))

        
    os.remove('%s.gz'%inputfile)

    cd = CompressionData(original_size,compressed_size,decompress_time)

    return cd



def paq8l_compress(inputfile,level,decompress):
    """
    Compresses one file using the paq8l tool, the size is
    determined by quering the file paq8l creates, this temporary file
    is removed when the process is over and it's size is returned

    Arguments: name of the file to be compressed,level of compression,
    whether or not decompression time should be calculated.

    Return: CompressionData object.

    Algorithm: The filename is passed to paq8l for compression wich
    generates a file with the same name plus the extension .paq8l.  A
    query is made on the system to find the what size of the generated
    file.  The file generated by paq8l is deleted.

    """
    subprocess.check_output('paq8l -%s "%s"'%(level,inputfile),shell=True,stderr=subprocess.STDOUT)
    original_size= int(os.stat(inputfile).st_size)
    compressed_size = int(os.stat(inputfile+'.paq8l').st_size)
    decompress_time=None
    if decompress:
        decompress_time = min(timeit.repeat('subprocess.check_output(\'paq8l -d "%s.paq8l"\',shell=True,stderr=subprocess.STDOUT)'%inputfile,number=25,repeat=3,setup='import subprocess'))
        
    os.remove('%s.paq8l'%inputfile)

    cd = CompressionData(original_size,compressed_size,decompress_time)

    return cd


def lzma_compress(inputfile,level,decompress):
    """
    Compresses one file using the python implementation of zlib, the
    size is determined by quering a temporary file created from the
    resulting string, this temporary file is removed when the
    process is over.

    Arguments: name of the file to be compressed,level of compression,
    whether or not decompression time should be calculated.

    Return: CompressionData object.

    Algorithm: The input file is opened and it's content extracted
    to a string, the compress function from the zlib module is
    called with that string as an argument. The string returned by
    the compress method is then writen to a temporary file.  A query
    is made on the system to find the size of the generated file.
    The temporary file generated is deleted.

    NOTE: The lzma module was created for python3, the backported
    version for python2.7, does allow the change of compression level,
    a default level 6 is used.
     """

    original_size= int(os.stat(inputfile).st_size)
    with open(inputfile,"rU") as fdorig:
        origlines=fdorig.read()
    origtext = memoryview(bytearray(origlines,"utf8"))
    compressedtext = bytearray(lzma.compress(origtext.tobytes()))#, preset=int(level)))this is a backported version of this module no levels implemneted ,preset=int(level) will be available in python3
    with open(inputfile+".lzma","wb") as fdout:
        fdout.write(compressedtext)
    compressed_size = int(os.stat(inputfile+'.lzma').st_size)

    decompress_time=None
    if decompress:
        decompress_time = min(timeit.repeat(lambda: lzma.decompress(compressedtext),number=10, repeat=3))
        
    os.remove('%s.lzma'%inputfile)

    cd = CompressionData(original_size,compressed_size,decompress_time)

    return cd




def bzip2_compress(inputfile,level,decompress):
    """
    Compresses one file using the python implementation of bzip2, the
    size is determined by quering a temporary file created from the
    resulting string, this temporary file is removed when the process
    is over.

    Arguments: name of the file to be compressed,level of compression,
    whether or not decompression time should be calculated.

    Return: CompressionData object.

    Algorithm: The input file is opened and it's content extracted
    to a string, the compress function from the bz2 module is
    called with that string as an argument. The string returned by
    the compress method is then writen to a temporary file.  A query
    is made on the system to find the size of the generated file.
    The temporary file generated is deleted.

    """

    original_size= int(os.stat(inputfile).st_size)
    with open(inputfile,"rU") as fdorig:
        origlines=fdorig.read()
    origtext = memoryview(bytearray(origlines,"utf8"))
    compressedtext = bytearray(bz2.compress(origtext.tobytes(),int(level)))
    with open(inputfile+".bz2","w") as fdout:
        fdout.write(compressedtext)
    compressed_size = int(os.stat(inputfile+'.bz2').st_size)

    decompress_time=None
    if decompress:
        decompress_time = min(timeit.repeat(lambda: bz2.decompress(compressedtext),number=10,repeat=3))
        
    os.remove('%s.bz2'%inputfile)

    cd = CompressionData(original_size,compressed_size,decompress_time)

    return cd

def ppmd_compress(inputfile,level):
    """
    Compresses one file using the ppmd tool, the size is determined by
    quering the a temporary file created by ppmd, this temporary file
    is removed when the process is over and it's size is returned.

    Arguments: name of the file to be compressed,level of compression.

    Return: Size of the compressed file.

    Algorithm: The filename is passed to ppmd for compression wich
    generates a file with the extension .ppmd.  A query is made on the
    system to find the what size of the generated file.  The file
    generated by ppmd is deleted.

    NOTE: This algorithm does not have a standard level, but the model
    order behaves as a compression level, so level here refers to the
    order level. Maximum memory is always used.
    """
    os.system('ppmd e -f"'+inputfile+'.ppmd" -m256 -o'+level+' "'+inputfile+'"')
    original_size= int(os.stat(inputfile).st_size)
    compressed_size = int(os.stat(inputfile+'.ppmd').st_size)
    os.remove(inputfile+'.ppmd')
    return (original_size,compressed_size)


def spbio_compress(inputfile,level):
    """
    Compresses one file using the spbio tool, the size is determined by
    quering the a temporary file created by spbio, this temporary file
    is removed when the process is over and it's size is returned

    Arguments: name of the file to be compressed,level of compression.

    Return: Size of the compressed file.

    Algorithm: The filename is passed to spbio for compression wich
    generates a file with the extension .sph.  A query is made on the
    system to find the what size of the generated file.  The file
    generated by spbio is deleted.

    NOTE: This compressor is only available for Windows and has no
    compression levels.
    """
    os.system('spbio "'+inputfile+'"')
    original_size= int(os.stat(inputfile).st_size)
    compressed_size = int(os.stat(inputfile+'.sph').st_size)
    os.remove(inputfile+'.sph')
    return (original_size,compressed_size)


#AUXILIARY FUNCTIONS

def test_compressors():
    """

    !!!Auxiliary function!!! Function to test the system for available
    compressors from within the ones that are implemented.

    Minimum and maximum levels are defined acording to the compressor,
    if there are no levels implemented both minimum and maximum are
    -1.
    """
    compressor_list={"paq8l":(1,8),"ppmd":(2,16),"spbio":(-1,-1)}
    available={}
    available["gzip"]=(1,9)
    available["bzip2"]=(1,9)
    if lzma_available:
        available["lzma"]=(6,6)
    exec_path = os.environ.get("PATH")
    exec_path = exec_path.split(';')
    if len(exec_path)==1:
        exec_path = exec_path[0].split(':')
    for compressor in compressor_list:
        for dir_in_path in exec_path:
            if os.path.exists(os.path.join(dir_in_path,compressor)) or  os.path.exists(os.path.join(dir_in_path,compressor+'.exe')):
                available[compressor]=compressor_list[compressor]
    return available

AVAILABLE_COMPRESSORS=test_compressors()


def add_parser_options(parser):
    """
    !!!Auxiliary function!!!  These are arguments for an argparse
    parser or subparser, and are the optional arguments for
    the entry function in this module

    Arguments: The parser to which you want the arguments added to.
    
    Return:None
    """
    parser.add_argument("-c","--compressor",dest="compressor",metavar="COMPRESSOR",action="store",choices=AVAILABLE_COMPRESSORS,default=list(AVAILABLE_COMPRESSORS.keys())[0],help="compression compressor to be used, available compressors:"+', '.join(AVAILABLE_COMPRESSORS)+";default:[%(default)s]")
    parser.add_argument("--decompress",dest="decompress",action="store_true",default=False,help="Use this options if you want the decompressio time instead of the compression size")
    parser.add_argument("--level",dest="level",metavar="LEVEL",action="store",type=int,help="compression level to be used, this variable is compressor dependent; default:[The maximum of wathever compressor was chosen]")

def set_level(options):
    if ((not options['level']) or 
        (options['level']> AVAILABLE_COMPRESSORS[options['compressor']][1])):
        level= AVAILABLE_COMPRESSORS[options['compressor']][1]
    elif options['level']< AVAILABLE_COMPRESSORS[options['compressor']][0]:
        level= AVAILABLE_COMPRESSORS[options['compressor']][0]
    else:
        level= options['level']
    return level
