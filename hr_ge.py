import datetime
import time
import os

from dotenv import load_dotenv
from selenium_config import get_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from turso_python.connection import TursoConnection
from turso_python.crud import TursoCRUD

load_dotenv()

ge_months = {
    "იან": "01", "თებ": "02", "მარ": "03", "აპრ": "04",
    "მაი": "05", "ივნ": "06", "ივლ": "07", "აგვ": "08",
    "სექ": "09", "ოქტ": "10", "ნოე": "11", "დეკ": "12"
}


def parse_georgian_date(text):
    text = text.strip().replace('-', '').replace('–', '').replace('  ', ' ')
    if "დღეს" in text:
        return datetime.date.today().strftime("%m-%d")
    parts = text.split()
    if len(parts) == 2:
        day, mon = parts
        mon = ge_months.get(mon[:3], "01")
        return f"{mon}-{int(day):02d}"
    return ""


def main():
    driver = get_driver()

    connection = TursoConnection(
        database_url=os.getenv("TURSO_DATABASE_URL"),
        auth_token=os.getenv("TURSO_AUTH_TOKEN")
    )
    crud = TursoCRUD(connection)

    connection.execute_query("""
        CREATE TABLE IF NOT EXISTS hr_ge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position TEXT,
            position_url TEXT UNIQUE,
            company TEXT,
            company_url TEXT,
            published_date TEXT,
            end_date TEXT,
            date TEXT
        )
    """)

    jobs_sent = 0
    max_jobs = 30

    try:
        driver.get('https://www.hr.ge/search-posting')
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '//div[@class="paging-container"]//a[contains(@class, "item")]'))
        )
        pages = driver.find_elements(By.XPATH, '//div[@class="paging-container"]//a[contains(@class, "item")]')
        last_page = int(pages[-1].text)

        for page in range(1, last_page + 1):
            if jobs_sent >= max_jobs:
                break

            driver.get(f'https://www.hr.ge/search-posting?pg={page}')
            time.sleep(2)

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "container--without-large-size")]'))
                )
            except TimeoutException:
                continue

            jobs = driver.find_elements(By.XPATH, '//div[contains(@class, "container--without-large-size")]')

            for job in jobs:
                if jobs_sent >= max_jobs:
                    break

                try:
                    position = job.find_element(By.XPATH, './/a[contains(@class, "title-link")]')
                    position_title = position.text
                    position_url = position.get_attribute('href')

                    try:
                        company = job.find_element(By.XPATH, './/div[contains(@class, "company")]/a/div').text
                        company_url = job.find_element(By.XPATH, './/div[contains(@class, "company")]/a').get_attribute('href')
                    except:
                        try:
                            company = job.find_element(By.XPATH, './/div[contains(@class, "company")]').text
                            company_url = ''
                        except:
                            company = 'Unknown'
                            company_url = ''

                    dates = job.find_elements(By.XPATH, './/div[@class="date"]/span')
                    published_date = parse_georgian_date(dates[0].text) if dates else ""
                    end_date = parse_georgian_date(dates[-1].text) if len(dates) > 1 else ""

                    job_data = {
                        "position": {"type": "text", "value": position_title},
                        "position_url": {"type": "text", "value": position_url},
                        "company": {"type": "text", "value": company},
                        "company_url": {"type": "text", "value": company_url},
                        "published_date": {"type": "text", "value": published_date},
                        "end_date": {"type": "text", "value": end_date},
                        "date": {"type": "text", "value": datetime.date.today().strftime("%Y-%m-%d")}
                    }

                    crud.create("hr_ge", job_data)
                    jobs_sent += 1
                    print(f"Sent: {position_title} @ {company}")

                except Exception as e:
                    print(f"Error parsing job: {e}")

    finally:
        driver.quit()
        print(f"\nTotal jobs sent: {jobs_sent}")


if __name__ == "__main__":
    main()
