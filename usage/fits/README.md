# Notes

**Our fits reader wrapper around** the fits reader given by the astropy
library... so for full featured functionality, please refer to
astropy documentation... 

There are two functions in our fits module, 
1. `readFits`
2. `fitsToCSV`

First, note it's fit**s** and not just fit.

Second, probably the `readFits` is the one that will be the most used.
`readFits` takes in a filename of the fits file and then a function
as an argument. The function to be passed to `readFits` is where you
do all the work you want after reading the fits file.

If you're not familiar with the pattern of passing function as an
argument, called funarg sometimes, you might want to get familiar
with that first. Also, our sample [usage file](./use-fits.py ) might
be helpful to look at.

The other function in this module, `fitsToCSV` might be barely
useful... but it's there for fun, when you need it.
It takes two arguments, the first is the location of the fits file and
the second is the location of the csvFile. If a csv file already
exists in that location, it overrides with the new data!

A csv file is a text-file of comma separated values. So, in our case,
it will most likely (for 1024X1024 images) be a long list of 1024 by
1024 entries separated by commas. 
