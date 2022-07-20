# M23 Data Processing

This repo is named `python-helpers`. But as the project has grown, the
code aims do to more than just provide some helper functions in
python, although the underlying philosophy of the current code is
still the same. This repo has grown to be a library around python
modules that collectively make our data processing program.

The repo has two folders: 
* [m23](./m23)
* [usage](./usage)

`m23` is where all the modules live. And `usage` is where those
modules are used to make something out of them. There are two good
examples of how to use the modules in `m23` currently in the `usage`
folder. One is [data processing](./usage/processing) and the other is
[super combination](./usage/supercombine). Data processing is our main data
processing code, that we used to do in IDL. 

**For information on how to
use the data processing, [go to that repo's
README](./usage/processing/README.md).**

But the point here is that you
can use as little of our modules in m23 to make something like a
[supercombine](./usage/supercombine) program or use it extensively to
make the entirety of our data processing. 

#### Using the software
To use this software, you must first clone this repo. You must go to
your terminal, or powershell/git bash (on windows) and type
```git clone git@github.com:LutherAstrophysics/python-helpers.git```
You must have ssh keys setup to authorize yourself to clone the repo, 
If you're new to this see [info on
github](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account).
Once you clone the repo, you must install the required pacakges for
our library. Using your terminal, `cd` into the correct repo where the
root of this library lives (if you're new to command line tools, see
some examples in google on how to navigate around directories using
command line on windows/linxu/mac whatever you're on). To install the
software it's recommended to first instal python virutal environment
by doing `python -m venv .venv`. This installs a virtual environment
in the directory you're on in a `.venv` folder. To activate the venv,
you must run command like `./.venv/bin/activate` or something similar.
This depends on your OS as well, so you can look it up. Once that is done, 
install the libraries by running `python -m pip install -r
requirements.txt`. Pip is a package manager for python and
`requirements.txt` is the file listing the packages that need to be
installed.
Once it's done, you're good to go. 

To see some example programs, look at the [usage folder](./usage).

If you've already clone the repo and there's a new change that you'd
like to pull you should run `git pull`. 

### Contributing
This library has bugs, like most software and needs contribution. To
make changes to it, you go to the respective folder (mostly m23) and
make changes in whatever module you're trying to. To commit your
changes to github, you need to know little about git, so look up how
to do that, and you're good to go.

