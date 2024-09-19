from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# Set up Selenium
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

driver.get('https://tradingeconomics.com/nigeria/government-bond-yield')

time.sleep(5)

# Start hovering - scraping from graph
graph_element = driver.find_element(By.XPATH, '//*[@id="trading_chart"]/div/div[2]')
actions = ActionChains(driver)

# Data Storage
data = []

# Set the initial offset and increment for moving the mouse
x_offset = -450  # Starting from the left of the graph
y_offset = 0  
increment = 1  # To move right by

# Move and scrape the data
while True:
    try:
        actions.move_to_element_with_offset(graph_element, x_offset, y_offset).perform()

        # Pause to allow the date and value to appear
        time.sleep(0.5)

        # Scrape the displayed date
        displayed_date = driver.find_element(By.XPATH, '/html/body/form/div[5]/div/div[1]/div[3]/div[1]/div/div/div[2]/div[2]/div[4]').text
        displayed_date = pd.to_datetime(displayed_date, format='%b %d %Y')

        # Scrape the data point
        data_point_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, '/html/body/form/div[5]/div/div[1]/div[3]/div[1]/div/div/div[5]/div[1]/div[2]/span[2]/span[1]'))
        )
        data_point = data_point_element.text  

        # Append
        print(f"{displayed_date}: {data_point}")
        data.append({'date': displayed_date, 'data_point': data_point})

    except Exception as e:
        print(f"Error scraping data or no more data available: {e}")
        break  # Break if an error occurs

    # Increment the x_offset to move further along the graph
    x_offset += increment

df = pd.DataFrame(data)

df.to_csv('bond_prices.csv', index=False)

driver.quit()
