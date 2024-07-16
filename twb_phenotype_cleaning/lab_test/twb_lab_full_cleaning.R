library(tidyverse)
library(gridExtra)

setwd("/Users/xuanchou/Documents/Github/twb_data_cleaning/twb_phenotype_cleaning/")

file_dir <- "/Volumes/Transcend/twb_survey_lab/"

# Load the files =====
# Load the measurement table
df <- read.delim(paste0(file_dir, "measure/release_list_measure.csv"), sep = ',')
# Load the file with release number, sex and age information
other_df <- read.delim(paste0(file_dir, "release_list_survey.csv"), sep = ",") %>% 
  select(Release_No, FOLLOW, SEX, AGE)
other_df$SEX <- ifelse(other_df$SEX == "1", "M", "F")
# Load the file with ID information for each experiment
id_info <- read.delim(paste0(file_dir, "lab_info.csv"), sep = ",")
id_info <- id_info %>% 
  select(Release_No, FOLLOW, TWB1_ID, TWB1_Batch, TWB2_ID, TWB2_Batch, Sample_Name, Platform)
merge_df <- merge(id_info, other_df, by = c("Release_No", "FOLLOW"), all = TRUE) %>% 
  merge(., df, by = c("Release_No", "FOLLOW"), all = TRUE)
# merge_df <- merge_df %>% filter(FOLLOW == "Baseline")

info_cols <- c("Release_No", "FOLLOW", "TWB1_ID", "TWB1_Batch", "TWB2_ID", "TWB2_Batch", 
               "Sample_Name", "Platform", "AGE", "SEX")
measure_cols <- c("BODY_HEIGHT", "BODY_WEIGHT", "BMI", "BODY_FAT_RATE", "BODY_WAISTLINE", "BODY_BUTTOCKS", "WHR",
                  "T_SCORE", "Z_SCORE", "FVC", "FEV10", "FEV10_FVC")
blood_pressure_cols <- c("SIT_1_SYSTOLIC_PRESSURE", "SIT_1_DIASTOLIC_PRESSURE", "SIT_2_SYSTOLIC_PRESSURE", "SIT_2_DIASTOLIC_PRESSURE", "SIT_3_SYSTOLIC_PRESSURE", "SIT_3_DIASTOLIC_PRESSURE", "SIT_1_HEARTBEAT_SPEED", "SIT_2_HEARTBEAT_SPEED", "SIT_3_HEARTBEAT_SPEED")
lab_cols <- c("RBC", "WBC", "HB", "HCT", "PLATELET", "HBA1C", "FASTING_GLUCOSE", 
              "T_CHO", "TG", "HDL_C", "LDL_C", "T_BILIRUBIN", "ALBUMIN", "SGOT", "SGPT", "GAMMA_GT",
              "AFP", "BUN", "CREATININE", "URIC_ACID", "MICROALB", "CREATININE_URINE")
subset_df <- merge_df %>% 
  select(all_of(c(info_cols, measure_cols, blood_pressure_cols, lab_cols))) %>% 
  filter(!is.na(SEX))

subset_df <- subset_df %>% rename(AC_GLUCOSE = FASTING_GLUCOSE)

# Clean the value =====
# Average the systolic pressure, diastolic pressure and heart rate
systolic_col <- blood_pressure_cols[grepl("SYSTOLIC", blood_pressure_cols)]
diastolic_col <- blood_pressure_cols[grepl("DIASTOLIC", blood_pressure_cols)]
hr_col <- blood_pressure_cols[grepl("HEARTBEAT", blood_pressure_cols)]

# Calculate the average values and append to the new columns
subset_df <- subset_df %>%
  rowwise() %>%
  mutate(
    SYSTOLIC_PRESSURE = round(mean(c_across(all_of(systolic_col)), na.rm = TRUE), digits = 1),
    DIASTOLIC_PRESSURE = round(mean(c_across(all_of(diastolic_col)), na.rm = TRUE), digits = 1),
    HEARTBEAT_SPEED = round(mean(c_across(all_of(hr_col)), na.rm = TRUE), digits = 1)
  )

