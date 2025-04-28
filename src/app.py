from flask import Flask, render_template, request, jsonify
import requests
import json
import re
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables

app = Flask(__name__)

# API setup
API_HOST = os.getenv('RAPIDAPI_HOST')
API_KEY = os.getenv('RAPIDAPI_KEY')
HEADERS = {
    'x-rapidapi-key': API_KEY,
    'x-rapidapi-host': API_HOST
}

# Expanded list of Indian cities with Booking.com dest_ids (partial list; expand as needed)
DEST_IDS = {
    "Mumbai": "-2092174",
    "Delhi": "-2106102",
    "Bangalore": "-2090174",
    "Chennai": "-2094192",
    "Kolkata": "-2097741",
    "Hyderabad": "-2098012",
    "Pune": "-2109889",
    "Ahmedabad": "-2083992",
    "Jaipur": "-2099632",
    "Goa": "-2096147",  # Note: Goa is a state, mapped to Panaji or similar
    "Lucknow": "-2104118",
    "Chandigarh": "-2091480",
    "Kochi": "-2101455",
    "Indore": "-2098908",
    "Bhopal": "-2087495",
    "Patna": "-2108911",
    "Nagpur": "-2106437",
    "Surat": "-2113537",
    "Vadodara": "-2116439",
    "Coimbatore": "-2092492",
    "Visakhapatnam": "-2117287",
    "Thiruvananthapuram": "-2114378",
    "Agra": "-2083478",
    "Varanasi": "-2116548",
    "Guwahati": "-2097172",
    "Kanpur": "-2100189",
    "Madurai": "-2104719",
    "Mysore": "-2106320",
    "Udaipur": "-2115890",
    "Amritsar": "-2084919",
    "Shimla": "-2111957",
    "Dehradun": "-2093300",
    "Jodhpur": "-2100135",
    "Ranchi": "-2110508",
    "Raipur": "-2110138",
    "Bhubaneswar": "-2087546",
    # Add more cities as needed (requires actual dest_ids from Booking.com API)
}

def parse_dates(dates):
    try:
        parts = dates.strip().split('-')
        if len(parts) != 2:
            return None, None
        check_in_part = parts[0].strip().split()
        check_out_part = parts[1].strip()
        if len(check_in_part) < 2:
            return None, None
        month, day_in = check_in_part[0], check_in_part[1]
        day_out = check_out_part
        months = {"January": "01", "February": "02", "March": "03", "April": "04", "May": "05", "June": "06",
                  "July": "07", "August": "08", "September": "09", "October": "10", "November": "11", "December": "12"}
        month_num = months.get(month.capitalize(), None)
        if not month_num:
            return None, None
        year = "2025"  # Hardcoded for simplicity
        return f"{year}-{month_num}-{day_in.zfill(2)}", f"{year}-{month_num}-{day_out.zfill(2)}"
    except Exception:
        return None, None

