import logging.config
import os
import sys
import time
import urllib.parse
import re
import datetime

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from database import save_article, create_tables

DEFAULT_LOGGING = {
    'version': 1,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s: %(message)s',
            'datefmt': '%Y-%m-%d - %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': "standard",
            'level': 'DEBUG',
            'stream': sys.stdout
        },
    },
    'loggers': {
        __name__: {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False
        },
    }
}

logging.config.dictConfig(DEFAULT_LOGGING)
logger = logging.getLogger(__name__)

load_dotenv()

credentials = {
    'username': os.getenv('EBSCO_USERNAME'),
    'password': os.getenv('EBSCO_PASSWORD'),
}
session_id = ""


def write_last_id(last_id):
    f = open(os.path.join("out", "_last_id.txt"), "w")
    f.seek(0)
    f.write(str(last_id))
    f.truncate()
    f.close()


def read_last_id():
    last_id = None
    try:
        f = open(os.path.join("out", "_last_id.txt"), "r")
        last_id = f.read().replace('\n', '')
        logger.info("Last id is: {}".format(last_id))
    except Exception as e:
        logger.info("No last id.")
    return last_id


def get_article_field(driver, title):
    result = ""
    try:
        result = driver.find_element(By.XPATH,
            "//dt[contains(text(),'{title}')]/following-sibling::dd".format(title=title)
        ).text
    except Exception as e:
        pass
    return result


def get_publication_date_from_source(text):
    result = None
    if text:
        try:
            match = re.search(r'\d{1,2}/\d{1,2}/\d{4}', text)
            result = datetime.datetime.strptime(
                match.group(), '%m/%d/%Y').date()
        except Exception as e:
            pass
    return result


def get_article_data(driver):
    logger.info("Get article data from page: {}".format(driver.current_url))
    text = title = ""
    source = get_article_field(driver, 'Источник:')
    publication_date = get_publication_date_from_source(source)
    database = get_article_field(driver, 'База данных:')
    report = get_article_field(driver, 'Реферат:')
    try:
        paragraphs = driver.find_elements(By.CSS_SELECTOR, "p.body-paragraph")
        for p in paragraphs:
            text += " " + p.text
    except Exception as e:
        pass
    try:
        title = driver.find_element(By.CSS_SELECTOR, "h2.ft-title").text
    except Exception as e:
        pass
    if not title:
        title = driver.find_element(By.CSS_SELECTOR, "dd.citation-title").text
    return {
        "title": title,
        "source": source,
        "database": database,
        "text": text,
        "report": report,
        "publication_date": publication_date,
    }


def site_login(driver):
    logger.info("Login to {}".format(os.getenv('EBSCO_URL')))
    driver.get(os.getenv('EBSCO_URL'))

    assert "EBSCO" in driver.title

    # Login page
    elem = driver.find_element(By.NAME, "user")
    elem.send_keys(credentials.get('username'))
    elem = driver.find_element(By.NAME, "password")
    elem.send_keys(credentials.get('password'))
    elem.send_keys(Keys.RETURN)


def set_parameters(driver):
    global session_id

    logger.info("Link to Database and set parameters")
    # Link to database
    driver.find_element(By.LINK_TEXT, 'EBSCOhost Web').click()

    # Set session ID
    session_id = urllib.parse.quote(str(driver.get_cookie(
        "EHost2").get('value').split("&")[0]).replace("sid=", ""))
    logger.info("Set session ID to: {}".format(session_id))

    #  Set databases
    time.sleep(8)
    driver.find_element(By.ID, 'selectDBLink').click()
    time.sleep(8)
    driver.find_element(By.NAME, "selectAll").click()
    driver.find_element(By.NAME, "selectAll").click()
    driver.find_element(By.ID, "ctrlSelectDb_dbList_ctl08_itemCheck").click()
    driver.find_element(By.ID, "ctrlSelectDb_dbList_ctl16_itemCheck").click()
    driver.find_element(By.ID, 'btnOK').click()
    driver.find_element(By.CSS_SELECTOR, "button.dd-active").click()
    driver.find_element(By.XPATH, "//label[@for='DbTag_1_1']").click()
    # Search
    driver.find_element(By.ID, 'Searchbox1').send_keys(
        os.getenv('EBSCO_SEARCH'))
    driver.find_element(By.ID, 'SearchButton').click()


def get_article_link(number):
    global session_id
    link = "https://web.b.ebscohost.com/ehost/detail/detail?vid={}" \
           "&sid={}&bdata=Jmxhbmc9cnUmc2l0ZT1laG9zdC1saXZl".format(
               str(number), session_id)
    # "https://web.b.ebscohost.com/ehost/detail/detail?vid=0&sid=d5b24ea5-073c-4a8f-978c-3b116600887c%40sessionmgr102&bdata=Jmxhbmc9cnUmc2l0ZT1laG9zdC1saXZl#AN=127979269&db=bwh"
    # "https://web.b.ebscohost.com/ehost/detail/detail?vid=8&sid=39f9a503-842a-4e7f-897d-5b355b13185a%40pdc-v-sessmgr03&bdata=Jmxhbmc9cnUmc2l0ZT1laG9zdC1saXZl#AN=111534847&db=bwh"
    # "https://web.b.ebscohost.com/ehost/detail/detail?vid=10&sid=39f9a503-842a-4e7f-897d-5b355b13185a%40pdc-v-sessmgr03&bdata=Jmxhbmc9cnUmc2l0ZT1laG9zdC1saXZl#AN=111569111&db=bwh"
    logger.info("Generated article link: {}".format(link))
    return link


def open_article_by_number(driver, article_number):
    logger.info("Open article by number: {}".format(article_number))
    driver.execute_script(
        "__doLinkPostBack('','target~~fulltext||args~~{}','');".format(article_number))


def main():
    create_tables()

    opts = Options()
    opts.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36")
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=opts)
    site_login(driver)
    set_parameters(driver)

    # For loop results
    last_article_id = read_last_id()
    if last_article_id:
        logger.info("Open page on last article ID")
        open_article_by_number(driver, last_article_id)
    else:
        logger.info("Open first article")
        driver.find_elements(
            By.CSS_SELECTOR, "li.result-list-li a.title-link")[0].click()
        last_article_id = 1

    last_article_id = int(last_article_id)

    while True:
        error = None
        try:
            error = driver.find_element(By.ID, 'ErrorMessageLabel')
        except Exception as e:
            pass
        if error:
            logger.info("Logout page! Need to relogin.")
            time.sleep(10)
            logger.info("Re login...")
            site_login(driver)
            set_parameters(driver)
            logger.info(
                "Open page on article link ID: {}".format(last_article_id))
            open_article_by_number(driver, last_article_id)
            driver.execute_script(
                "__doLinkPostBack('','target~~fulltext||args~~{}','');".format(last_article_id))
        article_data = get_article_data(driver)
        save_article(
            ext_id=last_article_id,
            url=driver.current_url,
            title=article_data.get("title"),
            source=article_data.get("source"),
            database=article_data.get("database"),
            text=article_data.get("text"),
            report=article_data.get("report"),
            publication_date=article_data.get("publication_date"),
        )
        logger.info("Article ID processed: {}".format(last_article_id))
        write_last_id(last_article_id)
        next_btn = None
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, "input.next")
        except Exception as e:
            pass
        if next_btn:
            next_btn.click()
            last_article_id += 1
        else:
            logger.info("Break on: {}".format(driver.current_url))
            break
    logger.info("Articles number: {}".format(last_article_id))
    logger.info("Success!")

    driver.close()


if __name__ == '__main__':
    main()
