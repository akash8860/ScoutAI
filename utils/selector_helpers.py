from bs4 import BeautifulSoup
from collections import Counter

def get_top_classes_from_html(html, tag="div", top_n=5):
    soup = BeautifulSoup(html, "html.parser")
    tags = soup.find_all(tag)
    classes = [cls[0] for el in tags if el.get("class") for cls in [el.get("class")]]
    most_common = Counter(classes).most_common(top_n)
    return [f".{cls}" for cls, _ in most_common]
