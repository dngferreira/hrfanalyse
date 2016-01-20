Python tool set to process heart rate frequency files, compression and entropy(using pyeeg --http://code.google.com/p/pyeeg/ ) are used, the results output is usually a .csv file which can be analysed however you feel like.

Available operations:

clean: clean a file by removing headers and extra columns.

partition: partition can be either cutting a chunk of the file( using time or number of lines), or cutting a file into several blocks.

compress: compress a single file; the tool look at the system path to test for the presence of the compressors.

entropy: calculate the entropy of a file.

These operations are always applied on a file granularity, but the interfaces allow you to pass a directory, and applies whatever operations you selected to all the files.