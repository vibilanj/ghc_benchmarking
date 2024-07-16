# GHC Benchmarking Tool (Parser Timings)

## Overview

This Python script is designed to benchmark the Glasgow Haskell Compiler (GHC). It automates the process of downloading, compiling, and analyzing the top Hackage packages to provide insights into GHC's performance, particularly focusing on the parsing phase of the compilation process.

## Features and Workflow
The script begins by downloading the top n Hackage packages with the most reverse dependencies, defaulting to 20. It fetches the source code for these packages and then compiles them using GHC with the [`--ddump-timings`](https://ghc.gitlab.haskell.org/ghc/doc/users_guide/debugging.html#ghc-flag--ddump-timings) flag. This flag allows GHC to output allocation and runtime statistics for various compilation stages, with allocations measured in bytes and timings in milliseconds.

After compilation, the script uses the [`time-ghc-modules`](https://github.com/codedownio/time-ghc-modules/releases/tag/2.0.0) tool (version 2.0.0 / commit 5eec634) to read the `--ddump-timings` files, generating JSON files that contain detailed timing information. These JSON files are collected and processed, focusing on the timing data by module and compiler phase, particularly the parsing phase. The data is then saved as a CSV file, which is further cleaned to retain only the parsing phase timings. Additional columns are added, including the total time taken for a module, the time spent on parsing as a percentage of the total time, and the size of the file corresponding to the module.

The script consolidates all the timing information into a single file, creating two versions: one with detailed module-level data and another with aggregated package-level data. The package-level data includes metrics such as total time, parsing time, parsing time as a percentage, and the average and geometric mean of module parser percentages, along with the total size of the package files.

Finally, the script generates various plots to visualize the data, including log scale and non-log scale versions of:
- Parser time vs. Total time
- Percentage of time spent on parsing vs. Total time
- Parser time vs. File size
- Percentage of time spent on parsing vs. File size

## Usage
1. Ensure you have Python and GHC installed on your system.
2. Install the required Python packages using:
```sh
pip install -r requirements.txt
```
3. Execute the script to start the benchmarking process:
```sh
python run.py
```
4. The timing data is stored under the `timing_data` directory, and the plots are saved in the `plots` directory.

## Analysis

As expected, there is a positive correlation between the amount of time spent parsing and the total time taken for compilation. Similarly, there is a positive correlation between the amount of time spent parsing and the size of the source files. However, the percentage plots show that the parsing phase takes up a relatively small portion of the total compilation time. As the total time or the size of the source files increases, the percentage of time spent parsing decreases, indicating that other compilation phases become more dominant.

There are some outliers in the parser time vs. size plots where smaller files take longer to parse than larger files. This cluster consisted of short preprocessed Haskell source files. They use the C Preprocessor (CPP) to include or conditionally compile code based on preprocessor directives. Examples of these modules are `Data.ByteString.ReadInt` and `Data.ByteString.ReadNat` from the `bytestring-0.12.1.0` package and `System.OsPath` from the `filepath-1.5.3.0` package.

Another interesting observation is about the modules that took the most time to parse. One such package was `Data.Text.Internal.Fusion.CaseMapping` from the `text-2.1.1` package. This file is a Haskell module that is automatically generated and contains numerous specific mappings for case conversions, particularly for Unicode characters. It uses `LambdaCase` to define an extensive set of pattern matches for different Unicode characters. This requires the parser to handle a large number of individual cases, which increases the parsing complexity and time.

In the percentage of time spent on parsing plots, there is a very dense almost vertical cluster on the left-most edge. This cluster consisted of Haskell module files that define and export specific functionality. Examples of these modules are `Data.Time.Format.Internal` and `Data.Time.Format` from the `time-1.14` package and `Data.Array.MArray` from the `array-0.5.7.0` package.