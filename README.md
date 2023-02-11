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

Generally, the following works for Windows. [See more here](./https://docs.python.org/3/library/venv.html#how-venvs-work)

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

##### Configuration Files

(B)rown comes before (R)ainbow so the file [./brown.tml](./brown.toml) denotes
the configuration for processing pre new camera (< June 16 2022) data.

[./rainbow.toml](./rainbow.toml) is an example configuration file for
processing data after the new camera (>= June 16 2022)

### Contributing

This library has bugs, like most software and needs contribution. To
make changes to it, you go to the respective folder (mostly m23) and
make changes in whatever module you're trying to. To commit your
changes to github, you need to know little about git, so look up how
to do that, and you're good to go.
