import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def scrape_classcentral_courses(query, pages=1):
    # Configure Chrome options
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")  # Run in headless mode

    # Path to your chromedriver (make sure it's installed and accessible)
    chromedriver_path = os.path.join(os.getcwd(), "driver", "chromedriver.exe")
    print(f"ChromeDriver path: {chromedriver_path}")
    service = Service(chromedriver_path)
    # Launch browser
    try:
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"Error launching browser in scraper: {e}")
        return {"error": f"Could not launch browser in scraper: {e}"}

    courses_data = []

    try:
        for page in range(1, int(pages) + 1):
            url = f"https://www.classcentral.com/search?q={query}&page={page}"
            driver.get(url)

            try:
                # Wait for the search results to be visible
                WebDriverWait(driver, 20).until(
                    EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "li.course-list-course"))
                )
            except TimeoutException:
                print(f"Timeout while waiting for page {page} to load in scraper.")
                continue

            # Select course elements
            courses = driver.find_elements(By.CSS_SELECTOR, "li.course-list-course")
            print(f"Found {len(courses)} courses on page {page} in scraper")

            for course in courses:
                try:
                    # Title selector
                    title_element = course.find_element(By.CSS_SELECTOR, "h2.text-1.weight-semi.line-tight.margin-bottom-xxsmall")
                    title = title_element.text.strip()

                    # Description selector
                    description_element = course.find_element(By.CSS_SELECTOR, "p.text-2.margin-bottom-xsmall a")
                    description = description_element.text.strip()

                    # Image selector
                    try:
                        image_element = course.find_element(By.CSS_SELECTOR, "img.absolute.top.left.width-100.height-100.cover.block")
                        image = image_element.get_attribute("src")
                    except NoSuchElementException:
                        image = None

                    # Scrape additional details from the ul
                    details = {}
                    details_list = course.find_elements(By.CSS_SELECTOR, "ul.margin-top-small li")
                    for item in details_list:
                        try:
                            icon_class = item.find_element(By.CSS_SELECTOR, "i").get_attribute("class")
                            text_element = item.find_element(By.CSS_SELECTOR, "span.text-3, a.text-3")
                            text = text_element.text.strip()

                            if "icon-provider" in icon_class:
                                details["provider"] = text
                            elif "icon-clock" in icon_class:
                                details["duration"] = text
                            elif "icon-calendar" in icon_class:
                                details["start_date"] = text
                            elif "icon-dollar" in icon_class:
                                details["pricing"] = text
                        except NoSuchElementException:
                            # Handle cases where the <i> tag might be missing
                            text_element = item.find_element(By.CSS_SELECTOR, "span.text-3, a.text-3")
                            text = text_element.text.strip()
                            if "On-Demand" in text or "Starts" in text:
                                details["start_date"] = text
                            elif "week" in text or "hour" in text or "day" in text:
                                details["duration"] = text
                            elif "Free" in text or "Paid" in text:
                                details["pricing"] = text

                    # Append course data to the list
                    courses_data.append({
                        "title": title,
                        "description": description,
                        "image": image,
                        "details": details
                    })

                except Exception as e:
                    print(f"Error parsing a course in scraper: {e}")
                    continue

    finally:
        if driver:
            driver.quit()

    return courses_data