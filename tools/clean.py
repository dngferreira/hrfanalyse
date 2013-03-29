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


This module is very specific to our datasets. The dataset files are always either
two columns -- the first is the time and the second the heat rate frequency or rr 
interval -- or more columns where only the first two interset us --again the time
and hrf wich in these files has to be divided by 1000 to get the usual three digit
number.

Dependign on the passed options the module either extracts the time stamp and 
heart rate frequency(hrf) or just the hrf. 

Optionaly a limit may be applied to eliminate signal loss, we consider the
signal to be lost if hrf is bellow 50 or above 250. If a particular line is 
considered as signal lost it is ommited from the resulting file.

This module's entry point function in clean(input_name,dest_dir,keep_time=False,
apply_limits=False)
"""

import os
import logging

module_logger=logging.getLogger('hrfanalyse.clean')

#ENTRY POINT FUNCTIONS

def clean(input_name,dest_dir,keep_time=False, apply_limits=False):
    """
    Cleans the file or every file from a directory named input_name,
    and saves the resulting files in dest_dir

    ARGUMENTS: Strin Input directory, String output directory, bool to decide 
    whether or not to keep the time column, bool to determine if limits(50-250) 
    are applied.  keep_time and apply_limits are optional to call this function.

    RETURN: None

    """
    module_logger.debug("The input name received: %s"%input_name)
    if os.path.isdir(input_name):
        filelist = os.listdir(input_name)
        for filename in filelist:
            clean_file( os.path.join(input_name,filename.strip()), 
                        os.path.join(dest_dir,filename.strip()), 
                        keep_time, 
                        apply_limits)
    else:
        filename= os.path.basename(input_name)
        clean_file( input_name, 
                    os.path.join(dest_dir,filename.strip()), 
                    keep_time,
                    apply_limits)

#IMPLEMENTATION

def clean_file(inputfile, dest_file , keep_time, apply_limits):
    """
    Clean operation of a single file.
    
    ARGUMENTS: String name of input file, String name of output file, keep_time 
    boolean indication whether timestamps should be preserved, apply_limits boolean
    that indicates if signal loss should be eliminated or not.
    
    RETURN: None
    
    """
    with open(inputfile,"rU") as fdin:
        with open(dest_file,"w") as fdout:
            for line in fdin:
                data =  line.split(',')
                
                #to clean any headers the file might have, this operates under the assumtion
                #headers never start with a number.
                try:
                    float(data[0])
                except ValueError:
                    continue
                if len(data)!=0:
                    hrf = float(data[1])
                    if(hrf >= 1000):
                        hrf = round(float(data[1])/1000)
                    if apply_limits and hrf>= 50 and hrf<=250:
                        if keep_time:
                            time = data[0]
                            fdout.write("%s "%time)
                        fdout.write("%.3f\n"%hrf)
                    else:
                        if keep_time:
                            time = data[0]
                            fdout.write("%s "%time)
                        fdout.write("%.3f\n"%hrf)    
                        


#AUXILIARY FUNCTIONS

def add_parser_options(parser):
    """
    !!!Auxiliary function!!!  These are arguments for an argparse
    parser or subparser, and are the optional arguments for
    the entry function in this module

    ARGUMENTS: The parser to which you want the arguments added to.
    
    RETURN:None
    """

    parser.add_argument("-kt",
                        "--keep-time",
                        dest="keep_time",
                        action="store_true",
                        default=False,
                        help="When cleaning keep both the hrf and time stamp")
    parser.add_argument("--apply-limits", 
                        dest="apply_limits", 
                        action="store_true", 
                        default=False,
                        help="When cleaning apply limit cutoffs")


