"""
Módulo de evaluación y scoring de oportunidades inmobiliarias.
Analiza cada propiedad, calcula el valor por m2, compara contra el benchmark del barrio y asigna un Score de Oportunidad.
Filtra de forma estricta pozos, preventas, emprendimientos, rangos multi-unidad y cocheras.
"""

import re
import unicodedata
from typing import Dict, Any, Optional, List

NEIGHBORHOOD_DEMAND_VIEWS = {
    "Palermo": 65, "Recoleta": 55, "Belgrano": 50, "Caballito": 55,
    "Villa Urquiza": 48, "Colegiales": 45, "Villa Crespo": 45,
    "Chacarita": 40, "Almagro": 42, "San Telmo": 38, "Villa Devoto": 36,
    "Nuñez": 48, "Nunez": 48, "Coghlan": 35, "Saavedra": 35, "Parque Centenario": 45,
    "Flores": 32, "Floresta": 28, "Boedo": 30, "Barracas": 26,
    "Parque Patricios": 32, "Parque Chacabuco": 32, "Balvanera": 38,
    "Once": 25, "Congreso": 30, "Monserrat": 25, "San Nicolas": 28,
    "San Nicolás": 28, "Centro / Microcentro": 25, "San Cristobal": 25,
    "San Cristóbal": 25, "Constitucion": 22, "Constitución": 22,
    "Villa del Parque": 35, "Paternal": 30, "Agronomia": 32,
    "Agronomía": 32, "Villa Santa Rita": 30, "Villa General Mitre": 30,
    "Villa Luro": 30, "Villa Pueyrredon": 32, "Villa Pueyrredón": 32,
    "Villa Real": 28, "Versalles": 28, "Monte Castro": 30,
    "Mataderos": 25, "Liniers": 26, "Nueva Pompeya": 22,
    "Villa Lugano": 20, "Villa Soldati": 20, "Default_CABA": 30
}

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
    
    min_price = search_cfg.get("min_price_usd", 25000)
    max_price = search_cfg.get("max_price_usd", 100000)
    min_m2 = search_cfg.get("min_m2", 48)
    max_usd_m2_limit = search_cfg.get("max_usd_m2", 2100)
    include_devs = search_cfg.get("include_developments", False)
    
    allowed_barrios = [normalize_text(b) for b in search_cfg.get("allowed_barrios", []) if b]
    excluded_barrios = [normalize_text(b) for b in search_cfg.get("excluded_barrios", []) if b]
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

    # 3. Validar Superficie m2 (Estricto >= 48 m2)
    m2_tot = raw_prop.get("m2_tot")
    if not m2_tot or m2_tot < min_m2:
        return None

    # 4. Descartar cocheras / bauleras
    title_norm = normalize_text(raw_prop.get("title", ""))
    ambientes = raw_prop.get("ambientes")
    
    if "cochera" in title_norm or "baulera" in title_norm or "garaje" in title_norm:
        if m2_tot < 25 and (ambientes is None or ambientes <= 1):
            return None

    # 5. Filtrar por Zonas y Barrios (Zonas Seguras, Cerca de Recoleta / Con Subte)
    location_raw = raw_prop.get("location", "")
    norm_loc = normalize_text(location_raw)
    title_norm = normalize_text(raw_prop.get("title", ""))
    full_loc_text = f"{norm_loc} {title_norm}"
    
    barrio_name, barrio_benchmark = match_neighborhood_benchmark(location_raw, benchmarks)
    norm_barrio = normalize_text(barrio_name)

    # A. Descartar estrictamente si pertenece a la lista de zonas excluidas
    for ex_b in excluded_barrios:
        if ex_b in norm_loc or ex_b in norm_barrio or (len(ex_b) >= 5 and ex_b in title_norm):
            return None

    # B. Verificar que pertenezca a la lista de zonas permitidas
    if allowed_barrios:
        is_allowed = any(
            ab in norm_loc or ab in norm_barrio or ab == norm_barrio
            for ab in allowed_barrios
        )
        if not is_allowed:
            return None

    # C. Filtro adicional manual si fue solicitado por CLI (--barrios)
    if filter_barrios:
        if not any(fb in norm_loc or fb in norm_barrio for fb in filter_barrios):
            return None

    # 6. Calcular USD / m2
    usd_m2 = round(price_val / m2_tot)
    if usd_m2 > max_usd_m2_limit or usd_m2 < 300:
        return None

    # 7. Calcular descuento porcentual vs benchmark del barrio
    discount_pct = round(((barrio_benchmark - usd_m2) / barrio_benchmark) * 100, 1)

    # Descartar propiedades que estén por encima del benchmark del barrio
    if discount_pct < 0:
        return None

    # 8. Calificación y Badge de Oportunidad (mínimo exigido: 'Buen Precio')
    if discount_pct >= 30 or (usd_m2 <= 1300 and barrio_benchmark >= 1800 and discount_pct >= 15):
        badge_text = "🔥 Super Oportunidad"
        badge_class = "badge-super"
    elif discount_pct >= 18 or (usd_m2 <= 1450 and barrio_benchmark >= 1800 and discount_pct >= 10):
        badge_text = "💎 Gran Oportunidad"
        badge_class = "badge-great"
    elif discount_pct >= 5 or (usd_m2 <= 1650 and discount_pct >= 0):
        badge_text = "🏷️ Buen Precio"
        badge_class = "badge-good"
    else:
        # No califica como oportunidad (es precio normal o poco atractivo): se descarta
        return None

    # 9. Score de Oportunidad (0 a 100)
    discount_score = max(0, min(100, (discount_pct + 5) * 2.2))
    price_score = max(0, min(100, (1 - (price_val - min_price) / max(1, max_price - min_price)) * 100))
    benchmark_weight = min(100, (barrio_benchmark / 2600) * 100)
    
    opportunity_score = round(0.60 * discount_score + 0.25 * price_score + 0.15 * benchmark_weight)
    opportunity_score = max(30, min(99, opportunity_score))

    # 10. Vistas y Demanda Comercial (Dato Real de Zonaprop)
    user_views = raw_prop.get("user_views")
    if user_views is None:
        user_views = 0

    source = raw_prop.get("source", "Zonaprop")
    source_badge = raw_prop.get("source_badge", f"🔵 {source}")

    enriched = dict(raw_prop)
    enriched.update({
        "barrio": barrio_name,
        "barrio_benchmark_m2": int(barrio_benchmark),
        "usd_m2": usd_m2,
        "discount_pct": discount_pct,
        "opportunity_score": opportunity_score,
        "user_views": user_views,
        "user_views_formatted": f"{user_views:,}".replace(",", "."),
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
