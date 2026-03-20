import os
import asyncio
import re
import csv
from playwright.async_api import async_playwright

async def bulk_scrape_jkpcb():
    print("\n" + "="*55)
    print(" JKPCB Bulk Research Scraper")
    print("="*55)

    base_folder = "JKPCB_AirQuality_Data"
    os.makedirs(base_folder, exist_ok=True)
    print(f"Created master folder: {base_folder}/")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print("\nConnecting to JKPCB...")
            await page.goto("https://jkpcb.jk.gov.in/airquality.aspx", wait_until="networkidle", timeout=60000)
            await page.wait_for_selector("select")

            region_options = await page.locator("#ddregion option").all_inner_texts()
            regions = [r.strip() for r in region_options if r.strip() != "Select"]

            for region in regions:
                print(f"\n" + "-"*40)
                print(f"REGION: {region}")
                print("-"*40)
                
                await page.locator("#ddregion").select_option(label=region)
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)

                district_options = await page.locator("#dddistrict option").all_inner_texts()
                districts = [d.strip() for d in district_options if d.strip() != "Select"]

                for district in districts:
                    
                    print(f"\nProcessing District: {district}")
                    
                    district_folder = os.path.join(base_folder, district)
                    os.makedirs(district_folder, exist_ok=True)
                    
                    try:
                        await page.locator("#dddistrict").select_option(label=district)
                        await page.wait_for_load_state("networkidle")
                        await asyncio.sleep(2)

                        station_elements = await page.locator("#ddstation option").element_handles()
                        station_map = {}
                        for opt in station_elements:
                            text = await opt.inner_text()
                            val = await opt.get_attribute("value")
                            clean_text = text.strip()
                            if clean_text and clean_text != "Select":
                                station_map[clean_text] = val

                        if not station_map:
                            print(f"   No stations found in {district}.")
                            continue

                        for station_name, station_val in station_map.items():
                            print(f"\n   Station: {station_name}")
                            
                            station_formatted = f"{station_name} + JKPCB"
                            safe_station = station_name.replace("/", "-").replace("\\", "-")
                            csv_filename = os.path.join(district_folder, f"{district} + {safe_station} + JKPCB.csv")
                            
                            station_upper = station_name.upper()
                            if "PM10" in station_upper and "PM2.5" not in station_upper:
                                target_params = ["PM10"]
                            elif "PM2.5" in station_upper and "PM10" not in station_upper:
                                target_params = ["PM2.5"]
                            else:
                                target_params = ["PM10", "PM2.5"]
                            target_params += ["SO2", "NO2"]

                            await page.locator("#ddstation").select_option(value=station_val)
                            await page.wait_for_load_state("networkidle")
                            await asyncio.sleep(1)
                            
                            year_opts = await page.locator("#ddyr1 option").all_inner_texts()
                            years = sorted([y.strip() for y in year_opts if y.strip().isdigit()])

                            with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
                                writer = csv.writer(csv_file)
                                headers = ['Station', 'Year', 'Month'] + target_params
                                writer.writerow(headers)

                                for year in years:
                                    print(f"      {year}: ", end="")
                                    yearly_data = {} 
                                    
                                    for param in target_params:
                                        print(f"{param}...", end="", flush=True)
                                        
                                        await page.locator("#ddstation").select_option(value=station_val)
                                        await asyncio.sleep(0.5)
                                        await page.locator("#ddyr1").select_option(label=year)
                                        await page.locator("#ddparam").select_option(label=param)

                                        await page.get_by_role("button", name="Show").click()
                                        await page.wait_for_load_state("networkidle")
                                        await asyncio.sleep(2) 

                                        # Extract Data
                                        data_points = []
                                        try:
                                            js_data = await page.evaluate("chartData12")
                                            if js_data:
                                                data_points = [(item.get('country'), item.get('visits')) for item in js_data]
                                        except Exception:
                                            content = await page.content()
                                            block_match = re.search(r'var chartData12\s*=\s*\[(.*?)\];', content, re.DOTALL)
                                            if block_match:
                                                raw_block = block_match.group(1)
                                                data_points = re.findall(r'"country":\s*[\'"](.*?)[\'"],\s*"visits":\s*[\'"](.*?)[\'"]', raw_block)
                                        
                                        for month, val in data_points:
                                            if month not in yearly_data:
                                                yearly_data[month] = {}
                                            yearly_data[month][param] = val

                                    print(" Done!")
                                    
                                    if yearly_data:
                                        for month, params_dict in yearly_data.items():
                                            row = [station_formatted, year, month]
                                            for param in target_params:
                                                row.append(params_dict.get(param, "N/A"))
                                            writer.writerow(row)
                                            
                            print(f"   Saved: {csv_filename}")

                    except Exception as district_err:
                        print(f"   Error processing district {district}: {district_err}")
                        continue

            print("\n" + "="*50)
            print(" BULK SCRAPING COMPLETE! CHECK YOUR FOLDERS!")
            print("="*50)

        except Exception as e:
            print(f"\nFATAL Error: Something broke the main crawler loop.")
            print(f"Details: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(bulk_scrape_jkpcb())
