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

COMPRESSORS IMPLEMENTED: paq8l, lzma, gzip, bzip2, ppmd, spbio.

!!!IMPLEMENTATION NOTE: Not all the compressor have an outpufile parameter, which
means those compressors produce a compressed file with the exact same name as the
original but with some extra prefix. To mantain some coherence troughout the code
a choice was made to force the same behavior in all the compressors who write 
output files. This however means the same directory/file cannot be compressed in
the same machine at the same time since one of the processes could delete or rewrite
the temporary file before the other was finished using it.!!!

MODULE EXTERNAL DEPENDENCIES: 
                     lzma module for python.
                     ppmd, paq8l and spbio have to be installed in the system 
                     path if you would like to use them.


ENTRY POINT: compress(input_name,compression_algorithm,level,decompress=False)

"""

import os
import subprocess
import sys
import zlib
import bz2
import timeit
import time
from collections import namedtuple
try:
    import lzma
    lzma_available=True
except ImportError:
    try:
        import pylzma as lzma
        lzma_available=True
    except ImportError:
        lzma_available=False



#from memoize import Memoize

#DATA TYPE DEFINITIONS
"""This is a data type defined to be used as a return for compression; it
contains the original size of the file, the size of the resulting compressed 
file and the time it takes to decompress it(null if the timing is not run)"""
CompressionData = namedtuple('CompressionData','original compressed time')

#ENTRY POINT FUNCTION
#@Memoize
def compress(input_name,compression_algorithm,level,decompress=False):
    """Given a file or directory named input_name, apply the desired
    compression algorithm to all the files. Optionaly a timming on 
    decompression may also be run.

    ARGUMENTS: String name of the directory/file where compression should be
    applied, String compression algorithm to use, int level of compression, bool
    whether or not to preform a timming for the decompression.
    
    RETURN: Dictionary, whith filenames as keys and CompressionData as values.

    """

    compressed ={}
    method_to_call= getattr(sys.modules[__name__],compression_algorithm+'_compress')
    
    if level>AVAILABLE_COMPRESSORS[compression_algorithm][1]: 
        level=AVAILABLE_COMPRESSORS[compression_algorithm][1]
    elif level<AVAILABLE_COMPRESSORS[compression_algorithm][0]: 
        level=AVAILABLE_COMPRESSORS[compression_algorithm][0]


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
    Compresses one file using the python implementation of zlib.

    ARGUMENTS: String name of the file to be compressed, int level of compression,
    bool whether or not decompression time should be calculated.

    RETURN: CompressionData object.

    Algorithm: The input file is opened and it's content extracted
    to a string wich is used to crate a memoyview, the compress function from 
    the zlib module is called with the byte buffer exposed by the memoryview.
    The length of the string(or bytearray in python3) returned by the compress 
    method is the size of the compressed data. If decompress is True the 
    decompression operation is run and the minimum run time is added to the 
    CompressionData type.

    NOTE: Although this uses the name gzip the actual tool being used
    is python's zlib which has the actual implementation of the deflate 
    compression algorithm. This is possible because the only difference between 
    gzip and zlib is the header added to the compressed file, which is not in the 
    resulting compressed string.
    """
    
    original_size= int(os.stat(inputfile).st_size)
    with open(inputfile,"rU") as fdorig:
        origlines=fdorig.read()
    origtext = memoryview(bytearray(origlines,"utf8"))
    compressedtext = memoryview(zlib.compress(origtext.tobytes(),int(level)))
    compressed_size = len(compressedtext)

    decompress_time=None
    if decompress:
        decompress_time = min(timeit.repeat(lambda: zlib.decompress(compressedtext.tobytes()),
                                            number=10,
                                            repeat=3,timer=time.clock))
    
    cd = CompressionData(original_size,compressed_size,decompress_time)

    return cd



