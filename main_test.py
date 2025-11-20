import json, os, csv

# Process only first 100 events from berlin.json
filename = "berlin.json"
csv_path = "outputs/berlin_test.csv"
all_events = []

json_file_path = os.path.join("events", filename)
with open(json_file_path, "r") as events_file:
    data = json.load(events_file)
    # LIMIT TO FIRST 100 EVENTS
    data = data[:100]
    total = len(data)

    for idx, event in enumerate(data, 1):
        event_id = event["event_id"]

        try:
            command = f"python event_data.py {event_id} -o temp/{event_id}.json"
            os.system(command)
            print(f"[{idx}/{total}] Scraped Event {event_id}")

            event_path = f"temp/{event_id}.json"
            if os.path.exists(event_path):
                with open(event_path, "r") as event_file:
                    event_data = json.load(event_file)
                    all_events.append(
                        {
                            "event_id": event_data.get("event_id"),
                            "area": event_data.get("area"),
                            "venue": event_data.get("venue"),
                            "address": event_data.get("address"),
                            "venue_url": event_data.get("venue_url"),
                            "latitude": event_data.get("latitude"),
                            "longitude": event_data.get("longitude"),
                            "timezone": event_data.get("timezone"),
                            "event_name": event_data.get("event_name"),
                            "event_date": event_data.get("event_date"),
                            "start_time": event_data.get("start_time"),
                            "end_time": event_data.get("end_time"),
                            "event_url": event_data.get("event_url"),
                            "poster_front": event_data.get("poster_front"),
                            "poster_back": event_data.get("poster_back"),
                            "promoters": event_data.get("promoters"),
                            "promoter_url": event_data.get("promoter_url"),
                            "artists": event_data.get("artists"),
                            "artist_url": event_data.get("artist_url"),
                            "interested": event_data.get("interested"),
                            "ticket_category": event_data.get("ticket_category"),
                            "ticket_price": event_data.get("ticket_price"),
                            "lineup": event_data.get("lineup"),
                            "minimum_age": event_data.get("minimum_age"),
                            "genre": event_data.get("genre"),
                            "information": event_data.get("information"),
                            "event_admin": event_data.get("event_admin"),
                            "website_url": event_data.get("website_url"),
                            "player_links": event_data.get("player_links"),
                            "is_festival": event_data.get("is_festival"),
                            "date_posted": event_data.get("date_posted"),
                            "date_updated": event_data.get("date_updated"),
                            "pick_blurb": event_data.get("pick_blurb"),
                            "pick_author": event_data.get("pick_author"),
                        }
                    )
            else:
                print(f"Warning: Scraped data for {event_id} does not exist.")
        except Exception as e:
            print(f"Error: {e}")
            print("Skipping...")

        # Cleanup temp file if it exists
        temp_path = f"temp/{event_id}.json"
        if os.path.exists(temp_path):
            os.remove(temp_path)

file_exists = os.path.isfile(csv_path)
with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
    fieldnames = all_events[0].keys() if all_events else []
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    writer.writeheader()
    for event in all_events:
        writer.writerow(event)

print(f"\n{'='*60}")
print(f"SUCCESS: Saved {len(all_events)} events to {csv_path}")
print(f"{'='*60}")
