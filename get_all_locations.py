import requests
import json
import time

URL = "https://ra.co/graphql"
HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://ra.co/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0",
}

print("Fetching all areas by iterating through area IDs...")
print("This will query each ID until we get errors\n")

all_areas_dict = {}  # Use dict with area_id as key for deduplication
delay_between_requests = 0.1  # Small delay to be gentle on the API
consecutive_failures = 0
max_consecutive_failures = 50  # Stop after 50 consecutive failures

area_id = 0  # Start from ID 0

while consecutive_failures < max_consecutive_failures:
    area_payload = {
        "operationName": "GET_AREA_WITH_GUIDEIMAGEURL_QUERY",
        "variables": {
            "id": str(area_id)
        },
        "query": """query GET_AREA_WITH_GUIDEIMAGEURL_QUERY($id: ID, $areaUrlName: String, $countryUrlCode: String) {
  area(id: $id, areaUrlName: $areaUrlName, countryUrlCode: $countryUrlCode) {
    id
    name
    urlName
    ianaTimeZone
    blurb
    country {
      id
      name
      urlCode
    }
  }
}"""
    }

    try:
        response = requests.post(URL, headers=HEADERS, json=area_payload)
        data = response.json()

        if data.get("data") and data["data"].get("area"):
            area = data["data"]["area"]
            consecutive_failures = 0  # Reset failure counter

            all_areas_dict[area["id"]] = {
                "id": area["id"],
                "name": area["name"],
                "urlName": area["urlName"],
                "country": {
                    "name": area["country"]["name"],
                    "urlCode": area["country"]["urlCode"]
                }
            }

            print(f"ID {area_id}: {area['name']} ({area['country']['name']}) ✓")

        else:
            consecutive_failures += 1
            if consecutive_failures == 1:
                print(f"ID {area_id}: Not found (consecutive failures: {consecutive_failures})")
            elif consecutive_failures % 10 == 0:
                print(f"ID {area_id}: Not found (consecutive failures: {consecutive_failures})")

        area_id += 1
        time.sleep(delay_between_requests)

    except Exception as e:
        consecutive_failures += 1
        print(f"ID {area_id}: Error - {e} (consecutive failures: {consecutive_failures})")
        area_id += 1

if consecutive_failures >= max_consecutive_failures:
    print(f"\nStopped after {max_consecutive_failures} consecutive failures")

print(f"\nFound {len(all_areas_dict)} unique areas total")

print(f"\n{'='*80}")
print(f"Fetching complete!")
print(f"{'='*80}\n")

if all_areas_dict:
    all_areas = list(all_areas_dict.values())

    # Save complete JSON
    with open("all_locations.json", "w", encoding="utf-8") as f:
        json.dump(all_areas, f, ensure_ascii=False, indent=2)

    # Create a readable text file organized by country
    areas_by_country = {}
    for area in all_areas:
        country = area["country"]["name"]
        if country not in areas_by_country:
            areas_by_country[country] = []
        areas_by_country[country].append(area)

    with open("all_locations.txt", "w", encoding="utf-8") as f:
        f.write("="*80 + "\n")
        f.write(f"RESIDENT ADVISOR - ALL LOCATIONS ({len(all_areas)} total)\n")
        f.write("="*80 + "\n\n")

        for country in sorted(areas_by_country.keys()):
            country_code = areas_by_country[country][0]["country"]["urlCode"]
            f.write(f"\n{country.upper()} ({country_code})\n")
            f.write("-"*80 + "\n")

            for area in sorted(areas_by_country[country], key=lambda x: x["name"]):
                f.write(f"  {area['name']:<30} | ID: {area['id']:<6} | URL: {area['urlName']}\n")

    # Print summary
    print(f"{'='*80}")
    print(f"SUCCESS: Found {len(all_areas)} locations across {len(areas_by_country)} countries")
    print(f"{'='*80}")
    print(f"\nSaved to:")
    print(f"  - all_locations.json (complete JSON data)")
    print(f"  - all_locations.txt (organized by country)")
    print(f"\nCountries with areas ({len(areas_by_country)}):")
    for country in sorted(areas_by_country.keys()):
        count = len(areas_by_country[country])
        print(f"  {country}: {count} location{'s' if count != 1 else ''}")
else:
    print("No areas found!")
