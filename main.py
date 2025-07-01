import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re 

# --- Configuration ---
# Base URL for the card list search
BASE_URL = "https://www.dbs-cardgame.com/fw/en/cardlist/index.php" 

# Headers to mimic a web browser and avoid being blocked
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
}

# --- Functions for Scraping ---

def fetch_page(page_number: int, category_id: str, sleep_time: float = 1.0) -> BeautifulSoup | None:
    """
    Fetches a single page of the card list using a GET request with query parameters.

    Args:
        page_number (int): The page number to fetch.
        category_id (str): The category ID for the expansion (e.g., '583201' for Manga Booster 01).
        sleep_time (float): Time to wait before making the request to be polite.

    Returns:
        BeautifulSoup | None: A BeautifulSoup object of the page content, or None if an error occurs.
    """
    print(f"Fetching list page {page_number} for category {category_id}...")
    time.sleep(sleep_time) 

    params = {
        "search": "true",
        "category[]": category_id,
        "page": str(page_number),
        "cost_min": "0",
        "cost_max": "9",
        "power_min": "0",
        "power_max": "55000",
        "combo_power_min": "0",
        "combo_power_max": "10000",
    }

    try:
        response = requests.get(BASE_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'lxml')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching list page {page_number}: {e}")
        return None

def fetch_card_details(detail_url: str, sleep_time: float = 0.5) -> str | None:
    """
    Fetches a single card's detail page and extracts its rarity.

    Args:
        detail_url (str): The URL of the card's detail page.
        sleep_time (float): Time to wait before making the request.

    Returns:
        str | None: The rarity of the card (e.g., 'R', 'SR', 'SCR'), or None if not found.
    """
    print(f"  Fetching details for: {detail_url}")
    time.sleep(sleep_time)

    try:
        response = requests.get(detail_url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

        # --- Extract rarity ---
        # Rarity is in a <div class="rarity"> directly, containing the rarity text.
        rarity_div = soup.find('div', class_='rarity')
        if rarity_div:
            rarity_text = rarity_div.text.strip()
            # Validate against rarities
            if rarity_text in ["R", "SR", "SCR", "C", "UC", "PR", "L"]:
                return rarity_text
            else:
                print(f"  Warning: Found rarity div but text '{rarity_text}' is not a known rarity type.")
        else:
            print(f"  Warning: 'div' with class 'rarity' not found for {detail_url}.")
        return None # Rarity not found or not in expected format

    except requests.exceptions.RequestException as e:
        print(f"  Error fetching detail page {detail_url}: {e}")
        return None

def parse_card_list_page(soup: BeautifulSoup) -> list[dict]:
    """
    Parses a BeautifulSoup object to extract card data from the list page,
    including the detail URL for subsequent fetching.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object of the page.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents a card.
    """
    cards_data = []
    card_items = soup.find_all('li', class_='cardItem')

    if not card_items:
        print("No card items found on this page. End of results or selector issue.")
        return []

    for card_item in card_items:
        card_name = None
        card_code = None
        detail_url = None 

        img_tag = card_item.find('img')
        if img_tag:
            alt_text = img_tag.get('alt', '').strip()

            if alt_text:
                code_pattern = r'^([A-Z0-9]+(?:-[A-Z0-9]+){1,2})?\s*(.*)$'
                match = re.match(code_pattern, alt_text)

                if match:
                    potential_code = match.group(1)
                    potential_name = match.group(2).strip()

                    if potential_code:
                        card_code = potential_code
                        card_name = potential_name if potential_name else alt_text
                    else:
                        card_name = alt_text
                        card_code = None
                else:
                    card_name = alt_text
                    card_code = None

        # Extract Detail Page URL using 'data-fancybox' attribute 
        detail_link_tag = card_item.find('a', attrs={'data-fancybox': 'cards'})

        if detail_link_tag:
            detail_fragment = detail_link_tag.get('data-src')
            if detail_fragment:
                detail_url = f"https://www.dbs-cardgame.com/fw/en/cardlist/{detail_fragment}"


        cards_data.append({
            'card_name': card_name,
            'card_code': card_code,
            'detail_url': detail_url, 
        })
    return cards_data

def scrape_dbs_cards(category_id: str, rarities: list[str], output_filename: str = 'dbs_cards.csv'):
    """
    Main function to scrape all cards for a given category/expansion,
    then fetch details for rarity, and finally filter.

    Args:
        category_id (str): The category ID for the expansion (e.g., '583201' for Manga Booster 01).
        rarities (list[str]): A list of rarity codes to filter by (e.g., ['R', 'SR', 'SCR']).
        output_filename (str): The name of the CSV file to save the data to.
    """
    all_extracted_cards_from_list = []
    page_number = 1
    last_page_card_count = -1

    print(f"Starting scrape for category ID: {category_id}. Will fetch details and filter rarities: {rarities}")

    # --- Step 1: Scrape all cards from list pages to get detail URLs ---
    while True:
        soup = fetch_page(page_number, category_id)
        if soup is None:
            print(f"Failed to fetch list page {page_number}. Stopping list scrape.")
            break

        current_page_cards = parse_card_list_page(soup)

        if not current_page_cards:
            print(f"No cards found on list page {page_number}. Likely reached end of list results.")
            break

        if len(current_page_cards) == last_page_card_count and page_number > 1:
            print(f"List page {page_number} returned the same number of cards as previous. Assuming end of unique list results.")
            break

        all_extracted_cards_from_list.extend(current_page_cards)
        last_page_card_count = len(current_page_cards)
        print(f"Extracted {len(current_page_cards)} cards from list page {page_number}. Total from list: {len(all_extracted_cards_from_list)}")

        page_number += 1

    if not all_extracted_cards_from_list:
        print("No cards were extracted from the list pages. Exiting.")
        return

    # --- Step 2: Fetch details for each card to get rarity ---
    final_cards_data = []
    total_cards_to_detail = len(all_extracted_cards_from_list)
    print(f"\nFetching details for {total_cards_to_detail} cards to get rarity...")

    for i, card_info in enumerate(all_extracted_cards_from_list):
        if card_info['detail_url']:
            card_rarity = fetch_card_details(card_info['detail_url'])
            card_info['card_rarity'] = card_rarity
            final_cards_data.append(card_info)
            print(f"  Processed {i+1}/{total_cards_to_detail} cards. Rarity: {card_rarity}")
        else:
            print(f"  Skipping card {card_info.get('card_code', card_info.get('card_name', 'Unknown'))}: No detail URL found.")
            card_info['card_rarity'] = None # Ensure rarity is set to None if no detail URL
            final_cards_data.append(card_info) # Still add to list even without detail

    # --- Step 3: Filter by rarity in Pandas and save ---
    if final_cards_data:
        df = pd.DataFrame(final_cards_data)
        # Drop detail_url column before saving if not needed in final output
        df.drop(columns=['detail_url'], inplace=True, errors='ignore')
        df.drop_duplicates(subset=['card_code'], inplace=True) 

        if rarities: # Only filter if specific rarities are provided
            initial_count = len(df)
            df = df[df['card_rarity'].isin(rarities)]
            print(f"\nFiltered from {initial_count} cards to {len(df)} based on rarities: {rarities}")

        df.to_csv(output_filename, index=False, encoding='utf-8')
        print(f"\nScraping complete! Total unique cards extracted and filtered: {len(df)}")
        print(f"Data saved to {output_filename}")
    else:
        print("No cards were extracted or all were filtered out.")

# --- Main ---
if __name__ == "__main__":
    # Example usage: Scrape cards for Manga Booster 01 and filter by R, SR, SCR
    MANGA_BOOSTER_01_CATEGORY_ID = "583201"
    TARGET_RARITIES = ["R", "SR", "SCR"] # Rare, Super Rare, Secret Rare

    scrape_dbs_cards(MANGA_BOOSTER_01_CATEGORY_ID, TARGET_RARITIES, 'dbs_manga_booster_01_cards.csv')
