# M23 Data Processing

This is a library of tools that compose raw image processing of fits files. It
includes modules for calibration, combination, alignment, extraction and
normalization. Additionally we also have a data processor module that processes
data based on a provided configuration file using all the aforementioned
modules.

### Configuration Files

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
