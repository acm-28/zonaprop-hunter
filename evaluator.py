"""
Módulo de evaluación y scoring de oportunidades inmobiliarias.
Analiza cada propiedad, calcula el valor por m2, compara contra el benchmark del barrio y asigna un Score de Oportunidad.
Filtra de forma estricta pozos, preventas, emprendimientos, rangos multi-unidad y cocheras.
"""

import re
import unicodedata
from typing import Dict, Any, Optional, List

def normalize_text(text: str) -> str:
    """Normaliza texto eliminando tildes y caracteres especiales para matching uniforme."""
    if not text:
        return ""
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    return text.strip().lower()

def is_pozo_or_development(prop: Dict[str, Any]) -> bool:
    """
    Verifica de forma estricta si un aviso es un pozo, preventa, emprendimiento o desarrollo inmobiliario.
    """
    text_to_check = " ".join([
        str(prop.get("title", "")),
        str(prop.get("description", "")),
        str(prop.get("features_raw", "")),
        str(prop.get("price_raw", "")),
        str(prop.get("location", "")),
        str(prop.get("link", ""))
    ]).lower()

    # Si la superficie o ambientes son rangos (ej: "25 - 89 m²", "1 a 4 ambs"), es un proyecto multi-unidad
    feat_text = str(prop.get("features_raw", ""))
    title_text = str(prop.get("title", ""))
    if re.search(r'\d+\s*-\s*\d+\s*m[²2]', feat_text) or re.search(r'\d+\s*a\s*\d+\s*amb', feat_text) or re.search(r'\d+\s*,\s*\d+\s*y\s*\d+\s*amb', title_text):
        return True

    # Patrones estrictos de pozos, preventas, emprendimientos y entregas futuras
    pozo_patterns = [
        r'\bpozo\b',
        r'\ben pozo\b',
        r'\bde pozo\b',
        r'\ba pozo\b',
        r'\bemprendimiento\b',
        r'\bedificio en pozo\b',
        r'\bpreventa\b',
        r'\ben construcci[oó]n\b',
        r'\bunidades disponibles\b',
        r'\bunidades en venta\b',
        r'\bdesde\b',
        r'\bcuotas\b',
        r'\bfinanciaci[oó]n\b',
        r'/emprendimiento/',
        r'ememvein',
        r'\b202[5-9]\b',                # Años futuros 2025, 2026, 2027, etc.
        r'\ba estrenar en\b',
        r'\bposesi[oó]n\b',
        r'\bentrega en\b',
        r'\bfideicomiso\b',
        r'\bal pozo\b',
        r'\bestudios\s*1\b',
        r'\ben pozo o a estrenar\b'
    ]

    for pat in pozo_patterns:
        if re.search(pat, text_to_check, re.IGNORECASE):
            return True

    return False

def match_neighborhood_benchmark(neighborhood_raw: str, benchmarks: Dict[str, float]) -> tuple[str, float]:
    """
    Identifica el barrio a partir del texto de ubicación y retorna (nombre_limpio, benchmark_usd_m2).
    """
    default_val = benchmarks.get("Default_CABA", 1900.0)
    norm_loc = normalize_text(neighborhood_raw)
    
    # 1. Coincidencia directa o subcadena
    for b_name, b_val in benchmarks.items():
        if b_name == "Default_CABA":
            continue
        norm_b = normalize_text(b_name)
        if norm_b in norm_loc:
            return b_name, float(b_val)
            
    # 2. Separar por comas/guiones
    parts = [p.strip() for p in re.split(r'[,\-|/]', neighborhood_raw) if p.strip()]
    for p in parts:
        norm_p = normalize_text(p)
        for b_name, b_val in benchmarks.items():
            if b_name == "Default_CABA":
                continue
            norm_b = normalize_text(b_name)
            if norm_b == norm_p or norm_b in norm_p:
                return b_name, float(b_val)
                
    return "CABA (General)", default_val

