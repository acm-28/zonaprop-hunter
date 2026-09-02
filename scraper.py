"""
Módulo de Scraping para Zonaprop Argentina.
Descarga y procesa páginas de listados de propiedades en venta en CABA.
"""

import time
import random
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
]

class ZonapropScraper:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.search_cfg = config.get("search", {})
        self.session = requests.Session()

    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
        }

    def build_url(self, location: str = "capital-federal", page: int = 1) -> str:
        """Construye la URL con filtros optimizados para Zonaprop."""
        prop_type = self.search_cfg.get("property_type", "departamentos")
        max_price = self.search_cfg.get("max_price_usd", 80000)
        sort_by = self.search_cfg.get("sort_by", "orden-publicado-descendente")

        loc_slug = location.strip().lower().replace(" ", "-")
        slug_parts = [prop_type, "venta", loc_slug]
        
        if max_price and max_price > 0:
            slug_parts.append(f"menos-{max_price}-dolar")
            
        if sort_by:
            slug_parts.append(sort_by)
            
        if page > 1:
            slug_parts.append(f"pagina-{page}")
            
        url = f"https://www.zonaprop.com.ar/{'-'.join(slug_parts)}.html"
        return url

    def fetch_page(self, url: str) -> Optional[str]:
        """Realiza la petición HTTP con reintentos y delay de cortesía."""
        headers = self._get_headers()
        for attempt in range(1, 4):
            try:
                time.sleep(random.uniform(1.2, 2.2))
                response = self.session.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 404:
                    print(f"  [404] No hay mas paginas en {url}")
                    return None
                else:
                    print(f"  [Intento {attempt}] Codigo {response.status_code} en {url}")
            except Exception as e:
                print(f"  [Intento {attempt}] Error al conectar con {url}: {e}")
                time.sleep(attempt * 2)
        return None

    def parse_card(self, card) -> Optional[Dict[str, Any]]:
        """Extrae de forma precisa todos los campos de una tarjeta de propiedad."""
        try:
            posting_id = card.get("data-id")
            if not posting_id:
                return None

            raw_link = card.get("data-to-posting", "")
            if not raw_link:
                a_tag = card.find("a", href=True)
                if a_tag:
                    raw_link = a_tag["href"]

            if not raw_link:
                return None

            clean_path = raw_link.split("?")[0]
            link = f"https://www.zonaprop.com.ar{clean_path}" if clean_path.startswith("/") else clean_path
            is_development = "emprendimiento" in link.lower()

            # 1. Antigüedad / Fecha de publicación
            antiquity_el = (
                card.select_one('[class*="posting-antiquity-date"], [class*="antiquity"], [class*="publication-date"]')
                or card.find(attrs={"data-qa": lambda x: x and ("antiquity" in x.lower() or "date" in x.lower())})
            )
            antiquity_text = antiquity_el.get_text(strip=True) if antiquity_el else ""

            if not antiquity_text:
                for div in card.find_all(['div', 'span']):
                    t = div.get_text(strip=True)
                    if t and any(w in t.lower() for w in ['publicado hoy', 'publicado ayer', 'hace ', 'publicado hace']):
                        antiquity_text = t
                        break

            # 2. Precio
            price_el = (
                card.find(attrs={"data-qa": lambda x: x and "price" in x.lower()})
                or card.select_one('[class*="price-value"], [class*="PriceValue"], [class*="price"], [class*="Price"]')
            )
            price_raw = price_el.get_text(strip=True) if price_el else ""

            currency = "USD"
            if "ARS" in price_raw or ("$" in price_raw and "USD" not in price_raw and "U$S" not in price_raw):
                currency = "ARS"

            price_val = None
            nums = re.findall(r'[\d\.]+', price_raw)
            if nums:
                clean_p = nums[-1].replace('.', '')
                try:
                    price_val = int(clean_p)
                except ValueError:
                    pass

            # 3. Expensas
            expenses_el = (
                card.find(attrs={"data-qa": lambda x: x and "expensas" in x.lower()})
                or card.select_one('[class*="expenses"], [class*="Expenses"]')
            )
            expenses_raw = expenses_el.get_text(strip=True) if expenses_el else ""

            # 4. Características principales (m2, amb, dorm, baños, coch)
            features_el = (
                card.find(attrs={"data-qa": lambda x: x and "feature" in x.lower()})
                or card.select_one('[class*="mainFeatures"], [class*="Features"], [class*="postingMainFeatures"]')
            )
            features_raw = features_el.get_text(separator=" | ", strip=True) if features_el else ""

            m2_tot = None
            m2_match = re.search(r'(\d+)\s*m[²2]\s*tot', features_raw, re.IGNORECASE) or re.search(r'(\d+)\s*m[²2]', features_raw, re.IGNORECASE)
            if m2_match:
                m2_tot = int(m2_match.group(1))

            m2_cub = None
            cub_match = re.search(r'(\d+)\s*m[²2]\s*cub', features_raw, re.IGNORECASE)
            if cub_match:
                m2_cub = int(cub_match.group(1))

            ambientes = None
            amb_match = re.search(r'(\d+)\s*amb', features_raw, re.IGNORECASE)
            if amb_match:
                ambientes = int(amb_match.group(1))

            dormitorios = None
            dorm_match = re.search(r'(\d+)\s*dorm', features_raw, re.IGNORECASE)
            if dorm_match:
                dormitorios = int(dorm_match.group(1))

            banos = None
            ban_match = re.search(r'(\d+)\s*bañ', features_raw, re.IGNORECASE)
            if ban_match:
                banos = int(ban_match.group(1))

            cocheras = None
            coch_match = re.search(r'(\d+)\s*coch', features_raw, re.IGNORECASE)
            if coch_match:
                cocheras = int(coch_match.group(1))

            # 5. Ubicación y Barrio
            loc_el = (
                card.find(attrs={"data-qa": lambda x: x and "location" in x.lower()})
                or card.select_one('[class*="location-text"], [class*="location"], [class*="Location"], [class*="postingLocation"]')
            )
            location_raw = loc_el.get_text(separator=" - ", strip=True) if loc_el else "Capital Federal"

            # 6. Dirección
            addr_el = card.select_one('[class*="location-address"], [class*="postingAddress"], [class*="Address"]')
            address = addr_el.get_text(strip=True) if addr_el else ""

            # 7. Imagen de Portada
            img_el = card.select_one('img')
            img_src = ""
            if img_el:
                img_src = img_el.get('src') or img_el.get('data-src') or img_el.get('data-lazy') or ""
                if img_el.get('srcset'):
                    parts = img_el['srcset'].split(',')
                    if parts:
                        img_src = parts[-1].strip().split(' ')[0]

            # 8. Título / Descripción del aviso
            title_el = (
                card.find(attrs={"data-qa": lambda x: x and "description" in x.lower()})
                or card.select_one('[class*="posting-description"], [class*="postingTitle"], [class*="Title"], h2, h3')
            )
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                title = f"Departamento {ambientes or ''} amb en {location_raw}".strip()

            return {
                "id": f"ZPROP-{posting_id}",
                "title": title,
                "description": title,
                "source": "Zonaprop",
                "source_badge": "🔵 Zonaprop",
                "publication_date_text": antiquity_text or "Reciente",
                "price_raw": price_raw,
                "price_val": price_val,
                "currency": currency,
                "expenses_raw": expenses_raw,
                "features_raw": features_raw,
                "m2_tot": m2_tot,
                "m2_cub": m2_cub,
                "ambientes": ambientes,
                "dormitorios": dormitorios,
                "banos": banos,
                "cocheras": cocheras,
                "location": location_raw,
                "address": address,
                "image": img_src,
                "link": link,
                "is_development": is_development,
            }
        except Exception:
            return None

    def scrape(self, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Ejecuta el rastreo de Zonaprop según la configuración.
        Soporta parada anticipada cuando se activa `only_published_today`.
        """
        pages = max_pages or self.search_cfg.get("pages_to_scrape", 5)
        location = self.search_cfg.get("location", "capital-federal")
        only_today = self.search_cfg.get("only_published_today", False)
        
        all_raw_properties = []
        seen_ids = set()

        print(f"\n[Scraper Zonaprop] Iniciando rastreo para: {location.upper()}")
        print(f"[Scraper Zonaprop] Páginas a consultar: {pages} | Precio Máx: USD {self.search_cfg.get('max_price_usd', 80000):,}")
        if only_today:
            print("[Scraper Zonaprop] Modo estricto activado: Filtrando SOLO publicaciones de hoy.")

        for page in range(1, pages + 1):
            url = self.build_url(location=location, page=page)
            print(f" -> [Zonaprop] Consultando página {page}/{pages}...")
            
            html = self.fetch_page(url)
            if not html:
                print(f"    No se pudo obtener contenido para la página {page}.")
                break

            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select('div[data-id][data-to-posting]')
            
            if not cards:
                cards = soup.find_all(attrs={"data-qa": lambda x: x and "posting" in x.lower()})

            page_count = 0
            reached_older_ads = False

            for card in cards:
                prop = self.parse_card(card)
                if not prop or prop["id"] in seen_ids:
                    continue

                seen_ids.add(prop["id"])
                
                pub_text = prop.get("publication_date_text", "").lower()
                is_today = "hoy" in pub_text or "hora" in pub_text or "minuto" in pub_text or "segundo" in pub_text
                
                if only_today and not is_today and pub_text and "reciente" not in pub_text:
                    reached_older_ads = True
                    continue

                all_raw_properties.append(prop)
                page_count += 1

            print(f"    [Zonaprop] Página {page}: {len(cards)} avisos en página ({page_count} procesados)")

            if only_today and reached_older_ads and page_count == 0:
                print("    [Info] Se alcanzaron publicaciones de días anteriores en Zonaprop. Finalizando rastreo.")
                break

        print(f"[Scraper Zonaprop] Finalizado. Total de avisos extraídos: {len(all_raw_properties)}")
        return all_raw_properties
