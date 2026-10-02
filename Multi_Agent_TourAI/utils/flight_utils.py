import os
import re
from functools import lru_cache #Least Recently Used Cache / Memoization - used to store the results of expensive function calls and return the cached result when the same inputs occur again. It increase execution speed
from pathlib import Path # Cross Platform (windows/linux) file path handling
from typing import Optional, Tuple, List #Type hinting - indicates expected data types for function arguments and return values (optional to run, but good for code readability and maintainability)
import yaml # YAML file parsing and loading
import airportsdata # Airport data library (for airport codes and information)
import pycountry # Country data library (for country names and codes)

# Default origin when user specifies only destination
# Default is Sri Lanka / Bandaranaike airport (CMB)
DEFAULT_ORIGIN_IATA = os.getenv("DEFAULT_ORIGIN_IATA", "CMB")

AIRPORTS = airportsdata.load("IATA") # Loads all airports with IATA codes from airportsdata library

# Load external configuration and domain mappings from YAML
CONFIG_FILE = Path(__file__).resolve().parent.parent / "config" / "config.yaml"




## ------ Configurations loading and helper function ------
# Check config.yaml file is present, if yes load it as dictionary and if not return empty dictionary {} with prevent code crash
def _load_mappings() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}
    return {}


# Load data to be used in functions - stops unneccessary reloads
# Extracts country aliases (e.g. srilanka: LK), Main airport aliases (e.g. LK: CMB) and city airport aliases (e.g. dubai: DXB) 
_mappings = _load_mappings()
COUNTRY_ALIASES = _mappings.get("country_aliases", {})
COUNTRY_AIRPORT = _mappings.get("country_airports", {})
CITY_AIRPORTS = _mappings.get("city_airports", {})
# avoiding unnecessary / NLP distract words from user query - for O(1) lookup speed and limiting tokens  
STOP_WORDS = set(_mappings.get("stop_words", [
    "flight", "flights", "ticket", "tickets", "trip",
    "travel", "traval", "plan", "complete", "days", "including", "hotel",
    "hotels", "sightseeing", "under", "budget", "info", "information",
    "to", "from", "for", "in", "at", "the", "a", "an"
]))




## ------------------Text Preprocessing and Cleanup -----------------------------
# Converts text to lowercase, removes punctuation and extra whitespace, and eliminates common stop words to improve matching accuracy
def clean_text(text: Optional[str]) -> str:
    """Cleans input text by lowercasing, stripping punctuation and stop words.
       e.g: "Flights to Dubai, under $500!" ➔ "dubai 500"
    """
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text) # removes symbols except letters, numbers and spaces
    text = re.sub(r"\s+", " ", text) # replaces multiple spaces with single space
    words = [w for w in text.split() if w not in STOP_WORDS] # removes stop words
    return " ".join(words).strip()



## -----------------------Country Name to ISO Code----------------------------------
@lru_cache(maxsize=256) # memoization cache - stores last 256 results to avoid recomputation - increases efficiency
def country_to_code(text: str) -> Optional[str]:
    """Converts a country name or alias into an ISO 3166-1 alpha-2 code.
        e.g: "Sri Lanka" -> "LK"
    """
    text_clean = clean_text(text) # Clean text function
    if not text_clean:
        return None

    if text_clean in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[text_clean]

    # Check without spaces (e.g. srilanka -> sri lanka)
    clean_no_space = text_clean.replace(" ", "")
    for alias, code in COUNTRY_ALIASES.items():
        if alias.replace(" ", "") == clean_no_space:
            return code

    try:
        country = pycountry.countries.lookup(text_clean)
        return country.alpha_2 # search exact matching from pycountry library and get ISO 2-digit country code(alpha_2)
    except LookupError:
        pass

    # fuzzy fallback - when exact matching fails, checks if Country name or partial of common name (at least 4 characters to avoid false positive)
    text_lower = text_clean.lower()
    for country in pycountry.countries:
        c_name = getattr(country, "name", "").lower()
        c_common = getattr(country, "common_name", "").lower()
        if text_lower == c_name or text_lower == c_common:
            return country.alpha_2
        if len(text_lower) >= 4 and text_lower in c_name:
            return country.alpha_2

    return None



