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


HRFAnalyseDirectory is a command line interface to apply operations
(compression, entropy, clean, partition) from the tools module
directly to a file or files in a directory. The objective here is 
to study the results of applying the compression or entropy directly on the files.

Usage: ./HRFAnalyseDirectory.py INPUT_DIRECTORY COMMAND COMMAND_OPTIONS

Common operations can be found in the examples section.

Three COMMANDs are available: clean, compress and entropy. 

It is assumed that when using compress or entropy the files only
contain the one column with the relevant information (hrf in our
case).

clean: This command allows you to apply clean and partitioning
      operations. Cleaning a file means extrating the heart rate
      frequencies (timestamps may also be saved).  Partitioning cuts
      the file acording to a given interval. Note that partitions
      starting at the end of file will generate files where the data
      is inverted.
      
      OUTCOME: Calling this command will create a new directory with a
      _clean appended to the original directory's name were all the
      clean files are saved (this directory is created whether you
      call this interface on a directory or file).
      
      COMMAND_OPTIONS for this command are:

       -kt, --keep-time      When cleaning keep both the hrf and time stamp

       --apply-limits        When cleaning apply limit cutoffs (50<=hrf<=250)

       --start-at-end        Partition from end of file instead of beginning
       
       -ds SECONDS, --defered-start SECONDS
                        Time gap between the start of the file and the start
                        of the interval; default:[0]
       -s SECONDS, --section SECONDS
                        Amount of time in seconds to be captured
       -g SECONDS, --gap SECONDS
                        gap between sections (if using --full-file option)
       --use-lines           Partition using line count instead of time
       --full-file           Partition the full file into blocks

compress: This command allows you to compress all the files in the
     given directory.  The list of available compressors is
     dynamically generated based on their availabillity in the system,
     below is the full list of all implemented compression algorithms.
     Unless changed the compression level used is always the max for
     the chosen algorithm (refer to the compressor's manual for this
     information).
     

     OUTCOME: Calling this command will create a csv file using ';'
     as a field delimiter. The compression algorithm and the
     compression level used are used to name the resulting file. This
     file will be created in the parent of the directory we are
     working with. Each file is represented by a row with three
     columns, the name of the file, it's original size and it's
     compressed size.

     COMMAND_OPTIONS for this command are:
     -c COMPRESSOR, --compressor COMPRESSOR
                        compression compressor to be used, available
                        compressors:paq8l, lzma, gzip, zip, bzip2, ppmd,
                        zlib, spbio;default:[paq8l]
     --level LEVEL      compression level to be used, this variable is
                        compressor dependent; default:[The maximum of whatever
                        compressor was chosen]
     --decompression    Use this option if you also wish to calculate how long
                        it takes to decompress the file once it's compressed


