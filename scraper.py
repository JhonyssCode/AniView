import requests
import json
import base64
import hashlib
import re
from Crypto.Cipher import AES
from Crypto.Util import Counter

class AniScraper:
    # Tabela de substituição do ani-cli (provider_init)
    HEX_TABLE = {
        '79':'A','7a':'B','7b':'C','7c':'D','7d':'E','7e':'F','7f':'G','70':'H','71':'I','72':'J','73':'K','74':'L','75':'M','76':'N','77':'O',
        '68':'P','69':'Q','6a':'R','6b':'S','6c':'T','6d':'U','6e':'V','6f':'W','60':'X','61':'Y','62':'Z',
        '59':'a','5a':'b','5b':'c','5c':'d','5d':'e','5e':'f','5f':'g','50':'h','51':'i','52':'j','53':'k','54':'l','55':'m','56':'n','57':'o',
        '48':'p','49':'q','4a':'r','4b':'s','4c':'t','4d':'u','4e':'v','4f':'w','40':'x','41':'y','42':'z',
        '08':'0','09':'1','0a':'2','0b':'3','0c':'4','0d':'5','0e':'6','0f':'7','00':'8','01':'9',
        '15':'-','16':'.','67':'_','46':'~','02':':','17':'/','07':'?','1b':'#',
        '63':'[','65':']','78':'@','19':'!','1c':'$','1e':'&','10':'(','11':')','12':'*','13':'+','14':',','03':';','05':'=','1d':'%'
    }

    def __init__(self):
        self.agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        self.headers = {
            "User-Agent": self.agent,
            "Referer": "https://allmanga.to",
            "Origin": "https://allmanga.to",
        }
        self.key = hashlib.sha256(b"Xot36i3lK3:v1").digest()
        print("[Scraper] AniView Scraper inicializado (motor direto AllAnime)")

    def get_poster(self, title):
        """Busca o poster oficial via Jikan API"""
        try:
            resp = requests.get(f"https://api.jikan.moe/v4/anime?q={title}&limit=1", timeout=5)
            data = resp.json()
            if data.get('data'):
                return data['data'][0]['images']['jpg']['image_url']
        except: pass
        return None

    def decode_provider_url(self, hex_str):
        """Decodifica URL do provider usando tabela de substituição do ani-cli"""
        result = ''
        for i in range(0, len(hex_str) - 1, 2):
            result += self.HEX_TABLE.get(hex_str[i:i+2], '')
        return result.replace('/clock', '/clock.json')

    def fetch_provider_video(self, relative_url):
        """Busca o link de vídeo real a partir da URL relativa do provider"""
        full_url = f"https://allanime.day{relative_url}"
        print(f"[Player] Buscando provider: {full_url[:80]}...")
        try:
            resp = requests.get(full_url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                matches = re.findall(r'"link":"([^"]+)"', resp.text)
                return [m.replace('\\/', '/') for m in matches if 'http' in m]
        except Exception as e:
            print(f"[Aviso] Provider falhou: {e}")
        return []

    def decode_source(self, blob):
        print("[Player] Descriptografando blob...")
        try:
            data = base64.b64decode(blob)
            iv = data[1:13]
            nonce = iv + b"\x00\x00\x00\x02"
            ciphertext = data[13:-16]
            ctr = Counter.new(128, initial_value=int.from_bytes(nonce, byteorder='big'))
            cipher = AES.new(self.key, AES.MODE_CTR, counter=ctr)
            decrypted = cipher.decrypt(ciphertext).decode('utf-8', errors='replace')

            try:
                parsed = json.loads(decrypted.strip().rstrip('\x00'))
                source_urls = parsed.get('episode', {}).get('sourceUrls', [])
            except:
                source_urls = []
                for m in re.finditer(r'"sourceUrl":"([^"]+)","[^"]*"[^}]*"sourceName":"([^"]+)"', decrypted):
                    source_urls.append({"sourceUrl": m.group(1), "sourceName": m.group(2)})

            links = []
            for s in source_urls:
                src = s.get('sourceUrl', '')
                name = s.get('sourceName', 'Unknown')
                if src.startswith('--'):
                    provider_path = self.decode_provider_url(src[2:])
                    print(f"[Player] Provider '{name}': {provider_path}")
                    for vl in self.fetch_provider_video(provider_path):
                        links.append({"name": name, "url": vl})
                elif src.startswith('//') or src.startswith('http'):
                    url = src if src.startswith('http') else 'https:' + src
                    print(f"[Player] Link direto '{name}': {url[:60]}...")
                    links.append({"name": name, "url": url})

            print(f"[Player] Total de {len(links)} link(s) encontrado(s).")
            return links
        except Exception as e:
            print(f"[Erro] decode_source falhou: {e}")
            return []

    def search_anime(self, query):
        print(f"\n[Busca] Pesquisando por: '{query}'...")
        gql = """
        query($search: SearchInput, $limit: Int, $page: Int, $translationType: VaildTranslationTypeEnumType, $countryOrigin: VaildCountryOriginEnumType) {
            shows(search: $search, limit: $limit, page: $page, translationType: $translationType, countryOrigin: $countryOrigin) {
                edges { _id name availableEpisodes }
            }
        }
        """
        variables = {
            "search": {"allowAdult": False, "allowUnknown": False, "query": query},
            "limit": 20, "page": 1, "translationType": "sub", "countryOrigin": "ALL"
        }
        try:
            resp = requests.post("https://api.allanime.day/api",
                                 json={"query": gql, "variables": variables},
                                 headers=self.headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get('data', {}).get('shows', {}).get('edges', [])
                print(f"[Busca] {len(data)} resultados encontrados.")
                return [{
                    "id": x['_id'],
                    "name": x['name'],
                    "episodes": x['availableEpisodes'].get('sub', 0),
                    "image": self.get_poster(x['name']),
                    "_result": x  # Mantém o objeto bruto
                } for x in data]
        except Exception as e:
            print(f"[Erro] Falha na busca: {e}")
        return []

    def get_episode_links(self, anime_id_or_result, ep_number):
        """Aceita tanto um ID string quanto o dict do resultado bruto"""
        anime_id = anime_id_or_result if isinstance(anime_id_or_result, str) else anime_id_or_result.get('_id', anime_id_or_result)
        print(f"\n[Player] Buscando EP {ep_number} (ID: {anime_id})...")

        query_hash = "d405d0edd690624b66baba3068e0edc3ac90f1597d898a1ec8db4e5c43c00fec"
        variables = {"showId": anime_id, "translationType": "sub", "episodeString": str(ep_number)}
        extensions = {"persistedQuery": {"version": 1, "sha256Hash": query_hash}}
        vars_json = json.dumps(variables, separators=(',', ':'))
        ext_json = json.dumps(extensions, separators=(',', ':'))

        ep_headers = self.headers.copy()
        ep_headers["Origin"] = "https://allmanga.to"
        ep_headers["Referer"] = "https://allmanga.to"

        try:
            api_url = f"https://api.allanime.day/api?variables={vars_json}&extensions={ext_json}"
            resp = requests.get(api_url, headers=ep_headers, timeout=10)
            if resp.status_code == 200:
                json_data = resp.json()
                data = json_data.get('data', {})
                if data and 'tobeparsed' in data:
                    print("[Player] Blob 'tobeparsed' encontrado!")
                    return self.decode_source(data['tobeparsed'])
                elif data and data.get('episode') and 'tobeparsed' in data['episode']:
                    return self.decode_source(data['episode']['tobeparsed'])
                else:
                    print(f"[Aviso] Estrutura inesperada: {list(data.keys())}")
        except Exception as e:
            print(f"[Erro] Falha na extração: {e}")
        return []