def paq8l_compress(inputfile,level,decompress):
    """
    Compresses one file using the paq8l compressor, the size is
    determined by quering the file paq8l creates, this temporary file
    is removed at the end of this function.

    ARGUMENTS: String name of the file to be compressed, int level of compression,
    bool whether or not decompression time should be calculated.

    RETURN: CompressionData object.

    ALGORITHM: The filename is passed to paq8l for compression wich generates a 
    file with the same name plus the extension .paq8l. A query is made on the 
    system to find the size of the generated  file. If decompressio is True the 
    decompression of this file is run three times and the minimum time is recorded. 
    The temporary compressed file is deleted.

    """
    subprocess.check_output('paq8l -%d "%s"'%(level,inputfile),
                            shell=True,
                            stderr=subprocess.STDOUT)
    original_size= int(os.stat(inputfile).st_size)
    compressed_size = int(os.stat(inputfile+'.paq8l').st_size)
    decompress_time=None
    if decompress:
        decompress_time = min(timeit.repeat('subprocess.check_output(\'paq8l -d "%s.paq8l"\',shell=True,stderr=subprocess.STDOUT)'%inputfile,
                                            number=10,
                                            repeat=3,
                                            setup='import subprocess'))
        
    os.remove('%s.paq8l'%inputfile)

    cd = CompressionData(original_size,compressed_size,decompress_time)

    return cd


def lzma_compress(inputfile,level,decompress):
    """
    Compresses one file using the python implementation of lzma.

    ARGUMENTS: String name of the file to be compressed, int level of compression,
    bool whether or not decompression time should be calculated.

    RETURN: CompressionData object.

    ALGORITHM: The input file is opened and it's content extracted to a string 
    which is used to crate a memoyview, the compress function from the lzma module
    is called with the byte buffer exposed by the memoryview.
    The length of the string(or bytearray in python3) returned by the compress 
    method is the size of the compressed data. If decompress is True the 
    decompression operation is run and the minimum run time is added to the 
    CompressionData type.
    
    NOTE: The lzma module was created for python3, the backported version for 
    python2.7, does not have a level parameter, a decision was made to keep this
    code compatible for Python2.7 so the level parameter is never used ( by 
    default the level used is 6).
     """

    original_size= int(os.stat(inputfile).st_size)
    with open(inputfile,"rU") as fdorig:
        origlines=fdorig.read()
    origtext = memoryview(bytearray(origlines,"utf8"))
    compressedtext = memoryview(lzma.compress(origtext.tobytes()))#, preset=level available in python3
    compressed_size = len(compressedtext)

    decompress_time=None
    if decompress:
        decompress_time = min(timeit.repeat(lambda: lzma.decompress(compressedtext.tobytes()),
                                            number=10, 
                                            repeat=3,timer=time.clock))

    cd = CompressionData(original_size,compressed_size,decompress_time)

    return cd




def bzip2_compress(inputfile,level,decompress):
    """
    Compresses one file using the python implementation of bzip2.

    ARGUMENTS: String name of the file to be compressed, int level of compression,
    bool whether or not decompression time should be calculated.

    RETURN: CompressionData object.

    ALGORITHM: The input file is opened and it's content extracted to a string 
    which is used to crate a memoyview, the compress function from the bzip 
    module is called with the byte buffer exposed by the memoryview.
    The length of the string(or bytearray in python3) returned by the compress 
    method is the size of the compressed data. If decompress is True the 
    decompression operation is run and the minimum run time is added to the 
    CompressionData type.

    """

    original_size= int(os.stat(inputfile).st_size)
    with open(inputfile,"rU") as fdorig:
        origlines=fdorig.read()
    origtext = memoryview(bytearray(origlines,"utf8"))
    compressedtext = memoryview(bz2.compress(origtext.tobytes(),level))
    compressed_size = len(compressedtext)

    decompress_time=None
    if decompress:
        decompress_time = min(timeit.repeat(lambda: bz2.decompress(compressedtext.tobytes()),
                                            number=10,
                                            repeat=3,timer=time.clock))

    cd = CompressionData(original_size,compressed_size,decompress_time)

    return cd

