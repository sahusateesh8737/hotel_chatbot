# Hotel Chatbot

A conversational interface for searching and finding hotels in Indian cities using the Booking.com API.

## Features

- Natural language processing for hotel search queries
- Support for multiple Indian cities
- Real-time price and availability checking
- Date parsing for flexible booking dates
- Budget-based filtering
- Rich hotel information including:
  - Room rates and total pricing
  - Star ratings
  - User reviews and scores
  - Hotel photos
  - Booking features (e.g., free cancellation)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/sahusateesh8737/hotel_chatbot.git
cd hotel_chatbot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Update the API key in `app.py`:
```python
API_KEY = "your_rapidapi_key_here"
```

## Usage

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser and navigate to `http://localhost:3000`

3. Enter queries in natural language, for example:
   - "I need a hotel in Mumbai for March 28-30 under ₹5000"
   - "Find me a place to stay in Delhi for April 15-17 under ₹3000"

## API Requirements

- Sign up for a RapidAPI account
- Subscribe to the Booking.com API
- Replace the API key in the code with your own key

## Tech Stack

- Python 3.x
- Flask
- HTML/CSS/JavaScript
- Booking.com API (via RapidAPI)

## License

MIT License

## Author

Sateesh Sahu