import json, os

# Process only first 100 events from a specific file
filename = "berlin.json"  # Change this to test different cities
output_path = f"outputs/{filename.replace('.json', '_full.json')}"
LIMIT = 100

json_file_path = os.path.join("events", filename)
with open(json_file_path, "r") as events_file:
    data = json.load(events_file)
    data = data[:LIMIT]  # Limit for testing
    total = len(data)

all_events = []

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
                all_events.append(event_data)
        else:
            print(f"Warning: Scraped data for {event_id} does not exist.")
    except Exception as e:
        print(f"Error: {e}")
        print("Skipping...")

    # Cleanup temp file if it exists
    temp_path = f"temp/{event_id}.json"
    if os.path.exists(temp_path):
        os.remove(temp_path)

# Save to JSON
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(all_events, f, ensure_ascii=False, indent=2)

print(f"\n{'='*60}")
print(f"SUCCESS: Saved {len(all_events)} events to {output_path}")
print(f"{'='*60}")
