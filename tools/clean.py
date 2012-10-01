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


This module is very specific to this application. It either extracts
the time stamp and heart rate frequency(hrf) or just the hrf. 

Optionaly a limit may be applied to eliminate signal loss, we consider the
signal to be lost if hrf is bellow 50 or above 250. If a particular line is 
considered as signal lost it is ommited from the resulting file.

This module's entry point function in clean(...)
"""

import os

#ENTRY POINT FUNCTIONS

def clean(input_name,dest_dir,keep_time=False, apply_limits=False):
    """
    Cleans the file or every file from a directory named input_name,
    and saves the resulting files in dest_dir

    Arguments: Input directory; output directory.  

    Optional arguments: keep_time, if true the time stamp will be kept
    along with hrf(False by default); apply_limits if true signal loss
    will be eliminated(False by default).

    Return: None

    Algorithm: If input_name is a directory, retrieve a complete list
    of files from input directory. Call the clean function for each of
    the file.

    """
    if os.path.isdir(input_name):
        filelist = os.listdir(input_name)
        for filename in filelist:
            clean_file(os.path.join(input_name,filename), os.path.join(dest_dir,filename.strip()), keep_time, apply_limits)
    else:
        filename= os.path.basename(input_name)
        clean_file(input_name, os.path.join(dest_dir,filename.strip()), keep_time,apply_limits)

#IMPLEMENTATION

def clean_file(inputfile, dest_file , keep_time, apply_limits):
    """
    Create a file based on the input file where only hrf (where hrf
    are transformed, the hrf saved is the division of the original hrf
    by 1000), and optionally timestamp are kept.

    Arguments: name of input file, name of output file, a boolean
    indication whether timestamps should be preserved, a boolean that
    indicates if signal loss should be eliminated or not.
    
    Return: None
    
    Algorithm: The input file is read and the heart rate column, and
    possibly the timestamp column, are written to the outpufile. If
    apply_limits is true then the line is only written if hrf is
    between 50 and 250, otherwise we jump to the next line.

    """
    filename = os.path.basename(inputfile).strip()
    with open(inputfile.strip(),"r") as fdin:
        with open(dest_file,"w") as fdout:
            for line in fdin:
                data =  line.split()
                #to clean any headers the file might have, this works
                #because headers never start with a number.
                
                try:
                    float(data[0])
                except ValueError:
                    continue
                if len(data)!=0:
                    hrf = float(data[1])
                    if(hrf >= 1000):
                        hrf = float(data[1])/1000
                    if apply_limits :
                        if hrf>= 50 and hrf<=250:
                            if keep_time:
                                time = data[0]
                                fdout.write(time+" ")
                            fdout.write(str(hrf)+"\n")
                    else:
                        if keep_time:
                            time = data[0]
                            fdout.write(time+" ")
                        fdout.write(str(hrf)+"\n")    
                        


#AUXILIARY FUNCTIONS

def add_parser_options(parser):
    """
    !!!Auxiliary function!!!  These are arguments for an argparse
    parser or subparser, and are the optional arguments for
    the entry function in this module

    Arguments: The parser to which you want the arguments added to.
    
    Return:None
    """

    parser.add_argument("-kt","--keep-time",dest="keep_time",action="store_true",default=False,help="When cleaning keep both the hrf and time stamp")
    parser.add_argument("--apply-limits", dest="apply_limits", action="store_true", default=False,help="When cleaning apply limit cutoffs")


