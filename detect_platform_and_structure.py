from urllib.parse import urlparse

def detect_platform(url):
    domain = urlparse(url).netloc.lower()

    if "magicbricks" in domain:
        return "magicbricks"
    elif "housing.com" in domain:
        return "housing"
    elif "squareyards" in domain:
        return "squareyards"
    elif any(x in domain for x in [
        "nobroker.in", "propertywala.com", "commonfloor.com",
        "99acres.com", "realestateindia.com", "royalerealtorsindia.com"
    ]):
        return "universal"
    else:
        return "unknown"
