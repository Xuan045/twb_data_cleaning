import pandas as pd
import numpy as np
import re

file_path = '/Volumes/Transcend/twb_survey_lab'
output_path = '/Users/xuanchou/Documents/Github/twb_data_cleaning/twb_phenotype_cleaning/survey'

# Load lab info data
lab_info_df = pd.read_csv(f'{file_path}/lab_info.csv')
lab_info_keep_col = ['Release_No', 'FOLLOW', 'TWB1_ID', 'TWB1_Batch', 'TWB2_ID', 'TWB2_Batch', 'Sample_Name', 'Platform']
lab_info_df = lab_info_df[lab_info_keep_col]

# Load survey data
release_list_df = pd.read_csv(f'{file_path}/release_list_survey.csv')

# Define keywords and patterns for columns to remove
keywords_to_remove = ['PLACE', 'JOB', 'DRK', 'SMK', 'NUT', 'SPO', 'WET', 'SLEEP', 'ILL', 'COOK', 'INCENSE', 'WATER', 'TEA', 'COFFEE', 'VEGE', 'SNAKE', 'SUPP', 'INCOME']
women_col = ['MENARCHE', 'MENOPAUSE', 'PREGNANCY', 'BIRTH', 'ABORTION', 'PARITY', 'HOMO', 'HORMONE', 'HERBAL']
other_col = ['BREAST_MILK', 'EDUCATION', 'MARRIAGE', 'DEPENDENCY', 'MEAL_TIMES', 'OUT_EAT']
cancer_col = release_list_df.columns[release_list_df.columns.str.contains('CA_')].tolist()

# Create list of columns to drop based on patterns
pattern = '|'.join(keywords_to_remove + ['^D_', '^I_', '^DRUG_'] + women_col + cancer_col + other_col)
columns_to_drop = [col for col in release_list_df.columns if re.search(pattern, col)]

# Keep the remaining columns
columns_to_keep = [col for col in release_list_df.columns if col not in columns_to_drop]
survey_clean = release_list_df[columns_to_keep]

# Merge lab info with cleaned survey data
merge_id_survey = pd.merge(lab_info_df, survey_clean, on=['Release_No', 'FOLLOW'])

# Function to calculate value counts
def calculate_metrics(df, columns):
    """Caluculate value counts for specified columns
    Parameters:
    df: datafrme to be calculated
    columns (list): specified columns

    Returns:
    val_count_df: results for value counts, the column names are 'phenoytpe' and 'val_count'. Each row represents a column in the original dataframe.
    """
    # Function to calculate value counts and format the result
    def compute_val_count_from_series(series):
        val_counts = series.value_counts()
        formatted_counts = [f"{val}({count})" for val, count in val_counts.items()]
        return "; ".join(formatted_counts)

    # Calculate "val_count" using the compute_val_count_from_series function
    df = df.reset_index(drop=True)
    val_count = df[columns].apply(compute_val_count_from_series)

    val_count_df = val_count.reset_index()
    val_count_df.columns = ["phenotype", "val_count"]

    return val_count_df

# Reassign values to SELF columns
self_cols = [col for col in merge_id_survey.columns if col.endswith("_SELF")]

# Function to check if a column name contains "_SELF" and is not in self_cols and doesn't end with "_MN" or "_YR"
def is_self_column(column_name, self_cols):
    return "_SELF" in column_name and column_name not in self_cols and not column_name.endswith('_MN') and not column_name.endswith('_YR')

# Generate other self columns
other_self_cols = [col for col in merge_id_survey.columns if is_self_column(col, self_cols)]
# ['ALLERGIC_SELF_MED', 'ARTHRITIS_SELF_KIND', 'OTHER_HEART_DIS_SELF_KIND', 'DIABETES_SELF_KIND']

# Create a new list with replaced column names
other_self_cols_replace = [col.replace('_MED', '_description').replace('_KIND', '_description') for col in other_self_cols]

# Apply the changes to merge_id_survey DataFrame
merge_id_survey = merge_id_survey.rename(columns=dict(zip(other_self_cols, other_self_cols_replace)))

other_info_cols = ["CRF_NAME_QN", "SURVEY_DATE", "AGE", "SEX"]
dz_cols = [col.replace("_SELF", "") for col in self_cols]
eye_disease = ['EYE_DIS', 'CATARACT', 'GLAUCOMA', 'XEROPHTHALMIA', 'RENTINAL_DETACHMENT', 'FLOATERS', 'BLIND', 'COLOR_BLIND', 'ARMD', 'MYOPIA_600', 'MYOPIA_1000', 'OTHER_EYE_DIS', 'CATARACT_L', 'CATARACT_R', 'GLAUCOMA_L', 'GLAUCOMA_R', 'XEROPHTHALMIA_L', 'XEROPHTHALMIA_R', 'RENTINAL_DETACHMENT_L', 'RENTINAL_DETACHMENT_R', 'FLOATERS_L', 'FLOATERS_R', 'BLIND_L', 'BLIND_R', 'COLOR_BLIND_L', 'COLOR_BLIND_R', 'ARMD_L', 'ARMD_R', 'MYOPIA_600L', 'MYOPIA_600R', 'MYOPIA_1000L', 'MYOPIA_1000R', 'OTHER_EYE_DIS_1', 'OTHER_EYE_DIS_1_L', 'OTHER_EYE_DIS_1_R', 'OTHER_EYE_DIS_2', 'OTHER_EYE_DIS_2_L', 'OTHER_EYE_DIS_2_R']

