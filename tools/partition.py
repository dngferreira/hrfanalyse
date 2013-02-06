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

This module presumes the files contain only two columns, the first
column is a timestamp the second is the heart rate frequency(hrf).

Timestamps can either be the cummulative passage of time, or just 
the time passed since the last timestamp.

The partitions using time stamps(not cummulative) do not use the real
time, but the mode of time this way the data is not affected by
extended periods of signal loss, and what we get is closer to the
period of aquired signal.

There are two entry point functions to this module:
 partition_chunck(...) --> Grabs a chunck from the file /files in a
 directory 
 
 partition_blocks(...) --> Partitions the file / files in a directory
 into sections

"""


import os
import sys
import pickle
import logging 

module_logger=logging.getLogger('hrfanalyse.partition')

#This number was randomly chosen, no meaning to it
SAMPLE_SIZE=42

#ENTRY POINT FUNCTIONS
def partition_chunk(input_name,dest_dir,cutting_method,starting_point=0,interval=-1,start_at_end=False):
    """
    Grab a chunck from input_name or from each file in input_name if
    input_name is a directory. A chunk may start anywhere in the file
    and it's size can be expressed in time ou lines.

    Arguments: name of the input directory/file, name of the output
    directory, what method should be used to cut the file
    ('using_lines', 'using_time'), starting point (in seconds or line
    number), length of the chunk, boolean indicating whether to start
    from the end of the file or not (by default False).

    Return: None

    Algorithm: Retrieve a complete list of files from input
    directory. Call the appropriate partition function for each of the
    files.

    """
    method_to_call= getattr(sys.modules[__name__],'partition_chunk_'+cutting_method)
    if os.path.isdir(input_name):
        filelist = os.listdir(input_name)
        for filename in filelist:
            method_to_call(os.path.join(input_name,filename.strip()),dest_dir,starting_point,interval,start_at_end)
    else:
        method_to_call(input_name.strip(),dest_dir,starting_point,interval,start_at_end)

def partition_blocks(input_name,dest_dir,section_secs,gap_secs):
    """
    Break input_name or each file in input_name if input_name is a
    directory into blocks. 

    
    Arguments: name of the input directory/file, name of the output
    directory, section size (in seconds ), gap size (in seconds).

    Return: A dictionary where the keys are the file names and the
    values are lists containing the real times for each partition's
    start and end in seconds.

    Algorithm: Retrieve a complete list of files from input
    directory. Call the partition function for each of the files.
    
    """
    blocks_times={}
    if os.path.isdir(input_name):
        filelist = os.listdir(input_name)
        for filename in filelist:
            file_block_dir = os.path.join(dest_dir,"%s_blocks"%filename.strip())
            if(not os.path.isdir(file_block_dir)):
                module_logger.info("Creating %s!"%file_block_dir)
                os.makedirs(file_block_dir)
            blocks_times[filename.strip()] = partition_file_blocks(os.path.join(input_name,filename.strip()),file_block_dir,section_secs,gap_secs)
    else:
        filename = os.path.basename(input_name.strip())
        file_block_dir = os.path.join(dest_dir,"%s_blocks"%filename)
        if(not os.path.isdir(file_block_dir)):
            module_logger.info("Creating %s!"%file_block_dir)
            os.makedirs(file_block_dir)
        blocks_times[filename] = partition_file_blocks(input_name.strip(),file_block_dir,section_secs,gap_secs)
    return blocks_times


#IMPLEMENTATION


def partition_file_blocks(inputfile,dest_dir,section_secs,gap_secs):
    """
    Partitions the input file into section with a user defined amount
    of time, where each section's beginning will have a gap to the next
    section's beginning. For example a 5 sec section with a 1 sec gap,
    means the first section start at second 0 end at second 5, the
    second would start at second 1 and end at 6, etc...
    The returned value is relative to the data in the file.

    Arguments: name of the file being read, directory where resulting
    partition files should be saved, length of the sections in
    seconds, length of the gap between sections in seconds.

    Return: List containing the real times for each partition's start
    and end in seconds.

    """

    filename = os.path.basename(inputfile)
    time_elapsed=0
    real_end = 0
    real_start = 0
    next_real_start=0
    line_index=0
    k=1
    block_minuts = []
    with open(inputfile,"r") as fdin:
        lines = fdin.readlines()
        if len(lines)==0:
            return
        cumulative, time_stamp = sniffer(lines[:SAMPLE_SIZE])
        next_partition_start = 0 
        fdpart = open(os.path.join(dest_dir,filename+'_'+str(k)),"w")
        while line_index < len(lines):
            time, hrf = lines[line_index].split()
            if cumulative:
                section_test = abs(float(time)-time_stamp) <= section_secs+((k-1)*gap_secs)
            else:
                section_test = time_elapsed+time_stamp <= section_secs*1000
            if section_test:
                fdpart.write("%s\n"%hrf)
                line_index, time_elapsed, real_end, next_partition_start, next_real_start = set_time_varibles(line_index, time, time_elapsed, time_stamp, k, gap_secs, next_partition_start, next_real_start, real_end, cumulative)
                if line_index>=len(lines):
                    break
            else:
                fdpart.close()
                k+=1
                line_index=next_partition_start
                block_minuts.append((real_start,real_end))
                real_start=next_real_start
                real_end=next_real_start
                time_elapsed=0
                fdpart = open(os.path.join(dest_dir,filename+'_'+str(k)),"w")
#                fdout.write(s.encode('windows-1252'))
                
    block_minuts.append((real_start,real_end))
    fdpart.close()
    return block_minuts

def set_time_varibles(line_index, time, time_elapsed, time_stamp, k, gap_secs, next_partition_start, next_real_start, real_end, cumulative):
    if cumulative:
        real_end = float(time)-time_stamp
        gap_test = abs(float(time)-time_stamp) <= k*gap_secs
    else:
        real_end += float(time)/1000
        gap_test = time_elapsed+time_stamp <= gap_secs*1000
        time_elapsed += time_stamp
    if gap_test:
        next_partition_start +=1 
        if cumulative:
            next_real_start=float(time)-time_stamp
        else:
            next_real_start+=float(time)/1000
        line_index+=1
    return (line_index, time_elapsed, real_end, next_partition_start, next_real_start)


def partition_chunk_using_time(inputfile,dest_dir,init_seconds,interval,start_at_end):
    """
    Grabs a part of the file with a certain time interval of captured
    signal starting from an initial time.

    Arguments: name of the file being read, directory where resulting
    partition files should be saved, seconds where partition starts,
    amount of time to keep after the initial stamp, boolean indicating
    whether or not to start from the end of the file.

    Return: None

    Algorithm: The input file is read into an array, the 'cursor' is
    advanced to init_seconds, after which all the lines within the
    time interval (interval will always end at init_seconds+ interval)
    are copied to the new file which is saved in the destination
    directory. Since we can have either a cumulative time stamp or
    periodic time stamp we use the sniffer auxiliary function to
    initialize the first time stamp or mode time stamp depending
    whether the timeline is cumulative or not.

    """

    filename = os.path.basename(inputfile)
    with open(inputfile,"r") as fdin:
        lines = fdin.readlines()

        #empty files return imediatly
        if len(lines)==0:
            return
        
        line_index, interval, cumulative, time_stamp = initialize_partition_variables(lines,init_seconds, start_at_end, interval)

        module_logger.debug("Initialization -- line_index: %d;interval: %d; cumulative:%d; time_stamp:%d"%(line_index,interval,cumulative,time_stamp))
            
    #If the init time in not 0 jump to that point in time, the cursor
    #is moved to exactly the start of the requested interval

        time_elapsed, line_index = jump_to_partition_init(lines,line_index, init_seconds, cumulative, start_at_end, time_stamp)

        module_logger.debug("After the Jump -- time_elapsed:%d; line_index: %d"%(time_elapsed,line_index))

  
    #write the data to the outfile until the end of the requested interval is reached
        time, hrf = lines[line_index].split()

        with open(os.path.join(dest_dir,filename),"w") as fdout:
            data = ""
            if cumulative:
                partition_test = abs(float(time)-time_stamp) <= interval
            else:
                partition_test = time_elapsed+time_stamp <= interval*1000
            while partition_test:
#                s=hrf+'\n'
                s = "%s %s\n"%(time,hrf)
#                fdout.write(s.encode('utf8'))
                if start_at_end:
                    data = s+data 
                    line_index-=1
                    if abs(line_index)>=len(lines):
                        break
                else:
                    data = data+s
                    line_index+=1
                    if line_index>=len(lines):
                        break

                time, hrf = lines[line_index].split()

                if cumulative:
                    partition_test = abs(float(time)-time_stamp) <= interval
                else:
                    time_elapsed += time_stamp
                    partition_test = time_elapsed + time_stamp <= interval*1000
            fdout.write(data)
            
#AUXILARY FUNCTIONS FOR PARTITIONS BASED ON TIME
def initialize_partition_variables(lines,init_seconds, start_at_end,interval):
    if start_at_end:
        line_index=-1
    else:
        line_index=0
        
    if interval!=-1:
        interval=init_seconds+interval
    else:
        interval=sys.maxint
            
    if start_at_end:
        cumulative, time_stamp = sniffer(lines[-SAMPLE_SIZE:],start_at_end)
    else:
        cumulative, time_stamp = sniffer(lines[:SAMPLE_SIZE],start_at_end)

    return (line_index, interval, cumulative, time_stamp)

def jump_to_partition_init(lines, line_index, init_seconds, cumulative, start_at_end, time_stamp):
    time, hrf = lines[line_index].split()

    time_elapsed = 0
    if init_seconds!=0:
        if cumulative:
            jump_to_init_test = abs(float(time)-time_stamp) < init_seconds
        else:
            jump_to_init_test = time_elapsed+time_stamp < init_seconds*1000
        while jump_to_init_test:
            if start_at_end:
                line_index-=1
            else:
                line_index+=1
            if abs(line_index) >=len(lines):
                break
            try:
                time, hrf = lines[line_index].split()
            except IndexError:
                return                     
            if cumulative:
                jump_to_init_test = abs(float(time)-time_stamp) < init_seconds
            else:
                time_elapsed += time_stamp
                jump_to_init_test = time_elapsed + time_stamp < init_seconds*1000
    return time_elapsed, line_index    


def partition_chunk_using_lines(inputfile,dest_dir,init_line,interval,start_at_end):
    """
    Grabs a part of the file with a certain number of lines starting
    from some initial line.
    
    Arguments: name of the file being read, directory where resulting
    file should be saved, starting line, number of lines to be kept,
    boolean indicating whether to start from the last line or not.

    Return: None

    Algorithm: The input file is read into an array, the line_index is
    set, and an interval number of lines is copied to the new file
    which is saved in the destination directory.
    

    """

    filename = os.path.basename(inputfile)
    with open(inputfile,"r") as fdin:
        with open(os.path.join(dest_dir,filename),"w") as fdout:
            lines = fdin.readlines()
            ###empty files or files with not enough lines return imediatly
            if len(lines)<=abs(init_line):
                return

            if start_at_end:
                line_index=-init_line
            else:
                line_index=init_line
            
            if interval!=-1:
                final_line=init_line+interval
            else:
                final_line=sys.maxint

            time, hrf = lines[line_index].split()

            while abs(line_index) < final_line:
#                s=hrf+'\n'
                s = time+" "+hrf+"\n"
#                fdout.write(s.encode('utf8'))
                fdout.write(s)
                if start_at_end:
                    line_index-=1
                    if abs(line_index)>=len(lines):
                        break
                else:
                    line_index+=1
                    if line_index>=len(lines):
                        break
    
                time, hrf = lines[line_index].split()
                

#AUXILIARY FUNCTIONS


def sniffer(lines,start_at_end=False):
    """
    !!!Auxiliary function!!!
    Recieves a sample of the file and extrapolates whether the
    timeline is cumulative or periodic. If it's cumulative than along
    with that information also sends the first timestamp, otherwise it
    sends the mode of the timestamps(unless signal is lost machines
    always capture the signal on a time frequency, the mode will give
    us that frequency).

    Arguments: sample data in an array.
    
    Return: a boolean that indicates if we have a cumulative timeline
    or not, and the first time stamp or the mode time stamp.

    """
    times={}
    crescent=0
    if start_at_end:
        first_stamp = lines[-1].split()[0]
    else:
        first_stamp = lines[0].split()[0]
    previous_time= lines[0].split()[0]
    moda_count = 0
    for line in lines:
        try:
            time,hrf = line.split()
        except:
            raise NameError(line)
        if times.has_key(time):
            times[time]+=1
        else:
            times[time]=1
        if time>previous_time:
            crescent+=1
            previous_time=time
    if crescent==len(lines)-1:
        cumulative=True
        time_stamp=first_stamp
    else:
        cumulative=False
        for time in times:
            if times[time]>moda_count:
                moda=time
                moda_count=times[time]
        time_stamp=moda
    return (cumulative,float(time_stamp))

def add_parser_options_chunks(parser):
    """
    !!!Auxiliary function!!!  These are arguments for an argparse
    parser or subparser, and are the optional arguments for
    the chunks entry function in this module

    Arguments: The parser to which you want the arguments added to.
    
    Return:None
    """

    parser.add_argument("--start-at-end",dest="start_at_end",action="store_true",default=None,help="Partition from end of file instead of beginning")
    parser.add_argument("-ps","--partition-start",dest="partition_start",metavar="MINUTE",action="store",type=int,default=0,help="Time gap between the start of the file and the start of the interval; default:[%(default)s]")
    parser.add_argument("-pi","--partition-interval",dest="partition_interval",metavar="INTERVAL",action="store",type=int,help="Amount of time in minutes to be captured")
    parser.add_argument("--use_lines",dest="using_lines", action="store_true", default=False,help="Partition using line count instead of time")

def add_parser_options_blocks(parser):
    """
    !!!Auxiliary function!!!  These are arguments for an argparse
    parser or subparser, and are the optional arguments for
    the blocks entry function in this module

    Arguments: The parser to which you want the arguments added to.
    
    Return:None
    """
    parser.add_argument("-s", "--section", dest="section",metavar="MINUTES",type=int,action="store", help="Partitions size in minutes [default: %(default)s]", default=5)
    parser.add_argument("-g","--gap",dest="gap",metavar="MINUTES",type=int,action="store",help="Gap between partitions [default: %(default)s]",default=5)
