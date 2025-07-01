# 🃏 Dragon Ball Card Data Extractor

This project is a personal endeavor born out of a genuine need as a trading card game player, Like many hobbies, getting specific data can sometimes be a manual chore. I wanted to automate the process of collecting card information each time a new set is released, particularly filtering by rarity, directly from the official card list website. This app is my solution to that very specific, yet incredibly useful, problem.

## ✨ Why I Built This

As a player, I often need quick access to card data, especially for specific rarities, to help with deck building, collection management. Manually navigating through pages and clicking on each card to check its rarity was simply too time-consuming. This tool automates that. 
The goal is enter the official website, filter and extract the needed data:
https://www.dbs-cardgame.com/fw/en/cardlist/?search=true&q=&category%5B%5D=583201&cost_min=0&cost_max=9&power_min=0&power_max=55000&combo_power_min=0&combo_power_max=10000

## 🚀 How It Works 

This application is essentially a two-phase web scraper, designed to be robust and efficient:

1. **Initial Scan (List Pages):** It first navigates through the main card list pages for a chosen expansion. During this phase, it collects basic information like the card's name, its unique code, and, crucially, the link to its individual detail page.

2. **Deep Dive (Detail Pages):** Once all the initial links are gathered, the scraper then systematically visits each individual card's detail page. This is where the magic happens for rarity! The rarity information (like 'R', 'SR', 'SCR') is only present on these specific detail pages, so the app extracts it directly from there.

3. **Data Consolidation & Filtering:** Finally, all the collected data (name, code, and rarity) is brought together. The application then filters this comprehensive list to include only the rarities I'm interested in (e.g., Rare, Super Rare, Secret Rare), before saving everything into a clean CSV file.

## 🛠️ Technologies Used

This project leverages some powerful Python libraries:

* **Python:** The core language for the application logic.

* **`requests`:** For making HTTP requests to fetch web page content.

* **`BeautifulSoup4` (with `lxml` parser):** For efficiently parsing HTML and navigating the page structure to extract specific data points.

* **`pandas`:** For powerful data manipulation, structuring the scraped data into a clean tabular format, and exporting it to CSV.

* **`re` (Regular Expressions):** For pattern matching, particularly useful in extracting card codes and names from text.




