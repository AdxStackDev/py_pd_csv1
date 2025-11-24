import requests
from tabulate import tabulate

NSE_URL = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
HOME_URL = "https://www.nseindia.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.nseindia.com/option-chain"
}



session = requests.Session()
session.headers.update(HEADERS)

def fetch_option_chain():
    """Fetch option chain JSON from NSE with proper session"""
    # Step 1: Visit home page to set cookies
    session.get(HOME_URL, timeout=10)

    # Step 2: Now hit the API
    resp = session.get(NSE_URL, timeout=10)
    resp.raise_for_status()
    return resp.json()

def filter_two_expiries(data):
    """Keep only two nearest expiry dates"""
    expiry_dates = data["records"]["expiryDates"][:2]   # first two expiries
    filtered = [item for item in data["records"]["data"] if item.get("expiryDate") in expiry_dates]
    return expiry_dates, filtered

def display_table(expiry_dates, filtered):
    """Show option chain in table format"""
    table = []
    for row in filtered:
        strike = row["strikePrice"]
        expiry = row["expiryDate"]

        ce_oi = row.get("CE", {}).get("openInterest", "-")
        pe_oi = row.get("PE", {}).get("openInterest", "-")

        ce_chg = row.get("CE", {}).get("changeinOpenInterest", "-")
        pe_chg = row.get("PE", {}).get("changeinOpenInterest", "-")

        table.append([expiry, strike, ce_oi, ce_chg, pe_oi, pe_chg])

    print("\nOption Chain (First 2 Expiries)")
    print(tabulate(table, headers=["Expiry", "Strike", "CE_OI", "ΔCE_OI", "PE_OI", "ΔPE_OI"], tablefmt="pretty"))

def main():
    data = fetch_option_chain()
    expiry_dates, filtered = filter_two_expiries(data)
    display_table(expiry_dates, filtered)

if __name__ == "__main__":
    main()
