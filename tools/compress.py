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
import timeit
import time
from collections import namedtuple
from memoize import Memoize

#DEFINITIONS

CompressionData = namedtuple('CompressionData','original compressed time')

#ENTRY POINT FUNCTION
@Memoize
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
    
    if level>AVAILABLE_COMPRESSORS[compression_algorithm][1] : level=str(AVAILABLE_COMPRESSORS[compression_algorithm][1])
    elif level<AVAILABLE_COMPRESSORS[compression_algorithm][0] : level=str(AVAILABLE_COMPRESSORS[compression_algorithm][0])
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

def zlib_compress(inputfile,level): 

    """ 
    Compresses one file using the python implementation of zlib, the
    size is determined by quering a temporary file created from the
    resulting string, this temporary file is removed when the
    process is over.

    Arguments: name of the file to be compressed,level of compression.

    Return: Size of the compressed file.

    Algorithm: The input file is opened and it's content extracted
    to a string, the compress function from the zlib module is
    called with that string as an argument. The string returned by
    the compress method is then writen to a temporary file.  A query
    is made on the system to find the size of the generated file.
    The temporary file generated is deleted.

    """
    original_size= int(os.stat(inputfile).st_size)
    with open(inputfile,"r") as fdorig:
        origlines=fdorig.readlines()
    origtext = '\n'.join(origlines)
    compressedtext = zlib.compress(origtext,int(level))
    with open(inputfile+".zlib","w") as fdout:
        fdout.write(compressedtext)
    compressed_size = int(os.stat(inputfile+'.zlib').st_size)
    os.remove(inputfile+'.zlib')
    return (original_size,compressed_size)


def paq8l_compress(inputfile,level,decompress):
    """
    Compresses one file using the paq8l tool, the size is
    determined by quering the file paq8l creates, this temporary file
    is removed when the process is over and it's size is returned

    Arguments: name of the file to be compressed,level of compression.

    Return: Size of the compressed file.

    Algorithm: The filename is passed to paq8l for compression wich
    generates a file with the same name plus the extension .paq8l.  A
    query is made on the system to find the what size of the generated
    file.  The file generated by paq8l is deleted.

    """
    subprocess.call('paq8l -%s "%s"'%(level,inputfile),shell=True)
    original_size= int(os.stat(inputfile).st_size)
    compressed_size = int(os.stat(inputfile+'.paq8l').st_size)
    decompress_time=None
    if decompress:
        decompress_time = timeit.timeit('subprocess.call(\'paq8l -d "%s.paq8l"\',shell=True)'%inputfile,number=10,setup='import subprocess')
        
    os.remove('%s.paq8l'%inputfile)

    cd = CompressionData(original_size,compressed_size,decompress_time)

    return cd


def lzma_compress(inputfile,level,decompress):
    """
    Compresses one file using the lzma tool, the size is determined by
    quering the a temporary file created by lzma, this temporary file
    is removed when the process is over and it's size is returned

    Arguments: name of the file to be compressed,level of compression.

    Return: Size of the compressed file.

    Algorithm: The filename is passed to lzma for compression wich
    generates a file with the extension .lzma.  A query is made on the
    system to find the what size of the generated file.  The file
    generated by lzma is deleted.

     """
    subprocess.call('lzma -c -%s "%s" > "%s.lzma"'%(level,inputfile,inputfile),shell=True)
    original_size= int(os.stat(inputfile).st_size)
    compressed_size = int(os.stat(inputfile+'.lzma').st_size)
    decompress_time=None
    
    if decompress:
        decompress_time = timeit.timeit('subprocess.call(\'lzma -dkf "%s.lzma"\',shell=True)'%inputfile,number=10,setup='import subprocess')     

    os.remove('%s.lzma'%inputfile)

    cd = CompressionData(original_size,compressed_size,decompress_time)
    return cd

def gzip_compress(inputfile,level,decompress):
    """
    Compresses one file using the gzip tool, the size is determined by
    quering the a temporary file created by gzip, this temporary file
    is removed when the process is over and it's size is returned

    Arguments: name of the file to be compressed,level of compression.

    Return: Size of the compressed file.

    Algorithm: The filename is passed to gzip for compression wich
    generates a file with the extension .gz.  A query is made on the
    system to find the what size of the generated file.  The file
    generated by gzip is deleted.

    """

    subprocess.call('gzip -c -%s "%s" > "%s.gz"'%(level,inputfile,inputfile),shell=True)
    original_size= int(os.stat(inputfile).st_size)
    compressed_size = int(os.stat(inputfile+'.gz').st_size)
    decompress_time=None
    if decompress:
        decompress_time = timeit.timeit('subprocess.check_output(\'gzip -dc "%s.gz"\',shell=True)'%inputfile,number=10,setup='import subprocess')     

    os.remove('%s.gz'%inputfile)

    cd = CompressionData(original_size,compressed_size,decompress_time)
    return cd

def zip_compress(inputfile,level):
    """
    Compresses one file using the zip tool, the size is determined by
    quering the a temporary file created by zip, this temporary file
    is removed when the process is over and it's size is returned

    Arguments: name of the file to be compressed,level of compression.

    Return: Size of the compressed file.

    Algorithm: The filename is passed to zip for compression wich
    generates a file with the extension .zip.  A query is made on the
    system to find the what size of the generated file.  The file
    generated by zip is deleted.

    """
    os.system('zip -'+level+' "'+inputfile+'.zip" "'+inputfile+'"')
    original_size= int(os.stat(inputfile).st_size)
    compressed_size = int(os.stat(inputfile+'.zip').st_size)

    os.remove(inputfile+'.zip')
    return (original_size,compressed_size)

def bzip2_compress(inputfile,level,decompress):
    """
    Compresses one file using the bzip2 tool, the size is determined by
    quering the a temporary file created by bzip2, this temporary file
    is removed when the process is over and it's size is returned

    Arguments: name of the file to be compressed,level of compression.

    Return: Size of the compressed file.

    Algorithm: The filename is passed to bzip2 for compression wich
    generates a file with the extension .bz2.  A query is made on the
    system to find the what size of the generated file.  The file
    generated by bzip2 is deleted.
    """
    subprocess.call('bzip2 -c -%s "%s" > "%s.bz2"'%(level,inputfile,inputfile),shell=True)
    original_size= int(os.stat(inputfile).st_size)
    compressed_size = int(os.stat(inputfile+'.bz2').st_size)
    decompress_time=None
    if decompress:
        decompress_time = timeit.timeit('subprocess.check_output(\'bzcat "%s.bz2"\',shell=True)'%inputfile,number=10,setup='import subprocess')     

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

    """
    compressor_list={"paq8l":(1,8),"lzma":(0,9),"gzip":(1,9),"zip":(1,9),"bzip2":(1,9),"ppmd":(2,16),"spbio":(None,None)}
    available={}
    exec_path = os.environ.get("PATH")
    exec_path = exec_path.split(';')
    if len(exec_path)==1:
        exec_path = exec_path[0].split(':')
    for compressor in compressor_list:
        for dir_in_path in exec_path:
            if os.path.exists(os.path.join(dir_in_path,compressor)) or  os.path.exists(os.path.join(dir_in_path,compressor+'.exe')):
                available[compressor]=compressor_list[compressor]
    available["zlib"]=(1,9)
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
    parser.add_argument("-c","--compressor",dest="compressor",metavar="COMPRESSOR",action="store",choices=AVAILABLE_COMPRESSORS,default=AVAILABLE_COMPRESSORS.keys()[0],help="compression compressor to be used, available compressors:"+', '.join(AVAILABLE_COMPRESSORS)+";default:[%(default)s]")
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
