import json, os, csv

events_path = "events"
BATCH_SIZE = 100  # Write to CSV every 100 events to avoid memory issues

for filename in os.listdir(events_path):
    csv_path = f"outputs/{filename.replace('.json', '')}.csv"

    if filename.endswith(".json"):
        json_file_path = os.path.join(events_path, filename)
        with open(json_file_path, "r") as events_file:
            data = json.load(events_file)
            total_events = len(data)

            # Initialize CSV file with headers
            file_exists = os.path.isfile(csv_path)
            if not file_exists:
                with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
                    fieldnames = ["event_id", "area", "venue", "address", "venue_url",
                                  "event_name", "event_date", "start_time", "end_time", "event_url",
                                  "promoters", "promoter_url", "interested", "ticket_category",
                                  "ticket_price", "lineup", "minimum_age", "genre", "information",
                                  "event_admin", "website_url"]
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                    writer.writeheader()

            batch = []
            for idx, event in enumerate(data, 1):
                event_id = event["event_id"]

                try:
                    command = f"python event_data.py {event_id} -o temp/{event_id}.json"
                    os.system(command)
                    print(f"[{idx}/{total_events}] Scraped Event {event_id}")

                    event_path = f"temp/{event_id}.json"
                    if os.path.exists(event_path):
                        with open(event_path, "r") as event_file:
                            event_data = json.load(event_file)
                            batch.append({
                                "event_id": event_data.get("event_id"),
                                "area": event_data.get("area"),
                                "venue": event_data.get("venue"),
                                "address": event_data.get("address"),
                                "venue_url": event_data.get("venue_url"),
                                "event_name": event_data.get("event_name"),
                                "event_date": event_data.get("event_date"),
                                "start_time": event_data.get("start_time"),
                                "end_time": event_data.get("end_time"),
                                "event_url": event_data.get("event_url"),
                                "promoters": event_data.get("promoters"),
                                "promoter_url": event_data.get("promoter_url"),
                                "interested": event_data.get("interested"),
                                "ticket_category": event_data.get("ticket_category"),
                                "ticket_price": event_data.get("ticket_price"),
                                "lineup": event_data.get("lineup"),
                                "minimum_age": event_data.get("minimum_age"),
                                "genre": event_data.get("genre"),
                                "information": event_data.get("information"),
                                "event_admin": event_data.get("event_admin"),
                                "website_url": event_data.get("website_url"),
                            })
                    else:
                        print(f"Warning: Scraped data for {event_id} does not exist.")
                except Exception as e:
                    print(f"Error: {e}")
                    print("Skipping...")

                # Cleanup temp file if it exists
                temp_path = f"temp/{event_id}.json"
                if os.path.exists(temp_path):
                    os.remove(temp_path)

                # Write batch to CSV every BATCH_SIZE events
                if len(batch) >= BATCH_SIZE:
                    with open(csv_path, "a", newline="", encoding="utf-8") as csv_file:
                        fieldnames = batch[0].keys() if batch else []
                        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                        for event_row in batch:
                            writer.writerow(event_row)
                    print(f"  → Wrote batch of {len(batch)} events to CSV")
                    batch = []  # Clear batch

            # Write any remaining events in final batch
            if batch:
                with open(csv_path, "a", newline="", encoding="utf-8") as csv_file:
                    fieldnames = batch[0].keys() if batch else []
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                    for event_row in batch:
                        writer.writerow(event_row)
                print(f"  → Wrote final batch of {len(batch)} events to CSV")

    print(f"\n{'='*60}")
    print(f"SUCCESS: Completed processing {filename}")
    print(f"Output: {csv_path}")
    print(f"{'='*60}\n")