def search_hotels(destination, dates, budget, hotel_type=None):
    try:
        check_in, check_out = parse_dates(dates)
        if not check_in or not check_out:
            return {"error": "Invalid date format. Use 'Month Day-Day' (e.g., 'March 28-30')"}
        
        dest_key = next((key for key in DEST_IDS.keys() if key.lower() == destination.lower()), None)
        if not dest_key:
            return {"error": f"Sorry, I don't recognize '{destination}'. Try cities like {', '.join(list(DEST_IDS.keys())[:5])}... (and more!)"}
        dest_id = DEST_IDS[dest_key]
        
        url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"
        params = {
            "dest_id": dest_id,
            "search_type": "CITY",
            "arrival_date": check_in,
            "departure_date": check_out,
            "adults": "1",
            "children_age": "0,17",
            "room_qty": "1",
            "page_number": "1",
            "units": "metric",
            "temperature_unit": "c",
            "languagecode": "en-us",
            "currency_code": "INR",
            "location": "IN"
        }
        
        # Modify API parameters based on hotel_type
        if hotel_type == "luxury":
            params["sort_by"] = "class_descending"  # Sort by hotel class (stars) descending
        elif hotel_type == "budget":
            params["sort_by"] = "price"  # Sort by price ascending
        
        print(f"Making API request with params: {params}")  # Debug log
        response = requests.get(url, headers=HEADERS, params=params)
        
        # Print response status and content for debugging
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text[:500]}")  # Print first 500 chars
        
        response.raise_for_status()  # Raise exception for bad status codes
        hotels_data = response.json()
        
        if "data" not in hotels_data or "hotels" not in hotels_data["data"]:
            return {"error": f"API response format unexpected: {str(hotels_data)[:200]}"}
        
        matching_hotels = []
        nights = (datetime.strptime(check_out, "%Y-%m-%d") - datetime.strptime(check_in, "%Y-%m-%d")).days
        for hotel in hotels_data["data"]["hotels"]:
            price = float(hotel["property"]["priceBreakdown"]["grossPrice"]["value"])
            price_per_night = price / nights
            
            # Apply additional filtering based on hotel_type
            if hotel_type == "luxury" and hotel["property"]["propertyClass"] < 4:
                continue  # Skip hotels with less than 4 stars for luxury searches
            elif hotel_type == "budget" and price_per_night > 3000:
                continue  # Skip hotels more expensive than 3000 for budget searches
            
            if price_per_night <= budget:
                matching_hotels.append({
                    "name": hotel["property"]["name"],
                    "stars": hotel["property"]["propertyClass"],
                    "price_per_night": round(price_per_night, 2),
                    "total_price": price,
                    "taxes": hotel["property"]["priceBreakdown"]["excludedPrice"]["value"],
                    "review_score": hotel["property"]["reviewScore"],
                    "review_word": hotel["property"]["reviewScoreWord"],
                    "review_count": hotel["property"]["reviewCount"],
                    "photo": hotel["property"]["photoUrls"][0] if hotel["property"]["photoUrls"] else "https://via.placeholder.com/300x150?text=No+Image",
                    "features": "Free cancellation" if "Free cancellation" in hotel["accessibilityLabel"] else "N/A"
                })
        
        # Additional sorting after API results are received
        if hotel_type == "luxury":
            matching_hotels.sort(key=lambda x: (-x["stars"], x["price_per_night"]))  # Sort by stars (desc) then price (asc)
        elif hotel_type == "budget":
            matching_hotels.sort(key=lambda x: (x["price_per_night"], -x["stars"]))  # Sort by price (asc) then stars (desc)
        else:
            matching_hotels.sort(key=lambda x: (-x["stars"], x["price_per_night"]))  # Default sort
        
        return matching_hotels if matching_hotels else {"error": f"No hotels found under ₹{budget}/night for your {hotel_type if hotel_type else 'search'} criteria"}
    
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse API response: {str(e)}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}