def ppmd_compress(inputfile,level,decompress):
    """
    Compresses one file using the ppmd compressor.

    ARGUMENTS: String name of the file to be compressed, int level of compression,
    bool whether or not decompression time should be calculated.

    RETURN: CompressionData object.

    ALGORITHM: The filename is passed to ppmd for compression which generates a 
    file with the same name plus the extension .ppmd.  A query is made on the 
    system to find the what size of the generated file. If decompressio is True 
    the decompression of this file is run three times and the minimum time is 
    recorded. The temporary compressed file is deleted.
    
    NOTE: This algorithm does not have a standard level, but the model
    order behaves as a compression level, so level here refers to the
    order level. Maximum memory is always used.
    """
    subprocess.call('ppmd e -s -f"%s.ppmd" -m256 -o%d "%s"'%(inputfile,level,inputfile),
                    shell=True)
    original_size= int(os.stat(inputfile).st_size)
    compressed_size = int(os.stat(inputfile+'.ppmd').st_size)
    
    decompress_time=None
    if decompress:
        decompress_time = min(timeit.repeat('subprocess.call(\'ppmd d -s "%s.ppmd"\',shell=True,stderr=subprocess.STDOUT)'%inputfile,
                                             number=5,
                                             repeat=3,
                                             setup='import subprocess'))
        
    os.remove('%s.ppmd'%inputfile)

    cd = CompressionData(original_size,compressed_size,decompress_time)

    return cd

def spbio_compress(inputfile,level,decompress):
    """
    Compresses one file using the spbio tool.

    ARGUMENTS: String name of the file to be compressed, int level of compression.
    bool whether or not decompression time should be calculated.

    RETURN: CompressionData object.

    ALGORITHM: The filename is passed to paq8l for compression which generates a
    file with the same name plus the extension .sph. A query is made on the system
    to find the what size of the generated file. Although it is in the options at
    this moment the decompress operation is not implemented. The temporary 
    compressed file is deleted.

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

    !!!Auxiliary function!!! Function to test the system path for available
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
    parser or subparser, and are the parameters taken by the entry function 
    in this module

    ARGUMENTS: The parser to which you want the arguments added to.
    
    RETURN: None
    """
    parser.add_argument("-c",
                        "--compressor",
                        dest="compressor",
                        metavar="COMPRESSOR",
                        action="store",
                        choices=AVAILABLE_COMPRESSORS,
                        default=list(AVAILABLE_COMPRESSORS.keys())[0],
                        help="compression compressor to be used, available compressors:"+', '.join(AVAILABLE_COMPRESSORS)+";default:[%(default)s]")
    parser.add_argument("--decompress",
                        dest="decompress",
                        action="store_true",
                        default=False,
                        help="Use this options if you want the decompressio time instead of the compression size")
    parser.add_argument("--level",
                        dest="level",
                        metavar="LEVEL",
                        action="store",
                        type=int,
                        help="compression level to be used, this variable is compressor dependent; default:[The maximum of wathever compressor was chosen]")

def set_level(options):
    """
    !!!Auxilary function!!!
    Changes the value of level in the options to be within the maximum or minimum 
    levels for the chosen compressor.
    
    ARGUMENTS: A dictionary of options with a compressor key for the chosen compressor.
    
    RETURN: None
    """
    if ((not options['level']) or 
        (options['level']> AVAILABLE_COMPRESSORS[options['compressor']][1])):
        level= AVAILABLE_COMPRESSORS[options['compressor']][1]
    elif options['level']< AVAILABLE_COMPRESSORS[options['compressor']][0]:
        level= AVAILABLE_COMPRESSORS[options['compressor']][0]
    else:
        level= options['level']
    return level