entropy: This command allows you to calculate the entropy for all
     files in a given directory.
    
     OUTCOME: Calling this command will create a csv file using ';'
     as a field delimiter. The entropy measure and the
     compression level used are used to name the resulting file. This
     file will be created in the parent of the directory we are
     working with. Each file is represented by a row with two columns,
     the name of the file and it's entropy.


    COMMAND_OPTIONS are the available entropy measures:

     sampen              Sample Entropy
     apen                Approximate Entropy
     apenv2              A slightly different implementation of Approximate Entropy

    For a sampen and apen documentation please look at:
             pyeeg (http://code.google.com/p/pyeeg/downloads/list)
             
   All functions take arguments as inner options, to look at a
   particular entropy's options type:

   ./HRFAnalyseDirectory.py INPUT_DIRECTORY entropy ENTROPY -h


Examples :


  =>Clean:
     Retrieve the hrf:
     ./HRFAnalyseDirect.py unittest_dataset clean

      Retrieve the timestamps and hrf from the first hour: 
     ./HRFAnalyseDirect.py unittest_dataset clean -kt -s 3600


     Retrieve the valid hrf(50<=hrf<=250) for the last hour:
     ./HRFAnalyseDirect.py unittest_dataset clean -s 3600 --apply_limits --start-at-end

     Retrieve the hrf for the interval 1m--61m
     ./HRFAnalyseDirect.py unittest_dataset clean -ds 1 -s 3600 

     Retrieve the hrf from first 2000 lines:
     ./HRFAnalyseDirect.py unittest_dataset clean -s 2000 --use_lines

     Break the file into 5 minute blocks where the blocks don't overlap
     ./HRFAnalyseDirect.py unittest_dataset clean -s 300 --full-file

     Break the file into 5 minute blocks where the blocks start with a one
      minute difference
    ./HRFAnalyseDirect.py unittest_dataset clean -s 300 -g 60 --full-file



  =>Compress
     Compress using the gzip algorithm (maximum compression level will be used)
     ./HRFAnalyseDirectory.py unittest_dataset compress -c gzip

     Compress using the bzip2 algorithm with minimum compression(1 in this case):
     ./HRFAnalyseDirectory.py unittest_dataset -c bzip2 --level 1


  =>Entropy
     Calcutate the entropy using Approximate entropy with tolerance 0.2 and matrix
      dimension 2 (reference values for the analysis of biological data)
     ./HRFAnalyseDirectory.py unittest_dataset entropy apen -t 0.2

"""

import argparse
import os
import tools.clean
import tools.compress
import tools.partition
import tools.entropy
import csv
import logging


def partition_procedures(inputdir, options):
    if options['start_at_end']:
        outputdir = "%s_last_%d_%d" % (inputdir, options['partition_start'], options['section'])
    else:
        outputdir = "%s_%d_%d" % (inputdir, options['partition_start'], options['section'])

    if not os.path.isdir(outputdir):
        logger.info("Creating %s for partitions" % outputdir)
        os.makedirs(outputdir)
    logger.info("Starting partition")
    tools.partition.partition(inputdir,
                              outputdir,
                              options['partition_start'],
                              options['section'],
                              options['gap'],
                              options['start_at_end'],
                              options['full_file'],
                              options['using_lines'])
    logger.info("Finished partitioning")
    return outputdir


def clean_procedures(inputdir, options):
    logger.info("Starting clean procedures")
    if options['keep_time'] or options['section']:
        if not os.path.isdir(inputdir):
            outputdir = os.path.dirname(inputdir) + "_clean_wtime"
        else:
            outputdir = inputdir + "_clean_wtime"
        if not os.path.isdir(outputdir):
            logger.info("Creating partition directory %s" % outputdir)
            os.makedirs(outputdir)
        tools.clean.clean(inputdir, outputdir, keep_time=True, apply_limits=options['apply_limits'])
    else:
        if not os.path.isdir(inputdir):
            outputdir = os.path.dirname(inputdir) + "_clean"
        else:
            outputdir = inputdir + "_clean"
        if not os.path.isdir(outputdir):
            logger.info("Creating clean directory %s" % outputdir)
            os.makedirs(outputdir)
        tools.clean.clean(inputdir, outputdir, apply_limits=options['apply_limits'])
    logger.info("Finished clean procedures")
    return outputdir


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Generates a table of file compression/entrop for a given directory")
    parser.add_argument("inputdir", metavar="INPUT DIRECTORY", help="Directory or case file to be used as input",
                        action="store")
    parser.add_argument("--log", action="store", metavar="LOGFILE", default=None, dest="log_file",
                        help="Use LOGFILE to save logs.")
    parser.add_argument("--log-level", dest="log_level", action="store", help="Set Log Level; default:[%(default)s]",
                        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"], default="WARNING")

    subparsers = parser.add_subparsers(help='Diferent commands to be run on directory', dest="command")

    clean = subparsers.add_parser('clean', help='clean all the files in the given directory')
    tools.clean.add_parser_options(clean)
    tools.partition.add_parser_options(clean, full_file_option=True)

    compress = subparsers.add_parser('compress', help='compress all the files in the given directory')
    tools.compress.add_parser_options(compress)

    entropy = subparsers.add_parser('entropy', help='calculate entropy for all the files in the given directory')
    tools.entropy.add_parser_options(entropy)

    args = parser.parse_args()
    options = vars(args)

    logger = logging.getLogger('hrfanalyse')
    logger.setLevel(getattr(logging, options['log_level']))

    if options['log_file'] is None:
        log_output = logging.StreamHandler()
    else:
        log_output = logging.FileHandler(options['log_file'])
    log_output.setLevel(getattr(logging, options['log_level']))
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    log_output.setFormatter(formatter)
    logger.addHandler(log_output)

    inputdir = options['inputdir'].strip()

    if inputdir.endswith('/'):
        inputdir = inputdir[:-1]

    if options['command'] == 'clean':
        outputdir = clean_procedures(inputdir, options)
        if options['section']:
            outputdir = partition_procedures(outputdir, options)
        inputdir = outputdir

    if not os.path.isdir(inputdir):
        output_name = "%s_%s" % (os.path.split(inputdir)[0], os.path.basename(inputdir))
    else:
        output_name = inputdir

    if options['command'] == 'compress':
        compressor = options['compressor']
        level = tools.compress.set_level(options)
        resulting_dict = tools.compress.compress(inputdir, compressor, level, options['decompress'])
        if options['decompress']:
            outfile = "%s_decompress_%s_%d.csv" % (output_name, compressor, level)
        else:
            outfile = "%s_%s_%d.csv" % (output_name, compressor, level)
        writer = csv.writer(open(outfile, "w"), delimiter=";")
        header = ["Filename", "Original Size", "Compressed Size"]
        if options['decompress']:
            header.append("Decompression Time")
        writer.writerow(header)
        for filename in sorted(resulting_dict.keys()):
            cd = resulting_dict[filename]
            data_row = [filename, cd.original, cd.compressed]
            if options['decompress']:
                data_row.append(cd.time)
            writer.writerow(data_row)

    elif options['command'] == 'entropy':
        files_stds = tools.entropy.calculate_std(inputdir)
        tolerances = dict((filename, files_stds[filename] * options["tolerance"]) for filename in files_stds)
        resulting_dict = tools.entropy.entropy(inputdir,
                                               options['entropy'],
                                               options['dimension'],
                                               tolerances)

        outfile = "%s_%s_%d_%f.csv" % (output_name, options['entropy'], options['dimension'], options['tolerance'])

        writer = csv.writer(open(outfile, "w"), delimiter=";")
        writer.writerow(["Filename", "Entropy"])
        for filename in sorted(resulting_dict.keys()):
            entropyData = resulting_dict[filename]
            writer.writerow([filename, entropyData.entropy])
