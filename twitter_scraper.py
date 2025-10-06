"""
Twitter Scraper för @Ten_Bagger (Marketmate)
Hämtar trade-setups, analyser och signaler
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

class TwitterScraper:
    def __init__(self, username="Ten_Bagger"):
        self.username = username
        self.tweets = []

    def scrape_via_nitter(self):
        """
        Använder Nitter (Twitter proxy) för att hämta tweets
        """
        nitter_instances = [
            "https://nitter.net",
            "https://nitter.poast.org",
            "https://nitter.privacydev.net"
        ]

        for nitter_url in nitter_instances:
            try:
                url = f"{nitter_url}/{self.username}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }

                response = requests.get(url, headers=headers, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    tweets = soup.find_all('div', class_='timeline-item')

                    for tweet in tweets:
                        tweet_data = self._parse_tweet(tweet)
                        if tweet_data:
                            self.tweets.append(tweet_data)

                    print(f"✅ Hämtade {len(self.tweets)} tweets från {nitter_url}")
                    return True

            except Exception as e:
                print(f"❌ Misslyckades med {nitter_url}: {e}")
                continue

        return False

    def _parse_tweet(self, tweet_element):
        """
        Extraherar trade-relevant info från tweet
        """
        try:
            # Hämta text
            text_elem = tweet_element.find('div', class_='tweet-content')
            if not text_elem:
                return None

            text = text_elem.get_text(strip=True)

            # Hämta datum
            date_elem = tweet_element.find('span', class_='tweet-date')
            date = date_elem.get_text(strip=True) if date_elem else ""

            # Extrahera trade-info
            trade_info = self._extract_trade_info(text)

            return {
                'text': text,
                'date': date,
                'trade_setup': trade_info,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Parse error: {e}")
            return None

    def _extract_trade_info(self, text):
        """
        Letar efter:
        - Aktienamn/ticker
        - Entry-pris
        - Stop loss
        - Target
        - Indikatorer (RSI, MACD, etc)
        """
        trade_info = {
            'ticker': None,
            'entry': None,
            'stop_loss': None,
            'target': None,
            'indicators': []
        }

        # Leta efter aktienamn (t.ex. VOLVO, SINCH, AMD)
        ticker_match = re.search(r'\b([A-Z]{2,6})\b', text)
        if ticker_match:
            trade_info['ticker'] = ticker_match.group(1)

        # Leta efter entry (t.ex. "Entry: 285", "Köper vid 285")
        entry_match = re.search(r'(?:entry|köper|inträde)[\s:]*(\d+[,.]?\d*)', text, re.IGNORECASE)
        if entry_match:
            trade_info['entry'] = float(entry_match.group(1).replace(',', '.'))

        # Leta efter stop loss
        stop_match = re.search(r'(?:stop|sl|stop loss)[\s:]*(\d+[,.]?\d*)', text, re.IGNORECASE)
        if stop_match:
            trade_info['stop_loss'] = float(stop_match.group(1).replace(',', '.'))

        # Leta efter target
        target_match = re.search(r'(?:target|tp|mål)[\s:]*(\d+[,.]?\d*)', text, re.IGNORECASE)
        if target_match:
            trade_info['target'] = float(target_match.group(1).replace(',', '.'))

        # Leta efter indikatorer
        if re.search(r'\bRSI\b', text, re.IGNORECASE):
            trade_info['indicators'].append('RSI')
        if re.search(r'\bMACD\b', text, re.IGNORECASE):
            trade_info['indicators'].append('MACD')
        if re.search(r'\bStoch', text, re.IGNORECASE):
            trade_info['indicators'].append('Stochastic')

        return trade_info

    def save_to_json(self, filename="ten_bagger_tweets.json"):
        """
        Sparar alla tweets till JSON-fil
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.tweets, f, indent=2, ensure_ascii=False)
        print(f"💾 Sparade {len(self.tweets)} tweets till {filename}")

    def get_trade_setups(self):
        """
        Returnerar endast tweets med trade-setup info
        """
        trade_tweets = []
        for tweet in self.tweets:
            setup = tweet.get('trade_setup', {})
            if setup.get('ticker') and (setup.get('entry') or setup.get('target')):
                trade_tweets.append(tweet)

        return trade_tweets

    def print_summary(self):
        """
        Visar sammanfattning av hittade trades
        """
        trade_setups = self.get_trade_setups()

        print(f"\n📊 SAMMANFATTNING:")
        print(f"Totalt tweets: {len(self.tweets)}")
        print(f"Trade-setups: {len(trade_setups)}")
        print(f"\n🎯 HITTADE TRADES:")

        for i, tweet in enumerate(trade_setups[:10], 1):
            setup = tweet['trade_setup']
            print(f"\n{i}. {setup['ticker']}")
            if setup['entry']:
                print(f"   Entry: {setup['entry']}")
            if setup['stop_loss']:
                print(f"   Stop: {setup['stop_loss']}")
            if setup['target']:
                print(f"   Target: {setup['target']}")
            print(f"   Text: {tweet['text'][:100]}...")


if __name__ == "__main__":
    print("🚀 Startar scraping av @Ten_Bagger...\n")

    scraper = TwitterScraper("Ten_Bagger")

    # Försök scrapa via Nitter
    if scraper.scrape_via_nitter():
        scraper.save_to_json()
        scraper.print_summary()
    else:
        print("❌ Kunde inte hämta tweets. Pröva manuell metod eller API.")
