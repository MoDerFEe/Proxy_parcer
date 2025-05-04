import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def get_proxy_list():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    proxies = []
    try:
        for i in range(10):
            driver.get(f"http://proxy-list.org/russian/index.php?p={i+1}")
            time.sleep(5)  # ждём загрузки JS
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            k=0
            for li in soup.find_all("li", class_="proxy"):
                if k == 0:
                    k=1
                    continue
                else:
                    proxies.append(f"http://{li.text.strip()}")
    finally:
        driver.quit()

    print(f'Парсинг proxy-list.org завершен, всего {len(proxies)} прокси')
    return proxies

def get_proxydb():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    proxies = []
    try:
        for k in range(15):
            driver.get(f"https://proxydb.net/?protocol=http&protocol=https&anonlvl=2&anonlvl=4&sort_column_id=checked&sort_order_desc=1&offset={k*30}")
            time.sleep(5)  # ждём загрузки JS
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            for row in soup.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    ip = cells[0].get_text(strip=True)
                    port = cells[1].get_text(strip=True)
                    if ip and port:
                        proxies.append(f"http://{ip}:{port}")
    finally:
        driver.quit()

    print(f'Парсинг proxydb.net завершен, всего {len(proxies)} прокси')
    return proxies

def get_free_proxy_list():
    proxies = []
    try:
        url = "https://free-proxy-list.net/"
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        for row in soup.select("table tbody tr"):
            tds = row.find_all("td")
            if len(tds) >= 7:
                proxy = f"http://{tds[0].text}:{tds[1].text}"
                proxies.append(proxy)
        print(f'Парсинг free-proxy-list.net завершен, всего {len(proxies)} прокси')
    except Exception as e:
        print(f'free-proxy-list.net Ошибка: {e}')
    return proxies

def get_proxy_list_download():
    proxies=[]
    try:
        url = "https://www.proxy-list.download/api/v1/get?type=http"
        r = requests.get(url)
        for line in r.text.strip().split("\r\n"):
            proxies.append(f'http://{line}')
        print(f'Парсинг proxy-list.download завершен, всего {len(proxies)} прокси')
    except Exception as e:
        print(f'proxy-list.download Ошибка: {e}')
    return proxies

def get_proxyscrape():
    proxies=[]
    try:
        url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text&timeout=3000&country=all&ssl=all&anonymity=all"
        r = requests.get(url)
        for line in r.text.strip().split("\n"):
            if 'http' in line:
                proxies.append(line)
        print(f'Парсинг proxyscrape.com завершен, всего {len(proxies)} прокси')
    except Exception as e:
        print(f'api.proxyscrape.com Ошибка: {e}')
    return proxies

def get_geonode():
    proxies = []
    try:
        url = "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"
        r = requests.get(url).json()
        for proxy in r['data']:
            proxies.append(f"http://{proxy['ip']}:{proxy['port']}")
        print(f'Парсинг proxylist.geonode.com завершен, всего {len(proxies)} прокси')
    except Exception as e:
        print(f'proxylist.geonode.com Ошибка: {e}')
    return proxies

def validate_proxy(proxy, timeout=5):
    try:
        r = requests.get("https://httpbin.org/ip", proxies={"http": proxy, "https": proxy}, timeout=timeout)
        return proxy if r.ok else None
    finally:
        return None

def gather_proxies():
    print("Сбор прокси...\n")
    all_proxies = set()

    sources = {
        "proxy-list": get_proxy_list,
        "proxydb": get_proxydb,
        "free-proxy-list": get_free_proxy_list,
        "proxy-list-download": get_proxy_list_download,
        "proxyscrape": get_proxyscrape,
        "geonode": get_geonode
    }

    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = [executor.submit(fn) for fn in sources.values()]
        for future in as_completed(futures):
            result = future.result()
            if result:
                all_proxies.update(result)

    print(f"Найдено всего: {len(all_proxies)} прокси")
    return list(all_proxies)

def check_all(proxies, start):
    working = []
    print("\nПроверка валидности...")
    with ThreadPoolExecutor(max_workers=100) as executor:
        for result in executor.map(validate_proxy, proxies):
            if result:
                working.append(result)
    duration = round(time.time() - start, 2)
    print(f"\nРабочих прокси: {len(working)} / {len(proxies)}")
    print(f"Время парсинга и проверки: {duration} с")
    return working

def main():
    start = time.time()
    proxies = gather_proxies()
    working = check_all(proxies, start)

    with open("working_proxies.txt", "w") as f:
        for p in working:
            f.write(p + "\n")
    print("Сохранено в working_proxies.txt")
    input('\nНажмите Enter для выхода...')

if __name__ == "__main__":
    main()
