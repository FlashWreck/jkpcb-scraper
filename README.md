# JKPCB Scraper

A tool to scrape and view air quality data from the [Jammu and Kashmir Pollution Control Board (JKPCB)](https://jkpcb.jk.gov.in/airquality.aspx).

## Background

The JKPCB site is built on a legacy ASP.NET Web Forms architecture that makes the data difficult to access programmatically:

- **Stateful Reloads (Postbacks):** The entire page re-renders on every dropdown change instead of using a modern API.
- **Hidden Tokens:** Massive `__VIEWSTATE` strings are used to preserve selections between reloads.
- **JavaScript Injection:** The actual data values are not in the HTML — they are injected into a JavaScript variable (`chartData12`) consumed by the AmCharts charting library.

## How It Works

- **Browser Automation:** Playwright drives a real Chromium browser, letting the site handle its own postbacks and hidden tokens.
- **Value Selection:** The underlying HTML `value` attributes of dropdowns are used directly to avoid errors from inconsistent visible text (whitespace, encoding, etc.).
- **Memory Snipping:** `page.evaluate()` pulls the `chartData12` array directly from the browser's live JavaScript memory, bypassing the need to parse the chart visually.

## Scripts

| Script | Purpose |
|---|---|
| `jkpcb.py` | Interactive, query a single station, year, and parameter |
| `jkpcb-bulk.py` | Automated, scrapes all regions, districts, stations, and years into CSV files |

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

## Output Data Structure

The bulk scraper organizes output into a nested folder hierarchy:

```
JKPCB_AirQuality_Data/
└── District_Name/
    └── District + Station + JKPCB.csv
```

Each CSV is structured for easy analysis:

| Station | Year | Month | PM10 | PM2.5 | SO2 | NO2 |
|---|---|---|---|---|---|---|
| Jammu Narwal + JKPCB | 2024 | January-2024 | 142 | 88 | 12 | 34 |

---

> **Disclaimer:** This project is intended strictly for educational and research purposes. It is not affiliated with or endorsed by JKPCB. Please use responsibly and in accordance with the website's terms of use.
