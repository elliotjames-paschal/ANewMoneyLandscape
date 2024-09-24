# Load required packages
library(xtable)

# Read your dataset (assuming it's saved in a file)
data <- read.csv("/Users/elliotpaschal/Desktop/Substitution_Data/Merged_Final_Modified.csv")

glimpse(data)

# Select columns starting from 'usdt' to the right
nqa_data <- data %>%
  select(usdt, usdp, usdc, tusd, gusd, frax, dai, busd, xrp, NGN, Lira)

# Generate summary statistics (Mean, Median, and Standard Deviation)
summary_stats <- data.frame(
  Mean = apply(nqa_data, 2, mean, na.rm = TRUE),
  Median = apply(nqa_data, 2, median, na.rm = TRUE),
  SD = apply(nqa_data, 2, sd, na.rm = TRUE)
)

# Output the summary statistics as LaTeX code using xtable
print(xtable(summary_stats, caption = "Summary statistics for stablecoins' distance from NQA"), 
      include.rownames = TRUE, 
      floating = TRUE, 
      table.placement = "H")
