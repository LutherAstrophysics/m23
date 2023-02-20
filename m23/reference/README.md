# Reference files location

[**R-I File**](MeanRI100.txt): Contains the reference Mean R-I for 2510 stars in 2003\
Each row in this file (excluding the header) corresponds to a star in our field of view in the order. This means that excluding the first row that's header, in order to look for the R-I color value for star 193, you would have to read the value from row 194.

[**Reference Image**](m23_3.5_071.fit): Reference image in 2003\
This is the image that is used to generate the reference file described below. This image is used as our alignment module requires an actual fit file with respect to which a subject is to be aligned. Other parts of the code, like the extraction module and inter night normalization code require the reference log file.

[**Reference File**](ref_revised_71.txt): Reference flux log file for the reference image in 2003\
Looking at this reference log file one might be confused that there are more rows than 2510 stars that we have. But once you eliminate the rows that contain `nan`s you'll find that the number of stars and the number of rows(excluding the header) are the same. Important to note is that this reference file is an ordered sequence of logs for various stars. Preserving the order, once you eliminate the `nan` rows, the with list of rows that you end up with, you can read the properties for any star k like its X and Y coordinate in the reference image and the star and sky ADU for the star. For star number 200, you'll find this information in 200th row (once you're eliminated header and `nan` rows).
