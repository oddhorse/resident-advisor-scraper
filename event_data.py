import requests, json, argparse, re, csv, os
from datetime import datetime

URL = "https://ra.co/graphql"
HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://ra.co/events/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0",
}

QUERY_TEMPLATE_PATH = "payloads/event.json"
DELAY = 2
VENUE_CACHE_FILE = "cache/venues_cache.json"


def load_venue_cache():
    """Load venue cache from disk"""
    if os.path.exists(VENUE_CACHE_FILE):
        with open(VENUE_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_venue_cache(cache):
    """Save venue cache to disk"""
    os.makedirs(os.path.dirname(VENUE_CACHE_FILE), exist_ok=True)
    with open(VENUE_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def geocode_address(address, area):
    """
    Geocode an address using Nominatim (OpenStreetMap).
    Returns (latitude, longitude) or (None, None) if geocoding fails.
    """
    if not address or address == "N/A":
        return None, None

    try:
        import time
        # Nominatim requires a user agent
        headers = {
            "User-Agent": "ResidentAdvisorScraper/1.0"
        }

        # Build query - don't duplicate area if already in address
        if area and area != "N/A" and area.lower() not in address.lower():
            query = f"{address}, {area}"
        else:
            query = address

        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "format": "json",
            "limit": 1
        }

        # Nominatim requires 1 second between requests
        time.sleep(1)

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data and len(data) > 0:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            print(f"  → Geocoded: {address[:50]}... → {lat}, {lon}")
            return lat, lon

    except Exception as e:
        print(f"  → Geocoding failed for {address[:50]}...: {e}")

    return None, None


def is_coordinate_suspicious(lat, lon):
    """
    Check if coordinates seem wrong:
    - Missing/N/A values
    - Integers (too imprecise, should have decimals)
    - Zero or very close to zero
    """
    if lat == "N/A" or lon == "N/A":
        return True

    try:
        lat_float = float(lat)
        lon_float = float(lon)

        # Check if they're integers (no decimal precision)
        if lat_float == int(lat_float) or lon_float == int(lon_float):
            return True

        # Check if they're zero or very close to zero
        if abs(lat_float) < 0.01 or abs(lon_float) < 0.01:
            return True

        return False
    except (ValueError, TypeError):
        return True


class EventFetcher:
    """
    A class to fetch and print event details from RA.co
    """

    def __init__(self, event_id):
        self.event_id = event_id
        self.payload = self.generate_payload(event_id)
        self.venue_cache = load_venue_cache()

    @staticmethod
    def generate_payload(event_id):
        """
        Generate the payload for the GraphQL request.

        :param event_id: The event id for a specific party/event.
        :return: The generated payload.
        """
        with open(QUERY_TEMPLATE_PATH, "r") as file:
            payload = json.load(file)

        payload["variables"]["id"] = event_id

        return payload

    def get_event_details(self):
        response = requests.post(URL, headers=HEADERS, json=self.payload)

        try:
            response.raise_for_status()
            data = response.json()
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"Error fetching event details: {e}")
            return None

        if "data" not in data or not data["data"]["event"]:
            print("Error: Event not found or invalid data returned.")
            return None

        return data["data"]["event"]

    def save_event_to_json(self, event, output_file="default.json"):
        def convertTime(datetime_string):
            if len(datetime_string.split(":")[-1]) == 1:
                datetime_string = datetime_string[:-1] + "0"

            datetime_object = datetime.fromisoformat(datetime_string)
            formatted_time = datetime_object.strftime("%a %H:%M")

            return formatted_time

        # Extract poster URLs from images array
        images = event.get("images", [])
        flyer_front = next(
            (img["filename"] for img in images if img.get("type") == "FLYERFRONT"),
            event.get("flyerFront") or "N/A"
        )
        flyer_back = next(
            (img["filename"] for img in images if img.get("type") == "FLYERBACK"),
            event.get("flyerBack") or "N/A"
        )

        # Extract venue data - check cache first
        venue_url = f"https://ra.co{event['venue'].get('contentUrl', '/')}"

        if venue_url in self.venue_cache:
            # Use cached venue data
            cached_venue = self.venue_cache[venue_url]
            venue_name = cached_venue["venue"]
            address = cached_venue["address"]
            area = cached_venue["area"]
            latitude = cached_venue["latitude"]
            longitude = cached_venue["longitude"]
            timezone = cached_venue["timezone"]
        else:
            # Extract from API response and cache it
            venue_name = event["venue"]["name"]
            address = event.get("venue", {}).get("address") or "N/A"
            area = event["venue"]["area"]["name"]
            venue_location = event.get("venue", {}).get("location", {})
            latitude = venue_location.get("latitude", "N/A")
            longitude = venue_location.get("longitude", "N/A")
            timezone = event.get("area", {}).get("ianaTimeZone", "N/A")

            # Check if coordinates are suspicious and try geocoding
            if is_coordinate_suspicious(latitude, longitude):
                print(f"  ⚠ Suspicious coordinates for {venue_name}: {latitude}, {longitude}")
                geocoded_lat, geocoded_lon = geocode_address(address, area)

                if geocoded_lat is not None and geocoded_lon is not None:
                    latitude = geocoded_lat
                    longitude = geocoded_lon
                    print(f"  ✓ Using geocoded coordinates: {latitude}, {longitude}")
                else:
                    print(f"  ✗ Geocoding failed, keeping original: {latitude}, {longitude}")

            # Add to cache
            self.venue_cache[venue_url] = {
                "venue": venue_name,
                "address": address,
                "area": area,
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone
            }

            # Save cache to disk
            save_venue_cache(self.venue_cache)

        # Extract player links (Soundcloud/Mixcloud)
        player_links = event.get("playerLinks", [])
        player_link_urls = ", ".join(
            [f"{link.get('audioService', {}).get('name', 'Unknown')}: {link.get('sourceId', '')}"
             for link in player_links]
        ) or "N/A"

        # Extract RA Pick info
        pick = event.get("pick")
        if pick:
            pick_blurb = pick.get("blurb", "N/A")
            pick_author = pick.get("author", {}).get("name", "N/A")
        else:
            pick_blurb = "N/A"
            pick_author = "N/A"

        data = {
            "event_id": event["id"],
            "area": area,
            "venue": venue_name,
            "address": address,
            "venue_url": venue_url,
            "event_name": event["title"],
            "event_date": event["date"][:10],
            "start_time": convertTime(event["startTime"]),
            "end_time": convertTime(event["endTime"]),
            "event_url": f"https://ra.co{event['contentUrl']}",
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "poster_front": flyer_front,
            "poster_back": flyer_back,
            "promoters": ", ".join(
                [promoter["name"] for promoter in event.get("promoters", [])]
            )
            or "N/A",
            "promoter_url": ", ".join(
                [
                    f"https://ra.co{promoter['contentUrl']}"
                    for promoter in event.get("promoters", [])
                ]
            )
            or "N/A",
            "artists": ", ".join(
                [artist["name"] for artist in event.get("artists", [])]
            )
            or "N/A",
            "artist_url": ", ".join(
                [
                    f"https://ra.co{artist['contentUrl']}"
                    for artist in event.get("artists", [])
                ]
            )
            or "N/A",
            "interested": event.get("interestedCount", 0),
            "ticket_category": ", ".join(
                [ticket.get("title", "") for ticket in event.get("tickets", [])]
            )
            or "N/A",
            "ticket_price": ", ".join(
                [str(ticket.get("priceRetail", "")) for ticket in event.get("tickets", []) if ticket.get("priceRetail")]
            )
            or "N/A",
            "lineup": re.sub(r"<.*?>", "", event["lineup"]).replace("\n", ", ").strip(),
            "minimum_age": event.get("minimumAge", None) or "18",
            "genre": ", ".join([genre["name"] for genre in event["genres"]]),
            "information": event.get("content", "N/A"),
            "event_admin": event["admin"]["username"],
            "website_url": ", ".join(
                [website["url"] for website in event.get("promotionalLinks", [])]
            )
            or "N/A",
            "player_links": player_link_urls,
            "is_festival": event.get("isFestival", False),
            "date_posted": event.get("datePosted", "N/A"),
            "date_updated": event.get("dateUpdated", "N/A"),
            "pick_blurb": pick_blurb,
            "pick_author": pick_author,
        }

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch events from ra.co and save them to a JSON file."
    )
    parser.add_argument(
        "event_id", type=int, help="The event id to fetch event details"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="default.json",
        help="The output file path (default: default.json).",
    )
    args = parser.parse_args()

    event_fetcher = EventFetcher(args.event_id)
    event = event_fetcher.get_event_details()

    if event:
        event_fetcher.save_event_to_json(event, args.output)
        print(f"Event details saved to {args.output}")
    else:
        print("No event details retrieved.")


if __name__ == "__main__":
    main()
