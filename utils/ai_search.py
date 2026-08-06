# utils/ai_search.py

from openai import OpenAI
from config import settings
import json
import models
from sqlalchemy.orm import Session
from utils.geocoding import geocode_city
from utils.distance import distance_miles
import re

client = OpenAI(api_key=settings.openai_api_key)


def extract_filters(query: str):
    system_prompt = """
You extract structured search filters from a hotel guest's natural language request.

Respond with ONLY a JSON object, no other text, matching this exact shape:

{
  "city": "string or null",
  "max_price": number or null,
  "amenities": ["list of amenity names the guest explicitly requires"],
  "semantic_query": "a short phrase capturing any vague/subjective quality the guest cares about (e.g. 'rustic', 'good pet experience'), or null",
  "sentiment_direction": "positive" or "negative"
}

Valid amenity names (use these exact strings): has_gym, accessibility_features,
has_balcony, free_wifi, has_cribs, pet_friendly, smoke_free, has_pool, has_laundry,
free_breakfast, has_parking, air_conditioned, has_kitchen, has_spa, airport_shuttle.

Rules:
- Only include an amenity in "amenities" if the guest explicitly asked for it
  (e.g. "with a gym", "pet-friendly"). Do not guess or infer amenities from vague language.
- "semantic_query" is ONLY for vague, subjective qualities that have no matching amenity
  field (e.g. "rustic", "posh", "good experience with kids"). Never put an explicit
  amenity request into semantic_query.
- "sentiment_direction" is "negative" only if the guest is explicitly looking for bad
  experiences, complaints, or hotels to avoid (e.g. "hotels with rude staff",
  "worst reviews"). Otherwise it is "positive".
- If no city was mentioned, use null. If no price was mentioned, use null.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ],
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


def filter_hotels(db: Session, filters: dict):
    all_hotels = db.query(models.Hotel).filter(models.Hotel.is_active == True).all()

    hotels = all_hotels

    if filters.get("city"):
        location = geocode_city(filters["city"])
        if location:
            hotels = [
                h
                for h in hotels
                if h.latitude
                and h.longitude
                and distance_miles(
                    location["latitude"], location["longitude"], h.latitude, h.longitude
                )
                <= 20
            ]

    for amenity in filters.get("amenities", []):
        if hasattr(models.Hotel, amenity):
            hotels = [h for h in hotels if getattr(h, amenity) is True]

    if filters.get("max_price"):
        hotels = [
            h
            for h in hotels
            if any(r.price_per_night <= filters["max_price"] for r in h.rooms)
        ]

    return hotels


def filter_hotels_with_explanation(db, filters):
    hotels = filter_hotels(db, filters)

    if hotels:
        return hotels[:2], None
    if filters.get("max_price"):
        relaxed = dict(filters)
        relaxed["max_price"] = None
        hotels_without_price = filter_hotels(db, relaxed)
        if hotels_without_price:
            closest = hotels_without_price[0]
            cheapest_room = min(closest.rooms, key=lambda r: r.price_per_night)
            explanation = (
                f"No hotels matched your budget of ${filters['max_price']}. "
                f"The closest match is {closest.name}, which meets your other criteria "
                f"but starts at ${cheapest_room.price_per_night}/night."
            )
            return [closest], explanation

    if filters.get("amenities"):
        for amenity in filters["amenities"]:
            relaxed = dict(filters)
            relaxed["amenities"] = [a for a in filters["amenities"] if a != amenity]
            hotels_without_amenity = filter_hotels(db, relaxed)
            if hotels_without_amenity:
                explanation = (
                    f"No hotels matched all your criteria. Removing the "
                    f"'{amenity.replace('_', ' ')}' requirement, {hotels_without_amenity[0].name} "
                    f"matches everything else."
                )
                return [hotels_without_amenity[0]], explanation

    return (
        [],
        "No hotels matched your search, even with relaxed criteria. Try a different city or fewer requirements.",
    )


def generate_recommendation(query: str, hotels: list, explanation: str | None = None):
    if not hotels:
        return (
            "No hotels matched your search. Try a different city or fewer requirements."
        )

    ## build one big string of text describing each hotel, so we can hand it to the AI to read
    hotel_context = ""
    for hotel in hotels:
        review_texts = []
        for room in hotel.rooms:
            for booking in room.bookings:
                if booking.review:
                    review_texts.append(
                        f"({booking.review.review_score}/10) {booking.review.review_description}"
                    )

        hotel_context += f"""
Hotel: {hotel.name} (id: {hotel.id})
Location: {hotel.city}
Description: {hotel.description}
Amenities: {", ".join(a for a in [
    "gym" if hotel.has_gym else None,
    "pool" if hotel.has_pool else None,
    "spa" if hotel.has_spa else None,
    "pet friendly" if hotel.pet_friendly else None,
    "free breakfast" if hotel.free_breakfast else None,
    "parking" if hotel.has_parking else None,
] if a) or "none listed"}
Reviews:
{chr(10).join(review_texts[:10]) if review_texts else "No reviews yet."}
---
"""
    system_prompt = f"""
You are a helpful hotel recommendation assistant. A guest made this request:

"{query}"

{"IMPORTANT: No hotel matched every one of the guest's criteria. " + explanation + " Begin your response by clearly stating that no exact match was found, before describing the closest alternative and its specific trade-offs." if explanation else ""}

Here is information about the candidate hotel(s), including their description and real guest reviews:

{hotel_context}

Write a short, natural paragraph (3-5 sentences) recommending the best matching hotel(s)
from the candidates above. Reference specific details from the description or reviews
where relevant to justify the recommendation. If the guest's request included subjective
qualities (like "rustic" or "posh") or asked about a specific experience (like pets or
families), address whether the hotel matches based on the actual description/reviews.
If the guest was looking for negative experiences (bad reviews, complaints), focus on
that instead. Format each hotel name in brackets like [Hotel Name], with no URL, just the brackets around the name, exactly matching the hotel name as given above.
 Do not invent details not present in the description or reviews above.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
        ],
    )

    return response.choices[0].message.content


def markdown_links_to_html(text: str) -> str:
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)


def insert_hotel_links(text: str, hotels: list) -> str:
    for hotel in hotels:
        text = text.replace(
            f"[{hotel.name}]", f'<a href="/hotel_info/{hotel.id}">{hotel.name}</a>'
        )
    return text
