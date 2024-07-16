import pandas as pd

# File directory
file_dir = '/Volumes/Transcend/twb_survey_lab/'
out_dir = '/Users/xuanchou/Documents/Github/twb_survey_cleaning/twb_ancestry/'

# Load ID information
lab_info_df = pd.read_csv(f'{file_dir}lab_info.csv')
lab_info_keep_col = ['Release_No', 'FOLLOW', 'TWB1_ID', 'TWB1_Batch', 'TWB2_ID', 'TWB2_Batch', 'Sample_Name', 'Platform']
lab_info_df = lab_info_df[lab_info_keep_col]

# Load release list information
release_list_df = pd.read_csv(f'{file_dir}release_list_survey.csv')

# Extract columns with names containing 'NATIVE' and column 'Release_No'
native_cols = release_list_df.columns[release_list_df.columns.str.contains('NATIVE')]
extract_cols = ['Release_No'] + native_cols.tolist()
filtered_release_list_df = release_list_df.loc[:, extract_cols]

# Remove rows where all 'NATIVE' columns are NA
filtered_release_list_df = filtered_release_list_df.dropna(how='all', subset=native_cols)

# Merge dataframes
id_native_df = lab_info_df.merge(filtered_release_list_df, on='Release_No', how='left')

# Define the dictionary with the codes and corresponding places
places_dict = {
    1: "Shanxi", 2: "Shandong", 3: "Sichuan", 4: "Gansu", 5: "Andong", 6: "Hejiang", 7: "Jilin", 8: "Jiangsu", 9: "Jiangxi", 10: "Anhui",
    11: "Xikang", 12: "Tibet", 13: "Songjiang", 14: "Hebei", 15: "Henan", 16: "Qinghai", 17: "Zhejiang", 18: "Shaanxi", 19: "Hainan", 20: "Heilongjiang",
    21: "Hubei", 22: "Hunan", 23: "Guizhou", 24: "Yunnan", 25: "Suiyuan", 26: "Fujian", 27: "Xinjiang", 28: "Chahar", 29: "Nenjiang", 30: "Ningxia",
    31: "Mongolia", 32: "Rehe", 33: "Guangdong", 34: "Guangxi", 35: "Liaobei", 36: "Liaoning", 37: "Xing'an"
}

# Define the broader categorization by regions with provinces grouped into North China and South China divided by the Yangtze River
province_categories_yangtze = {
    "Northern China": ["Shanxi", "Hebei", "Shandong", "Henan", "Jiangsu", "Anhui", "Hubei", "Sichuan", "Chongqing", "Shaanxi", "Gansu", "Qinghai", "Ningxia", "Xinjiang", "Tianjin", "Beijing", "Liaoning", "Jilin", "Heilongjiang", "Inner Mongolia", "Liaobei"],
    "Southern China": ["Zhejiang", "Fujian", "Jiangxi", "Shanghai", "Hunan", "Guangdong", "Guangxi", "Hainan", "Guizhou", "Yunnan", "Tibet"],
    "Other China": ["Andong", "Hejiang", "Xikang", "Songjiang", "Suiyuan", "Chahar", "Nenjiang", "Mongolia", "Rehe", "Xing'an"]
}

# Reverse lookup dictionary to find the category of a province
province_to_category = {province: category for category, provinces in province_categories_yangtze.items() for province in provinces}

# Helper function to process each individual's origin information
def process_origin(row, origin_prefix):
    origin_mapping = {
        'F': 'Holo',
        'H': 'Hakka',
        'CHINA': 'China',
        'AB': 'Aborigine',
        'O': 'Other'
    }
    ancestry_columns = [origin_prefix + '_F', origin_prefix + '_H', origin_prefix + '_CHINA', origin_prefix + '_AB', origin_prefix + '_O']
    
    ancestry = None
    descriptions = []
    china_descriptions_1 = None
    china_descriptions_2 = None
    china_region = None

    if sum(row[col] for col in ancestry_columns if pd.notna(row[col])) > 1:
        ancestry = 'DUP'
    else:
        for col in ancestry_columns:
            if row[col] == 1.0:
                ancestry = origin_mapping[col.split('_')[-1]]
                break

    other_description_cols = [origin_prefix + '_AB_1', origin_prefix + '_AB_2', origin_prefix + '_ODC']
    if ancestry in ['Aborigine', 'Other']:
        for col in other_description_cols:
            if pd.notna(row[col]):
                descriptions.append(str(row[col]))
    elif ancestry == 'China':
        regions = []
        if pd.notna(row[origin_prefix + '_CHINA_1']):
            place_code = int(row[origin_prefix + '_CHINA_1'])
            china_descriptions_1 = places_dict.get(place_code, str(place_code))
            regions.append(province_to_category.get(china_descriptions_1, 'Undefined China'))

        if pd.notna(row[origin_prefix + '_CHINA_2']):
            place_code = int(row[origin_prefix + '_CHINA_2'])
            china_descriptions_2 = places_dict.get(place_code, str(place_code))
            regions.append(province_to_category.get(china_descriptions_2, 'Undefined China'))

        # Remove duplicates and sort the regions
        regions = sorted(set(regions), key=lambda x: ['Southern China', 'Northern China', 'Other China'].index(x))
        
        # Join regions if there are multiple
        if regions:
            china_region = '/'.join(regions)
        else:
            china_region = 'Other China'

        ancestry = china_region


    description = ', '.join(descriptions)
    
    return ancestry, description, china_descriptions_1, china_descriptions_2

