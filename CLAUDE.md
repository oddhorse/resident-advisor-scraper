# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python scraper for Resident Advisor (ra.co) electronic music events. Uses RA's GraphQL API to collect event data including venues, artists, dates, locations (lat/long), ticket info, and audio player links (Soundcloud/Mixcloud).

## Commands

**Important:** Always activate the virtual environment before running scripts. Use `source venv/bin/activate && python` rather than directly invoking `./venv/bin/python` - it works better.

```bash
# Activate virtual environment (required before running any script)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Scraping Workflow

**Step 1: Get area ID for a location**
```bash
python get_area_code.py                    # Interactive prompt for city/country
python get_all_locations.py                # Fetch all 639 RA locations worldwide
```

**Step 2: Fetch event list for an area**
```bash
python total_events.py <area_id> <start_date> [-e <end_date>] -o events/<city>.json
# Example: python total_events.py 34 2025-01-01 -e 2026-01-01 -o events/berlin.json
```

**Step 3: Enrich events with full details**
```bash
python main_json.py          # Process all files in events/ → outputs/<city>_full.json
python main_json_test.py     # Process first 100 events from one file (for testing)
python main.py               # Same as main_json but outputs CSV
```

**Single event lookup**
```bash
python event_data.py <event_id> -o output.json
```

## Architecture

### Three-Stage Pipeline

1. **Discovery** (`total_events.py`): Queries `eventListings` GraphQL endpoint with area filter and date range. Uses date chunking (3-month chunks by default) to avoid RA's 10k result limit. Outputs `events/<city>.json` with basic event IDs and dates.

2. **Detail Fetching** (`event_data.py`): Queries individual event details via GraphQL. Extracts 37 fields including lat/long, venue info, artists, player_links, ticket tiers, RA pick info, etc.

3. **Aggregation** (`main_json.py` / `main.py`): Iterates through event list, calls `event_data.py` for each, saves progress every 100 events (resumable), outputs enriched JSON or CSV.

### Key Files

- `payloads/all_events.json` - GraphQL query template for event listings
- `payloads/event.json` - GraphQL query template for single event details
- `locations/all_locations.json` - Cached list of all RA area IDs worldwide

### API Details

- Endpoint: `https://ra.co/graphql`
- No authentication required, but uses browser-like headers
- Rate limiting: 2-second delay between requests built into scrapers

### Data Fields (37 total)

Core: event_id, event_name, event_date, start_time, end_time, event_url
Location: area, venue, address, venue_url, latitude, longitude, timezone
Media: poster_front, poster_back, player_links (Soundcloud/Mixcloud)
Artists: artists, artist_url, lineup, promoters, promoter_url
Tickets: ticket_category, ticket_price, minimum_age
Metadata: genre, information, is_festival, date_posted, date_updated, pick_blurb, pick_author
