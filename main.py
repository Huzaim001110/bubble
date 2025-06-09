import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import json

def add_option(driver, value, text):
    script = """
    var select = arguments[0];
    var optionExists = false;
    for (var i = 0; i < select.options.length; i++) {
        if (select.options[i].value === arguments[1]) {
            optionExists = true;
            break;
        }
    }
    if (!optionExists) {
        var option = document.createElement("option");
        option.value = arguments[1];
        option.text = arguments[2];
        select.add(option);
    }
    """
    select_element = driver.find_element(By.ID, 'tradingBoardTable_length').find_element(By.TAG_NAME, 'select')
    driver.execute_script(script, select_element, value, text)

def send_to_bubble(record):
    url = "https://psx-37874.bubbleapps.io/version-test/api/1.1/obj/psx"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 246a39ba6e52437f2e023ddb9e0bc3e5"
    }

    payload = {
        "SYMBOL": record["SYMBOL"],
        "NAME": record["NAME"],
        "BID VOL.": record["BID VOL."],
        "BID PRICE": record["BID PRICE"],
        "OFFER PRICE": record["OFFER PRICE"],
        "OFFER VOL.": record["OFFER VOL."],
        "LDCP": record["LDCP"],
        "CHANGE": record["CHANGE"],
        "VOLUME": record["VOLUME"]
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code in [200, 201]:
        print("✅ Sent to Bubble:", payload["SYMBOL"])
    else:
        print(f"❌ Error for {payload['SYMBOL']}: {response.status_code} - {response.text}")

def scrape_data():
    print("Scraping data...")
    option = Options()
    option.add_argument('--headless')

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=option)

        driver.get('https://dps.psx.com.pk/trading-panel/')

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'tradingBoardTable_length'))
        )

        try:
            add_option(driver, '1000', '1000')
            select_element = driver.find_element(By.ID, 'tradingBoardTable_length').find_element(By.TAG_NAME, 'select')
            modelSelect = Select(select_element)
            modelSelect.select_by_value('1000')
        except Exception as e:
            print(f"Failed to add/select option: {e}")
            driver.quit()
            return

        time.sleep(2)

        table = driver.find_element(By.ID, 'tradingBoardTable')
        rows = table.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')

        print("Records found:", len(rows))

        for row in rows:
            cols = row.find_elements(By.TAG_NAME, 'td')
            if len(cols) == 9:
                record = {
                    "SYMBOL": cols[0].find_element(By.TAG_NAME, 'strong').text,
                    "NAME": cols[1].text.strip(),
                    "BID VOL.": float(cols[2].text.replace(",", "") or 0),
                    "BID PRICE": float(cols[3].text.replace(",", "") or 0),
                    "OFFER PRICE": float(cols[4].text.replace(",", "") or 0),
                    "OFFER VOL.": float(cols[5].text.replace(",", "") or 0),
                    "LDCP": float(cols[6].text.replace(",", "") or 0),
                    "CHANGE": float(cols[7].text.replace(",", "") or 0),
                    "VOLUME": float(cols[8].text.replace(",", "") or 0)
                }
                send_to_bubble(record)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_data()
