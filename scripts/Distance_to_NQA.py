import pandas as pd
import numpy as np
from scipy.optimize import fsolve, minimize
from scipy.stats import norm
import logging
import os

# Prompt for file paths or use default relative paths
data_file_path = input("Enter the path to the dataset CSV file (e.g., 'Official_Data.csv'): ")
log_file_path = input("Enter the path to the log file (e.g., 'log.csv'): ")

# Set up logging to capture solver failures
logging.basicConfig(filename=log_file_path, level=logging.INFO)

# Constants
V_d = 100  # Market value of debt and equity claims
D_d = 1    # Face value of debt redeemed
rolling_window = 90  # 90 days for volatility calculation

# List of fiat and regular cryptocurrencies (where we won't apply the P > 1 adjustment)
non_stablecoins = ['bit', 'eth', 'xrp', 'NGN', 'Lira']

# Cryptocurrencies to handle separately
cryptos_to_handle_separately = ['bit', 'eth']

# Load dataset 
df = pd.read_csv(data_file_path, index_col=0)  


def price_equation(h_D, P_d, sigma, r_f, is_stablecoin):
    """
    Calculate the price using a modified Black-Scholes equation, adjusted for debt contract

    Parameters:
        h_D (float): The variable to solve for.
        P_d (float): Observed price of the asset.
        sigma (float): Volatility of the asset (standard deviation of log returns).
        r_f (float): Risk-free rate for the period.
        is_stablecoin (bool): Whether the asset is a stablecoin (True) or not (False).

    Returns:
        float: The adjusted or unadjusted price difference (P_hat - P_d).
    """
    N_h = norm.cdf(h_D)
    N_h_sigma = norm.cdf(h_D + sigma)

    # Calculate price from the equation
    PEx = (V_d * (1 - N_h_sigma) + (1 / (1 + r_f)) * D_d * N_h) / D_d

    if is_stablecoin:
        # Apply the PEx > 1 adjustment for stablecoins
        P_hat = 1 / PEx if PEx > 1 else PEx
    else:
        # For fiat and regular crypto, use the original price directly
        P_hat = PEx

    # Return the difference between calculated price and observed price
    return P_hat - P_d


def calculate_d_for_crypto(currency_data, risk_free_rate, initial_guess):
    """
    Calculate the d-values for cryptocurrencies like Bitcoin and Ethereum using the Nelder-Mead method.

    Parameters:
        currency_data (Series): Time series of currency prices.
        risk_free_rate (Series): Time series of risk-free rates.
        initial_guess (float): Initial guess for the solver.

    Returns:
        List[float]: Calculated d-values.
    """
    d_values = []

    # Iterate through each day starting from the 90th day
    for i in range(rolling_window, len(currency_data)):
        sigma = currency_data[i - rolling_window:i].pct_change().std()  
        P_d = currency_data.iloc[i]  
        r_f = risk_free_rate.iloc[i]  

        def price_diff(h_D):
            """Objective function for minimizing the price difference."""
            return abs(price_equation(h_D, P_d, sigma, r_f, False))

        #Nelder-Mead
        result = minimize(price_diff, initial_guess, method='nelder-mead')

        if result.success:
            d_values.append(result.x[0])
        else:
            logging.info(f"Nelder-Mead solver failed on day {i} for {currency_data.name}. Message: {result.message}")
            d_values.append(np.nan)

    # First 90 days will have NaN due to lack of data
    return [np.nan] * rolling_window + d_values


def calculate_d_for_currency(currency_data, risk_free_rate, is_stablecoin, initial_guess):
    """
    Calculate the d-values for regular currencies and stablecoins using fsolve.

    Parameters:
        currency_data (Series): Time series of currency prices.
        risk_free_rate (Series): Time series of risk-free rates.
        is_stablecoin (bool): Whether the asset is a stablecoin (True) or not (False).
        initial_guess (float): Initial guess for the solver.

    Returns:
        List[float]: Calculated d-values.
    """
    d_values = []

    # Iterate through each day starting from the 90th day
    for i in range(rolling_window, len(currency_data)):
        sigma = currency_data[i - rolling_window:i].pct_change().std() 
        P_d = currency_data.iloc[i] 
        r_f = risk_free_rate.iloc[i]  

        try:
            h_D_solution, infodict, ier, msg = fsolve(
                price_equation, initial_guess, args=(P_d, sigma, r_f, is_stablecoin), full_output=True
            )

            if ier == 1:  # Check if solver converged
                d_values.append(h_D_solution[0])
            else:
                logging.info(f"fsolve failed on day {i} for {currency_data.name}. Message: {msg}")
                d_values.append(np.nan)
        except Exception as e:
            logging.error(f"Error on day {i} for {currency_data.name}: {e}")
            d_values.append(np.nan)

    # First 90 days will have NaN due to lack of data
    return [np.nan] * rolling_window + d_values


# Main loop to calculate d-values for all currencies
d_results = pd.DataFrame(index=df.index)

# Risk-free rate (daily column for 3-month Treasury bond rates)
risk_free_rate = df['DGS3MO']

# Loop through each currency column and calculate d for each one
for currency in df.columns:
    if currency != 'DGS3MO':  
        is_stablecoin = currency not in non_stablecoins

        # Handle BTC and ETH separately with Nelder-Mead
        if currency in cryptos_to_handle_separately:
            initial_guess = 75  
            d_results[currency] = calculate_d_for_crypto(df[currency], risk_free_rate, initial_guess)
        else:
            # Use the regular solver for stablecoins and other assets
            initial_guess = 2.0  
            d_results[currency] = calculate_d_for_currency(df[currency], risk_free_rate, is_stablecoin, initial_guess)

# Save the results to a CSV file
output_file_path = input("Enter the output file path (default: './output/Official_d_data.csv'): ") or './output/Official_d_data.csv'
d_results.to_csv(output_file_path)

print("Done!")
