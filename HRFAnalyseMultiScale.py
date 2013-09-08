#!/usr/bin/python
# -*- coding: utf-8 -*-
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

HRFAnalyseMultiScale is a command line interface to apply the multiscale method
based on (http://www.physionet.org/physiotools/mse/tutorial/), but using
compression also.

Usage:./HRFAnalyseMultiScale [OPTIONS] INPUT COMMAND [COMMAND OPTIONS]

OPTIONS to apply when creating the scales:
  -start SCALE, --scale-start SCALE
                        Start scales whith this amount of points. Default:[1]
  -stop SCALE, --scale-stop SCALE
                        Stop scales whith this amount of points. Default:[20]
  -step STEP, --scale-step STEP
                        Step between every two scales.Default:[1]
  --multiply MUL ORDER  before calculating the resulting scale, multiply every
                        number in the series by MUL ORDER, -1 disables this
                        option; Default:[-1]
  --round-to-int

The two available commands are compress and entropy.

compress: This command allows you to compress all the files in the
     given directory.  The list of available compressors is
     dynamically generated based on their availabillity in the system,
     below is the full list of all implemented compression algorithms.
     Unless changed the compression level used is always the max for
     the chosen algorithm (refer to the compressor's manual for this
     information).
     

     OUTCOME: Calling this commmand will create a csv file using ';'
     as a field delimiter. The compression algorith and the
     compression level used are used to name the resulting file. This
     file will be created in the parent of the directory we are
     working with. Each file is represented by a row with two
     columns per scale, it's original size and it's compressed size.

     COMMAND_OPTIONS for this command are:
     -c COMPRESSOR, --compressor COMPRESSOR
                        compression compressor to be used, available
                        compressors:paq8l, lzma, gzip, zip, bzip2, ppmd,
                        zlib, spbio;default:[paq8l]
     --level LEVEL      compression level to be used, this variable is
                        compressor dependent; default:[The maximum of wathever
                        compressor was chosen]
     --decompression    Use this option if you also wish to calculate how long it takes to decompress the file once it's compressed


entropy: This command allows you to calculate the entropy for all
     files in a given directory.
    
     OUTCOME: Calling this commmand will create a csv file using ';'
     as a field delimiter. The entropy measure and the
     compression level used are used to name the resulting file. This
     file will be created in the parent of the directory we are
     working with. Each file is represented by a row with one column per scale,
     it's entropy.


    COMMAND_OPTIONS are the available entropy measures:

     sampen              Sample Entropy
     apen                Aproximate Entropy
     apenv2              A slightly different implementation of Aproximate Entropy


    For a sampen and apen documentation please look at:
             pyeeg (http://code.google.com/p/pyeeg/downloads/list)
             
   All functions take arguments as inner options, to look at a
   particular entropy's options type:

   ./HRFAnalyseMultiScale.py INPUT_DIRECTORY entropy ENTROPY -h


Examples:

Multiscale entropy for all the files starting at scale 1(original files)
 and ending in scale 20
./HRFAnalyseMultiscale unittest_dataset entropy sampen

Multiscale compression with rounded results for scale, since the scales are constructed
by avaraging a given number of point we are bound to have floats, this options
rounds those numbers to an integer.
./HRFAnalyseMultiscale unittest_dataset --round-to-int compression

Multiscale compression with rounded results for scale, multiplyed by 10, the scale
point is multiplied by 10 and rounded.
./HRFAnalyseMultiscale unittest_dataset --round-to-int --multiply 10 compression -c paq8l


"""

import argparse
import csv
import operator
import functools
import tools.multiscale
import tools.compress
import tools.entropy
import logging

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Generates a tables of file multiscaled compression/entropy")
    parser.add_argument("inputdir",metavar="INPUT DIRECTORY", help="Directory to be used as input")
    parser.add_argument("--log",action="store",metavar="LOGFILE",default=None,dest="log_file",help="Use LOGFILE to save logs.")
    parser.add_argument("--log-level",dest="log_level",action="store",help="Set Log Level; default:[%(default)s]",choices=["CRITICAL","ERROR","WARNING","INFO","DEBUG","NOTSET"],default="WARNING")


    tools.multiscale.add_parser_options(parser)

    commands = parser.add_subparsers(help="MultiScale using compression or entropy",dest="command")

    compress = commands.add_parser("compress", help="use compression on multiscale")
    tools.compress.add_parser_options(compress)


    entropy = commands.add_parser("entropy",help="use entropy on multiscale")
    
    tools.entropy.add_parser_options(entropy)

    args = parser.parse_args()
    options = vars(args)

    logger = logging.getLogger('hrfanalyse')
    logger.setLevel(getattr(logging,options['log_level']))

    if(options['log_file']==None):
        log_output = logging.StreamHandler()
    else:
        log_output = logging.FileHandler(options['log_file'])
    log_output.setLevel(getattr(logging,options['log_level']))
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    log_output.setFormatter(formatter)
    logger.addHandler(log_output)

    input_dir= options['inputdir'].strip()

    if input_dir.endswith('/'):
        input_dir = input_dir[:-1]
    
    scales_dir = '%s_Scales'%input_dir
    if options['round']:
        scales_dir+="_int"
    if options['mul_order']!=-1:
        scales_dir+='_%d'%(options['mul_order'])

    logger.info("Creating Scales Directory")
    tools.multiscale.create_scales(input_dir,scales_dir,options["scale_start"],options["scale_stop"]+1,options["scale_step"],options['mul_order'],options['round'])
    logger.info("Scales Directory created")

    if options["command"]=="compress":
        options["level"]=tools.compress.set_level(options)
        if options['decompress']:
            outfile="%s_multiscale_%d_%d_%d_decompress_%s%s"%(input_dir, options["scale_start"], options["scale_stop"], options["scale_step"], options["compressor"], options["level"])
        else:
            outfile="%s_multiscale_%d_%d_%d_%s%s"%(input_dir, options["scale_start"], options["scale_stop"], options["scale_step"], options["compressor"], options["level"])
        if options['round']:
            outfile+="_int"
        if options['mul_order']!=-1:
            outfile+="_%d"%(options["mul_order"])
        outfile+=".csv"                            

        compression_table = tools.multiscale.multiscale_compression(input_dir,
                                                                    options["scale_start"],
                                                                    options["scale_stop"]+1,
                                                                    options["scale_step"],
                                                                    options["compressor"],
                                                                    options["level"],
                                                                    options["decompress"])

        writer=csv.writer(open(outfile,"w"),delimiter=";")
        if options['decompress']:
            header = ["Filename"]+list(functools.reduce(operator.add,[("Escala%d Original"%s,"Escala%d Compressed"%s,"Escala%d Decompression"%s) for s in range(options["scale_start"],options["scale_stop"]+1,options["scale_step"])]))
        else:
            header = ["Filename"]+list(functools.reduce(operator.add,[("Escala%d Original"%s,"Escala%d Compressed"%s) for s in range(options["scale_start"],options["scale_stop"]+1,options["scale_step"])]))
        writer.writerow(header)
        for filename in sorted(compression_table.keys()):
            writer.writerow([filename]+compression_table[filename])
        
    elif options["command"]=="entropy":
        if (options['entropy']=='apen' or options['entropy']=='apenv2' or options['entropy']=="sampen"):
            outfile="%s_multiscale_%d_%d_%d_%s%d%.2f.csv"%(input_dir, 
                                                           options["scale_start"], 
                                                           options["scale_stop"], 
                                                           options["scale_step"], 
                                                           options["entropy"], 
                                                           options["dimension"],
                                                           options["tolerance"])
            entropy_table={}
            
            entropy_table = tools.multiscale.multiscale_entropy(input_dir,
                                                                options["scale_start"],
                                                                options["scale_stop"]+1,
                                                                options["scale_step"],
                                                                options["entropy"],
                                                                options["dimension"],
                                                                options["tolerance"])
            
            
            writer=csv.writer(open(outfile,"w"),delimiter=";")
            header = ["Filename"]+[ "Escala%d Entropy"%s for s in range(options["scale_start"],options["scale_stop"]+1,options["scale_step"])]
            writer.writerow(header)
            for filename in sorted(entropy_table.keys()):
                writer.writerow([filename]+entropy_table[filename])            
        else:
            logger.error("Multiscale not implemented for %s"%options["entropy"])

    
