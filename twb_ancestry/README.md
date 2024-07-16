# TWB Native Information Processing

This repository contains a Python script for processing and categorizing native information from the Taiwan Biobank (TWB) survey data. The script performs various data cleaning tasks, including merging data, mapping codes to regions, and generating new columns based on specific conditions.

## Script Details

The script performs the following steps:

1.	Load Data:
    - Loads lab information data and survey data from specified CSV files.
    - Extracts columns related to native information.
2.	Data Cleaning:
    - Removes rows where all ‘NATIVE’ columns are NA.
    - Merges lab information data with the filtered survey data.
3.	Process Origin Information:
    - Maps codes to regions and categorizes provinces into broader regions (Northern China, Southern China, Other China).
    - Processes each individual’s native origin information and generates new columns (NATIVE_MOM, NATIVE_FA, and corresponding description columns).
4.	Combine Native Information:
    - Combines native information from both parents into a single column NATIVE_COMBINE.
    - Handles cases with duplicated or missing native information.
5.	Output:
    - Saves the processed DataFrame to a CSV file.
    - Outputs value counts of the combined native information to a text file.
    - Saves rows with duplicated native information to a separate CSV file for review.

## Output Files

The script generates the following output files in the specified output directory:

  - `processed_origin.csv`: The cleaned and processed DataFrame with combined native information.
  - `duplicated_origin.csv`: Rows with duplicated native information.
  - `value_counts.txt`: Value counts of the combined native information.