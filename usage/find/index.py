from statistics import mean
from astropy.io.fits import getdata
from photutils.detection import DAOStarFinder
from astropy.io import ascii
import numpy as np

### m23 imports
# from m23.calibrate.calibration import getCenterAverage

file = "C:\Data Processing\RefImage\m23_3.5_071.fit"
saveas = r"C:\Data Processing\RefImage\result2.csv"
starData = getdata(file)
mean, median, std = np.mean(starData), np.median(starData), np.std(starData)

print((mean, median, std))

daofind = DAOStarFinder(fwhm=3.5, threshold=50, exclude_border=True)
sources = daofind(starData - median)

for col in sources.colnames:
    sources[col].info.format = '%.2f'

ascii.write(sources, saveas, overwrite=True, delimiter='\t', exclude_names=['id'])
# sources.write(saveas, overwrite=True, format='ascii')