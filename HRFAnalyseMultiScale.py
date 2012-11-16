#!/usr/bin/python

import argparse
import os
import csv
import operator
import tools.multiscale
import tools.compress
import tools.entropy

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Generates a tables of file multiscaled compression/entropy")
    parser.add_argument("inputdir",metavar="INPUT DIRECTORY", help="Directory to be used as input")
    tools.multiscale.add_parser_options(parser)

    commands = parser.add_subparsers(help="MultiScale using compression or entropy",dest="command")

    compress = commands.add_parser("compress", help="use compression on multiscale")
    tools.compress.add_parser_options(compress)


    entropy = commands.add_parser("entropy",help="use entropy on multiscale")
    
    tools.entropy.add_parser_options(entropy)

    args = parser.parse_args()
    options = vars(args)

    input_dir= options['inputdir'].strip()

    if input_dir.endswith('/'):
        input_dir = input_dir[:-1]
    
    scales_dir = input_dir+'_Scales'

    print "Creating Scales Directory"
    tools.multiscale.create_scales(input_dir,scales_dir,options["scale_start"],options["scale_stop"]+1,options["scale_step"])
    print "Scales Directory created"

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

        writer=csv.writer(open(outfile,"wb"),delimiter=";")
        if options['decompress']:
            header = ["Filename"]+list(reduce(operator.add,[("Escala%d Original"%s,"Escala%d Compressed"%s,"Escala%d Decompression"%s) for s in xrange(options["scale_start"],options["scale_stop"]+1,options["scale_step"])]))
        else:
            header = ["Filename"]+list(reduce(operator.add,[("Escala%d Original"%s,"Escala%d Compressed"%s) for s in xrange(options["scale_start"],options["scale_stop"]+1,options["scale_step"])]))
        writer.writerow(header)
        for filename in sorted(compression_table.keys()):
            writer.writerow([filename]+compression_table[filename])
        
    elif options["command"]=="entropy":
        if (options['entropy']=='apen' or options['entropy']=="sampen"):
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
            header = ["Filename"]+[ "Escala%d Entropy"%s for s in xrange(options["scale_start"],options["scale_stop"]+1,options["scale_step"])]
            writer.writerow(header)
            for filename in sorted(entropy_table.keys()):
                writer.writerow([filename]+entropy_table[filename])            
        else:
            print "Multiscale not implemented for %s"%options["entropy"]

    
