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

HRFAnalyseFileBlocks is a command line interface to study a file


"""

import argparse
import tools.partition
import tools.compress
import tools.entropy
import tools.separate_blocks
import os
import csv
import logging

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Analysis of the file's blocks")
    parser.add_argument("inputfile",metavar="INPUT FILE",help="File to be analysed")
    parser.add_argument("--log",action="store",metavar="LOGFILE",default=None,dest="log_file",help="Use LOGFILE to save logs.")
    parser.add_argument("--log-level",dest="log_level",action="store",help="Set Log Level; default:[%(default)s]",choices=["CRITICAL","ERROR","WARNING","INFO","DEBUG","NOTSET"],default="WARNING")

    
    tools.partition.add_parser_options(parser, full_file_option=False)
    
    subparsers = parser.add_subparsers(help='Diferent commands to be run on directory', dest="command")

    compress = subparsers.add_parser('compress', help='compress all the files in the given directory')
    tools.compress.add_parser_options(compress)

    entropy = subparsers.add_parser('entropy', help='calculate entropy for all the files in the given directory')
    tools.entropy.add_parser_options(entropy)
#    tools.separate_blocks.add_parser_options(parser)
        

    args = parser.parse_args()
    options=vars(args)
    

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

    if options['inputfile'].endswith('/'):
        options['inputfile']=options['inputfile'][:-1]

    if os.path.isdir(options['inputfile']):
        dest_dir= "%s_parts_%d_%d"%(options['inputfile'],options['section'],options['gap'])
    else:
        dest_dir= "%s_parts_%d_%d"%(os.path.dirname(options['inputfile']),options['section'],options['gap'])
    if(not os.path.isdir(dest_dir)):
        logger.info("Creating %s!"%dest_dir)
        os.makedirs(dest_dir)

    logger.info("%s will be used to store file partitions"%dest_dir)

    block_minutes={}
    logger.info("Partitioning file in %d minutes intervals with %d gaps " %(options['section'],options['gap']))
    if options['gap']==0:
        options['gap'] = options['section']
    block_minutes = tools.partition.partition(options['inputfile'],
                                                dest_dir,
                                                options['partition_start'],
                                                options['section'],
                                                options['gap'],
                                                options['start_at_end'],
                                                True,
                                                options['using_lines'])
    logger.info("Partitioning complete")
    

    if options['command']=='compress':
        compressed={}        
        options['level']=tools.compress.set_level(options)
        for filename in block_minutes:
            logger.info("Compression started for %s" %os.path.join(dest_dir,"%s_blocks"%filename))
            #The extensions had to be removed from the original name when
            #creating the block for compatibility with windows, so this line
            #changes the filename
            bfile = os.path.splitext(filename)[0]
            compressed[bfile] = tools.compress.compress(os.path.join(dest_dir,"%s_blocks"%bfile),options['compressor'],options['level'],options['decompress'])
            logger.info("Compression complete")
        
        for filename in compressed:
            if options['decompress']:
                fboutname = "%s_decompress_%s.csv"%(filename,options['compressor'])
            else:
                fboutname = "%s_%s%s.csv"%(filename,options['compressor'],options['level'])
            writer = csv.writer(open(fboutname,"w"),delimiter=";")
            header = ["Block","Original Size","Compressed Size"]
            if options['decompress']:
                header.append("Decompression Time")
            writer.writerow(header)    
            for blocknum in compressed[filename]:
                block_results = compressed[filename][blocknum]
                row_data=[blocknum,block_results.original,block_results.compressed]
                if options['decompress']:
                    row_data.append(block_results.time)
                writer.writerow(row_data)
    elif options['command']=='entropy':
        entropy={}
        for filename in block_minutes:
            logger.info("Entropy calculations started for %s" %os.path.join(dest_dir,"%s_blocks"%filename))
            files_stds = tools.entropy.calculate_std(os.path.join(dest_dir,"%s_blocks"%filename))
            tolerances = dict((filename,files_stds[filename]*options["tolerance"]) for filename in files_stds)
            entropy[filename] = tools.entropy.entropy(os.path.join(dest_dir,"%s_blocks"%filename),
                                                      options['entropy'],
                                                      options['dimension'],
                                                      tolerances)
            logger.info("Entropy calculations complete")
        for filename in entropy:
            fboutname = "%s_%s_%d_%f.csv"%(filename,options['entropy'],options['dimension'],options['tolerance'])
            writer = csv.writer(open(fboutname,"w"),delimiter=";")
            header = ["Block","Entropy"]
            writer.writerow(header)    
            for blocknum in entropy[filename]:
                block_results = entropy[filename][blocknum]
                row_data=[blocknum,block_results.entropy]
                writer.writerow(row_data)
        

    
##    logger.info("Using %s metric to separate blocks"%options['limits'])
##    below_lower, above_upper = tools.separate_blocks.apply_metric(compressed,block_minutes,options['limits'])
##    
##    
##    for filename in compressed:
##        csvname = '%s_%d_%d_%s_%s.csv'%(filename.strip(),options['section'],options['gap'],options['compressor'],options['limits'])
##        writer = csv.writer(open(csvname, 'wb'),delimiter=";")
##        writer.writerow(["Inferior"])
##        writer.writerow(["Bloco","Segundo Inicial","Segundo Final"])
##        for block in below_lower[filename]:
##            writer.writerow([block,below_lower[filename][block][0],below_lower[filename][block][1]])
##        writer.writerow(["Superior"])
##        writer.writerow(["Bloco","Segundo Inicial","Segundo Final"])
##        for block in above_upper[filename]:
##            writer.writerow([block,above_upper[filename][block][0],above_upper[filename][block][1]])
