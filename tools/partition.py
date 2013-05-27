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
import logging 

module_logger=logging.getLogger('hrfanalyse.partition')

#This number was randomly chosen, no meaning to it
SAMPLE_SIZE=42

#ENTRY POINT FUNCTIONS

def partition(input_name,dest_dir,starting_point=0,section=-1,gap=-1,start_at_end=False,full_file=False,lines=False):
    """
    (str,str,int,int,int,bool,bool,bool) -> ( dict of str: list of tuples(float, float))

    Partition all the file in input_name using cutting_method(lines or time), start the partition with size interval
    at starting_point, if start_at_end is True partition from the file\'s end. Create a file for the partition in
    dest_dir.

    """
    block_times={}

    if os.path.isdir(input_name):
        file_list = os.listdir(input_name)
        for filename in file_list:
            block_times[filename] = partition_file(os.path.join(input_name,filename.strip()),dest_dir,starting_point,section, gap,start_at_end,full_file, lines)
    else:
        filename = os.path.basename(input_name)
        block_times[filename] = partition_file(input_name.strip(),dest_dir,starting_point,section,gap,start_at_end,full_file,lines)
    return block_times


def partition_file(input_name, dest_dir, starting_point, section, gap, start_at_end, full_file, lines):
    """
    (str,str,str,int,int,bool) -> list of tuples (float, float)

    Partition a single file using cutting_method(lines or time), start the partition with size interval
    at starting_point, if start_at_end is True partition from the file\'s end. Create a file for the partition in
    dest_dir.
    """
    if lines:
        return partition_by_lines(input_name, dest_dir, starting_point, section, gap, start_at_end, full_file)
    else:
        return partition_by_time(input_name, dest_dir, starting_point, section, gap, start_at_end, full_file)


def partition_by_lines(input_name, dest_dir, starting_point, section, gap, start_at_end, full_file):
    """
    (str, str, int, int, int, bool, bool) --> list of tuples (float, float)


    Partition a single file using the number of lines to measure the size of the partition.
    """

    with open(input_name,'rU') as fdin:
        lines = fdin.readlines()
    filename = os.path.splitext(os.path.basename(input_name))[0]
    if full_file:
        k=1
        file_block_dir = os.path.join(dest_dir,"%s_blocks"%filename)
        if(not os.path.isdir(file_block_dir)):
            module_logger.info("Creating %s!"%file_block_dir)
            os.makedirs(file_block_dir)
        p_init, p_end = initial_indexes_lines(starting_point, section,False, len(lines)-1)
        while p_end < len(lines):
            partname = "%s_%d"%(filename,k)
            write_partition(lines, os.path.join(file_block_dir,partname),p_init,p_end)
            k+=1
            p_init, p_end = next_indexes_lines(p_init,p_end,gap)
        partname = "%s_%d"%(filename,k)
        write_partition(lines, os.path.join(file_block_dir,partname),p_init,len(lines))
    else:
        p_init, p_end = initial_indexes_lines(starting_point, section,start_at_end, len(lines)-1)
        write_partition(lines, os.path.join(dest_dir,filename),p_init,p_end)
    return []

def initial_indexes_lines(starting_point, section, start_at_end, total_len):
    if start_at_end:
        p_init = total_len-section
        p_end = total_len-starting_point
    else:
        p_init = starting_point
        p_end = section
    return int(p_init), int(p_end)

def next_indexes_lines(p_init,p_end, gap):
    p_init += gap
    p_end += gap
    return int(p_init), int(p_end)


def partition_by_time(input_name, dest_dir, starting_point, section, gap, start_at_end, full_file):
    with open(input_name,'rU') as fdin:
        lines= fdin.readlines()
    filename = os.path.splitext(os.path.basename(input_name))[0]
    if start_at_end:
        cumulative, time_stamp = sniffer(lines[-SAMPLE_SIZE:], start_at_end)
    else:
        cumulative, time_stamp = sniffer(lines[:SAMPLE_SIZE], start_at_end)
    if full_file:
        k=1
        file_block_dir = os.path.join(dest_dir,"%s_blocks"%filename)
        if(not os.path.isdir(file_block_dir)):
            module_logger.info("Creating %s!"%file_block_dir)
            os.makedirs(file_block_dir)
        p_init, p_end = initial_indexes_time(lines, starting_point, section, False, cumulative, time_stamp)
        while p_end < len(lines):
            partname = "%s_%d"%(filename,k)
            write_partition(lines, os.path.join(file_block_dir,partname),p_init,p_end)
            k+=1
            p_init, p_end = next_indexes_time(lines, p_init, p_end, gap, section, cumulative, time_stamp)

        partname = "%s_%d"%(filename,k)
        write_partition(lines, os.path.join(file_block_dir,partname),p_init,p_end)
 
    else:
        p_init, p_end = initial_indexes_time(lines, starting_point, section,start_at_end, cumulative, time_stamp)
        print("pinit:%d, pend:%d"%(p_init,p_end))
        write_partition(lines, os.path.join(dest_dir,filename),p_init,p_end)
    return []

