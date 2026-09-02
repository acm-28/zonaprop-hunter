"""
Módulo de Scraping para Mercado Libre Inmuebles Argentina.
Descarga y procesa páginas de departamentos y PHs publicados HOY en Capital Federal.
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

    def build_urls(self, page: int = 1) -> List[str]:
        """Construye las URLs con filtro estricto de publicados hoy para departamentos y PHs."""
        min_price = self.search_cfg.get("min_price_usd", 18000)
        max_price = self.search_cfg.get("max_price_usd", 80000)
        only_today = self.search_cfg.get("only_published_today", True)

        today_slug = "_PublishedToday_YES" if only_today else ""
        filter_slug = f"_PriceRange_{min_price}USD-{max_price}USD{today_slug}"

        urls = []
        # 1. Departamentos
        base_deptos = "https://inmuebles.mercadolibre.com.ar/departamentos/venta/capital-federal/"
        if page > 1:
            offset = (page - 1) * 48 + 1
            urls.append(f"{base_deptos}_Desde_{offset}{filter_slug}")
        else:
            urls.append(f"{base_deptos}{filter_slug}")

        # 2. PHs (Propiedad Horizontal)
        base_ph = "https://inmuebles.mercadolibre.com.ar/ph/venta/capital-federal/"
        if page > 1:
            offset = (page - 1) * 48 + 1
            urls.append(f"{base_ph}_Desde_{offset}{filter_slug}")
        else:
            urls.append(f"{base_ph}{filter_slug}")

        return urls

    def fetch_page(self, url: str) -> Optional[str]:
        """Realiza la petición HTTP con reintentos y delay de cortesía."""
        headers = self._get_headers()
        for attempt in range(1, 4):
            try:
                time.sleep(random.uniform(1.0, 1.8))
                response = self.session.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 404:
                    return None
            except Exception as e:
                time.sleep(attempt * 1.5)
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
            if " - " in features_raw and "m²" in features_raw:
                m2_match = re.search(r'(\d+)\s*m[²2]', features_raw)
            else:
                m2_match = re.search(r'(\d+)\s*m[²2]', features_raw, re.IGNORECASE)
                
            if m2_match:
                m2_tot = int(m2_match.group(1))

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

            # 5. Imagen de Portada
            img_el = card.select_one('img')
            img_src = ""
            if img_el:
                img_src = img_el.get('src') or img_el.get('data-src') or img_el.get('data-lazy') or ""

            return {
                "id": posting_id,
                "title": title or f"Propiedad {ambientes or ''} amb en {location_raw}".strip(),
                "description": title,
                "source": "Mercado Libre",
                "source_badge": "🟡 Mercado Libre",
                "publication_date_text": "Publicado hoy",
                "is_new": True,
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
                "is_development": False,
            }
        except Exception:
            return None

    def scrape(self, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """Ejecuta el rastreo estricto de publicaciones de HOY en Mercado Libre."""
        pages = max_pages or self.search_cfg.get("pages_to_scrape", 3)
        all_raw_properties = []
        seen_ids = set()

        print(f"\n[Scraper MercadoLibre] Iniciando rastreo de publicaciones de HOY en CABA...")
        print(f"[Scraper MercadoLibre] Filtro: Publicados Hoy | Precio Máx: USD {self.search_cfg.get('max_price_usd', 80000):,}")

        for page in range(1, pages + 1):
            urls = self.build_urls(page=page)
            for url in urls:
                cat_name = "Deptos" if "/departamentos/" in url else "PHs"
                html = self.fetch_page(url)
                if not html:
                    continue

                soup = BeautifulSoup(html, "html.parser")
                cards = soup.select('li.ui-search-layout__item, div.ui-search-result__wrapper, div.poly-card')

                page_count = 0
                for card in cards:
                    prop = self.parse_card(card)
                    if prop and prop["id"] not in seen_ids:
                        seen_ids.add(prop["id"])
                        all_raw_properties.append(prop)
                        page_count += 1

                print(f"    [MercadoLibre] {cat_name} Pág {page}: {len(cards)} avisos de hoy ({page_count} procesados)")

        print(f"[Scraper MercadoLibre] Finalizado. Total de avisos de HOY: {len(all_raw_properties)}")
        return all_raw_properties
