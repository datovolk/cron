import os
import time
import asyncio
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium_config import get_driver
from turso_python.connection import TursoConnection
from turso_python.crud import TursoCRUD

load_dotenv()


def scrape_jobs(max_jobs=100000) -> list[dict]:
    driver = get_driver()
    driver.get("https://jobs.ge/")
    time.sleep(3)

    for _ in range(5):
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        time.sleep(0.3)

    rows = driver.find_elements(By.XPATH, '//table[@id="job_list_table"]//tr')[1:]
    data = []

    for i, row in enumerate(rows):
        if i >= max_jobs:
            break
        try:
            title_el = row.find_element(By.XPATH, './/td/a[contains(@class, "vip")]')
            tds = row.find_elements(By.XPATH, './/td')

            title = title_el.text.strip()
            title_url = title_el.get_attribute("href")

            company_text = ""
            company_url = ""
            for td in tds[2:]:
                text = td.text.strip()
                links = td.find_elements(By.TAG_NAME, 'a')
                if text:
                    company_text = text
                    if links:
                        company_url = links[0].get_attribute("href")
                    break

            published = tds[-2].text
            end = tds[-1].text

            data.append({
                "position": title,
                "position_url": title_url,
                "company": company_text,
                "company_url": company_url,
                "published_date": published,
                "end_date": end,
                "date": time.strftime("%m-%d")
            })
        except:
            continue
    driver.quit()
    return data
def send_to_turso(jobs: list[dict]):
    conn = TursoConnection(
        database_url=os.getenv("TURSO_DATABASE_URL"),
        auth_token=os.getenv("TURSO_AUTH_TOKEN")
    )
    crud = TursoCRUD(conn)

    conn.execute_query("""
        CREATE TABLE IF NOT EXISTS jobs_ge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position TEXT,
            company TEXT,
            date TEXT,
            published_date TEXT,
            end_date TEXT,
            company_url TEXT,
            position_url TEXT UNIQUE
        );
    """)

    for job in jobs:
        job_data = {
            "position": {"value": job["position"], "type": "text"},
            "company": {"value": job["company"], "type": "text"},
            "date": {"value": job["date"], "type": "text"},
            "published_date": {"value": job["published_date"], "type": "text"},
            "end_date": {"value": job["end_date"], "type": "text"},
            "company_url": {"value": job["company_url"], "type": "text"},
            "position_url": {"value": job["position_url"], "type": "text"},
        }
        try:
            result = crud.create("jobs_ge", job_data)

            print(f"Uploaded: {job['position']} @ {job['company']}")
        except Exception as e:
            print(f"Skipping (dup or error): {e}")

if __name__ == "__main__":
    jobs = scrape_jobs(max_jobs=100000)
    print(f"Collected {len(jobs)} jobs locally.")
    send_to_turso(jobs)

