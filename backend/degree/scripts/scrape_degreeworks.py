from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.expected_conditions import title_contains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
import time
import requests

driver = webdriver.Chrome()
driver.get("https://degreeworks-prod-j.isc-seo.upenn.edu:9904/")
WebDriverWait(driver, timeout=100).until(title_contains("Dashboard"))

# Click "what if" button
what_if = driver.find_element(By.XPATH, '//button[@id="what-if"]')
# what_if = driver.find_element(By.ID, 'what-if')
what_if.click()

# Wait for what-if to load
time.sleep(5)

# Get section with the dropdowns
what_if_goals = driver.find_element(By.ID, "WhatIfGoals")

catalog_year = what_if_goals.find_element(By.XPATH, '//div[@id="catalogYear_label_value"]')
catalog_year.click()

print(driver.get_cookies())

catalog_year_options = driver.find_elements(By.XPATH, '//ul[@aria-labelledby="catalogYear_label_label"]/li')
# [print(option.get_attribute("outerHTML")) for option in catalog_year_options]
selected_option = catalog_year_options[0]
selected_option.click()

driver.quit()