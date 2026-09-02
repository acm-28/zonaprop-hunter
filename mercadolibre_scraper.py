"""
Módulo de Scraping para Mercado Libre Inmuebles Argentina.
Descarga y procesa páginas de departamentos en venta en Capital Federal.
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
]

class MercadoLibreScraper:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.search_cfg = config.get("search", {})
        self.session = requests.Session()

    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
        }

    def build_url(self, page: int = 1) -> str:
        """Construye la URL con filtros optimizados para Mercado Libre Inmuebles."""
        prop_type = self.search_cfg.get("property_type", "departamentos")
        min_price = self.search_cfg.get("min_price_usd", 18000)
        max_price = self.search_cfg.get("max_price_usd", 80000)

        base_url = f"https://inmuebles.mercadolibre.com.ar/{prop_type}/venta/capital-federal/"
        filter_slug = f"_PriceRange_{min_price}USD-{max_price}USD_OrderId_BEGINS*DESC"

        if page > 1:
            offset = (page - 1) * 48 + 1
            url = f"{base_url}_Desde_{offset}{filter_slug}"
        else:
            url = f"{base_url}{filter_slug}"

        return url

    def fetch_page(self, url: str) -> Optional[str]:
        """Realiza la petición HTTP con reintentos y delay de cortesía."""
        headers = self._get_headers()
        for attempt in range(1, 4):
            try:
                time.sleep(random.uniform(1.2, 2.0))
                response = self.session.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 404:
                    print(f"  [MercadoLibre 404] No hay más páginas en {url}")
                    return None
                else:
                    print(f"  [MercadoLibre Intento {attempt}] Código {response.status_code} en {url}")
            except Exception as e:
                print(f"  [MercadoLibre Intento {attempt}] Error de conexión: {e}")
                time.sleep(attempt * 2)
        return None

    def parse_card(self, card) -> Optional[Dict[str, Any]]:
        """Extrae todos los campos de una tarjeta de propiedad de Mercado Libre."""
        try:
            # 1. Título y Enlace
            title_el = (
                card.select_one('.poly-component__title')
                or card.select_one('h2.ui-search-item__title')
                or card.select_one('a[title]')
                or card.select_one('h2')
            )
            title = title_el.get_text(strip=True) if title_el else ""

            link_el = card.select_one('a[href]')
            if not link_el:
                return None

            raw_link = link_el["href"]
            clean_link = raw_link.split("?")[0].split("#")[0]
            if not clean_link.startswith("http"):
                return None

            id_match = re.search(r'(MLA-?\d+)', clean_link)
            posting_id = f"MELI-{id_match.group(1).replace('-', '')}" if id_match else f"MELI-{abs(hash(clean_link)) % 100000000}"

            card_full_text = card.get_text().lower()
            is_development = "unidades disponibles" in card_full_text and "desde" in card_full_text

            # 2. Precio y Moneda
            price_el = (
                card.select_one('.andes-money-amount__fraction')
                or card.select_one('.poly-price__current .andes-money-amount__fraction')
                or card.select_one('.price-tag-fraction')
            )
            price_raw = price_el.get_text(strip=True) if price_el else ""
            
            curr_el = card.select_one('.andes-money-amount__currency-symbol')
            curr_symbol = curr_el.get_text(strip=True) if curr_el else "US$"
            currency = "USD" if ("US$" in curr_symbol or "U$S" in curr_symbol or "USD" in curr_symbol or "$" not in curr_symbol) else "ARS"

            price_val = None
            if price_raw:
                clean_p = price_raw.replace('.', '').replace(',', '')
                try:
                    price_val = int(clean_p)
                except ValueError:
                    pass

            # 3. Ubicación
            loc_el = (
                card.select_one('.poly-component__location')
                or card.select_one('.ui-search-item__location')
                or card.select_one('[class*="location"]')
            )
            location_raw = loc_el.get_text(strip=True) if loc_el else "Capital Federal"

            # 4. Atributos (Superficie, Ambientes, Dormitorios, Baños)
            attr_elements = card.select('li[class*="attributes_list__item"], span[class*="attributes_list__item"], .poly-attributes-list__item')
            attr_texts = [a.get_text(strip=True) for a in attr_elements]
            features_raw = " | ".join(attr_texts) if attr_texts else card.get_text(separator=" | ", strip=True)

            m2_tot = None
            m2_match = re.search(r'(\d+)(?:\s*-\s*\d+)?\s*m[²2]', features_raw, re.IGNORECASE)
            if m2_match:
                m2_tot = int(m2_match.group(1))

            ambientes = None
            amb_match = re.search(r'(\d+)(?:\s*a\s*\d+)?\s*amb', features_raw, re.IGNORECASE)
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

            # 5. Imagen de Portada
            img_el = card.select_one('img')
            img_src = ""
            if img_el:
                img_src = img_el.get('src') or img_el.get('data-src') or img_el.get('data-lazy') or ""

            # 6. Fecha / Antigüedad
            antiquity_text = "Reciente"
            if "hoy" in card_full_text:
                antiquity_text = "Publicado hoy"

            return {
                "id": posting_id,
                "title": title or f"Departamento {ambientes or ''} amb en {location_raw}".strip(),
                "description": title,
                "source": "Mercado Libre",
                "source_badge": "🟡 Mercado Libre",
                "publication_date_text": antiquity_text,
                "price_raw": f"USD {price_raw}" if currency == "USD" else f"$ {price_raw}",
                "price_val": price_val,
                "currency": currency,
                "expenses_raw": "Consultar expensas",
                "features_raw": features_raw,
                "m2_tot": m2_tot,
                "m2_cub": m2_tot,
                "ambientes": ambientes,
                "dormitorios": dormitorios,
                "banos": banos,
                "cocheras": None,
                "location": location_raw,
                "address": location_raw.split(",")[0] if "," in location_raw else "",
                "image": img_src,
                "link": clean_link,
                "is_development": is_development,
            }
        except Exception:
            return None

    def scrape(self, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """Ejecuta el rastreo de Mercado Libre Inmuebles."""
        pages = max_pages or self.search_cfg.get("pages_to_scrape", 3)
        all_raw_properties = []
        seen_ids = set()

        print(f"\n[Scraper MercadoLibre] Iniciando rastreo en CABA...")
        print(f"[Scraper MercadoLibre] Páginas a consultar: {pages} | Precio Máx: USD {self.search_cfg.get('max_price_usd', 80000):,}")

        for page in range(1, pages + 1):
            url = self.build_url(page=page)
            print(f" -> [MercadoLibre] Consultando página {page}/{pages}...")
            
            html = self.fetch_page(url)
            if not html:
                break

            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select('li.ui-search-layout__item, div.ui-search-result__wrapper, div.poly-card')

            page_count = 0
            for card in cards:
                prop = self.parse_card(card)
                if prop and prop["id"] not in seen_ids:
                    seen_ids.add(prop["id"])
                    all_raw_properties.append(prop)
                    page_count += 1

            print(f"    [MercadoLibre] Página {page}: {len(cards)} avisos encontrados ({page_count} procesados)")

        print(f"[Scraper MercadoLibre] Finalizado. Total de avisos extraídos: {len(all_raw_properties)}")
        return all_raw_properties
