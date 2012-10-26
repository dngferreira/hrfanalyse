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
import tools.separate_blocks
import os
import sys
import csv

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Analysis of the file's blocks")
    parser.add_argument("inputfile",metavar="INPUT FILE",help="File to be analysed")
    
    tools.partition.add_parser_options_blocks(parser)
    
    tools.compress.add_parser_options(parser)

    parser.add_argument("-pbc","--block-compression",action="store_true",default=False,help="Print block compression per file")

    tools.separate_blocks.add_parser_options(parser)
        

    args = parser.parse_args()
    options=vars(args)
    
    if options['inputfile'].endswith('/'):
        options['inputfile']=options['inputfile'][:-1]

    dest_dir= "%s_parts_%d_%d"%(options['inputfile'],options['section'],options['gap'])
    if(not os.path.isdir(dest_dir)):
        print "Creating ",dest_dir,"..."
        os.makedirs(dest_dir)

    print dest_dir," will be used to store file partitions"

    section_secs = options['section']*60
    gap_secs= options['gap']*60

    block_minutes={}
    print "Partitioning file in %d minutes intervals with %d gaps " %(options['section'],options['gap'])
    block_minutes = tools.partition.partition_blocks(options['inputfile'],dest_dir,section_secs,gap_secs)
    print "Partitioning complete"

    compressed={}        
    options['level']=tools.compress.set_level(options)
    for filename in block_minutes:
        file_blocks_dir = os.path.join(dest_dir,"%s_blocks"%filename)
        
        print "Compressing files in",file_blocks_dir,"..."
        compressed[filename] = tools.compress.compress(file_blocks_dir,options['compressor'],options['level'],options['decompress'])
        print "Compression complete"

    for filename in compressed:
        if options['decompress']:
            fboutname = os.path.join(dest_dir,
                                     "%s_decompress_%s"%(filename,options['compressor']))
        else:
            fboutname = os.path.join(dest_dir,
                                     "%s_%s%s"%(filename,options['compressor'],options['level']))
        with open(fboutname,"w") as fbout:
            for blocknum in compressed[filename]:
                if options['decompress']:
                    fbout.write("%f\n"%compressed[filename][blocknum].time)
                else:
                    fbout.write("%d\n"%compressed[filename][blocknum].compressed)
    
    print "Using ",options['limits'],"metric to separate blocks"
    below_lower, above_upper = tools.separate_blocks.apply_metric(compressed,block_minutes,options['limits'])
    
    
    for filename in compressed:
        csvname = '%s_%d_%d_%s_%s.csv'%(filename.strip(),options['section'],options['gap'],options['compressor'],options['limits'])
        writer = csv.writer(open(csvname, 'wb'),delimiter=";")
        writer.writerow(["Inferior"])
        writer.writerow(["Bloco","Segundo Inicial","Segundo Final"])
        for block in below_lower[filename]:
            writer.writerow([block,below_lower[filename][block][0],below_lower[filename][block][1]])
        writer.writerow(["Superior"])
        writer.writerow(["Bloco","Segundo Inicial","Segundo Final"])
        for block in above_upper[filename]:
            writer.writerow([block,above_upper[filename][block][0],above_upper[filename][block][1]])
