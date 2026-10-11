# itinerary_agent
ITINERARY_SYSTEM_PROMPT = "You are an expert travel agent"

ITINERARY_PROMPT_TEMPLATE = """
Create a complete travel itinerary.
User Query:
{user_query}
Flight Results:
{flight_results}
Hotel Results:
{hotel_results}
Weather Results:
{weather_results}
Make the itinerary practical, budget-aware, and easy to follow.
"""

# flight_agent
FLIGHT_SYSTEM_PROMPT = "You are an expert travel flight planning agent"

FLIGHT_PROMPT_TEMPLATE = """
You are a travel flight expert.
User Query:
{user_query}
Airport Information:
{list_airports}
Airport Information:
{list_airlines}
Airport Information:
{list_routes}
Airport Information:
{future_flights_arrival_departure_schedule}
Airport Information:
{list_taxes}
Generate:
1.Likely departure airport
2.likely arrival airport
3.Airlines serving this route
4.typical flight duration
5.estimated airfare range
6.peak season price warnings
7.booking advice

Return consise trave; guidedance
"""



# final_agent
FINAL_RESPONSE_SYSTEM_PROMPT = "You are a professional AI travel booking assistant."

FINAL_RESPONSE_PROMPT_TEMPLATE = """
Here is the complete cost effective travel plan. Present it nicely.
User Query:
{user_query}
Flights:
{flight_results}
Hotels:
{hotel_results}
Itinerary:
{itinerary}
Weather & Climate Conditions:
{weather_results}

Format the final answer beautifully using these sections:
1. Travel Overview
2. Flight Information
3. Hotel Suggestions
4. Weather Forecast & Packing Tips
5. Day-by-Day Itinerary
6. Cost Estimation
7. Final Recommendations and Travel Tips

Important:
- Be clear and practical.
- Mention that live flight API may not provide ticket prices if pricing is unavailable.
- Use the real-time weather and forecast data to advise on what clothes to pack and best times for outdoor activities.
- Keep the response useful for real travel planning.
"""



# Weather_agent
DESTINATION_EXTRACTOR_PROMPT_TEMPLATE = """
Extract ONLY the destination city name from the travel query.
Do NOT include any punctuation, quotes, or extra words.
Query:
{query}
Destination:
"""