def evaluate_property(raw_prop: Dict[str, Any], config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Evalúa, valida y enriquece una propiedad con métricas financieras y de oportunidad.
    Descarta estrictamente pozos, emprendimientos, cocheras o precios inconsistentes.
    """
    search_cfg = config.get("search", {})
    benchmarks = config.get("neighborhood_benchmarks_usd_m2", {})
    
    min_price = search_cfg.get("min_price_usd", 18000)
    max_price = search_cfg.get("max_price_usd", 80000)
    min_m2 = search_cfg.get("min_m2", 18)
    max_usd_m2_limit = search_cfg.get("max_usd_m2", 2200)
    include_devs = search_cfg.get("include_developments", False)
    filter_barrios = [normalize_text(b) for b in search_cfg.get("filter_barrios", []) if b]

    # 1. Filtro estricto anti-pozos y anti-emprendimientos
    if not include_devs and is_pozo_or_development(raw_prop):
        return None

    # 2. Validar Precio en USD
    price_val = raw_prop.get("price_val")
    currency = raw_prop.get("currency", "USD")
    
    if currency != "USD" or not price_val:
        return None
    
    if price_val < min_price or price_val > max_price:
        return None

    # 3. Validar Superficie m2
    m2_tot = raw_prop.get("m2_tot")
    if not m2_tot or m2_tot < min_m2:
        return None

    # 4. Descartar cocheras / bauleras
    title_norm = normalize_text(raw_prop.get("title", ""))
    ambientes = raw_prop.get("ambientes")
    
    if "cochera" in title_norm or "baulera" in title_norm or "garaje" in title_norm:
        if m2_tot < 25 and (ambientes is None or ambientes <= 1):
            return None

    # 5. Filtrar por barrios si fue solicitado
    location_raw = raw_prop.get("location", "")
    barrio_name, barrio_benchmark = match_neighborhood_benchmark(location_raw, benchmarks)
    
    if filter_barrios:
        norm_loc = normalize_text(location_raw)
        if not any(fb in norm_loc or fb in normalize_text(barrio_name) for fb in filter_barrios):
            return None

    # 6. Calcular USD / m2
    usd_m2 = round(price_val / m2_tot)
    if usd_m2 > max_usd_m2_limit or usd_m2 < 300:
        return None

    # 7. Calcular descuento porcentual vs benchmark del barrio
    discount_pct = round(((barrio_benchmark - usd_m2) / barrio_benchmark) * 100, 1)

    # 8. Score de Oportunidad (0 a 100)
    discount_score = max(0, min(100, (discount_pct + 10) * 1.8))
    price_score = max(0, min(100, (1 - (price_val - min_price) / max(1, max_price - min_price)) * 100))
    benchmark_weight = min(100, (barrio_benchmark / 2800) * 100)
    
    opportunity_score = round(0.55 * discount_score + 0.30 * price_score + 0.15 * benchmark_weight)
    opportunity_score = max(10, min(99, opportunity_score))

    # Badge de Oportunidad
    if discount_pct >= 35 or (usd_m2 <= 1300 and barrio_benchmark >= 2000):
        badge_text = "🔥 Super Oportunidad"
        badge_class = "badge-super"
    elif discount_pct >= 20 or (usd_m2 <= 1500 and barrio_benchmark >= 2000):
        badge_text = "💎 Gran Oportunidad"
        badge_class = "badge-great"
    elif discount_pct >= 10 or usd_m2 <= 1650:
        badge_text = "🏷️ Buen Precio"
        badge_class = "badge-good"
    else:
        badge_text = "📊 Precio Normal"
        badge_class = "badge-fair"

    source = raw_prop.get("source", "Zonaprop")
    source_badge = raw_prop.get("source_badge", f"🔵 {source}")

    enriched = dict(raw_prop)
    enriched.update({
        "barrio": barrio_name,
        "barrio_benchmark_m2": int(barrio_benchmark),
        "usd_m2": usd_m2,
        "discount_pct": discount_pct,
        "opportunity_score": opportunity_score,
        "badge_text": badge_text,
        "badge_class": badge_class,
        "source": source,
        "source_badge": source_badge,
        "price_usd_formatted": f"USD {price_val:,.0f}".replace(",", "."),
        "usd_m2_formatted": f"USD {usd_m2:,.0f}/m²".replace(",", "."),
        "benchmark_formatted": f"USD {int(barrio_benchmark):,.0f}/m²".replace(",", "."),
        "publication_date_text": raw_prop.get("publication_date_text", "Reciente")
    })

    return enriched

def evaluate_and_rank_properties(raw_properties: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Filtra, enriquece y ordena todas las propiedades recolectadas por score de oportunidad.
    """
    evaluated = []
    seen_ids = set()

    for p in raw_properties:
        prop_id = p.get("id")
        if prop_id in seen_ids:
            continue
        seen_ids.add(prop_id)
        
        eval_p = evaluate_property(p, config)
        if eval_p:
            evaluated.append(eval_p)

    # Ordenar por Score de Oportunidad de mayor a menor
    evaluated.sort(key=lambda x: (x.get("opportunity_score", 0), -x.get("usd_m2", 99999)), reverse=True)
    return evaluated
