import requests
import json
import time
import sys
import argparse
from datetime import datetime, timedelta

URL = "https://de.ra.co/graphql"
HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://de.ra.co/events/de/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0",
}

QUERY_TEMPLATE_PATH = "payloads/all_events.json"
DELAY = 2


class EventFetcher:
    """
    A class to fetch and print event details from RA.co
    Fixed version with proper date chunking to avoid 10k API limit
    """

    def __init__(self, areas, listing_date_gte, listing_date_lte=None):
        self.areas = areas
        self.listing_date_gte = listing_date_gte
        self.listing_date_lte = listing_date_lte
        self.payload = self.generate_payload(areas, listing_date_gte, listing_date_lte)

    @staticmethod
    def generate_payload(areas, listing_date_gte, listing_date_lte=None):
        """
        Generate the payload for the GraphQL request.

        :param areas: The area code to filter events.
        :param listing_date_gte: The start date for event listings (inclusive).
        :param listing_date_lte: The end date for event listings (inclusive, optional).
        :return: The generated payload.
        """
        with open(QUERY_TEMPLATE_PATH, "r") as file:
            payload = json.load(file)

        payload["variables"]["filters"]["areas"]["eq"] = areas
        payload["variables"]["filters"]["listingDate"]["gte"] = listing_date_gte

        # Add end date filter if provided
        if listing_date_lte:
            payload["variables"]["filters"]["listingDate"]["lte"] = listing_date_lte

        return payload

    def get_events(self, page_number):
        """
        Fetch events for the given page number.

        :param page_number: The page number for event listings.
        :return: A list of events and total results count.
        """
        self.payload["variables"]["page"] = page_number
        response = requests.post(URL, headers=HEADERS, json=self.payload)

        try:
            response.raise_for_status()
            data = response.json()
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"Error: {response.status_code} - {e}")
            return [], 0

        if "data" not in data:
            print(f"Error: {data}")
            return [], 0

        total_results = data["data"]["eventListings"]["totalResults"]
        events = data["data"]["eventListings"]["data"]

        return events, total_results

    def fetch_all_events(self):
        """
        Fetch all events for the configured date range.
        Uses pagination to get all pages.

        :return: A list of all events.
        """
        all_events = []
        page_number = 1
        total_results = None

        while True:
            events, total_count = self.get_events(page_number)

            if total_results is None:
                total_results = total_count
                total_pages = (total_results // 100) + 1
                print(f"  Total results: {total_results}, Pages: {total_pages}")

            if not events:
                break

            all_events.extend(events)
            print(f"  Fetched page {page_number}, got {len(events)} events (total so far: {len(all_events)})")

            # Check if we've fetched all pages
            if len(all_events) >= total_results:
                break

            page_number += 1
            time.sleep(DELAY)

        return all_events

    def save_events_to_json(self, events, output_file="events.json"):
        """
        Save events to a JSON file.

        :param events: A list of events.
        :param output_file: The output file path. (default: "events.json")
        """
        data = []
        for idx, event in enumerate(events):
            event_data = event["event"]
            data.append(
                {
                    "id": idx,
                    "date": event_data["date"],
                    "event_id": int(event_data["contentUrl"].split("/")[-1]),
                }
            )

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        print(f"\nSaved {len(data)} events to {output_file}")


def generate_date_chunks(start_date, end_date, chunk_months=1):
    """
    Generate date range chunks to avoid hitting API limits.

    :param start_date: Start date (datetime object)
    :param end_date: End date (datetime object)
    :param chunk_months: Size of each chunk in months
    :return: List of (start, end) date tuples
    """
    chunks = []
    current = start_date

    while current < end_date:
        # Calculate chunk end (either chunk_months ahead or end_date, whichever is sooner)
        chunk_end = min(
            current + timedelta(days=30 * chunk_months),  # Approximate month
            end_date
        )
        chunks.append((current, chunk_end))
        current = chunk_end + timedelta(days=1)  # Start next chunk the day after

    return chunks


def main():
    parser = argparse.ArgumentParser(
        description="Fetch events from ra.co and save them to a JSON file. "
                    "Uses date chunking to avoid API limits."
    )
    parser.add_argument("areas", type=int, help="The area code to filter events.")
    parser.add_argument(
        "start_date",
        type=str,
        help="The start date for event listings (inclusive, format: YYYY-MM-DD).",
    )
    parser.add_argument(
        "-e",
        "--end-date",
        type=str,
        default=None,
        help="The end date for event listings (optional, format: YYYY-MM-DD). "
             "If not provided, fetches until present day.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="events.json",
        help="The output file path (default: events.json).",
    )
    parser.add_argument(
        "-c",
        "--chunk-months",
        type=int,
        default=3,
        help="Size of date chunks in months (default: 3). "
             "Smaller chunks = more requests but safer for large date ranges.",
    )
    args = parser.parse_args()

    # Parse dates
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d") if args.end_date else datetime.now()

    print(f"Fetching events for area {args.areas}")
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Chunk size: {args.chunk_months} months\n")

    # Generate date chunks
    chunks = generate_date_chunks(start_date, end_date, args.chunk_months)
    print(f"Split into {len(chunks)} chunks to avoid API limits:\n")

    all_events = []

    for i, (chunk_start, chunk_end) in enumerate(chunks, 1):
        start_str = chunk_start.strftime("%Y-%m-%d")
        end_str = chunk_end.strftime("%Y-%m-%d")

        print(f"Chunk {i}/{len(chunks)}: {start_str} to {end_str}")

        # Create fetcher for this chunk
        listing_date_gte = f"{start_str}T00:00:00.000Z"
        listing_date_lte = f"{end_str}T23:59:59.999Z"

        event_fetcher = EventFetcher(args.areas, listing_date_gte, listing_date_lte)
        events = event_fetcher.fetch_all_events()

        all_events.extend(events)
        print(f"Chunk complete. Running total: {len(all_events)} events\n")

        # Small delay between chunks
        if i < len(chunks):
            time.sleep(DELAY)

    # Save all events
    print(f"\n{'='*60}")
    print(f"COMPLETE: Fetched {len(all_events)} total events")
    print(f"{'='*60}\n")

    # Create a dummy fetcher just to use the save method
    event_fetcher = EventFetcher(args.areas, "")
    event_fetcher.save_events_to_json(all_events, args.output)


if __name__ == "__main__":
    main()
