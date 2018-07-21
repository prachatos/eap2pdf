import bs4
import requests


def page_exists(uri):
    page = requests.get(uri)
    if page.status_code == 404:
        return False, ""
    else:
        html = bs4.BeautifulSoup(page.text, "lxml")
    return True, html
