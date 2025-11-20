import requests, json, argparse, re, csv
from datetime import datetime

URL = "https://ra.co/graphql"
HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://ra.co/events/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0",
}

QUERY_TEMPLATE_PATH = "payloads/event.json"
DELAY = 2


class EventFetcher:
    """
    A class to fetch and print event details from RA.co
    """

    def __init__(self, event_id):
        self.event_id = event_id
        self.payload = self.generate_payload(event_id)

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

        # Extract venue location
        venue_location = event.get("venue", {}).get("location", {})
        latitude = venue_location.get("latitude", "N/A")
        longitude = venue_location.get("longitude", "N/A")

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

        # Extract timezone
        timezone = event.get("area", {}).get("ianaTimeZone", "N/A")

        data = {
            "event_id": event["id"],
            "area": event["venue"]["area"]["name"],
            "venue": event["venue"]["name"],
            "address": event.get("venue", {}).get("address") or "N/A",
            "venue_url": f"https://ra.co{event['venue'].get('contentUrl', '/')}",
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
