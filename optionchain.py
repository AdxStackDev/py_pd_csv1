import requests
import logging
from storage import storage

NSE_OPTION_CHAIN_URL = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
NSE_HOME_URL = "https://www.nseindia.com"
STORAGE_KEY = "option_chain_state"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json",
    "Connection": "keep-alive",
    "Host": "www.nseindia.com"
}

def load_previous_data():
    """Load previous option chain data from storage (Redis or in-memory)."""
    data = storage.get_json(STORAGE_KEY)
    return data if data else {}

def save_current_data(data):
    """Save current option chain data to storage (Redis or in-memory)."""
    # Store with 24 hour expiration
    storage.set_json(STORAGE_KEY, data, ex=86400)

def fetch_raw_data():
    """Fetch raw option chain data from NSE."""
    session = requests.Session()
    session.headers.update(headers)
    try:
        # Visit home page to set cookies
        session.get(NSE_HOME_URL, timeout=10)
        # Fetch option chain data
        resp = session.get(NSE_OPTION_CHAIN_URL, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logging.error(f"Error fetching option chain: {e}")
        return None

def get_option_chain_data():
    """
    Fetch and process option chain data with difference tracking.
    Returns: (processed_rows, spot_price, atm_strike)
    """
    raw_data = fetch_raw_data()
    previous_data = load_previous_data()
    
    if not raw_data:
        return [], 0, None

    records = raw_data.get("records", {})
    spot_price = records.get("underlyingValue", 0)
    
    # The PHP script iterates over $optionChainData['filtered']['data']
    # In Python, this corresponds to raw_data['filtered']['data']
    filtered_data = raw_data.get("filtered", {}).get("data", [])
    
    if not filtered_data:
        return [], spot_price, None

    atm_strike = int(round(spot_price / 50) * 50) if spot_price else None

    processed_rows = []
    new_session_data = previous_data.copy()  # Start with existing data to preserve other strikes if needed

    for item in filtered_data:
        strike = item["strikePrice"]
        expiry = item["expiryDate"]
        
        # Extract current values
        # PHP: $data['CE']['openInterest'] etc.
        ce = item.get("CE", {})
        pe = item.get("PE", {})
        
        curr_ce = {
            "OI": ce.get("openInterest", 0),
            "ChangeInOI": ce.get("changeinOpenInterest", 0),
            "Volume": ce.get("totalTradedVolume", 0),
            "IV": ce.get("impliedVolatility", 0),
            "LTP": ce.get("lastPrice", 0)
        }
        
        curr_pe = {
            "OI": pe.get("openInterest", 0),
            "ChangeInOI": pe.get("changeinOpenInterest", 0),
            "Volume": pe.get("totalTradedVolume", 0),
            "IV": pe.get("impliedVolatility", 0),
            "LTP": pe.get("lastPrice", 0)
        }

        # Get previous values (Keyed by Strike)
        # PHP: $previousCE = $_SESSION['previousData'][$strikePrice]['CE'] ?? ...
        prev_item = previous_data.get(str(strike), {}) 
        prev_ce = prev_item.get("CE", {"OI": 0, "ChangeInOI": 0, "Volume": 0})
        prev_pe = prev_item.get("PE", {"OI": 0, "ChangeInOI": 0, "Volume": 0})

        # Calculate Diffs
        # PHP: $diffCE['OI'] = $currentCE['OI'] - $previousCE['OI']
        diff_ce = {
            "OI": curr_ce["OI"] - prev_ce.get("OI", 0),
            "ChangeInOI": curr_ce["ChangeInOI"] - prev_ce.get("ChangeInOI", 0),
            "Volume": curr_ce["Volume"] - prev_ce.get("Volume", 0)
        }
        
        diff_pe = {
            "OI": curr_pe["OI"] - prev_pe.get("OI", 0),
            "ChangeInOI": curr_pe["ChangeInOI"] - prev_pe.get("ChangeInOI", 0),
            "Volume": curr_pe["Volume"] - prev_pe.get("Volume", 0)
        }

        row_data = {
            "strikePrice": strike,
            "expiryDate": expiry,
            "CE": curr_ce,
            "PE": curr_pe,
            "diffCE": diff_ce,
            "diffPE": diff_pe
        }
        
        processed_rows.append(row_data)
        
        # Store for next session
        # PHP: $_SESSION['previousData'][$strikePrice] = ...
        new_session_data[str(strike)] = {"CE": curr_ce, "PE": curr_pe}

    # Save current data as previous data for next time
    save_current_data(new_session_data)

    return processed_rows, spot_price, atm_strike
