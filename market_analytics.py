"""
Módulo de Inteligencia de Mercado Inmobiliario y Analytics para CABA.
Procesa el conjunto de datos de avisos para calcular métricas macro, mapas de calor por barrio,
distribución de precios, análisis por tipología y generación automatizada de insights para inversores.
"""

import statistics
from typing import List, Dict, Any

def compute_market_analytics(properties: List[Dict[str, Any]], config: Dict[str, Any], historical_snapshots: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Calcula el análisis completo de mercado a partir de las propiedades evaluadas.
    """
    if not properties:
        return {
            "macro": {},
            "neighborhoods": [],
            "typologies": {},
            "price_distribution": {},
            "insights": [],
            "timeline": historical_snapshots or []
        }

    prices = [p["price_val"] for p in properties if p.get("price_val")]
    sqm_prices = [p["usd_m2"] for p in properties if p.get("usd_m2")]
    discounts = [p.get("discount_pct", 0) for p in properties]
    m2_sizes = [p["m2_tot"] for p in properties if p.get("m2_tot")]

    # 1. Macro KPIs
    total_props = len(properties)
    new_today = sum(1 for p in properties if p.get("is_new") or "hoy" in str(p.get("publication_date_text", "")).lower())
    super_deals = sum(1 for p in properties if p.get("opportunity_score", 0) >= 75 or "Super" in str(p.get("badge_text", "")))
    
    avg_usd_m2 = round(statistics.mean(sqm_prices)) if sqm_prices else 0
    median_usd_m2 = round(statistics.median(sqm_prices)) if sqm_prices else 0
    min_price = min(prices) if prices else 0
    avg_price = round(statistics.mean(prices)) if prices else 0
    median_price = round(statistics.median(prices)) if prices else 0
    avg_discount = round(statistics.mean(discounts), 1) if discounts else 0.0

    macro_kpis = {
        "total_properties": total_props,
        "new_today": new_today,
        "super_deals_count": super_deals,
        "avg_usd_m2": avg_usd_m2,
        "median_usd_m2": median_usd_m2,
        "min_price": min_price,
        "avg_price": avg_price,
        "median_price": median_price,
        "avg_discount_pct": avg_discount,
        "avg_m2_size": round(statistics.mean(m2_sizes), 1) if m2_sizes else 0
    }

    # 2. Análisis y Mapa de Calor por Barrio
    benchmarks = config.get("neighborhood_benchmarks_usd_m2", {})
    barrio_groups = {}

    for p in properties:
        b = p.get("barrio", "CABA (General)")
        if b not in barrio_groups:
            barrio_groups[b] = []
        barrio_groups[b].append(p)

    neighborhoods_analytics = []
    for b_name, b_props in barrio_groups.items():
        b_prices = [p["price_val"] for p in b_props if p.get("price_val")]
        b_sqm = [p["usd_m2"] for p in b_props if p.get("usd_m2")]
        b_disc = [p.get("discount_pct", 0) for p in b_props]
        b_benchmark = b_props[0].get("barrio_benchmark_m2", benchmarks.get(b_name, 1900))
        b_super = sum(1 for p in b_props if p.get("opportunity_score", 0) >= 75 or "Super" in str(p.get("badge_text", "")))

        b_avg_sqm = round(statistics.mean(b_sqm)) if b_sqm else 0
        b_avg_disc = round(statistics.mean(b_disc), 1) if b_disc else 0.0
        b_min_p = min(b_prices) if b_prices else 0
        b_avg_p = round(statistics.mean(b_prices)) if b_prices else 0

        # Opportunity Density Score (0-100)
        density_score = min(100, round((b_avg_disc * 2.2) + (len(b_props) * 4) + (b_super * 15)))

        neighborhoods_analytics.append({
            "name": b_name,
            "count": len(b_props),
            "avg_usd_m2": b_avg_sqm,
            "benchmark_usd_m2": b_benchmark,
            "avg_discount_pct": b_avg_disc,
            "min_price": b_min_p,
            "avg_price": b_avg_p,
            "super_deals_count": b_super,
            "opportunity_density_score": max(10, density_score)
        })

    # Ordenar barrios por cantidad de oportunidades y luego por mejor descuento
    neighborhoods_analytics.sort(key=lambda x: (x["count"], x["avg_discount_pct"]), reverse=True)

    # 3. Matriz por Tipología (1, 2, 3+ Ambientes)
    typologies = {
        "1_amb": {"label": "Monoambientes (1 Amb)", "count": 0, "prices": [], "sqm": [], "m2": []},
        "2_amb": {"label": "2 Ambientes", "count": 0, "prices": [], "sqm": [], "m2": []},
        "3_plus_amb": {"label": "3+ Ambientes", "count": 0, "prices": [], "sqm": [], "m2": []}
    }

    for p in properties:
        amb = p.get("ambientes")
        key = "1_amb" if amb == 1 else ("2_amb" if amb == 2 else ("3_plus_amb" if amb and amb >= 3 else None))
        if key and key in typologies:
            typ = typologies[key]
            typ["count"] += 1
            if p.get("price_val"): typ["prices"].append(p["price_val"])
            if p.get("usd_m2"): typ["sqm"].append(p["usd_m2"])
            if p.get("m2_tot"): typ["m2"].append(p["m2_tot"])

    typology_summary = {}
    for k, v in typologies.items():
        typology_summary[k] = {
            "label": v["label"],
            "count": v["count"],
            "min_price": min(v["prices"]) if v["prices"] else 0,
            "avg_price": round(statistics.mean(v["prices"])) if v["prices"] else 0,
            "median_price": round(statistics.median(v["prices"])) if v["prices"] else 0,
            "avg_usd_m2": round(statistics.mean(v["sqm"])) if v["sqm"] else 0,
            "avg_m2": round(statistics.mean(v["m2"]), 1) if v["m2"] else 0
        }

    # 4. Distribución de Precios (Rangos)
    price_ranges = {
        "under_45k": {"label": "< USD 45.000", "count": 0, "color": "#10b981"},
        "45k_to_60k": {"label": "USD 45k - 60k", "count": 0, "color": "#38bdf8"},
        "60k_to_75k": {"label": "USD 60k - 75k", "count": 0, "color": "#818cf8"},
        "above_75k": {"label": "> USD 75.000", "count": 0, "color": "#f97316"}
    }

    for p in properties:
        val = p.get("price_val", 0)
        if val < 45000:
            price_ranges["under_45k"]["count"] += 1
        elif 45000 <= val < 60000:
            price_ranges["45k_to_60k"]["count"] += 1
        elif 60000 <= val < 75000:
            price_ranges["60k_to_75k"]["count"] += 1
        else:
            price_ranges["above_75k"]["count"] += 1

    # 5. Generación Automatizada de Insights de Mercado ("Radar del Experto")
    insights = []

    # Insight 1: Barrio más accesible por m2
    valid_barrios_by_m2 = [b for b in neighborhoods_analytics if b["count"] >= 1 and b["name"] != "CABA (General)"]
    if valid_barrios_by_m2:
        cheapest_barrio = min(valid_barrios_by_m2, key=lambda x: x["avg_usd_m2"])
        insights.append({
            "category": "ACCESIBILIDAD",
            "icon": "🏷️",
            "title": f"{cheapest_barrio['name']}: El metro cuadrado más accesible",
            "desc": f"Registra un valor medio de oportunidad de USD {cheapest_barrio['avg_usd_m2']:,}/m² con propiedades desde USD {cheapest_barrio['min_price']:,}.".replace(",", ".")
        })

    # Insight 2: Mayor potencial de revalorización / Arbitraje
    if valid_barrios_by_m2:
        top_discount_barrio = max(valid_barrios_by_m2, key=lambda x: x["avg_discount_pct"])
        if top_discount_barrio["avg_discount_pct"] > 0:
            insights.append({
                "category": "OPORTUNIDAD DE ARBITRAJE",
                "icon": "🚀",
                "title": f"{top_discount_barrio['name']} lidera el margen de descuento",
                "desc": f"Los avisos capturados promedian un descuento del {top_discount_barrio['avg_discount_pct']}% respecto al valor histórico del barrio (USD {top_discount_barrio['avg_usd_m2']:,}/m² vs benchmark USD {top_discount_barrio['benchmark_usd_m2']:,}/m²).".replace(",", ".")
            })

    # Insight 3: Tipología con mejor ticket de entrada
    if typology_summary.get("1_amb", {}).get("count", 0) > 0 and typology_summary.get("2_amb", {}).get("count", 0) > 0:
        mono_min = typology_summary["1_amb"]["min_price"]
        dos_min = typology_summary["2_amb"]["min_price"]
        insights.append({
            "category": "TICKET DE ENTRADA",
            "icon": "🚪",
            "title": "Brecha de acceso por tipología",
            "desc": f"El piso de entrada para un Monoambiente en CABA hoy es de USD {mono_min:,}, mientras que un 2 ambientes arranca en USD {dos_min:,}.".replace(",", ".")
        })

    # Insight 4: Concentración de Super Oportunidades
    if super_deals > 0:
        insights.append({
            "category": "RADAR DE OFERTAS",
            "icon": "🔥",
            "title": f"{super_deals} propiedades califican como 'Super Oportunidad'",
            "desc": f"Representan el {round((super_deals / total_props) * 100)}% de la oferta analizada, con precios y valores por m² más de 25% por debajo de la media zonal."
        })

    # Insight 5: Recomendación Estratégica del Algoritmo
    prime_barrios = ["Palermo", "Recoleta", "Belgrano", "Caballito", "Villa Crespo", "Colegiales"]
    prime_deals = [p for p in properties if any(pb in p.get("barrio", "") for pb in prime_barrios) and p.get("opportunity_score", 0) >= 60]
    if prime_deals:
        best_prime = prime_deals[0]
        insights.append({
            "category": "ZONA PRIME / ALTA DEMANDA",
            "icon": "💎",
            "title": f"Oportunidad líquida destacada en {best_prime['barrio']}",
            "desc": f"Unidad a {best_prime['price_usd_formatted']} ({best_prime['usd_m2_formatted']}) con {best_prime.get('discount_pct', 0)}% de descuento en zona de máxima demanda y reventa rápida."
        })

    # Preparar resumen para snapshot
    top_neighborhoods_summary = [
        {"name": b["name"], "count": b["count"], "avg_usd_m2": b["avg_usd_m2"]}
        for b in neighborhoods_analytics[:5]
    ]

    return {
        "macro": macro_kpis,
        "neighborhoods": neighborhoods_analytics,
        "typologies": typology_summary,
        "price_distribution": price_ranges,
        "insights": insights,
        "top_neighborhoods_summary": top_neighborhoods_summary,
        "timeline": historical_snapshots or []
    }
