import os
import re
import time
import ast
import json
import streamlit as st
import requests

from dotenv import load_dotenv
from datetime import datetime, timedelta
from crewai import Agent, Task, Crew, LLM
from amadeus import Client, ResponseError
from crewai.tools import tool
from tabulate import tabulate

# Load env variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

# === LLM: Groq ===
llm = LLM(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# === Amadeus Setup ===
amadeus = Client(
    client_id=os.getenv("AMADEUS_CLIENT_ID"),
    client_secret=os.getenv("AMADEUS_CLIENT_SECRET"),
    hostname="test" if os.getenv("AMADEUS_ENV") == "test" else "production"
)

# === Helpers ===
def safe_llm_call(*args, max_retries=3, **kwargs):
    """Call llm.call with simple retry on rate limit-like errors."""
    for attempt in range(max_retries):
        try:
            return llm.call(*args, **kwargs)
        except Exception as e:
            s = str(e).lower()
            if "rate limit" in s or "tpm" in s or "rate_limit" in s or "ratelimit" in s or "rate_limit_exceeded" in s:
                wait = 5 * (attempt + 1)
                st.warning(f"⚠️ LLM rate limit detected, sleeping {wait}s and retrying... ({attempt+1}/{max_retries})")
                time.sleep(wait)
                continue
            raise

def extract_json_from_text(text: str):
    """Attempt to extract JSON object from an LLM reply (strip code fences etc)."""
    if not isinstance(text, str):
        return None
    # If text already starts with { or [, try direct load
    txt = text.strip()
    # Remove Markdown code fences
    txt = re.sub(r"```(?:json)?", "", txt, flags=re.IGNORECASE).strip()
    # Find first { and last } (best-effort)
    start = txt.find("{")
    end = txt.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = txt[start:end+1]
        try:
            return json.loads(candidate)
        except Exception:
            pass
    # Try to directly json.loads
    try:
        return json.loads(txt)
    except Exception:
        pass
    # Try ast.literal_eval
    try:
        return ast.literal_eval(txt)
    except Exception:
        pass
    return None

def parse_date_str(date_str: str):
    """
    Parse human date like '25th September' or '25 Sep 2025' into 'YYYY-MM-DD'.
    If year missing, pick current year or next year if that date already passed.
    """
    if not date_str:
        return None
    s = date_str.strip()
    # remove ordinals
    s = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", s, flags=re.IGNORECASE)
    s = s.replace(",", "").strip()
    now = datetime.now()
    formats = [
        "%Y-%m-%d", "%d %B %Y", "%d %b %Y", "%d %B", "%d %b",
        "%d-%m-%Y", "%d/%m/%Y", "%d %m %Y", "%Y/%m/%d"
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            # if format lacked year, add logic below
            if "%Y" not in fmt:
                dt = dt.replace(year=now.year)
                if dt.date() < now.date():
                    dt = dt.replace(year=now.year + 1)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    # Fallback: try parsing only day and month words (e.g., "25 September")
    m = re.match(r"^(\d{1,2})\s+([A-Za-z]+)$", s)
    if m:
        day = int(m.group(1))
        month_name = m.group(2)
        try:
            dt = datetime.strptime(f"{day} {month_name} {now.year}", "%d %B %Y")
        except Exception:
            try:
                dt = datetime.strptime(f"{day} {month_name} {now.year}", "%d %b %Y")
            except Exception:
                return None
        if dt.date() < now.date():
            dt = dt.replace(year=now.year + 1)
        return dt.strftime("%Y-%m-%d")
    # If the string already looks like YYYY, try to return it
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s
    return None

# Common fallback mapping for major cities worldwide
FALLBACK_IATA = {
    # Indian cities
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "bombay": "BOM",
    "mumbai": "BOM",
    "delhi": "DEL",
    "new delhi": "DEL",
    "chenai": "MAA",  # note: common typo; MAA is Chennai
    "chennai": "MAA",
    "kolkata": "CCU",
    "calcutta": "CCU",
    # International major cities
    "london": "LHR",
    "new york": "JFK",
    "new york city": "JFK",
    "nyc": "JFK",
    "paris": "CDG",
    "tokyo": "NRT",
    "dubai": "DXB",
    "singapore": "SIN",
    "bangkok": "BKK",
    "hong kong": "HKG",
    "sydney": "SYD",
    "melbourne": "MEL",
    "los angeles": "LAX",
    "san francisco": "SFO",
    "chicago": "ORD",
    "miami": "MIA",
    "amsterdam": "AMS",
    "frankfurt": "FRA",
    "madrid": "MAD",
    "barcelona": "BCN",
    "rome": "FCO",
    "milan": "MXP",
    "zurich": "ZUR",
    "istanbul": "IST",
    "doha": "DOH",
    "kuwait": "KWI",
    "riyadh": "RUH",
    "cairo": "CAI",
    "johannesburg": "JNB",
    "nairobi": "NBO",
    "lagos": "LOS",
}

def get_google_place_details(hotel_name: str, city_code: str):
    """
    Fetch hotel details from Google Places API using text search + details API.
    Returns dict with rating, photo_url, user_ratings_total, etc.
    """
    if not GOOGLE_API_KEY:
        return None

    try:
        # Step 1: Text Search
        query = f"{hotel_name} {city_code}"
        textsearch_url = f"https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {"query": query, "key": GOOGLE_API_KEY}
        resp = requests.get(textsearch_url, params=params).json()
        if not resp.get("results"):
            return None

        place = resp["results"][0]
        place_id = place.get("place_id")

        # Step 2: Place Details
        details_url = f"https://maps.googleapis.com/maps/api/place/details/json"
        fields = "name,rating,user_ratings_total,formatted_address,photos,website"
        d_params = {"place_id": place_id, "fields": fields, "key": GOOGLE_API_KEY}
        d_resp = requests.get(details_url, params=d_params).json()
        if not d_resp.get("result"):
            return None

        result = d_resp["result"]

        # Construct photo URL if available
        photo_url = None
        if "photos" in result and result["photos"]:
            ref = result["photos"][0]["photo_reference"]
            photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={ref}&key={GOOGLE_API_KEY}"

        return {
            "google_rating": result.get("rating"),
            "google_reviews": result.get("user_ratings_total"),
            "google_address": result.get("formatted_address"),
            "google_website": result.get("website"),
            "google_photo": photo_url
        }
    except Exception as e:
        st.error(f"Google Places error: {e}")
        return None

def get_iata_code(city_name: str):
    """
    Convert a city/airport name to its IATA code using Amadeus API (best effort).
    Returns None if not found.
    """
    if not city_name:
        return None
    name = city_name.strip()
    # If already 3-letter code, return uppercase
    if re.fullmatch(r"[A-Za-z]{3}", name):
        return name.upper()
    # First try Amadeus lookup
    try:
        resp = amadeus.reference_data.locations.get(keyword=name, subType=["CITY", "AIRPORT"])
        if resp and getattr(resp, "data", None):
            first = resp.data[0]
            iata = first.get("iataCode") or first.get("id")
            if iata:
                return iata.upper()
    except Exception:
        # ignore and fallback
        pass
    # fallback mapping
    key = name.lower()
    return FALLBACK_IATA.get(key)

# === Flight Search ===
def _search_flights(origin: str, destination: str, departure_date: str, currency: str = "USD", return_date: str | None = None, non_stop: bool = False):
    """Search flights using Amadeus API (plain function, safe for direct calls)."""
    try:
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": 1,
            "currencyCode": currency
        }
        if return_date:
            params["returnDate"] = return_date

        if non_stop:
            params["nonStop"] = "true"

        response = amadeus.shopping.flight_offers_search.get(**params)

        results = []
        for offer in response.data[:8]:
            out_itin = offer["itineraries"][0]
            out_segments = out_itin["segments"]
            out_first = out_segments[0]
            out_last = out_segments[-1]

            flight_data = {
                "airline": offer.get("validatingAirlineCodes", ["N/A"])[0],
                "price": offer["price"]["total"],
                "currency": offer["price"].get("currency", currency),
                "origin": out_first["departure"].get("iataCode") or origin,
                "destination": out_last["arrival"].get("iataCode") or destination,
                "departure": out_first["departure"]["at"],
                "arrival": out_last["arrival"]["at"],
                "stops": max(len(out_segments) - 1, 0),
                "duration": out_itin.get("duration")
            }

            if return_date and len(offer["itineraries"]) > 1:
                ret_itin = offer["itineraries"][1]
                ret_segments = ret_itin["segments"]
                r_first = ret_segments[0]
                r_last = ret_segments[-1]
                flight_data.update({
                    "return_origin": r_first["departure"].get("iataCode"),
                    "return_destination": r_last["arrival"].get("iataCode"),
                    "return_departure": r_first["departure"]["at"],
                    "return_arrival": r_last["arrival"]["at"],
                    "return_stops": max(len(ret_segments) - 1, 0),
                    "return_duration": ret_itin.get("duration"),
                })

            results.append(flight_data)
        return results
    except ResponseError as error:
        # Amadeus gives detailed message in response / body
        details = None
        try:
            details = error.response.body
        except:
            details = str(error)

        return {"error": f"Amadeus API error: {details}"}

# === Hotel Search ===
def _search_hotels(city_code: str, check_in: str, check_out: str, adults: int = 1, currency: str = "USD"):
    """
    Search hotels in a given city using Amadeus API and enrich with Google Places.
    """
    try:
        # Step 1: Get hotel IDs for the city
        hotel_list = amadeus.reference_data.locations.hotels.by_city.get(cityCode=city_code)
        if not hotel_list.data:
            return {"error": f"No hotels found in city {city_code}"}

        hotel_ids = [h.get("hotelId") for h in hotel_list.data if h.get("hotelId")]
        if not hotel_ids:
            return {"error": f"No valid hotel IDs found in {city_code}"}

        # Step 2: Fetch hotel offers
        response = amadeus.shopping.hotel_offers_search.get(
            hotelIds=",".join(hotel_ids[:10]),
            checkInDate=check_in,
            checkOutDate=check_out,
            adults=adults,
            currency=currency,
            roomQuantity=1,
        )

        if not response.data:
            return {"error": f"No hotel offers available for {city_code} in sandbox data."}

        results = []
        for hotel in response.data[:8]:  # take first 8 results
            hotel_info = hotel.get("hotel", {})
            offer = hotel.get("offers", [{}])[0]

            base = {
                "name": hotel_info.get("name"),
                "address": hotel_info.get("address", {}).get("lines", ["?"])[0],
                "category": hotel_info.get("hotelCategory"),
                "price": offer.get("price", {}).get("total"),
                "currency": offer.get("price", {}).get("currency", currency),
                "check_in": offer.get("checkInDate"),
                "check_out": offer.get("checkOutDate"),
                "image": (hotel_info.get("media") or [{}])[0].get("uri"),
                "amenities": hotel_info.get("amenities"),
            }

            # 🔹 Enrich with Google Places details
            g_details = get_google_place_details(hotel_info.get("name"), city_code)
            if g_details:
                base.update(g_details)  # adds google_rating, google_reviews, google_photo, etc.
                if g_details.get("google_photo"):
                    base["image"] = g_details["google_photo"]

            results.append(base)

        return results

    except ResponseError as error:
        details = None
        try:
            details = error.response.body
        except:
            details = str(error)
        return {"error": f"Amadeus API error: {details}"}

def _search_attractions(city_code: str, limit: int = 5):
    """
    Search attractions using Amadeus API.
    """
    try:
        response = amadeus.reference_data.locations.points_of_interest.get(
            latitude=0,  # Will be overridden by cityCode
            longitude=0,
            radius=50,
            categoryCode="SIGHTS",
        )
        
        results = []
        for poi in response.data[:limit]:
            results.append({
                "name": poi.get("name"),
                "category": poi.get("category"),
                "rank": poi.get("rank"),
                "geoCode": poi.get("geoCode")
            })
        
        return results
    except ResponseError as error:
        return {"error": f"Amadeus API error: {error}"}

# === CrewAI Tools ===
@tool
def search_flights(origin_city: str, destination_city: str, departure_date: str, return_date: str | None = None, currency: str = "USD") -> str:
    """
    Search for flights between two cities.
    
    Args:
        origin_city: Origin city name (e.g., 'Mumbai', 'New York')
        destination_city: Destination city name
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Return date in YYYY-MM-DD format (optional for round trip)
        currency: Currency code (default: USD)
    
    Returns:
        JSON string with flight results or error message
    """
    # Convert city names to IATA codes
    origin_iata = get_iata_code(origin_city)
    dest_iata = get_iata_code(destination_city)
    
    if not origin_iata:
        return json.dumps({"error": f"Could not find IATA code for origin city: {origin_city}"})
    if not dest_iata:
        return json.dumps({"error": f"Could not find IATA code for destination city: {destination_city}"})
    
    # Parse departure date
    dep_date = parse_date_str(departure_date)
    if not dep_date:
        return json.dumps({"error": f"Invalid departure date format: {departure_date}"})
    
    # Parse return date if provided
    ret_date = None
    if return_date:
        ret_date = parse_date_str(return_date)
        if not ret_date:
            return json.dumps({"error": f"Invalid return date format: {return_date}"})
    
    # Search flights
    results = _search_flights(origin_iata, dest_iata, dep_date, currency, ret_date)
    
    return json.dumps(results, indent=2)

@tool
def search_hotels(city: str, check_in_date: str, check_out_date: str, adults: int = 1, currency: str = "USD") -> str:
    """
    Search for hotels in a city.
    
    Args:
        city: City name (e.g., 'Mumbai', 'Paris')
        check_in_date: Check-in date in YYYY-MM-DD format
        check_out_date: Check-out date in YYYY-MM-DD format
        adults: Number of adults (default: 1)
        currency: Currency code (default: USD)
    
    Returns:
        JSON string with hotel results or error message
    """
    # Convert city name to IATA code
    city_iata = get_iata_code(city)
    if not city_iata:
        return json.dumps({"error": f"Could not find IATA code for city: {city}"})
    
    # Parse dates
    check_in = parse_date_str(check_in_date)
    check_out = parse_date_str(check_out_date)
    
    if not check_in:
        return json.dumps({"error": f"Invalid check-in date format: {check_in_date}"})
    if not check_out:
        return json.dumps({"error": f"Invalid check-out date format: {check_out_date}"})
    
    # Search hotels
    results = _search_hotels(city_iata, check_in, check_out, adults, currency)
    
    return json.dumps(results, indent=2)

@tool
def search_attractions(city: str, limit: int = 5) -> str:
    """
    Search for attractions and points of interest in a city.
    
    Args:
        city: City name (e.g., 'Mumbai', 'Paris')
        limit: Maximum number of attractions to return (default: 5)
    
    Returns:
        JSON string with attraction results or error message
    """
    # Convert city name to IATA code
    city_iata = get_iata_code(city)
    if not city_iata:
        return json.dumps({"error": f"Could not find IATA code for city: {city}"})
    
    # Search attractions
    results = _search_attractions(city_iata, limit)
    
    return json.dumps(results, indent=2)

# === CrewAI Agents ===
def create_travel_agent():
    """Create a travel planning agent."""
    return Agent(
        role="Travel Planning Specialist",
        goal="Plan comprehensive travel itineraries including flights, hotels, and attractions",
        backstory="""You are an expert travel planner who finds the best flights, hotels, 
        and attractions for travelers.""",
        tools=[search_flights, search_hotels, search_attractions],
        llm=llm,
        verbose=False,
        allow_delegation=False
    )

def create_travel_task(user_request: str):
    """Create a travel planning task based on user request."""
    return Task(
        description=f"""
        Plan a comprehensive travel itinerary based on this request: {user_request}
        
        Your response should include:
        1. Flight options with prices and details
        2. Hotel recommendations with ratings and amenities
        3. Top attractions and activities
        4. A structured itinerary suggestion
        
        Use the available tools to search for real flight, hotel, and attraction data.
        Provide specific recommendations with prices, dates, and booking details.
        """,
        expected_output="""A detailed travel plan with:
        - Flight options (departure/arrival times, prices, airlines)
        - Hotel recommendations (names, prices, ratings, amenities)
        - Attraction suggestions (names, categories, descriptions)
        - Day-by-day itinerary structure""",
        agent=create_travel_agent()
    )

# === Streamlit UI ===
def main():
    st.set_page_config(
        page_title="AI Travel Agent",
        page_icon="✈️",
        layout="wide"
    )
    
    st.title("✈️ AI Travel Agent")
    st.write("Plan your perfect trip with AI-powered travel recommendations!")
    
    # Check API keys
    if not all([
        os.getenv("GROQ_API_KEY"),
        os.getenv("AMADEUS_CLIENT_ID"),
        os.getenv("AMADEUS_CLIENT_SECRET")
    ]):
        st.error("⚠️ Missing required API keys. Please check your environment variables.")
        st.stop()
    
    # Sidebar for quick searches
    with st.sidebar:
        st.header("Quick Search")
        
        # Flight search
        st.subheader("🛫 Flights")
        origin = st.text_input("From", placeholder="Mumbai")
        destination = st.text_input("To", placeholder="Paris")
        departure = st.date_input("Departure", value=datetime.now() + timedelta(days=7))
        return_date = st.date_input("Return (optional)", value=None)
        
        if st.button("Search Flights"):
            if origin and destination:
                with st.spinner("Searching flights..."):
                    ret_str = return_date.strftime("%Y-%m-%d") if return_date else None
                    results = search_flights(origin, destination, departure.strftime("%Y-%m-%d"), ret_str)
                    st.json(results)
        
        # Hotel search
        st.subheader("🏨 Hotels")
        hotel_city = st.text_input("City", placeholder="Paris")
        check_in = st.date_input("Check-in", value=datetime.now() + timedelta(days=7))
        check_out = st.date_input("Check-out", value=datetime.now() + timedelta(days=10))
        
        if st.button("Search Hotels"):
            if hotel_city:
                with st.spinner("Searching hotels..."):
                    results = search_hotels(hotel_city, check_in.strftime("%Y-%m-%d"), check_out.strftime("%Y-%m-%d"))
                    st.json(results)
    
    # Main content area
    st.header("🤖 AI Travel Planner")
    st.write("Describe your travel plans and let our AI agent create a complete itinerary for you!")
    
    # Travel request input
    user_request = st.text_area(
        "Describe your travel plans:",
        placeholder="I want to travel from Mumbai to Paris from December 15-22, 2024. I'm looking for mid-range hotels and interested in museums and historical sites. Budget is around $2000.",
        height=100
    )
    
    if st.button("Plan My Trip", type="primary"):
        if not user_request.strip():
            st.warning("Please describe your travel plans first!")
            return
        
        with st.spinner("🤖 AI is planning your trip... This may take a few minutes."):
            try:
                # Create and execute the travel planning task
                task = create_travel_task(user_request)
                crew = Crew(
                    agents=[create_travel_agent()],
                    tasks=[task],
                    verbose=False
                )
                
                # Execute the crew
                result = crew.kickoff()
                
                # Display results
                st.success("✅ Your travel plan is ready!")
                st.markdown("## 📋 Your AI-Generated Travel Plan")
                st.markdown(str(result))
                
            except Exception as e:
                st.error(f"❌ Error planning your trip: {str(e)}")
                st.write("Please check your API keys and try again.")
    
    # Example requests
    with st.expander("💡 Example Travel Requests"):
        st.markdown("""
        **Business Trip:**
        "I need to travel from New York to London for a 3-day business trip next month. Looking for convenient flights and a business hotel near the city center."
        
        **Family Vacation:**
        "Planning a family vacation to Tokyo for 7 days in spring. We have 2 adults and 2 kids. Looking for family-friendly hotels and attractions."
        
        **Romantic Getaway:**
        "Want to plan a romantic 5-day trip to Paris for our anniversary in February. Looking for luxury hotels and romantic activities."
        
        **Budget Travel:**
        "Planning a budget backpacking trip to Thailand for 2 weeks. Looking for affordable accommodations and must-see attractions."
        """)

if __name__ == "__main__":
    main()
