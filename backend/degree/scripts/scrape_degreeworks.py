from selenium import webdriver
from selenium.webdriver.support.expected_conditions import title_contains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
import requests
from selenium.webdriver.common.keys import Keys
import os

driver = webdriver.Chrome()

driver.get("https://degreeworks-prod-j.isc-seo.upenn.edu:9904/")

# autofill
driver.find_element(By.ID, "pennname").send_keys("aagamd")
password = os.environ.get("PENNKEY_PASSWORD")
password_field = driver.find_element(By.ID, "password")
if password is None:
    password_field.send_keys("") # focus password
else:
    password_field.send_keys(password)
    password_field.send_keys(Keys.ENTER)

WebDriverWait(driver, timeout=100).until(title_contains("Dashboard"))

cookies = driver.get_cookies()

s = requests.Session()

simple_cookies = {
    cookie["name"]: cookie["value"] for cookie in cookies
    if cookie["name"] in ["REFRESH_TOKEN", "NAME", "X-AUTH-TOKEN"]
}
s.cookies.update(simple_cookies),

s.headers.update({
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Host": "degreeworks-prod-j.isc-seo.upenn.edu:9904",
    "Origin": "https://degreeworks-prod-j.isc-seo.upenn.edu:9904",
    "Pragma": "no-cache",
    "Referer": "https://degreeworks-prod-j.isc-seo.upenn.edu:9904/worksheets/whatif",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
})

params = {
    "studentId": "71200681",
    "school": "UG",
    "degree": "BS",
    # "is-process-new": "false",
    # "audit-type": "AA",
    # "auditId": "W0001DfM",
    # "include-inprogress": "true",
    # "include-preregistered": "true",
    # "aid-term": "undefined"
}

res = s.get(
    "https://degreeworks-prod-j.isc-seo.upenn.edu:9904/api/audit/",
    params=params
)

print(res.status_code, res.text)

driver.close()