##--------------------------Airport Heuristic Scoring Algorithm-----------------------
# check wether airport data is matched with country code - using Country code, Country name, airport country name
def airport_country_matches(airport: dict, country_code: str) -> bool:
    """Checks if an airport dictionary matches the given country alpha-2 code."""
    airport_country = str(airport.get("country", "").upper().strip())

    if airport_country == country_code:
        return True

    try:
        country = pycountry.countries.get(alpha_2=country_code)
        if country and airport_country.lower() == country.name.lower():
            return True
    except Exception:
        pass

    return False

# If country name not in COUNTRY_AIRPORT dictionary, search for the best airport in that country using airport_country_matches function and return the best airport IATA code (e.g. if user enters LK -> CMB, JP -> HND)
@lru_cache(maxsize=128)
def get_best_airport_for_country(country_code: str) -> Optional[str]:
    """Finds the primary/best international airport IATA code for a country."""
    preferred = COUNTRY_AIRPORT.get(country_code)

    if preferred and preferred in AIRPORTS:
        return preferred

    candidates = []

    for iata, airport in AIRPORTS.items():
        if not iata:
            continue

        if airport_country_matches(airport, country_code):
            name = str(airport.get("name", "")).lower()
            city = str(airport.get("city", "")).lower()

            score = 0

            # Heuristic scoring - international/capital airports are given higher priority, also checks city presence
            if "international" in name:
                score += 50
            if "intl" in name:
                score += 40
            if "capital" in name:
                score += 20
            if city:
                score += 5

            candidates.append((score, iata))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    return candidates[0][1]

## --------------------Cascading Location Resolver--------------------------
@lru_cache(maxsize=256)
def resolve_location_to_iata(location: Optional[str]) -> Optional[str]:
    """
    Converts country/city/airport/IATA string into an IATA code.

    Examples:
    Japan -> HND / NRT
    Tokyo -> HND / NRT
    Colombo (Bandaranaike) -> CMB
    Sri Lanka -> CMB
    """
    if not location:
        return None

    raw_location = location.strip()

    # Direct 3-letter IATA code
    if re.fullmatch(r"[A-Za-z]{3}", raw_location):
        code = raw_location.upper()
        if code in AIRPORTS:
            return code

    location_clean = clean_text(raw_location)

    if not location_clean:
        return None

    # City preferred airport
    if location_clean in CITY_AIRPORTS:
        return CITY_AIRPORTS[location_clean]

    # Country preferred airport
    country_code = country_to_code(location_clean)
    if country_code:
        airport = get_best_airport_for_country(country_code)
        if airport:
            return airport

    # Exact/fuzzy city match from airport db
    city_matches = []

    for iata, airport in AIRPORTS.items():
        city = str(airport.get("city", "")).lower().strip()
        name = str(airport.get("name", "")).lower().strip()

        score = 0

        if city == location_clean:
            score += 100
        elif location_clean in city:
            score += 70

        if location_clean in name:
            score += 40

        if "international" in name:
            score += 10

        if score > 0:
            city_matches.append((score, iata))

    if city_matches:
        city_matches.sort(reverse=True)
        return city_matches[0][1]

    return None

def resolve_to_iata(location: Optional[str]) -> Optional[str]:
    """Resolve a city, country, or airport string to a 3-letter IATA airport code."""
    return resolve_location_to_iata(location)

##---------------------Finding Mentions in Text--------------------------------
def find_location_mentions(query: str) -> List[str]:
    """
    Finds country or city names inside a natural language query and preserves their appearance order in the text.
    """
    q = query.lower()
    found = []

    def record_matches(names):
        for name in names:
            pattern = rf"\b{re.escape(name)}\b"
            for match in re.finditer(pattern, q):
                found.append((match.start(), name))

    record_matches(COUNTRY_ALIASES.keys())
    record_matches([c.name.lower() for c in pycountry.countries if len(c.name) >= 4])
    record_matches(CITY_AIRPORTS.keys())

    # Sort by character position in the query string
    found.sort(key=lambda x: x[0])

    # Remove duplicates while preserving position order
    unique_mentions = []
    for _, name in found:
        if name not in unique_mentions:
            unique_mentions.append(name)

    return unique_mentions