# Process each row and add the new columns
def process_dataframe(df):
    new_columns = ['NATIVE_MOM', 'NATIVE_MOM_OTHER_description', 'NATIVE_MOM_CHINA_PROVINCE_1', 'NATIVE_MOM_CHINA_PROVINCE_2',
                   'NATIVE_FA', 'NATIVE_FA_OTHER_description', 'NATIVE_FA_CHINA_PROVINCE_1', 'NATIVE_FA_CHINA_PROVINCE_2']
    for col in new_columns:
        df[col] = None

    for index, row in df.iterrows():
        mom_ancestry, mom_description, mom_china_1, mom_china_2 = process_origin(row, 'NATIVE_MOM')
        fa_ancestry, fa_description, fa_china_1, fa_china_2 = process_origin(row, 'NATIVE_FA')
        
        df.at[index, 'NATIVE_MOM'] = mom_ancestry
        df.at[index, 'NATIVE_MOM_OTHER_description'] = mom_description
        df.at[index, 'NATIVE_MOM_CHINA_PROVINCE_1'] = mom_china_1
        df.at[index, 'NATIVE_MOM_CHINA_PROVINCE_2'] = mom_china_2
        df.at[index, 'NATIVE_FA'] = fa_ancestry
        df.at[index, 'NATIVE_FA_OTHER_description'] = fa_description
        df.at[index, 'NATIVE_FA_CHINA_PROVINCE_1'] = fa_china_1
        df.at[index, 'NATIVE_FA_CHINA_PROVINCE_2'] = fa_china_2

    return df

# Function to combine native information
def combine_native_info(mom_native, fa_native):
    priority_order = ['Holo', 'Hakka', 'Aborigine', 'Southern China', 'Southern China/Northern China', 'Southern China/Other China', 
                      'Northern China', 'Northern China/Other China', 'Other China', 'Other']
    if mom_native == fa_native:
        return mom_native
    else:
        ancestries = [ancestry for ancestry in [mom_native, fa_native] if ancestry]
        # Split combined ancestries into individual components, flatten the list
        ancestries_flat = [sub_ancestry for ancestry in ancestries for sub_ancestry in ancestry.split('/')]
        # Remove duplicates and sort by priority order
        ancestries_unique = sorted(set(ancestries_flat), key=lambda x: priority_order.index(x))
        # Join the unique, sorted ancestries
        return '/'.join(ancestries_unique)

# Apply the processing to the DataFrame
processed_df = process_dataframe(id_native_df)

# Check rows with duplicated native information
duplicated_df = processed_df[(processed_df['NATIVE_MOM'] == 'DUP') | (processed_df['NATIVE_FA'] == 'DUP')]
duplicated_df.to_csv(f'{out_dir}duplicated_origin.csv', index=False)

# Apply the combination logic to the DataFrame
processed_df = processed_df[~((processed_df['NATIVE_MOM'] == 'DUP') | 
                             (processed_df['NATIVE_FA'] == 'DUP') |
                             (processed_df['NATIVE_MOM'].isna()) | 
                             (processed_df['NATIVE_FA'].isna()))]
print(processed_df["NATIVE_FA"].value_counts())
print(processed_df['NATIVE_MOM'].value_counts())

processed_df['NATIVE_COMBINE'] = processed_df.apply(lambda row: combine_native_info(row['NATIVE_MOM'], row['NATIVE_FA']), axis=1)

# Drop original 'NATIVE' columns
processed_df = processed_df.drop(columns=[col for col in native_cols])

# Save the processed DataFrame to CSV
processed_df.to_csv(f'{out_dir}processed_origin.csv', index=False)

# Print value counts of NATIVE_COMBINE to a new txt file
with open(f'{out_dir}value_counts.txt', 'w') as f:
    f.write("Value counts for NATIVE_COMBINE:\n")
    f.write(processed_df['NATIVE_COMBINE'].value_counts().to_string())
