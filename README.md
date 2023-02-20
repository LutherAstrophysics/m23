# M23 Data Processing

This is a library of tools that compose raw image processing of fits files. It
includes modules for calibration, combination, alignment, extraction and
normalization. Additionally we also have a data processor module that processes
data based on a provided configuration file using all the aforementioned
modules.

### Installation

This packages is available in pypi and can be installed via the `pip` package manger.
It is recommended that you install this library in a virtual environment however.
An ideal setup could be to create a directory where you keep the `toml` data processing
configuration files (explained below) and install this library there so that you can
easily run the data processing command right from where your configuration files are.

To run the following commands, if you're in Linux/MacOS use `terminal` app and if you're
on Windows, use the terminal that can be launched from VS Code or the Windows `powershell`.

```
cd ~/Desktop
mkdir data-processing; cd data-processing
```

After this use python >= 3.10 to create virtual environment. Instead of typing
`python3.10` you might have to type `py3` or `python` or `python3` or sth else
depending on what is configured on your system.

```
python3 -m venv .venv
```

Then we activate the virtual environment. This is OS and your shell specific, so
if the following command doesn't work for your just google how to activate
python virtual environment using `venv` package in Windows/Ubuntu/etc.

Generally, the following works for UNIX

```
source ./.venv/bin/activate
```

