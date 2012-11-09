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

This module creates the multiple scales for a file or all the files in
a directory. 

A scale is related to the number of points in a time series in this
case the practical creation of a scale N is achieved by taking every N
numbers and transforming them into one by calculating their mean.

MODULE DEPENDENCIES:
numpy(http://numpy.scipy.org/)

This module's entry point funtion is multiscale(...)
"""

import os
import numpy

#ENTRY POINT FUNCTION

def multiscale(input_name,dest_dir,start,stop,step):
    """
    Create all the scales in a given interval.

    Arguments: name of input directory/file, name of the output
    directory, first scale to be calculated, last scale to be
    calculated, jump between one scale and the next.

    Return: None
    """
    for scale in xrange(start,stop,step):
        output_dir = os.path.join(dest_dir,"Escala %d"%scale)
        if not os.path.isdir(output_dir):
            print "Creating Scale %d..."%scale
            os.makedirs(output_dir)
        else: 
            print "Scale %d exists, skipping..."%scale
        if os.path.isdir(input_name):
            filelist = os.listdir(input_name)
            for filename in filelist:
                create_scale(os.path.join(input_name,filename.strip()),output_dir,scale)
        else:
            create_scale(input_name.strip(),output_dir,scale)


#IMPLEMENTATION
def create_scale(inputfile, output_dir, scale):
    """
    This function creates a particular scale for one file.

    Arguments: name of file, directory where resulting file should be
    saved, scale size.

    Return: None

    Algorithm: Iteratively pass the file,on each iteration and
    calculate the mean of N numbers starting after the last number
    used in the previous iteration. Write the mean number into the
    resulting file.
    """
    filename=os.path.basename(inputfile)
    line_index=0
    with open(inputfile,"r") as fdin:
        with open(os.path.join(output_dir,filename),"w") as fdout:
            lines = fdin.readlines()
            lines = map(float,lines)
            while line_index+scale <=len(lines):
                scaled_hrf = numpy.mean(lines[line_index:line_index+scale])
                fdout.write('%.3f\n'%scaled_hrf)
                line_index+=scale


#AUXILIARY FUNCTIONS
def add_parser_options(parser):
    """
    !!!Auxiliary function!!!  These are arguments for an argparse
    parser or subparser, and are the optional arguments for
    the entry function in this module

    Arguments: The parser to which you want the arguments added to.
    
    Return:None
    """

    parser.add_argument("-start","--scale-start",metavar="SCALE",type=int,dest="scale_start",action="store",help="Start scales whith this amount of points. Default:[%(default)s]",default=2)
    parser.add_argument("-stop","--scale-stop",metavar="SCALE",type=int,dest="scale_stop",action="store",help="Stop scales whith this amount of points. Default:[%(default)s]",default=20)
    parser.add_argument("-step","--scale-step",metavar="STEP",type=int,dest="scale_step", action="store",help="Step between every two scales.Default:[%(default)s]", default=1)
