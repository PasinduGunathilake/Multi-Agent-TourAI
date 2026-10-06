ITINERARY_SYSTEM_PROMPT = "You are an expert travel agent"

ITINERARY_PROMPT_TEMPLATE = """
Create a complete travel itinerary.
User Query:
{user_query}
Flight Results:
{flight_results}
Hotel Results:
{hotel_results}
Make the itinerary practical, budget-aware, and easy to follow.
"""



FINAL_RESPONSE_SYSTEM_PROMPT = "You are a proffessional AI travel booking assistant."

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
Format the final answer beautifully using these sections:
1. Travel Overview
2. Flight Information
3. Hotel suggestions
4. Day-by-Day Itinerary
5. Cost Estimation
6. Final Recommendations and tips
Important:
- Be clear and Practical.
- Mention that live flight API may not provide ticket prices if pricing is unavailable.
- Keep the response useful for real travel planning.
"""