Generally, the following works for Windows. [See more here](https://docs.python.org/3/library/venv.html#how-venvs-work)
If you get permissions error in windows, you might have to run the command `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
as suggested [here](https://docs.python.org/3/library/venv.html#how-venvs-work)

```
./.venv/Scripts/activate.bat
# OR
./.venv/Scripts/Activate.ps1
```

Now, we can install the `m23` library

```
python -m pip install m23
```

### Usage

Once you've installed `m23` you can use any of the modules present (example.
calibration, extraction, normalization, etc) individually or just use the main
programs `m23` that do data processing for your. To process data for a
night/nights, you must define a configuration file. The processor reads the
data processing settings along with the path to input and output directories
from the configuration file.

### Reference files

Most of the modules will ask for various reference files. For convenience we have included a sample of the kind of reference files used by this library [here](./m23/reference/). Note that it's the responsibility of the person processing data to provide a correct reference file for the task. The reference files listed in this repo are aren't to be used but for sample so that it will help you understand the kind of reference file you're supposed to provide. We don't like to hardcode these sample reference files in the code because if the reference files change or that you like to experiment with processing with different reference files, you have that power to change reference files by merely changing the configuration file. Use this power wisely.

#### Process Command

Examples for configuration file for process command provided here are named Brown
and Rainbow. (B)rown comes before (R)ainbow so the file [./brown.tml](./brown.toml) denotes
the configuration for processing pre new camera (< June 16 2022) data.

[./rainbow.toml](./rainbow.toml) is an example configuration file for
processing data after the new camera (>= June 16 2022)

A sample configuration file (for old camera images) looks like this. For example of new camera
configuration file see [./rainbow.toml](./rainbow.toml).

```
# This is a comment
[image]
rows = 1024
columns = 1024
crop_region = [] # We don't crop old camera images < June 16 2022


[processing]
no_of_images_to_combine = 10
radii_of_extraction = [3, 4, 5]


[reference]
# The image file is an actual fit image while the reffile refers to the stats file for that image
image = "C://Data Processing/Reference/RefImage.fit"
file = "C://Data Processing/Reference/reffile.txt"


[input]

    [[input.nights]]
    path = "F://Summer 2019/September 4, 2019"
    masterflat = "C://Data Processing/2019/Python Processed/September 4 2019"

    [[input.nights]]
    path = "F://Summer 2019/September 9, 2019"
    # Because we haven't provided masterflat, this night must have flats to use

    [[input.nights]]
    path = "F://Summer 2019/September 8, 2019"
    # Because we haven't provided masterflat, this night must have flats to use


[output]
path = "C://Data Processing/2019 Python Processed"
```

The file should be pretty self explanatory. Note that `#` denotes the beginning end of line comment.
Still few things to note:

1. Provide masterflat for only those nights where we would like to use masterflat of other nights.
2. Any of the paths except the output path provided in the configuration file must exist, otherwise the configuration file is deemed to be problematic. Output path (along with any intermediary directories) are created if they don't already exist. This applies to masterflat path as well. So you cannot process a night that doesn't have flats before the masterflat that you want to use for the night exists.
3. Make sure that you are not processing old camera nights and new camera images together, unless you absolutely know what you're doing.

Once you have a configuration file, you can start processing by invoking the command line interface as follows:

```
python -m m23 process config_file_path

# Example, if you have 1.toml in current directory
python -m m23 process 1.toml
```

#### Norm Command

`norm` is another command (a subcommand, technically) available in `m23` CLI. This is a command to renormalize LOG_FILES_COMBINED for one or more nights.
The way our data processing works is that we first do a full data processing (full meaning involving Calibration, Combination, Alignment, Extraction, and Normalization) and then re-normalize the data. To re-normalize, we look at the normfactors and see what section of night of has non-erratic data. The `norm` subcommand take a configuration file that describes what section of the night to use to generate LOG_FILES_COMBINED. The section of the night is described by two numbers `fist_logfile_number`, and `last_logfile_number` that describe the the range of logfiles to use. The file [./renormalize.toml](./renormalize.toml) contains an example of re-normalization configuration file.

```
[processing]
radii_of_extraction = [3, 4, 5,]


[reference]
file = "C://Data Processing/Reference/refile.txt"


[input]

    [[input.nights]]
    path = "F://Summer 2022/September 04, 2022"
    first_logfile_number = 10
    last_logfile_number = 45

    [[input.nights]]
    path = "F://Summer 2022/September 12, 2022"
    first_logfile_number = 30
    last_logfile_number = 66
```

As you can see in the renormalization configuration, the `norm` subcommand lets you re-normalize multiple nights in a go. You can run the renormalization command as follows:

```
# Assuming you have conf.toml in your directory
python -m m23 norm conf.toml
```

#### mf Command

`mf` is another command available as part of `m23` CLI. It takes a configuration file specifying the input night folder
and generates a masterflat for that night based to the provided output folder (creating the folder if it doesn't already exist). Note that
in order to generate the masterflat, it uses the flats from the nights provided as input. These flats should be inside the standard Calibration Frames folder that we use for our raw image processing (with the calibration folder itself being inside the folder for the night
provided as input. Additionally note that the provided folder name should match the naming convention of our raw image night folder.) The output is just a single masterflat file whose name is prepended with the date of the night and is generated in the output folder path specified in the config file. The configuration file also found in [./mf.toml](./mf.toml) is as follows:

```
# Note that it's important to define input and output before image definition
[input] = "F://Summer 2019/September 4, 2019"
[output] = "C://Data Processing/Masterflat"


[image]
rows = 2048
columns = 2048
# New camera images (>= June 16 2022) have vignetting ring effect which we crop.
# Array of crop regions. The last and first co-ordinate are joined to make an enclosing region
crop_region = [
    [[0, 448], [0, 0], [492, 0], [210, 181]],
    [[0, 1600], [0, 2048], [480, 2048], [210, 1867]],
    [[1400, 2048], [2048, 2048], [2048, 1500], [1834, 1830]],
    [[1508, 0], [1852, 241], [2048, 521], [2048, 0]]
]

```

Unlike other commands, this command can only process one night at a time and is invoked as follows:

```
# Assuming you have mf.toml in your directory
python -m m23 mf mf.toml
```

#### Using specific module

If you want to do data processing or invoke any of the `m23` modules as part of your python program, you can import
the respective module/functions/variables as follows

```
from m23 import start_data_processing # Data processing function
from m23.align.alignment import imageAlignment
from m23.constants import ALIGNED_COMBINED_FOLDER_NAME
```

For detailed info on the behavior these functions/variables, look up the source code.

### Upgrading package

The package's is available in pypi at <https://pypi.org/project/m23/>. If the version that you've isn't the lasted version,
it is recommended that you upgrade the package by running the following command after activating your virtual environment.

```
python -m pip install --upgrade m23
```

### Developer notes

If you're making changes to this package, here are a few things to note.

1. To publish the package to pypi, make sure you update the version number in [./pyproject.toml](./pyproject.toml) and then commit your changes. Then create a release from the this repos github homepage. This should trigger the github workflow that builds uploads the package to
   pypi.

### Contributing

This library has bugs, like most software and needs your valuable contribution.
