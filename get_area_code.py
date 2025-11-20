import requests
import json

print("Enter city/area name (e.g., 'berlin', 'london', 'newyork')")
city = input("City: ").strip().lower()

print("\nEnter country code (e.g., 'de', 'uk', 'us', 'fr', 'es', 'jp')")
print("Leave blank to search globally (may return first match)")
country = input("Country code (optional): ").strip().lower() or None

headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.5',
    'content-type': 'application/json',
    'origin': 'https://ra.co',
    'referer': f'https://ra.co/events/{country or ""}{"/" if country else ""}{city}',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
}

# Build GraphQL query variables
variables = {"areaUrlName": city}
if country:
    variables["countryUrlCode"] = country

payload = {
    "operationName": "GET_AREA_WITH_GUIDEIMAGEURL_QUERY",
    "variables": variables,
    "query": """query GET_AREA_WITH_GUIDEIMAGEURL_QUERY($id: ID, $areaUrlName: String, $countryUrlCode: String) {
  area(id: $id, areaUrlName: $areaUrlName, countryUrlCode: $countryUrlCode) {
    ...areaFields
    guideImageUrl
    __typename
  }
}

fragment areaFields on Area {
  id
  name
  urlName
  ianaTimeZone
  blurb
  country {
    id
    name
    urlCode
    requiresCookieConsent
    currency {
      id
      code
      exponent
      symbol
      __typename
    }
    __typename
  }
  __typename
}
"""
}

response = requests.post('https://ra.co/graphql', headers=headers, json=payload)

try:
    data = response.json()
    if data.get("data") and data["data"].get("area"):
        area = data["data"]["area"]
        print(f"\n{'='*60}")
        print(f"Area ID: {area['id']}")
        print(f"Name: {area['name']}")
        print(f"Country: {area['country']['name']} ({area['country']['urlCode'].upper()})")
        print(f"Timezone: {area['ianaTimeZone']}")
        print(f"{'='*60}")
    else:
        print(f"\nError: Area '{city}' not found")
        if country:
            print(f"Try without country code, or check spelling")
        print(f"\nAPI Response: {json.dumps(data, indent=2)}")
except Exception as e:
    print(f"\nError: {e}")
    print(f"Response: {response.text}")