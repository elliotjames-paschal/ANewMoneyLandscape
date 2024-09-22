# Required libraries
library(tidyverse)
library(lmtest)
library(sandwich)
library(xtable)

data <- read.csv("/Users/elliotpaschal/Desktop/Substitution_Data/Merged_Final.csv")

# regressions for individual stablecoins and fiat currencies
usdt_model <- lm(USDT_APY_CY ~ usdt, data = data)
usdc_model <- lm(USDC_APY_CY ~ usdc, data = data)
dai_model <- lm(DAI_APY_CY ~ dai, data = data)
frax_model <- lm(FRAX_APY_CY ~ frax, data = data)
ngn_model <- lm(NGN_APY_USD_CY ~ NGN, data = data)
lira_model <- lm(LIRA_APY_USD_CY ~ Lira, data = data)

# HAC standard errors
usdt_se_hac <- sqrt(diag(vcovHAC(usdt_model)))
usdc_se_hac <- sqrt(diag(vcovHAC(usdc_model)))
dai_se_hac <- sqrt(diag(vcovHAC(dai_model)))
frax_se_hac <- sqrt(diag(vcovHAC(frax_model)))
ngn_se_hac <- sqrt(diag(vcovHAC(ngn_model)))
lira_se_hac <- sqrt(diag(vcovHAC(lira_model)))

# models
models <- list(usdt_model, usdc_model, dai_model, frax_model, ngn_model, lira_model)

# Function to add stars based on significance
add_stars <- function(coef, pval) {
  if (pval < 0.01) {
    return(paste0(round(coef, 2), "***"))
  } else if (pval < 0.05) {
    return(paste0(round(coef, 2), "**"))
  } else if (pval < 0.10) {
    return(paste0(round(coef, 2), "*"))
  } else {
    return(round(coef, 2))
  }
}

# Extracting coefficients and p-values, then applying star notation
coef_with_stars <- sapply(models, function(model) {
  coefs <- coef(model)[2]  
  pval <- coeftest(model, vcov = vcovHAC(model))[2, 4]  
  add_stars(coefs, pval)  # Apply star notation
})

# R-squared and number of observations
r_squared <- sapply(models, function(model) summary(model)$r.squared)
n_obs <- sapply(models, function(model) nobs(model))

# Label names for coins and fiat currencies with manual numbering
labels <- c("(1) USDT", "(2) USDC", "(3) DAI", "(4) FRAX", "(5) NGN (Naira)", "(6) TRY (Lira)")

# Combine into a data frame
results <- data.frame(
  "Coin" = labels,
  "Distance" = coef_with_stars,
  "R-squared" = round(r_squared, 2),
  "N" = n_obs
)

# Create the xtable object
xtable_results <- xtable(results, caption = "Distance to NQA and Convenience Yield")

# Print LaTeX code from xtable with required modifications
print(xtable_results, 
      type = "latex", 
      caption.placement = "top", 
      include.rownames = FALSE, 
      sanitize.text.function = function(x) {x},  # Allows LaTeX formatting in table
      add.to.row = list(pos = list(0), command = "\\renewcommand{\\arraystretch}{1.25} \\vspace{0.25cm} "))



