"""
InmoHunter CABA - Script Principal Multi-Portal
Rastreador, Evaluador y Monitor de Market Intelligence Inmobiliario (Zonaprop + Mercado Libre).
"""

import os
import sys

# Configurar encoding UTF-8 en stdout/stderr para compatibilidad con terminales Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import json
import shutil
import argparse
import webbrowser
from datetime import datetime

from scraper import ZonapropScraper
from mercadolibre_scraper import MercadoLibreScraper
from evaluator import evaluate_and_rank_properties
from storage import process_properties_history, record_daily_market_snapshot, load_history
from market_analytics import compute_market_analytics
from html_generator import generate_html_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DEFAULT_OUTPUT_HTML = os.path.join(BASE_DIR, "output", "zonaprop_oportunidades.html")
ROOT_INDEX_HTML = os.path.join(BASE_DIR, "index.html")

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def main():
    parser = argparse.ArgumentParser(description="InmoHunter - Oportunidades & Market Intelligence CABA (Zonaprop + Mercado Libre)")
    parser.add_argument("--max-price", type=int, help="Precio maximo en USD (ej: 75000)")
    parser.add_argument("--min-price", type=int, help="Precio minimo en USD (ej: 20000)")
    parser.add_argument("--pages", type=int, help="Cantidad de paginas por portal a consultar (ej: 4)")
    parser.add_argument("--barrios", type=str, help="Barrios separados por coma (ej: palermo,recoleta,caballito)")
    parser.add_argument("--max-usd-m2", type=int, help="Tope maximo de USD por m2 (ej: 1900)")
    parser.add_argument("--sources", type=str, help="Portales a consultar separados por coma (ej: zonaprop,mercadolibre)")
    parser.add_argument("--only-today", action="store_true", help="Filtrar estrictamente SOLO anuncios publicados hoy")
    parser.add_argument("--sort", type=str, choices=["orden-publicado-descendente", "orden-precio-menor"], help="Criterio de ordenamiento en portales")
    parser.add_argument("--no-browser", action="store_true", help="No abrir automaticamente el navegador al finalizar")
    parser.add_argument("--output", type=str, help="Ruta de guardado del archivo HTML de reporte")
    
    args = parser.parse_args()

    config = load_config()
    search_cfg = config.setdefault("search", {})

    # Sobrescribir configuracion con argumentos CLI si fueron provistos
    if args.max_price:
        search_cfg["max_price_usd"] = args.max_price
    if args.min_price:
        search_cfg["min_price_usd"] = args.min_price
    if args.pages:
        search_cfg["pages_to_scrape"] = args.pages
    if args.max_usd_m2:
        search_cfg["max_usd_m2"] = args.max_usd_m2
    if args.only_today:
        search_cfg["only_published_today"] = True
    if args.sort:
        search_cfg["sort_by"] = args.sort
    if args.barrios:
        search_cfg["filter_barrios"] = [b.strip() for b in args.barrios.split(",") if b.strip()]
    if args.sources:
        search_cfg["enabled_sources"] = [s.strip().lower() for s in args.sources.split(",") if s.strip()]

    enabled_sources = search_cfg.get("enabled_sources", ["zonaprop", "mercadolibre"])
    output_file = args.output or DEFAULT_OUTPUT_HTML

    print("=" * 68)
    print(" [INMOHUNTER & MARKET INTELLIGENCE CABA - MULTI-PORTAL]")
    print(f" Fecha y Hora:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Portales Activos:   {', '.join([s.upper() for s in enabled_sources])}")
    print(f" Filtro Precio Max:  USD {search_cfg.get('max_price_usd', 80000):,}")
    print(f" Tope USD/m2:        USD {search_cfg.get('max_usd_m2', 2200):,}")
    print(f" Modo Publicados Hoy:{' ACTIVADO' if search_cfg.get('only_published_today') else ' Todos los recientes'}")
    print(f" Paginas por portal: {search_cfg.get('pages_to_scrape', 4)}")
    if search_cfg.get("filter_barrios"):
        print(f" Barrios filtrados:  {', '.join(search_cfg['filter_barrios'])}")
    print("=" * 68)

    all_raw_properties = []
    seen_ids = set()

    # 1. Scrapear Zonaprop si está habilitado
    if "zonaprop" in enabled_sources:
        try:
            zp_scraper = ZonapropScraper(config)
            zp_props = zp_scraper.scrape()
            for p in zp_props:
                if p["id"] not in seen_ids:
                    seen_ids.add(p["id"])
                    all_raw_properties.append(p)
        except Exception as e:
            print(f"[Error] Fallo al scrapear Zonaprop: {e}")

    # 2. Scrapear Mercado Libre si está habilitado
    if "mercadolibre" in enabled_sources or "meli" in enabled_sources:
        try:
            meli_scraper = MercadoLibreScraper(config)
            meli_props = meli_scraper.scrape()
            for p in meli_props:
                if p["id"] not in seen_ids:
                    seen_ids.add(p["id"])
                    all_raw_properties.append(p)
        except Exception as e:
            print(f"[Error] Fallo al scrapear Mercado Libre: {e}")

    if not all_raw_properties:
        print("\n[Aviso] No se encontraron avisos que coincidan con los criterios.")
        sys.exit(0)

    # 3. Evaluar y rankear oportunidades
    print("\n[Evaluador] Analizando y calculando scores de oportunidad multi-portal...")
    ranked_properties = evaluate_and_rank_properties(all_raw_properties, config)

    # 4. Procesar historial de propiedades (identificar novedades de hoy)
    processed_properties, new_count = process_properties_history(ranked_properties)

    # 5. Calcular Inteligencia de Mercado y Métricas Avanzadas
    print("[Market Intelligence] Generando mapas de calor, matrices y radar de insights...")
    history_data = load_history()
    past_snapshots = history_data.get("daily_snapshots", [])
    
    analytics = compute_market_analytics(processed_properties, config, historical_snapshots=past_snapshots)
    
    # Registrar snapshot diario en el acumulador histórico
    record_daily_market_snapshot(analytics.get("macro", {}))

    # 6. Generar Reporte HTML (en output/ y en index.html para Vercel)
    print(f"[Reporte] Generando dashboard interactivo en: {output_file}")
    generated_path = generate_html_report(processed_properties, analytics, output_file)
    
    try:
        shutil.copyfile(output_file, ROOT_INDEX_HTML)
        print(f"[Vercel] Actualizado index.html en la raíz del proyecto.")
    except Exception as e:
        print(f"[Aviso] No se pudo copiar a index.html: {e}")

    # 7. Resumen de resultados en consola
    macro = analytics.get("macro", {})
    zp_count = sum(1 for p in processed_properties if p.get("source") == "Zonaprop")
    meli_count = sum(1 for p in processed_properties if p.get("source") == "Mercado Libre")

    print("\n" + "=" * 68)
    print(" 📊 RESUMEN EJECUTIVO MULTI-PORTAL")
    print("=" * 68)
    print(f" ✅ Total avisos analizados:        {len(all_raw_properties)} (Zonaprop: {len([p for p in all_raw_properties if p.get('source')=='Zonaprop'])}, MeLi: {len([p for p in all_raw_properties if p.get('source')=='Mercado Libre'])})")
    print(f" 💎 Oportunidades calificadas CABA: {len(processed_properties)} (Zonaprop: {zp_count}, MeLi: {meli_count})")
    print(f" ✨ Nuevas oportunidades hoy:       {new_count}")
    print(f" 📐 Valor medio metro cuadrado:     USD {macro.get('avg_usd_m2', 0):,}/m²")
    print(f" 🏷️ Descuento medio vs barrio:      {macro.get('avg_discount_pct', 0)}%")
    print(f" 🚪 Mediana de precio en oferta:    USD {macro.get('median_price', 0):,}")

    if processed_properties:
        top_deal = processed_properties[0]
        print(f"\n 🔥 TOP OPORTUNIDAD DEL DIA:")
        print(f"    - Portal:      {top_deal.get('source_badge', top_deal.get('source'))}")
        print(f"    - Barrio:      {top_deal['barrio']} ({top_deal.get('address', 'Sin calle')})")
        print(f"    - Precio:      {top_deal['price_usd_formatted']} ({top_deal['usd_m2_formatted']})")
        print(f"    - Descuento:   {top_deal['discount_pct']}% vs promedio del barrio")
        print(f"    - Link:        {top_deal['link']}")

    insights = analytics.get("insights", [])
    if insights:
        print(f"\n 🎯 INSIGHTS DEL RADAR:")
        for ins in insights[:3]:
            print(f"    • {ins['title']}: {ins['desc']}")

    print("\n[OK] Dashboard y reporte HTML generado exitosamente.")
    
    # 8. Abrir en navegador
    if not args.no_browser:
        abs_path = os.path.abspath(generated_path)
        print(f"[Navegador] Abriendo {abs_path}...")
        webbrowser.open(f"file:///{abs_path.replace(os.sep, '/')}")

if __name__ == "__main__":
    main()