def parse_prompt(prompt):
    prompt = prompt.lower()
    destination = None
    dates = None
    budget = 5000  # Default budget
    hotel_type = None  # Add hotel_type parameter
    
    # Check if the prompt is a single city name (common follow-up response)
    if re.match(r'^[a-z\s]+$', prompt) and prompt.strip() in [city.lower() for city in DEST_IDS.keys()]:
        # This appears to be just a city name
        destination = prompt.strip()
        # Set default dates for simple city queries (next day for 2 nights)
        today = datetime.now()
        tomorrow = today.replace(day=today.day + 1)
        day_after = today.replace(day=today.day + 2)
        month_name = tomorrow.strftime("%B")
        dates = f"{month_name} {tomorrow.day}-{day_after.day}"
        return destination, dates, budget, hotel_type, None
    
    # Extended patterns for destination extraction
    dest_patterns = [
        r'in\s+([a-z]+)(?:\s+for|\s*$)',                    # "hotels in Mumbai"
        r'place\s+to\s+stay\s+in\s+([a-z]+)',               # "place to stay in Delhi"
        r'hotels?\s+(?:in|at)\s+([a-z]+)',                  # "hotel in Bangalore" or "hotels at Bangalore"
        r'accommodations?\s+(?:in|at)\s+([a-z]+)',          # "accommodation in Chennai"
        r'rooms?\s+(?:in|at)\s+([a-z]+)',                   # "room in Kolkata"
        r'book\s+(?:a\s+)?(?:hotel|room|stay)\s+in\s+([a-z]+)',  # "book a hotel in Hyderabad"
        r'visiting\s+([a-z]+)',                             # "visiting Mumbai"
        r'traveling\s+to\s+([a-z]+)',                       # "traveling to Jaipur"
        r'trip\s+to\s+([a-z]+)',                            # "trip to Goa"
        r'(?:budget|cheap|affordable)\s+(?:stay|hotels?|accommodations?)\s+in\s+([a-z]+)',  # "Budget stay in Bangalore"
        r'(?:luxury|premium|5\s*star)\s+hotels?\s+in\s+([a-z]+)'  # "Luxury hotels in Goa"
    ]
    
    # Try each pattern until we find a match
    for pattern in dest_patterns:
        dest_match = re.search(pattern, prompt)
        if dest_match:
            destination = dest_match.group(1).strip()
            break
    
    # Extract dates - expanded to handle more formats
    date_patterns = [
        r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})\s*-\s*(\d{1,2})',  # "April 15-17"
        r'from\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:\s+to|\s*-\s*)(\d{1,2})',  # "from April 15 to 17"
        r'between\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:\s+and|\s*-\s*)(\d{1,2})',  # "between April 15 and 17"
        r'(\d{1,2})(?:st|nd|rd|th)?\s*-\s*(\d{1,2})(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december)',  # "15th-17th April"
        r'(\d{1,2})(?:st|nd|rd|th)?\s+to\s+(\d{1,2})(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december)'   # "15th to 17th April"
    ]
    
    for pattern in date_patterns:
        date_match = re.search(pattern, prompt)
        if date_match:
            groups = date_match.groups()
            # Handle different date formats
            if groups[0].lower() in ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]:
                month, day_in, day_out = groups
                dates = f"{month.capitalize()} {day_in}-{day_out}"
            else:
                day_in, day_out, month = groups
                dates = f"{month.capitalize()} {day_in}-{day_out}"
            break
    
    # Extract budget - expanded to handle more formats
    budget_patterns = [
        r'under\s*[₹]?(\d+)',                 # "under ₹3000"
        r'less\s+than\s*[₹]?(\d+)',           # "less than ₹3000"
        r'budget\s*(?:of|is)?\s*[₹]?(\d+)',   # "budget of ₹3000" or "budget is ₹3000"
        r'max(?:imum)?\s*[₹]?(\d+)',          # "max ₹3000" or "maximum ₹3000"
        r'not\s+more\s+than\s*[₹]?(\d+)',     # "not more than ₹3000"
        r'cheaper\s+than\s*[₹]?(\d+)',        # "cheaper than ₹3000"
        r'below\s*[₹]?(\d+)',                 # "below ₹3000"
        r'up\s+to\s*[₹]?(\d+)'                # "up to ₹3000"
    ]
    
    for pattern in budget_patterns:
        budget_match = re.search(pattern, prompt)
        if budget_match:
            budget = int(budget_match.group(1))
            break
    
    # Extract hotel type (budget, luxury, etc.)
    hotel_type_patterns = [
        r'(budget|cheap|affordable)\s+(?:stay|hotels?|accommodations?)',  # "Budget stay in Bangalore"
        r'(luxury|premium|5\s*star|high-end)\s+(?:stay|hotels?|accommodations?)',  # "Luxury hotels in Goa"
        r'(mid-range|standard|3\s*star)\s+(?:stay|hotels?|accommodations?)'  # "Mid-range stay"
    ]
    
    for pattern in hotel_type_patterns:
        type_match = re.search(pattern, prompt)
        if type_match:
            hotel_type = type_match.group(1).strip()
            # Adjust budget based on hotel type
            if hotel_type in ["budget", "cheap", "affordable"]:
                hotel_type = "budget"
                budget = min(budget, 3000)  # Lower budget for budget stays
            elif hotel_type in ["luxury", "premium", "5 star", "high-end"]:
                hotel_type = "luxury"
                budget = max(budget, 10000)  # Higher budget for luxury stays
            elif hotel_type in ["mid-range", "standard", "3 star"]:
                hotel_type = "mid-range"
                budget = max(min(budget, 8000), 3000)  # Mid-range budget
            break
    
    if not destination:
        return None, None, None, None, "Please tell me the city (e.g., Mumbai, Delhi)."
    if not dates:
        return None, None, None, None, "Please include dates like 'March 28-30' or '28-30 March'."
    
    return destination, dates, budget, hotel_type, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '').strip()
    if not user_message:
        return jsonify({"response": "Please say something!"})
    
    destination, dates, budget, hotel_type, error = parse_prompt(user_message)
    if error:
        return jsonify({"response": error})
    
    result = search_hotels(destination, dates, budget, hotel_type)
    if isinstance(result, dict) and "error" in result:
        return jsonify({"response": result["error"]})
    
    # Format bot response as HTML for the chat
    type_message = ""
    if hotel_type:
        type_message = f" looking for {hotel_type} options"
    
    response = f"Here are some hotels in {destination.capitalize()} for {dates}{type_message} under ₹{budget}/night:<br><ul>"
    for hotel in result[:5]:  # Limit to 5 for brevity
        response += (
            f"<li><strong>{hotel['name']}</strong><br>"
            f"Stars: {'★' * hotel['stars']}{'☆' * (5 - hotel['stars'])}<br>"
            f"Price: ₹{hotel['price_per_night']}/night (Total: ₹{hotel['total_price']} + ₹{hotel['taxes']} taxes)<br>"
            f"Rating: {hotel['review_score']} {hotel['review_word']} ({hotel['review_count']} reviews)<br>"
            f"Features: {hotel['features']}<br>"
            f"<img src='{hotel['photo']}' alt='{hotel['name']}' style='max-width: 200px; height: auto;'></li>"
        )
    response += "</ul>"
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)