def parse_route(query: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parses a query into departure and arrival IATA codes.

    Returns:
    dep_iata, arr_iata

    Can return:
    None, None  -> global live flights
    CMB, HND    -> filtered route
    CMB, None   -> all flights from CMB
    None, HND   -> all flights to HND
    """
    q = query.strip()
    q_lower = q.lower()

    # Global / all-country check query
    global_keywords = [
        "all country",
        "all countries",
        "global flight",
        "global flights",
        "all flight",
        "all flights",
        "worldwide flight",
        "worldwide flights",
    ]

    if any(keyword in q_lower for keyword in global_keywords):
        return None, None

    # Direct IATA code route: e.g. "CMB to DXB", "cmb - dxb", "CMB -> DXB"
    iata_match = re.search(r"\b([A-Za-z]{3})\s*(?:to|->|-)\s*([A-Za-z]{3})\b", q)
    if iata_match:
        c1, c2 = iata_match.group(1).upper(), iata_match.group(2).upper()
        if c1 in AIRPORTS and c2 in AIRPORTS:
            return c1, c2

    # Direct 2+ uppercase IATA codes anywhere in query
    codes = re.findall(r"\b[A-Z]{3}\b", q)
    valid_codes = [c for c in codes if c in AIRPORTS]
    if len(valid_codes) >= 2:
        return valid_codes[0], valid_codes[1]

    # Pattern: from X to Y
    match = re.search(
        r"\bfrom\s+(.+?)\s+\bto\s+(.+?)(?:\s+(?:on|for|under|including|with|in|at)\b|[.!?]|$)",
        q_lower,
    )

    if match:
        origin_text = match.group(1)
        dest_text = match.group(2)

        dep_iata = resolve_location_to_iata(origin_text)
        arr_iata = resolve_location_to_iata(dest_text)

        return dep_iata, arr_iata

    # Pattern: "to Y from X" Pattern
    match = re.search(
        r"\bto\s+(.+?)\s+\bfrom\s+(.+?)(?:\s+(?:on|for|under|including|with|in|at)\b|[.!?]|$)",
        q_lower,
    )

    if match:
        dest_text = match.group(1)
        origin_text = match.group(2)

        dep_iata = resolve_location_to_iata(origin_text)
        arr_iata = resolve_location_to_iata(dest_text)

        return dep_iata, arr_iata

    # Location mentions in order of appearance in query
    mentions = find_location_mentions(q)

    # Pattern: flights from X (e.g. "Japan trip from SriLanka" or "flights from Sri Lanka")
    match = re.search(r"\bfrom\s+(.+?)(?:[.!?]|$)", q_lower)
    if match:
        origin_text = match.group(1)
        dep_iata = resolve_location_to_iata(origin_text)
        for mention in mentions:
            if mention not in origin_text:
                arr_iata = resolve_location_to_iata(mention)
                if arr_iata and arr_iata != dep_iata:
                    return dep_iata, arr_iata
        return dep_iata, None

    # Pattern: flights to X
    match = re.search(r"\bto\s+(.+?)(?:[.!?]|$)", q_lower)
    if match:
        dest_text = match.group(1)
        arr_iata = resolve_location_to_iata(dest_text)
        for mention in mentions:
            if mention not in dest_text:
                dep_iata = resolve_location_to_iata(mention)
                if dep_iata and dep_iata != arr_iata:
                    return dep_iata, arr_iata
        return None, arr_iata

    # Pattern: X to Y without 'from' (e.g. "Colombo to Dubai" or "Sri Lanka to Japan")
    match = re.search(r"^(.+?)\s+\bto\s+(.+?)(?:[.!?]|$)", q_lower)
    if match:
        c_orig = resolve_location_to_iata(match.group(1))
        c_dest = resolve_location_to_iata(match.group(2))
        if c_orig and c_dest:
            return c_orig, c_dest

    # Fallback: location mentions in order of appearance
    if len(mentions) >= 2:
        dep_iata = resolve_location_to_iata(mentions[0])
        arr_iata = resolve_location_to_iata(mentions[1])
        return dep_iata, arr_iata

    if len(mentions) == 1:
        arr_iata = resolve_location_to_iata(mentions[0])
        return DEFAULT_ORIGIN_IATA, arr_iata

    return None, None
