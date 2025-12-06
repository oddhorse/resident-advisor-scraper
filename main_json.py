import json, os, argparse

events_path = "events"
BATCH_SIZE = 100  # Write to JSON every 100 events to avoid memory issues

# Parse command-line arguments
parser = argparse.ArgumentParser(
    description="Process RA event files and fetch full event details"
)
parser.add_argument(
    "filename",
    type=str,
    nargs="?",  # Optional argument
    help="Specific event file to process (e.g., berlin.json). If not provided, processes all files in events/"
)
args = parser.parse_args()

# Ensure required directories exist
os.makedirs("cache", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

# Determine which files to process
if args.filename:
    # Single file mode
    files_to_process = [args.filename]
else:
    # All files mode (current behavior)
    files_to_process = [f for f in os.listdir(events_path) if f.endswith(".json")]

for filename in files_to_process:

    output_path = f"outputs/{filename.replace('.json', '_full.json')}"
    json_file_path = os.path.join(events_path, filename)

    # Validate file exists
    if not os.path.exists(json_file_path):
        print(f"Error: File {json_file_path} not found")
        continue

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
