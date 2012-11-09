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
    
    scales_dir = input_dir+'_Escalas'

    print "Creating Scales Directory"
    tools.multiscale.multiscale(input_dir,scales_dir,options["scale_start"],options["scale_stop"]+1,options["scale_step"])
    print "Scales Directory created"

    if options["command"]=="compress":
        options["level"]=tools.compress.set_level(options)
        if options['decompress']:
            outfile="%s_multiscale_%d_%d_%d_decompress_%s%s.csv"%(input_dir, options["scale_start"], options["scale_stop"], options["scale_step"], options["compressor"], options["level"])
        else:
            outfile="%s_multiscale_%d_%d_%d_%s%s.csv"%(input_dir, options["scale_start"], options["scale_stop"], options["scale_step"], options["compressor"], options["level"])

        compression_table={}
        for scale in xrange(options["scale_start"],options["scale_stop"]+1,options["scale_step"]):
            dir_to_compress=os.path.join(scales_dir,"Escala %d"%scale)

            compression_results = tools.compress.compress(dir_to_compress,options["compressor"],options["level"],options['decompress'])
            if compression_table=={}:
                if options['decompress']:
                    compression_table= dict((k,[compression_results[k].original,compression_results[k].compressed,compression_results[k].time]) for k in compression_results)
                else:
                    compression_table= dict((k,[compression_results[k].original,compression_results[k].compressed]) for k in compression_results)
            else:
                for k in compression_table:
                    compression_table[k].append(compression_results[k].original)
                    compression_table[k].append(compression_results[k].compressed)
                    if options['decompress']:
                        compression_table[k].append(compression_results[k].time)
        

        writer=csv.writer(open(outfile,"wb"),delimiter=";")
        if options['decompress']:
            header = ["Filename"]+list(reduce(operator.add,[("Escala%d Original"%s,"Escala%d Compressed"%s,"Escala%d Decompression"%s) for s in xrange(options["scale_start"],options["scale_stop"]+1,options["scale_step"])]))
        else:
            header = ["Filename"]+list(reduce(operator.add,[("Escala%d Original"%s,"Escala%d Compressed"%s) for s in xrange(options["scale_start"],options["scale_stop"]+1,options["scale_step"])]))
        writer.writerow(header)
        for filename in sorted(compression_table.keys()):
            writer.writerow([filename]+compression_table[filename])
        
    else:
        if (options['entropy']=='apen') or (options['entropy']=='sampen'):
            outfile="%s_multiscale_%d_%d_%d_%s%d%.2f.csv"%(input_dir, 
                                                         options["scale_start"], 
                                                         options["scale_stop"], 
                                                         options["scale_step"], 
                                                         options["entropy"], 
                                                         options["dimension"],
                                                         options["tolerance"])
            entropy_table={}
            for scale in xrange(options["scale_start"],options["scale_stop"]+1,options["scale_step"]):
                scale_dir=os.path.join(scales_dir,"Escala %d"%scale)
                entropy_results = tools.entropy.entropy(scale_dir, 
                                              options['entropy'],
                                              options['dimension'],
                                              options['tolerance'])
                if entropy_table=={}:
                    entropy_table= dict((k,[entropy_results[k][1]]) for k in entropy_results)
                else:
                    for k in entropy_table:
                        entropy_table[k].append(entropy_results[k][1])

            writer=csv.writer(open(outfile,"wb"),delimiter=";")
            header = ["Filename"]+[ "Escala%d Entropy"%s for s in xrange(options["scale_start"],options["scale_stop"]+1,options["scale_step"])]
        writer.writerow(header)
        for filename in sorted(entropy_table.keys()):
            writer.writerow([filename]+entropy_table[filename])

            

        # if options['entropy']=="specen":
        #     resulting_dict = entropy_dir(inputdir,options['entropy'],Band,Fs)
        #     outfile= inputdir+'_'+options['entropy']+'.csv'
        # if options['entropy']=="hurst" or options['entropy']=="dfa" or options['entropy']=="hjorth" or  options['entropy']=="pfd":
        #     resulting_dict = entropy_dir(inputdir,options['entropy'])
        #     outfile= inputdir+'_'+options['entropy']+'.csv'
        # if options['entropy']=="hfd":
        #     resulting_dict = entropy_dir(inputdir,options['entropy'],options['kmax'])
        #     outfile= inputdir+'_'+options['entropy']+'_'+str(options['kmax'])+'.csv'
        # if options['entropy']=='fi' or options['entropy']=='svden':
        #     resulting_dict = entropy_dir(inputdir,options['entropy'],options['dimension'],options['tau'])
        #     outfile= inputdir+'_'+options['entropy']+'_'+str(options['dimension'])+'_'+str(options['tau'])+'.csv'
        
