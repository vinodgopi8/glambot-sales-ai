import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote

class LeadScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def get_leads(self, query="Event Planners in Chennai"):
        # Using DuckDuckGo HTML version for zero-cost scraping
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                print(f"Failed to fetch leads: {response.status_code}")
                # Fallback to dummy data if blocked
                return [
                    {"name": "Fallback: Event Planner Chennai", "location": "Chennai", "description": "Local event planner fallback."},
                    {"name": "Fallback: Wedding Studio Chennai", "location": "Chennai", "description": "Local wedding studio fallback."}
                ]
            
            soup = BeautifulSoup(response.text, "lxml")
            leads = []
            
            # DuckDuckGo HTML result blocks
            results = soup.find_all("div", class_="result")
            
            for res in results[:5]: # Get top 5 results
                title_tag = res.find("a", class_="result__a")
                snippet_tag = res.find("a", class_="result__snippet")
                
                if title_tag:
                    name = title_tag.get_text().strip()
                    link = title_tag.get("href")
                    
                    # Clean the link if it's a DDG redirect
                    if "/l/?kh=-1&uddg=" in link:
                        link = link.split("uddg=")[1].split("&")[0]
                        link = unquote(link)
                    
                    snippet = snippet_tag.get_text().strip() if snippet_tag else "No description available."
                    
                    leads.append({
                        "name": name,
                        "location": "Chennai",
                        "description": snippet,
                        "url": link
                    })
            
            return leads
        except Exception as e:
            print(f"Scraper error: {e}")
            return []
