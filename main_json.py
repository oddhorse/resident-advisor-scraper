import json, os

events_path = "events"
BATCH_SIZE = 100  # Write to JSON every 100 events to avoid memory issues

for filename in os.listdir(events_path):
    if not filename.endswith(".json"):
        continue

    output_path = f"outputs/{filename.replace('.json', '_full.json')}"
    json_file_path = os.path.join(events_path, filename)

    with open(json_file_path, "r") as events_file:
        data = json.load(events_file)
        total_events = len(data)

    all_events = []

    # Load existing progress if file exists
    if os.path.isfile(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            all_events = json.load(f)
        print(f"Resuming from {len(all_events)} already processed events")
        processed_ids = {e["event_id"] for e in all_events}
    else:
        processed_ids = set()

    for idx, event in enumerate(data, 1):
        event_id = event["event_id"]

        # Skip already processed
        if event_id in processed_ids:
            continue

        try:
            command = f"python event_data.py {event_id} -o temp/{event_id}.json"
            os.system(command)
            print(f"[{idx}/{total_events}] Scraped Event {event_id}")

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

        # Save progress every BATCH_SIZE events
        if len(all_events) % BATCH_SIZE == 0:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(all_events, f, ensure_ascii=False, indent=2)
            print(f"  → Saved progress: {len(all_events)} events")

    # Final save
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_events, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"SUCCESS: Completed processing {filename}")
    print(f"Output: {output_path} ({len(all_events)} events)")
    print(f"{'='*60}\n")