def next_indexes_time(lines, p_init, p_end, gap, section, cumulative, time_stamp):
    time_elapsed=0
    time, hrf =lines[p_init].split()        
    if cumulative:
        time_stamp = float(time)
    while test_time_limit(cumulative, time, time_stamp, time_elapsed, gap):
        p_init +=1
        time, hrf = lines[p_init].split()
        if not cumulative:
           time_elapsed += time_stamp
        
    while test_time_limit(cumulative, time, time_stamp, time_elapsed, gap+section) and abs(p_end) < len(lines):
        p_end +=1
        if p_end== len(lines):
            break
        time, hrf = lines[p_end].split()
        if not cumulative:
            time_elapsed += time_stamp
        
    return p_init, p_end

    

def initial_indexes_time(lines, starting_point, section, start_at_end, cumulative, time_stamp):
    if start_at_end:
        aux_index=-1
    else:
        aux_index=0
        
    time_elapsed=0
    time, hrf = lines[aux_index].split()

    while test_time_limit(cumulative, time, time_stamp, time_elapsed, starting_point) and abs(aux_index) < len(lines):
        if start_at_end:
            aux_index -=1
        else:
            aux_index +=1
        time, hrf = lines[aux_index].split()
        if not cumulative:
           time_elapsed += time_stamp

    if start_at_end:
        p_end = aux_index
    else:
        p_init = aux_index

        
    while test_time_limit(cumulative, time, time_stamp, time_elapsed, starting_point+section) and abs(aux_index) < len(lines):
        if start_at_end:
            aux_index -=1
        else:
            aux_index +=1
        if abs(aux_index) >=len(lines):
            break
        time, hrf = lines[aux_index].split()
        if not cumulative:
            time_elapsed += time_stamp

    if start_at_end:
        p_init = aux_index
    else:
        p_end = aux_index


    return p_init, p_end


        
        

def test_time_limit(cumulative, time, time_stamp, time_elapsed, desired_time):
    if cumulative:
        current_time = abs(float(time) - time_stamp)
        return current_time < desired_time
    else:
        current_time = time_elapsed + time_stamp
        return current_time < desired_time*1000
    
    
def write_partition(lines, output_file, i_index, f_index):
    with open(output_file,"w") as fdout:
        while i_index < f_index:
            try:
                time, hrf = lines[i_index].split()
            except ValueError:
                hrf = lines[i_index].strip()
            fdout.write("%s\n"%hrf)
            i_index+=1


                

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
        time,hrf = line.split()
        if times.has_key(time):
            times[time]+=1
        else:
            times[time]=1
        if float(time)>float(previous_time):
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

def add_parser_options(parser, full_file_option):
    """
    """

    parser.add_argument("--start-at-end",dest="start_at_end",action="store_true",default=None,help="Partition from end of file instead of beginning")
    parser.add_argument("-ds","--defered-start",dest="partition_start",metavar="SECONDS",action="store",type=float,default=0,help="Time gap between the start of the file and the start of the interval; default:[%(default)s]")
    parser.add_argument("-s","--section",dest="section",metavar="SECONDS",action="store",type=float,help="Amount of time in seconds to be captured")
    parser.add_argument("-g", "--gap", dest="gap", metavar="SECONDS", type=float, action="store", help="gap between sections (if using --full-file option)", default=0)
    parser.add_argument("--use-lines",dest="using_lines", action="store_true", default=False,help="Partition using line count instead of time")
    if full_file_option:
        parser.add_argument("--full-file", dest="full_file", action="store_true", default=False, help="Partition the full file into blocks")
