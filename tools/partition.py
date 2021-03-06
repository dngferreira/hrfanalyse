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

!!!IMPLEMETNTATION NOTE: This module presumes the files contain only two columns, the first
column is a time series the second is the heart rate frequency(hrf).

The time series can either be a cummulative passage of time, or timestamps where
each stamp indicates the time passed since the last timestamp.

The partitions using time stamps do not use the actual value of the timestamp, it
uses the mode of all timestamps this way the data is not affected by
extended periods of signal loss, and what we get is closer to the
period of aquired signal. !!!

ENTRY POINT:partition(input_name,dest_dir,starting_point=0,section=-1,gap=-1,start_at_end=False,full_file=False,lines=False)

"""

import os
import sys
import logging

module_logger = logging.getLogger('hrfanalyse.partition')

# This number was randomly chosen, no meaning to it
SAMPLE_SIZE = 42


# ENTRY POINT FUNCTIONS

def partition(input_name, dest_dir, starting_point=0, section=-1, gap=-1, start_at_end=False, full_file=False,
              lines=False):
    """
    (str,str,int,int,int,bool,bool,bool) -> ( dict of str: list of tuples(float, float))

    Partition all the file in input_name, start the first cut at at starting_point and cut a section sized chunck of the
    file, if full_file option is activated cut the hole file into sections, where each section(si) starts at starting_point+gap*si.
    If start_at_end is used partition from the file\'s end. Partitions can be done by time(default) or by number of lines (
    by activating the lines option).

    """
    block_times = {}

    if os.path.isdir(input_name):
        file_list = os.listdir(input_name)
        for filename in file_list:
            block_times[filename] = partition_file(os.path.join(input_name, filename.strip()), dest_dir, starting_point,
                                                   section, gap, start_at_end, full_file, lines)
    else:
        filename = os.path.basename(input_name)
        block_times[filename] = partition_file(input_name.strip(), dest_dir, starting_point, section, gap, start_at_end,
                                               full_file, lines)
    return block_times


# IMPLEMENTATION

def partition_file(input_name, dest_dir, starting_point, section, gap, start_at_end, full_file, lines):
    """
    (str,str,int,int,int,bool, bool, bool) -> list of tuples (float, float)

    Partition a single file, start the first partition at starting_point, and cut a section sized chunck of the
    file, if full_file option is activated cut the hole file into sections, where each section(si) starts at starting_point+gap*si.
    If start_at_end is used partition from the file\'s end. Partitions can be done by time(default) or by number of lines (
    by activating the lines option)
    
    """
    if lines:
        return partition_by_lines(input_name, dest_dir, starting_point, section, gap, start_at_end, full_file)
    else:
        return partition_by_time(input_name, dest_dir, starting_point, section, gap, start_at_end, full_file)


def partition_by_lines(input_name, dest_dir, starting_point, section, gap, start_at_end, full_file):
    """
    (str, str, int, int, int, bool, bool) --> list of tuples (float, float)


    Partition a single file using the number of lines to measure the size of the partition. Returns the real
    (not just aquired signal time) times for beginning and end of the partitions.
    """

    with open(input_name, 'rU') as fdin:
        lines = fdin.readlines()
    lines = [line for line in lines if line != "\n"]
    filename = os.path.splitext(os.path.basename(input_name))[0]
    if start_at_end:
        cumulative, time_stamp = sniffer(lines[-SAMPLE_SIZE:], start_at_end)
    else:
        cumulative, time_stamp = sniffer(lines[:SAMPLE_SIZE], start_at_end)
    p_init, p_end = initial_indexes_lines(starting_point, section, start_at_end, len(lines) - 1)
    r_start = get_p_rtime(lines[:p_init + 1], 0, cumulative)
    r_end = get_p_rtime(lines[p_init:p_end], r_start, cumulative)
    p_times = []
    if full_file:
        k = 1
        file_block_dir = os.path.join(dest_dir, "%s_blocks" % filename)
        if not os.path.isdir(file_block_dir):
            module_logger.info("Creating %s!" % file_block_dir)
            os.makedirs(file_block_dir)
        while p_end < len(lines):
            partname = "%s_%d" % (filename, k)
            write_partition(lines, os.path.join(file_block_dir, partname), p_init, p_end)
            p_times.append((r_start, r_end))
            k += 1
            r_start = get_p_rtime(lines[p_end:p_end + 1], r_end, cumulative)
            p_init, p_end = next_indexes_lines(p_init, p_end, gap)
            r_end = get_p_rtime(lines[p_init:p_end], r_start, cumulative)
        partname = "%s_%d" % (filename, k)
        write_partition(lines, os.path.join(file_block_dir, partname), p_init, len(lines))
        p_times.append((r_start, r_end))
    else:
        write_partition(lines, os.path.join(dest_dir, filename), p_init, p_end)
        p_times.append((r_start, r_end))
    return p_times


def initial_indexes_lines(starting_point, section, start_at_end, total_len):
    """
    (int,int,bool,int) -> (int, int)

    Return the initial and final indexes for the first partition.
    These indexes are calculated by assuming each line in the file as an array position.
    First line in the file is line 0, last line in the file is total_len.

    """
    if start_at_end:
        p_init = total_len - section
        p_end = total_len - starting_point
    else:
        p_init = starting_point
        p_end = section
    return int(p_init), int(p_end)


def next_indexes_lines(p_init, p_end, gap):
    """
    (int, int, int) -> (int, int)

    Take the last partitions initial and final indexes and return the next partition's indexes.
    
    """
    p_init += gap
    p_end += gap
    return int(p_init), int(p_end)


def get_p_rtime(lines, real_s, cumulative):
    """
    (list, float, bool) -> float
    
    Calculate the real time at the end of the partition. The data in the partition is passed as a list,
    and the time at the start of this partition is passed as an argument.    
    """
    r_time = real_s
    for line in lines:
        try:
            time, hrf = line.split()
        except ValueError:
            time = 0
        if cumulative:
            r_time = float(time)
        else:
            r_time += float(time)
    return r_time


def partition_by_time(input_name, dest_dir, starting_point, section, gap, start_at_end, full_file):
    """
    (str, str, int, int, int, bool, bool) --> list of tuples (float, float)


    Partition a single file using the elapsed time to measure the size of the partition. Returns the real
    (not just aquired signal time) times for beginning and end of the partitions.
    """
    with open(input_name, 'rU') as fdin:
        lines = fdin.readlines()
    lines = [line for line in lines if line != "\n"]
    filename = os.path.splitext(os.path.basename(input_name))[0]
    if start_at_end:
        cumulative, time_stamp = sniffer(lines[-SAMPLE_SIZE:], start_at_end)
    else:
        cumulative, time_stamp = sniffer(lines[:SAMPLE_SIZE], start_at_end)
    p_init, p_end = initial_indexes_time(lines, starting_point, section, start_at_end, cumulative, time_stamp)
    r_start = get_p_rtime(lines[:p_init + 1], 0, cumulative)
    r_end = get_p_rtime(lines[p_init:p_end], r_start, cumulative)
    p_times = []
    if full_file:
        k = 1
        file_block_dir = os.path.join(dest_dir, "%s_blocks" % filename)
        if not os.path.isdir(file_block_dir):
            module_logger.info("Creating %s!" % file_block_dir)
            os.makedirs(file_block_dir)
        while p_end < len(lines):
            partname = "%s_%d" % (filename, k)
            write_partition(lines, os.path.join(file_block_dir, partname), p_init, p_end)
            p_times.append((r_start, r_end))
            k += 1
            r_start = get_p_rtime(lines[p_end:p_end + 1], r_end, cumulative)
            p_init, p_end = next_indexes_time(lines, p_init, p_end, gap, section, cumulative, time_stamp)
            r_end = get_p_rtime(lines[p_init:p_end], r_start, cumulative)
        partname = "%s_%d" % (filename, k)
        write_partition(lines, os.path.join(file_block_dir, partname), p_init, p_end)
        p_times.append((r_start, r_end))
    else:
        write_partition(lines, os.path.join(dest_dir, filename), p_init, p_end)
        p_times.append((r_start, r_end))
    return p_times


def next_indexes_time(lines, p_init, p_end, gap, section, cumulative, time_stamp):
    """
    (int, int, int) -> (int, int)

    Take the last partitions initial and final indexes and return the next partition's indexes.
    
    """
    time_elapsed = 0
    time, hrf = lines[p_init].split()
    if cumulative:
        time_stamp = float(time)
    while test_time_limit(cumulative, float(time), time_stamp, time_elapsed, gap):
        p_init += 1
        time, hrf = lines[p_init].split()
        if not cumulative:
            time_elapsed += time_stamp

    while test_time_limit(cumulative, float(time), time_stamp, time_elapsed, gap + section) and abs(p_end) < len(lines):
        p_end += 1
        if p_end == len(lines):
            break
        time, hrf = lines[p_end].split()
        if not cumulative:
            time_elapsed += time_stamp

    return p_init, p_end


def initial_indexes_time(lines, starting_point, section, start_at_end, cumulative, time_stamp):
    """
    (int,int,bool,int) -> (int, int)

    Return the initial and final indexes for the first partition.

    """
    if start_at_end:
        aux_index = -1
    else:
        aux_index = 0

    time_elapsed = 0
    time, hrf = lines[aux_index].split()

    while test_time_limit(cumulative, float(time), time_stamp, time_elapsed, starting_point) and abs(aux_index) < len(
            lines):
        if start_at_end:
            aux_index -= 1
        else:
            aux_index += 1
        time, hrf = lines[aux_index].split()
        if not cumulative:
            time_elapsed += time_stamp

    if start_at_end:
        p_end = aux_index
    else:
        p_init = aux_index

    while test_time_limit(cumulative, float(time), time_stamp, time_elapsed, starting_point + section) and abs(
            aux_index) < len(lines):
        if start_at_end:
            aux_index -= 1
        else:
            aux_index += 1
        if abs(aux_index) >= len(lines):
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
    """
    (bool, float, float, float, float) -> bool

    Auxilary function to help test a current time agains a spipulated time limit.

    If the time series is cumulative then we test how much time has passed by
    subtracting the last time read from the inital time read at the beginning of the
    partition.
    If the time series is not cumulative then time_elapsed keep track of how much
    time has passed since the beginning of the partition.
    """
    if cumulative:
        current_time = abs(float(time) - time_stamp)
        return current_time < desired_time
    else:
        current_time = time_elapsed + time_stamp
        return current_time < desired_time * 1000


def write_partition(lines, output_file, i_index, f_index):
    """
    (list, str, int, int) -> NoneType

    Take the hrf file contents ( in a list) and write the lines from a partition to
    output_file.
    """
    with open(output_file, "w") as fdout:
        while i_index < f_index:
            try:
                time, hrf = lines[i_index].split()
            except ValueError:
                hrf = lines[i_index].strip()
            fdout.write("%s\n" % hrf)
            i_index += 1


# AUXILIARY FUNCTIONS


def sniffer(lines, start_at_end=False):
    """
    (list, bool) -> (bool, float)

    Recieves a sample of the file and extrapolates whether the
    timeline is cumulative or periodic. If it's cumulative than along
    with that information also sends the first timestamp, otherwise it
    sends the mode of the timestamps(unless signal is lost machines
    always capture the signal on a time frequency, the mode will give
    us that frequency).

    """
    # If the file only has the hrf column it can still be partitioned by lines,
    # the values returned in that case are irrelevant
    if len(lines[0].split()) < 2:
        return False, 0
    times = {}
    crescent = 0
    if start_at_end:
        first_stamp = lines[-1].split()[0]
    else:
        first_stamp = lines[0].split()[0]
    previous_time = lines[0].split()[0]
    moda_count = 0
    for line in lines:
        time, hrf = line.split()
        if time in times:
            times[time] += 1
        else:
            times[time] = 1
        if float(time) > float(previous_time):
            crescent += 1
            previous_time = time
    if crescent == len(lines) - 1:
        cumulative = True
        time_stamp = first_stamp
    else:
        cumulative = False
        for time in times:
            if times[time] > moda_count:
                moda = time
                moda_count = times[time]
        time_stamp = moda
    return cumulative, float(time_stamp)


def add_parser_options(parser, full_file_option=True):
    """
     (argparse.ArgumentParser, bool) -> NoneType

    !!!Auxiliary function!!!  These are arguments for an argparse
    parser or subparser, and are the parameters taken by the entry function 
    in this module. The full_file_option disables/enables the presence of the
    full_file option.
    """

    parser.add_argument("--start-at-end", dest="start_at_end", action="store_true", default=None,
                        help="Partition from end of file instead of beginning")
    parser.add_argument("-ds", "--defered-start", dest="partition_start", metavar="SECONDS", action="store", type=float,
                        default=0,
                        help="Time gap between the start of the file and the start of the interval; default:[%(default)s]")
    parser.add_argument("-s", "--section", dest="section", metavar="SECONDS", action="store", type=float,
                        help="Amount of time in seconds to be captured")
    parser.add_argument("-g", "--gap", dest="gap", metavar="SECONDS", type=float, action="store",
                        help="gap between sections", default=0)
    parser.add_argument("--use-lines", dest="using_lines", action="store_true", default=False,
                        help="Partition using line count instead of time")
    if full_file_option:
        parser.add_argument("--full-file", dest="full_file", action="store_true", default=False,
                            help="Partition the full file into blocks")