# Sort the remaining columns
combined_order_replace = dz_cols + self_cols + other_self_cols_replace
sorted_cols_replace = sorted(combined_order_replace, key=lambda col: dz_cols.index(col.split('_SELF')[0]))

# Disease value cleaning
# 1. Calcluate unique value counts before assigning 0/1 to SELF column
# 2. Assigning 0 to SELF column according to disease column
#    - If Disease is not NA & Disease_self is not 1 -> Replace NA with 0 in _self column

# Extract the columns
full_df_reassign = merge_id_survey[lab_info_keep_col + other_info_cols + sorted_cols_replace + eye_disease]

# Iterate over each row in the DataFrame
for row_index, row in full_df_reassign.iterrows():
    # Iterate over each pair of self_col and dz_col
    for self_col, dz_col in zip(self_cols, dz_cols):
        # Check if the dz_col is not NA and the self_col is NA
        if pd.notna(row[dz_col]) and pd.isna(row[self_col]):
            # Set the self_col to 0
            full_df_reassign.loc[row_index, self_col] = 0

# Append new columns based on the description of the disease
# Create a list of keywords for ARTHRITIS
arthritis_keywords = {
    '退化性': 'Degenerative',
    '類風濕性': 'Rheumatoid',
    '僵直性脊椎炎': 'AnkylosingSpondylitis',
    '五十肩': 'FrozenShoulder',
    '反覆性風濕症': 'RecurrentRheumatism',
    '乾癬性': 'Psoriatic'
}

# Iterate through the rows and set new columns based on ARTHRITIS keywords
for ch_key, en_key in arthritis_keywords.items():
    column_name = f'ARTHRITIS_{en_key}'
    for row_index, row in full_df_reassign.iterrows():
        # Convert the cell value to a string before checking for the keyword
        description = str(row['ARTHRITIS_SELF_description'])
        if pd.notna(full_df_reassign.loc[row_index, 'ARTHRITIS']):  # Check if 'ARTHRITIS' is not NaN
            description = str(description)
            full_df_reassign.at[row_index, column_name] = int(ch_key in description)
        else:
            full_df_reassign.at[row_index, column_name] = None  # Set to NaN (None) if ARTHRITIS is NaN

# Create a list of keywords for DIABETES
diabetes_keywords = {
    '第二型': 'Type2',
    '妊娠型': 'Gestational',
    '第一型': 'Type1'
}

# Create new columns in twb2_df_reassign based on DIABETES keywords
for ch_key, en_key in diabetes_keywords.items():
    column_name = f'DIABETES_{en_key}'
    for row_index, row in full_df_reassign.iterrows():
        # Convert the cell value to a string before checking for the keyword
        description = str(row['DIABETES_SELF_description'])
        if pd.notna(full_df_reassign.loc[row_index, 'DIABETES']):  # Check if 'DIABETES' is not NaN
            full_df_reassign.at[row_index, column_name] = int(ch_key in description)
            # Check if "SEX" == 1 (Male), if yes, convert "DIABETES_Gestational" to NaN
            if ch_key == '妊娠型' and row['SEX'] == 1:
                full_df_reassign.at[row_index, column_name] = None
        else:
            full_df_reassign.at[row_index, column_name] = None  # Set to NaN (None) if DIABETES is NaN
            
# Create a list of the new columns created for ARTHRITIS and DIABETES
new_columns = [f'ARTHRITIS_{keyword}' for keyword in arthritis_keywords.values()] + [f'DIABETES_{keyword}' for keyword in diabetes_keywords.values()]

# Reorder columns to place new columns next to the respective _SELF_description columns
column_order = full_df_reassign.columns.tolist()

# Remove new columns from the list (if they exist)
columns_to_remove = set(new_columns).intersection(column_order)
column_order = [col for col in column_order if col not in columns_to_remove]

for keyword in arthritis_keywords.values():
    column_order.insert(column_order.index('ARTHRITIS_SELF_description') + 1, f'ARTHRITIS_{keyword}')

for keyword in diabetes_keywords.values():
    column_order.insert(column_order.index('DIABETES_SELF_description') + 1, f'DIABETES_{keyword}')
    
full_df_reassign = full_df_reassign[column_order]
full_df_reassign.to_csv(f'{output_path}/full_df_survey.csv', index=False)

# Output the final columns
with open(f'{output_path}/final_columns.txt', 'w') as f:
    f.write('\n'.join(full_df_reassign.columns))

# Calculate value counts for the full_df_reassign DataFrame
val_count_col = sorted_cols_replace + new_columns + eye_disease
full_val_reassign_append = calculate_metrics(full_df_reassign, val_count_col)
full_val_reassign_append.to_csv(f'{output_path}/full_val_count.csv', index=False)
