
[![Build Status](https://travis-ci.org/dngferreira/hrfanalyse.svg?branch=master)](https://travis-ci.org/dngferreira/hrfanalyse)
[![Coverage Status](https://coveralls.io/repos/github/dngferreira/hrfanalyse/badge.svg?branch=master)](https://coveralls.io/github/dngferreira/hrfanalyse?branch=master)
      
## Documentation

The tool set is extensively documented using pydoc. To launch the graphical interface run:

        pydoc -g 

in the command line.

## HRFAnalyseDirect

The main interface HRFAnalyseDirect allows for operations to be applied to files or directories (no subdirectories):


### Examples :


* Clean:
     
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



* Compress
     
    Compress using the gzip algorithm (maximum compression level will be used)
        
        ./HRFAnalyseDirectory.py unittest_dataset compress -c gzip
    
    Compress using the bzip2 algorithm with minimum compression(1 in this case):
        
        ./HRFAnalyseDirectory.py unittest_dataset -c bzip2 --level 1


* Entropy
    
    Calculate the entropy using Approximate entropy with tolerance 0.2 and matrix
    dimension 2 (reference values for the analysis of biological data)
     
        ./HRFAnalyseDirectory.py unittest_dataset entropy apen -t 0.2


## HRFAnalyseFileBlocks

The auxiliary interface HRFAnalyseFileBlocks does the partition and compression of the file blocks
automatically.

### Examples:


* Compress

       Cut files into 5min blocks with no overlap and compress each one with the default compressor
        
        ./HRFAnalyseFileBlocks.py unittest_dataset/ -s 300 compress
        
        
       Cut files into blocks with 300 lines with no overlap and compress each one with the default compressor
        
        ./HRFAnalyseFileBlocks.py unittest_dataset/ -s 300 --use-lines compress
        
        
       Cut files into blocks with 5 min where one block starts 1 min later then the previous one did. Compress each one with the paq8l compressor
        
        ./HRFAnalyseFileBlocks.py unittest_dataset/ -s 300 -g 60 compress -c paq8l


* Entropy
    
       Cut files into blocks with 5 min where one block starts 1 min later then the previous one did. Calculte each files entropy using the Sample entropy.
        
        ./HRFAnalyseFileBlocks.py unittest_dataset/ -s 300 -g 60 entropy sampen
    

## HRFAnalyseMultiScale

The last interface HRFAnalyseMultiScale is specific to calculate MultiScale entropy and compression:

### Examples:

* Multiscale entropy for all the files starting at scale 1(original files) and ending in scale 20

        ./HRFAnalyseMultiscale unittest_dataset entropy sampen

* Multiscale compression with rounded results for scale, since the scales are constructed
by averaging a given number of point we are bound to have floats, this options
rounds those numbers to an integer.

        ./HRFAnalyseMultiscale unittest_dataset --round-to-int compression

* Multiscale compression with rounded results for scale, multiplyed by 10, the scale
point is multiplied by 10 and rounded.
    
        ./HRFAnalyseMultiscale unittest_dataset --round-to-int --multiply 10 compression -c paq8l

_______________________________________________________________________________

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
