# TWB Phenotype Data Cleaning

This repository contains a script for cleaning and processing phenotype data from the Taiwan Biobank (TWB). The script performs various data cleaning tasks, including removing unwanted columns, merging data, and generating new columns based on specific conditions.

# Survey data

## Script Details

The script performs the following steps:

1. **Load Data:**
   - Loads lab information data and survey data from CSV files downloaded from TWB official website.

2. **Data Cleaning:**
   - Removes columns based on specific keywords and patterns, including those related to diet habits, cancer associations, economic status, and sociological information.
   - Merges the cleaned survey data with the lab information data.
   - Reassigns values in `_SELF` columns based on corresponding disease columns.

3. **Generate New Columns:**
   - Generates new columns for specific diseases (`ARTHRITIS` and `DIABETES`) based on keywords found in the `_SELF_description` columns.
   - Reorders columns to place the new columns next to the respective `_SELF_description` columns.

4. **Output:**
   - Saves the cleaned DataFrame to a CSV file.
   - Outputs the final column names to a text file.
   - Calculates and saves value counts for the cleaned DataFrame.

## Output Files

The script generates the following output files in the specified output directory:

- `full_df_survey.csv`: The cleaned and processed DataFrame.
- `final_columns.txt`: A text file containing the names of the final columns in the DataFrame.
- `full_val_count.csv`: A CSV file containing value counts for the specified columns in the cleaned DataFrame.

# Lab test data

## Script Details

The script performs the following steps:

1.	Load Data:
    - Loads measurement data, survey data, and lab information from specified CSV files.
    - Merges these datasets into a single DataFrame.
2.	Data Cleaning:
    - Removes unwanted characters (like > and <) from specified columns and converts the values to numeric.
    - Calculates average values for blood pressure and heartbeat measurements.
    - Drops the raw blood pressure and heartbeat columns.
    - Calculates eGFRcr (estimated Glomerular Filtration Rate) using a specified formula.
3.	Generate Plots:
    - Creates distribution plots for each phenotype and saves them as a PNG file.
4.	Summary Statistics:
    - Calculates mean, median, and standard deviation for each phenotype, grouped by sex.
    - Saves the summary statistics to a CSV file.

## Output Files

The script generates the following output files in the specified output directory:

- `full_df_lab.csv`: The cleaned and processed DataFrame.
- `distribution_of_traits.png`: A PNG file containing the distribution plots for each phenotype.
- `summary_of_phenotypes_raw.csv`: A CSV file containing summary statistics for each phenotype.
