#!/usr/bin/python

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

    logger.info("Creating Scales Directory")
    tools.multiscale.create_scales(input_dir,scales_dir,options["scale_start"],options["scale_stop"]+1,options["scale_step"],options['mul_order'])
    logger.info("Scales Directory created")

    if options["command"]=="compress":
        options["level"]=tools.compress.set_level(options)
        if options['decompress']:
            outfile="%s_multiscale_%d_%d_%d_decompress_%s%s.csv"%(input_dir, options["scale_start"], options["scale_stop"], options["scale_step"], options["compressor"], options["level"])
        else:
            outfile="%s_multiscale_%d_%d_%d_%s%s.csv"%(input_dir, options["scale_start"], options["scale_stop"], options["scale_step"], options["compressor"], options["level"])

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
            
            
            writer=csv.writer(open(outfile,"wb"),delimiter=";")
            header = ["Filename"]+[ "Escala%d Entropy"%s for s in range(options["scale_start"],options["scale_stop"]+1,options["scale_step"])]
            writer.writerow(header)
            for filename in sorted(entropy_table.keys()):
                writer.writerow([filename]+entropy_table[filename])            
        else:
            logger.error("Multiscale not implemented for %s"%options["entropy"])

    
