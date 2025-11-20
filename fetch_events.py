import json, os

with open("locations/cities.json", "r") as cities_file:
    cities = json.load(cities_file)

for city_data in cities:
    city = city_data["name"]
    area = int(city_data["area"])
    fromDate = "2025-01-01"

    command = f"python total_events.py {area} {fromDate} -o events/{city}.json"
    os.system(command)
    print(f"|- Scraped All Events of {city} \n")
