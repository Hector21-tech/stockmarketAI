"""
Twitter Scraper med Selenium - Kräver inloggning
Hämtar @Ten_Bagger tweets med trade-setups
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import re
from datetime import datetime

class TwitterScraperSelenium:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.tweets = []
        self.driver = None

    def setup_driver(self):
        """Sätter upp Chrome driver"""
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Kör i bakgrunden (kommentera ut för att se)
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        # Automatisk installation av ChromeDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Chrome driver startad")

    def login(self):
        """Loggar in på Twitter/X"""
        try:
            print("Loggar in pa X...")
            self.driver.get("https://x.com/login")
            time.sleep(3)

            # Ange användarnamn
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
            )
            username_input.send_keys(self.username)
            username_input.send_keys(Keys.RETURN)
            time.sleep(2)

            # Ange lösenord
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
            )
            password_input.send_keys(self.password)
            password_input.send_keys(Keys.RETURN)
            time.sleep(5)

            print("Inloggad pa X")
            return True

        except Exception as e:
            print(f"Inloggning misslyckades: {e}")
            return False

    def scrape_user(self, target_user="Ten_Bagger", max_tweets=100, save_interval=50):
        """Hämtar tweets från specifik användare"""
        try:
            print(f"Hamtar tweets fran @{target_user}...")
            self.driver.get(f"https://x.com/{target_user}")
            time.sleep(3)

            # Scrolla och samla tweets
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            tweets_collected = 0

            while tweets_collected < max_tweets:
                # Hitta alla tweet-artiklar
                tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')

                for tweet_elem in tweet_elements[tweets_collected:]:
                    tweet_data = self._parse_tweet_element(tweet_elem)
                    if tweet_data and tweet_data not in self.tweets:
                        self.tweets.append(tweet_data)
                        tweets_collected += 1
                        print(f"Tweet {tweets_collected}/{max_tweets}")

                        # Auto-save varje X tweets
                        if tweets_collected % save_interval == 0:
                            self.save_to_json(f"ten_bagger_tweets_backup.json")
                            print(f"  -> Auto-saved {tweets_collected} tweets")

                    if tweets_collected >= max_tweets:
                        break

                # Scrolla nedåt
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                # Kolla om vi nått botten
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    print("Nadde slutet av timeline")
                    break
                last_height = new_height

            print(f"Samlade totalt {len(self.tweets)} tweets")
            return True

        except Exception as e:
            print(f"Scraping misslyckades: {e}")
            return False

    def _parse_tweet_element(self, element):
        """Extraherar data från tweet-element"""
        try:
            # Hämta tweet-text
            text_elem = element.find_element(By.CSS_SELECTOR, 'div[data-testid="tweetText"]')
            text = text_elem.text if text_elem else ""

            # Hämta datum
            try:
                time_elem = element.find_element(By.TAG_NAME, 'time')
                date = time_elem.get_attribute('datetime')
            except:
                date = datetime.now().isoformat()

            # Extrahera trade-info
            trade_info = self._extract_trade_info(text)

            return {
                'text': text,
                'date': date,
                'trade_setup': trade_info,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return None

    def _extract_trade_info(self, text):
        """Extraherar trade-setup från tweet-text"""
        trade_info = {
            'ticker': None,
            'action': None,  # Köper, Säljer, Kort, etc
            'entry': None,
            'stop_loss': None,
            'target': None,
            'position_size': None,
            'indicators': [],
            'pattern': None
        }

        # Leta efter ticker (t.ex. $VOLVO, SINCH, AMD)
        ticker_patterns = [
            r'\$([A-Z]{2,6})',  # $TSLA
            r'\b([A-Z]{2,6})\s+[BEA]\b',  # VOLVO B
            r'(?:köper|säljer|short|long)\s+([A-Z]{2,6})',  # köper SINCH
        ]

        for pattern in ticker_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                trade_info['ticker'] = match.group(1)
                break

        # Action (Köper, Säljer, Kort, etc)
        if re.search(r'\b(köper|köp|long)\b', text, re.IGNORECASE):
            trade_info['action'] = 'BUY'
        elif re.search(r'\b(säljer|säl[jt]|exit)\b', text, re.IGNORECASE):
            trade_info['action'] = 'SELL'
        elif re.search(r'\b(kort|short|går kort)\b', text, re.IGNORECASE):
            trade_info['action'] = 'SHORT'

        # Entry
        entry_patterns = [
            r'(?:entry|inträde|köper vid)[\s:]+(\d+[,.]?\d*)',
            r'vid\s+(\d+[,.]?\d*)\s*kr',
        ]
        for pattern in entry_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                trade_info['entry'] = float(match.group(1).replace(',', '.'))
                break

        # Stop loss
        stop_patterns = [
            r'(?:stop|sl|stop loss)[\s:]+(\d+[,.]?\d*)',
            r'stopp[\s:]+(\d+[,.]?\d*)',
        ]
        for pattern in stop_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                trade_info['stop_loss'] = float(match.group(1).replace(',', '.'))
                break

        # Target
        target_patterns = [
            r'(?:target|tp|mål)[\s:]+(\d+[,.]?\d*)',
            r'siktar[\s:]+(\d+[,.]?\d*)',
        ]
        for pattern in target_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                trade_info['target'] = float(match.group(1).replace(',', '.'))
                break

        # Position size
        pos_match = re.search(r'(\d+[,.]?\d*)\s*%\s*position', text, re.IGNORECASE)
        if pos_match:
            trade_info['position_size'] = float(pos_match.group(1).replace(',', '.'))

        # Indikatorer
        indicators = ['RSI', 'MACD', 'Stochastic', 'EMA', 'SMA', 'Volume', 'VWAP']
        for indicator in indicators:
            if re.search(rf'\b{indicator}\b', text, re.IGNORECASE):
                trade_info['indicators'].append(indicator)

        # Mönster
        patterns = ['bullflagga', 'bearflagga', 'triangel', 'head and shoulders',
                   'double top', 'double bottom', 'breakout', 'breakdown']
        for pattern in patterns:
            if re.search(rf'\b{pattern}\b', text, re.IGNORECASE):
                trade_info['pattern'] = pattern
                break

        return trade_info

    def save_to_json(self, filename="ten_bagger_tweets.json"):
        """Sparar tweets till JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.tweets, f, indent=2, ensure_ascii=False)
        print(f"Sparade {len(self.tweets)} tweets till {filename}")

    def get_trade_setups(self):
        """Returnerar endast tweets med trade-info"""
        trade_tweets = []
        for tweet in self.tweets:
            setup = tweet.get('trade_setup', {})
            if setup.get('ticker') and (setup.get('entry') or setup.get('target') or setup.get('action')):
                trade_tweets.append(tweet)
        return trade_tweets

    def print_summary(self):
        """Visar sammanfattning"""
        trade_setups = self.get_trade_setups()

        print(f"\n{'='*60}")
        print(f"SAMMANFATTNING")
        print(f"{'='*60}")
        print(f"Totalt tweets: {len(self.tweets)}")
        print(f"Trade-setups: {len(trade_setups)}")

        print(f"\n{'='*60}")
        print(f"TRADE-SETUPS")
        print(f"{'='*60}")

        for i, tweet in enumerate(trade_setups[:20], 1):
            setup = tweet['trade_setup']
            print(f"\n{i}. {setup.get('ticker', 'N/A')} - {setup.get('action', 'N/A')}")
            if setup.get('entry'):
                print(f"   Entry: {setup['entry']} kr")
            if setup.get('stop_loss'):
                print(f"   Stop: {setup['stop_loss']} kr")
            if setup.get('target'):
                print(f"   Target: {setup['target']} kr")
            if setup.get('pattern'):
                print(f"   Pattern: {setup['pattern']}")
            if setup.get('indicators'):
                print(f"   Indikatorer: {', '.join(setup['indicators'])}")
            print(f"   Datum: {tweet['date'][:10]}")
            print(f"   Text: {tweet['text'][:150]}...")

    def close(self):
        """Stänger browser"""
        if self.driver:
            self.driver.quit()
            print("Browser stangd")


def main():
    print("="*60)
    print("TWITTER SCRAPER FOR @TEN_BAGGER")
    print("="*60)

    # Användare anger sina credentials
    twitter_username = input("\nTwitter username/email: ")
    twitter_password = input("Twitter password: ")

    scraper = TwitterScraperSelenium(twitter_username, twitter_password)

    try:
        # Starta browser
        scraper.setup_driver()

        # Logga in
        if not scraper.login():
            print("Kunde inte logga in")
            return

        # Scrapa @Ten_Bagger
        # max_tweets: antal tweets att hämta (sätt högt för lång scraping, t.ex. 5000)
        # save_interval: sparar backup varje X tweets (default 50)
        if scraper.scrape_user("Ten_Bagger", max_tweets=1000, save_interval=50):
            scraper.save_to_json()
            scraper.print_summary()

    except Exception as e:
        print(f"Fel: {e}")

    finally:
        scraper.close()


if __name__ == "__main__":
    main()
