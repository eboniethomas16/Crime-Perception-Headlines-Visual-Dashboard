from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
import pandas as pd
import time

from power-bi-scraper import PowerBIScraper

url = "https://app.powerbi.com/view?r=eyJrIjoiYTIyMDUzYWItOGQ3ZC00NWNkLThiZjItNzk2ZmYzYTFlZGM1IiwidCI6IjFmYmQ2NWJmLTVkZWYtNGVlYS1hNjkyLWEwODljMjU1MzQ2YiIsImMiOjh9"

scraper = PowerBIScraper(url)

visuals = scraper.get_visuals()
print(visuals)


# Extract data from a specific visual
df = scraper.get_visual_data("visualContainer10")  # example ID
print(df)

# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import time

# options = Options()
# options.add_argument("--start-maximized")
# driver = webdriver.Chrome(options=options)

# url = "https://app.powerbi.com/view?r=eyJrIjoiYTIyMDUzYWItOGQ3ZC00NWNkLThiZjItNzk2ZmYzYTFlZGM1IiwidCI6IjFmYmQ2NWJmLTVkZWYtNGVlYS1hNjkyLWEwODljMjU1MzQ2YiIsImMiOjh9"
# driver.get(url)

# print("Loading dashboard...")
# time.sleep(10)

# # ---------------------------------------------------------
# # 1. Switch into the Power BI iframe
# # ---------------------------------------------------------
# iframe = WebDriverWait(driver, 30).until(
#     EC.presence_of_element_located((By.CSS_SELECTOR, "iframe"))
# )
# driver.switch_to.frame(iframe)
# print("Switched into Power BI iframe.")

# # ---------------------------------------------------------
# # 2. Click the tile using FULL XPATH
# # ---------------------------------------------------------
# full_xpath = "/html/body/div[1]/report-embed/div/div/div[2]/logo-bar/div/div/div/logo-bar-navigation/span/button[2]"

# try:
#     tile = WebDriverWait(driver, 30).until(
#         EC.element_to_be_clickable((By.XPATH, full_xpath))
#     )
#     tile.click()
#     print("Clicked the Public Perceptions by Borough tile.")

# except Exception as e:
#     print("Could not click the tile:", e)
#     driver.quit()
#     exit()

# # ---------------------------------------------------------
# # 3. Wait for borough data page to load
# # ---------------------------------------------------------
# print("Waiting for borough data page to load...")
# time.sleep(10)

# print("Ready to extract table data.")

