# 🧠 ScoutAI

[![Sponsor ScoutAI](https://img.shields.io/badge/Sponsor-ScoutAI-brightgreen)](https://github.com/sponsors/akash8860)

💡 ScoutAI is free and open-source. If you’d like priority support or tailored scraping, check our [Subscription Plans](SUBSCRIPTIONS.md).


**ScoutAI** is an AI-enhanced, modular web scraping framework built with **FastAPI** and **Playwright**, offering a dual interface: a RESTful API backend and a Chrome extension frontend. It is purpose-built for structured data extraction from dynamic real estate websites like Housing.com, MagicBricks, and SquareYards.

> 🧩 Key Innovation: A plug-and-play scraping engine that adapts to various DOM structures, with fallback strategies and modular strategies per platform.

---

## ⚙️ Features

- 🌐 **FastAPI Backend** with fully async support
- 🧠 **Modular scraping architecture** (strategy design pattern)
- 🔁 **Handles multiple pagination styles** (scroll, load-more, numbered)
- 📤 **Chrome Extension UI** for non-technical users
- 📊 **Excel/CSV output** with auto-naming and status tracking
- 🔄 **Real-time scrape status endpoint** (optional)
- 🔐 Optional **login & session support** via middleware
- 🧩 Easily extendable to new platforms by adding strategies

---

## 🗂️ Folder Structure

```
ScoutAI/
├── app/
│   ├── api_server.py
│   ├── users.py
│   ├── batch_upload.py
│   ├── history.py
│   └── status_tracker.py
├── modules/
│   ├── Universal_web_scraper.py
│   ├── Housing_scraper.py
│   ├── Magicbrick_updated.py
│   └── Squaretest_updated.py
├── strategies/
│   ├── pagination_handler.py
│   └── instant_like_scraper.py
├── extension/
│   ├── manifest.json
│   ├── popup.html
│   ├── popup.js
│   └── icons/
├── output/
├── users.json
├── status.json
├── history.json
├── requirements.txt
└── README.md
```

---

## 🚀 How to Run (Locally)

### 1. ⚡️ Start the FastAPI server

```bash
uvicorn app.api_server:app --reload
```

### 2. 🧩 Load Chrome Extension

- Go to: `chrome://extensions`
- Enable **Developer Mode**
- Click **Load Unpacked** → select `extension/` folder

---

## 🧠 How It Works

1. User inputs a URL, city, and mode
2. The backend detects the platform and calls the right scraper
3. Scraper handles pagination, extraction, and fallback
4. Output is saved in `/output/`
5. File is available at `/download` endpoint

---

## 🧪 Platforms Supported

- ✅ Housing.com  
- ✅ MagicBricks  
- ✅ SquareYards  
- 🚧 Extendable to more

---

## 📦 API Reference

| Method | Endpoint     | Description                      |
|--------|--------------|----------------------------------|
| POST   | /scrape      | Trigger scraping                 |
| GET    | /download    | Download the latest Excel file   |
| POST   | /upload      | Upload Excel for batch scrape    |
| GET    | /status      | Get scrape status (optional)     |

---

## 🧩 Technologies Used

- FastAPI
- Playwright
- Pandas + OpenPyXL
- BeautifulSoup / Selectolax
- JavaScript (Chrome extension)

---

## 🌍 Deployment

- Render / Railway / EC2 / Docker
- For local tunneling: `ngrok http 8000`

---

## 📄 License

MIT License *(to be added)*

---

## 🙋‍♂️ Author

**Akash Sharma**  
[GitHub](https://github.com/akash8860)

---