# Remove characters like ">" or "<" and convert all the values to numeric
cols_to_check <- c(measure_cols, "SYSTOLIC_PRESSURE", "DIASTOLIC_PRESSURE", "HEARTBEAT_SPEED", lab_cols) %>%
  map_chr(~sub("FASTING_GLUCOSE", "AC_GLUCOSE", .))

# Remove '>' and '<' from the specified columns
subset_df <- subset_df %>%
  mutate(across(all_of(cols_to_check), ~ gsub("[><]", "", .))) %>%
  mutate(across(where(is.character), ~ na_if(.x, ""))) %>%
  mutate(across(all_of(cols_to_check), as.numeric))

# Remove raw columns of blood pressure and heartbeat
subset_df <- subset_df %>% 
  select(-all_of(c(systolic_col, diastolic_col, hr_col)))

# Calculate EGFRcr
calculate_eGFRcr <- function(cre, gender, age) {
  # Constants
  k <- ifelse(gender == "F", 0.7, 0.9)
  a <- ifelse(gender == "F", -0.241, -0.302)
  
  # Calculations
  min_term <- min(cre/k, 1)
  max_term <- max(cre/k, 1)
  
  eGFRcr <- 142 * min_term^a * max_term^(-1.200) * 0.9938^age * 1.012^(ifelse(gender == "F", 1, 0))
  
  return(eGFRcr)
}

# Add EGFRcr column to subset_df
subset_df <- subset_df %>%
  mutate(EGFRcr = calculate_eGFRcr(CREATININE, SEX, AGE))

# Plot distribution for every phenotypes
create_distribution_plots <- function(data, cols, bin_width = NULL, fill_color = "lightblue", border_color = "black") {
  plot_list <- lapply(cols, function(col_name) {
    if (col_name %in% names(data)) {
      col_data <- data[[col_name]]
      if (is.null(bin_width)) {
        # Calculate bin width as 1/30th of the data range
        bin_width <- (max(col_data, na.rm = TRUE) - min(col_data, na.rm = TRUE)) / 30
      }
      ggplot(data, aes_string(x = col_name)) +
        geom_histogram(aes(y = ..density..), binwidth = bin_width, fill = fill_color, color = border_color) +
        labs(title = col_name, x = col_name, y = "Density") +
        theme_minimal()
    } else {
      NULL
    }
  })
  
  # Remove NULL
  plot_list <- plot_list[!sapply(plot_list, is.null)]
  
  # Arrange multiple plots in a single big plot
  distribution_plt_rm <- grid.arrange(grobs = plot_list, top = "Distribution of each trait")
  return(distribution_plt_rm)
}

cols_to_check_egfr <- c(cols_to_check, "EGFRcr")
distribution_plt <- create_distribution_plots(subset_df, cols_to_check_egfr)
distribution_plt
ggsave(distribution_plt, filename = "distribution_of_traits.png", dpi = 300, width = 15, height = 8)
write_csv(subset_df, file = "full_df_lab.csv")

## Summary statistics for each phenotypes =====
# Create a new data frame with the specified columns
data_subset <- subset_df %>%
  select(SEX, all_of(cols_to_check_egfr))

# Reshape the data
data_long <- data_subset %>% pivot_longer(cols = cols_to_check_egfr, names_to = "Variable", values_to = "Value")
data_long$Variable <- factor(data_long$Variable, levels = cols_to_check_egfr)

# Group by SEX and Variable, then calculate mean, median, and sd
result <- data_long %>%
  group_by(SEX, Variable) %>%
  summarize(
    Count = sum(!is.na(Value)),
    Mean = sprintf("%.3f", mean(Value, na.rm = TRUE)),
    Median = sprintf("%.3f", median(Value, na.rm = TRUE)),
    SD = sprintf("%.3f", sd(Value, na.rm = TRUE))
  )

# Format the numeric columns with commas
result[, c("Count")] <- lapply(result[, c("Count")], function(x) format(as.numeric(x), big.mark = ","))
write_csv(result, file = "summary_of_phenotypes_raw.csv")
