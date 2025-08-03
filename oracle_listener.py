import os
import requests
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv
from plyer import notification
import sys

# Загружаем тайные знания из .env
load_dotenv()

# --- Скрижали Оракула ---
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')
API_ENDPOINT = 'https://api.etherscan.io/api'
# Ключевые активы, которые служат "подношениями" для великих дел
OFFERING_ASSETS = {
    '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2': {'symbol': 'WETH', 'decimals': 18},
    '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48': {'symbol': 'USDC', 'decimals': 6},
    '0xdAC17F958D2ee523a2206206994597C13D831ec7': {'symbol': 'USDT', 'decimals': 6},
}

class OracleListener:
    def __init__(self, eth_omen_threshold, stable_omen_threshold):
        if not ETHERSCAN_API_KEY:
            raise EnvironmentError("Ключ к знаниям (ETHERSCAN_API_KEY) не найден. Проверьте ваш .env файл.")
        
        self.eth_omen = eth_omen_threshold
        self.stable_omen = stable_omen_threshold
        self.session = requests.Session()
        self.pantheon = self.load_pantheon()
        self.seen_tx_hashes = set()

    def load_pantheon(self):
        """Загружает пантеон Титанов из файла watch_list.txt."""
        titans = {}
        try:
            with open('watch_list.txt', 'r') as f:
                for line in f:
                    if not line.strip() or line.startswith('#'): continue
                    parts = [p.strip() for p in line.split(',')]
                    address = parts[0].lower()
                    name = parts[1] if len(parts) > 1 else f"Титан ({address[:5]}...)"
                    titans[address] = {'name': name}
            if not titans: raise FileNotFoundError
            self.log(f"Пантеон из {len(titans)} Титанов собран. Бдение начинается.")
            return titans
        except FileNotFoundError:
            print("[!] Ошибка: священный свиток 'watch_list.txt' не найден или пуст.", file=sys.stderr)
            sys.exit(1)

    def fetch_recent_events(self, address):
        """Слушает эфир на предмет недавних событий (транзакций)."""
        params = {
            'module': 'account',
            'action': 'tokentx',
            'address': address,
            'page': 1, 'offset': 25, 'sort': 'desc',
            'apikey': ETHERSCAN_API_KEY
        }
        token_events = self.session.get(API_ENDPOINT, params=params).json().get('result', [])
        
        params['action'] = 'txlist'
        native_events = self.session.get(API_ENDPOINT, params=params).json().get('result', [])

        return (token_events or []) + (native_events or [])

    def send_vision(self, title, message):
        """Посылает пророческое видение на рабочий стол."""
        try:
            notification.notify(title=title, message=message, app_name='CryptoOracle', timeout=30)
        except Exception as e:
            print(f"[!] Видение не смогло пробиться сквозь пелену реальности: {e}", file=sys.stderr)

    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def start_vigil(self):
        """Основной цикл бдения Оракула."""
        self.log("🔮 CryptoOracle начинает свое бдение...")
        self.log(f"Знамение ETH: > {self.eth_omen}, Знамение стейблов: > {self.stable_omen}.")

        try:
            while True:
                for address, data in self.pantheon.items():
                    events = self.fetch_recent_events(address)
                    
                    for event in events:
                        event_hash = event['hash']
                        if event_hash in self.seen_tx_hashes: continue
                        
                        # Нас интересуют только входящие подношения
                        if event['to'].lower() != address:
                            self.seen_tx_hashes.add(event_hash)
                            continue

                        is_native = 'tokenSymbol' not in event
                        amount, symbol, threshold = 0, '', 0

                        if is_native:
                            amount = int(event['value']) / 10**18
                            symbol, threshold = 'ETH', self.eth_omen
                        else: # Это токен ERC20
                            token_addr = event['contractAddress'].lower()
                            if token_addr in OFFERING_ASSETS:
                                token = OFFERING_ASSETS[token_addr]
                                amount = int(event['value']) / 10**token['decimals']
                                symbol = token['symbol']
                                threshold = self.eth_omen if symbol == 'WETH' else self.stable_omen

                        if amount >= threshold:
                            self.log("❗️ ОРАКУЛ ГОВОРИТ! ПОЛУЧЕНО ВИДЕНИЕ!")
                            self.log(f"Титан: {data['name']} ({address[:6]}...{address[-4:]})")
                            self.log(f"Подношение: {amount:.2f} {symbol}")
                            self.log(f"Первоисточник: https://etherscan.io/tx/{event_hash}")
                            
                            title = f"🔮 Видение от Оракула: {data['name']}"
                            message = f"Совершено подношение в {amount:.2f} {symbol}.\nВеликое деяние может быть близко."
                            self.send_vision(title, message)
                        
                        self.seen_tx_hashes.add(event_hash)
                    
                    time.sleep(3) # Даем Оракулу перевести дух между Титанами
                
                # Очищаем память Оракула, чтобы он не сошел с ума от старых видений
                if len(self.seen_tx_hashes) > 1500: self.seen_tx_hashes.clear()
                
                time.sleep(45) # Пауза между полными циклами прослушивания эфира
        except KeyboardInterrupt:
            self.log("🔮 Оракул умолкает до следующего призыва.")
            sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CryptoOracle - ваш провидец в мире блокчейна.")
    parser.add_argument("--eth-omen", type=float, default=10.0, help="Минимальный размер подношения в ETH/WETH для получения видения.")
    parser.add_argument("--stable-omen", type=float, default=20000.0, help="Минимальный размер подношения в USDC/USDT.")
    
    args = parser.parse_args()
    
    try:
        oracle = OracleListener(args.eth_omen, args.stable_omen)
        oracle.start_vigil()
    except (ValueError, EnvironmentError) as e:
        print(f"Ошибка призыва Оракула: {e}", file=sys.stderr)
