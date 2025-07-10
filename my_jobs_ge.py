import os
import time
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium_config import get_driver
from turso_python.connection import TursoConnection
from turso_python.crud import TursoCRUD

load_dotenv()


def scrape_jobs(max_jobs=30) -> list[dict]:
    driver = get_driver()
    driver.get("https://myjobs.ge/ka/vacancy?page=1")
    time.sleep(3)

    data = []
    current_page = 1

    while len(data) < max_jobs:
        containers = driver.find_elements(By.XPATH, '//div[@class="flex justify-between border-neutral-40 w-full"]')

        for container in containers:
            if len(data) >= max_jobs:
                break
            try:
                position = container.find_element(By.TAG_NAME, 'h5').text.strip()
                company = container.find_element(By.XPATH, './/div[@class="flex gap-2 pb-1"]/p').text.strip()
                date_els = container.find_elements(By.XPATH, './/div[@class="absolute inset-0 flex items-center justify-end"]/span')
                published = date_els[0].text.strip() if date_els else ""

                current_tab = driver.current_window_handle
                container.click()
                time.sleep(1.5)

                new_tabs = [tab for tab in driver.window_handles if tab != current_tab]
                if not new_tabs:
                    print("No new tab opened.")
                    continue

                driver.switch_to.window(new_tabs[0])
                position_url = driver.current_url
                driver.close()
                driver.switch_to.window(current_tab)

                data.append({
                    "position": position,
                    "position_url": position_url,
                    "company": company,
                    "company_url": "",  # Not available
                    "published_date": published,
                    "end_date": "",  # Not available
                    "date": time.strftime("%m-%d")
                })
            except Exception as e:
                print(f"Error: {e}")
                continue

        # Pagination step
        current_page += 1
        try:
            next_button = driver.find_element(By.XPATH, f'//ul[contains(@class, "react-paginate")]/li/a[text()="{current_page}"]')
            next_button.click()
            time.sleep(2)
        except:
            break  # No more pages

    driver.quit()
    return data


def send_to_turso(jobs: list[dict]):
    conn = TursoConnection(
        database_url=os.getenv("TURSO_DATABASE_URL"),
        auth_token=os.getenv("TURSO_AUTH_TOKEN")
    )
    crud = TursoCRUD(conn)

    conn.execute_query("""
        CREATE TABLE IF NOT EXISTS myjobs_ge (
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
            crud.create("myjobs_ge", job_data)
            print(f"Uploaded: {job['position']} @ {job['company']}")
        except Exception as e:
            print(f"Skipping (dup or error): {e}")


if __name__ == "__main__":
    jobs = scrape_jobs(max_jobs=30)
    print(f"Collected {len(jobs)} jobs locally.")
    send_to_turso(jobs)
