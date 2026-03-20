import asyncio
import re
import questionary
from playwright.async_api import async_playwright

async def interactive_scraper():
    print("\n" + "="*45)
    print("   JKPCB Live Interactive Scraper")
    print("="*45)
    
    region = await questionary.text("Enter Region (e.g., Jammu):").ask_async()
    if not region:
        print("Cancelled.")
        return
    
    district = await questionary.text("Enter District (e.g., Doda):").ask_async()
    if not district:
        print("Cancelled.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print(f"\nConnecting to JKPCB to fetch stations in {district}...")
            await page.goto("https://jkpcb.jk.gov.in/airquality.aspx", wait_until="networkidle")
            
            await page.locator("#ddregion").select_option(label=region)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(1)

            await page.locator("#dddistrict").select_option(label=district)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2) # Give the site time to load stations

            options = await page.locator("#ddstation option").all_inner_texts()
            stations = [opt.strip() for opt in options if opt.strip() != "Select"]

            if not stations:
                print(f"No stations found for '{district}'. Check your spelling and try again!")
                return

            print("\n")
            station = await questionary.select(
                "Select Station:",
                choices=stations
            ).ask_async()
            if not station: return

            year = await questionary.select(
                "Select Year:",
                choices=["2026", "2025", "2024", "2023", "2022"]
            ).ask_async()
            if not year: return

            parameter = await questionary.select(
                "Select Parameter:",
                choices=["AQI", "PM10", "PM2.5", "NO2", "SO2"]
            ).ask_async()
            if not parameter: return

            print(f"\nFetching data for {parameter} in {year}...")
            await page.locator("#ddstation").select_option(label=station)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(1)

            await page.locator("#ddyr1").select_option(label=year)
            await page.locator("#ddparam").select_option(label=parameter)

            await page.get_by_role("button", name="Show").click()
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            try:
                js_data = await page.evaluate("() => window.chartData12")
                print(f"\nSUCCESS! Data for {parameter} in {year}:")
                print("-" * 35)
                for item in js_data:
                    print(f"{item.get('country').ljust(20)} : {item.get('visits')}")
                print("-" * 35)
                
            except Exception:
                content = await page.content()
                block_match = re.search(r'var chartData12\s*=\s*\[(.*?)\];', content, re.DOTALL)
                
                if block_match:
                    raw_block = block_match.group(1)
                    data_points = re.findall(r'"country":\s*[\'"](.*?)[\'"],\s*"visits":\s*[\'"](.*?)[\'"]', raw_block)
                    
                    print(f"\nSUCCESS! Data for {parameter} in {year}:")
                    print("-" * 35)
                    for month, val in data_points:
                        print(f"{month.ljust(20)} : {val}")
                    print("-" * 35)
                else:
                    print("Could not find the chart data on the page.")

        except Exception as e:
            print("\nError: Something went wrong communicating with the site.")
            print(f"Details: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(interactive_scraper())
