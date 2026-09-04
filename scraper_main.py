"""
Zonaprop Hunter CABA - Script Principal
Rastreador, Evaluador y Monitor de Market Intelligence Inmobiliario en Capital Federal.
Mantiene un histórico activo de oportunidades de los últimos 10 días.
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
from evaluator import evaluate_and_rank_properties
from storage import merge_and_sync_history, record_daily_market_snapshot, load_history
from market_analytics import compute_market_analytics
from html_generator import generate_html_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DEFAULT_OUTPUT_HTML = os.path.join(BASE_DIR, "output", "zonaprop_oportunidades.html")
ROOT_INDEX_HTML = os.path.join(BASE_DIR, "index.html")

class DualLogger:
    def __init__(self, filepath, orig_stream, append=False):
        self.orig_stream = orig_stream
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        mode = "a" if append else "w"
        self.file = open(filepath, mode, encoding="utf-8", errors="replace")

    def write(self, data):
        self.orig_stream.write(data)
        self.file.write(data)
        self.file.flush()

    def flush(self):
        self.orig_stream.flush()
        self.file.flush()

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def main():
    log_dir = os.path.join(BASE_DIR, "logs")
    last_log = os.path.join(log_dir, "task_last_run.log")
    try:
        sys.stdout = DualLogger(last_log, sys.stdout)
        sys.stderr = DualLogger(last_log, sys.stderr, append=True)
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Zonaprop Hunter - Oportunidades & Market Intelligence CABA")
    parser.add_argument("--max-price", type=int, help="Precio maximo en USD (ej: 75000)")
    parser.add_argument("--min-price", type=int, help="Precio minimo en USD (ej: 20000)")
    parser.add_argument("--pages", type=int, help="Cantidad de paginas de Zonaprop a consultar (ej: 5)")
    parser.add_argument("--barrios", type=str, help="Barrios separados por coma (ej: palermo,recoleta,caballito)")
    parser.add_argument("--max-usd-m2", type=int, help="Tope maximo de USD por m2 (ej: 1900)")
    parser.add_argument("--retention-days", type=int, help="Cantidad de dias de historico a retener en cartera (ej: 10)")
    parser.add_argument("--all-dates", action="store_true", help="Desactivar filtro estricto de hoy y traer todos los recientes")
    parser.add_argument("--sort", type=str, choices=["orden-publicado-descendente", "orden-precio-menor"], help="Criterio de ordenamiento en Zonaprop")
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
    if args.all_dates:
        search_cfg["only_published_today"] = False
    if args.retention_days:
        search_cfg["history_retention_days"] = args.retention_days
    if args.sort:
        search_cfg["sort_by"] = args.sort
    if args.barrios:
        search_cfg["filter_barrios"] = [b.strip() for b in args.barrios.split(",") if b.strip()]

    only_today = search_cfg.get("only_published_today", True)
    retention_days = search_cfg.get("history_retention_days", 10)
    output_file = args.output or DEFAULT_OUTPUT_HTML

    print("=" * 68)
    print(" [ZONAPROP HUNTER & MARKET INTELLIGENCE CABA]")
    print(f" Fecha y Hora:        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Filtro Precio Max:   USD {search_cfg.get('max_price_usd', 80000):,}")
    print(f" Tope USD/m2:         USD {search_cfg.get('max_usd_m2', 2200):,}")
    print(f" Modo Publicados Hoy: {' ACTIVADO (Solo avisos de hoy)' if only_today else ' Todos los recientes'}")
    print(f" Histórico en cartera:{retention_days} días de retención continua")
    print(f" Paginas a explorar:  {search_cfg.get('pages_to_scrape', 5)}")
    if search_cfg.get("filter_barrios"):
        print(f" Barrios filtrados:   {', '.join(search_cfg['filter_barrios'])}")
    print("=" * 68)

    # 1. Scrapear propiedades de Zonaprop
    scraper = ZonapropScraper(config)
    raw_properties = scraper.scrape(max_pages=search_cfg.get("pages_to_scrape", 5))

    if not raw_properties:
        print("\n[Aviso] No se encontraron avisos nuevos en Zonaprop en esta corrida.")
        # Aun asi, si hay histórico previo de los últimos 10 días, cargarlo para no dejar la web vacía
        processed_properties, new_count = merge_and_sync_history([], retention_days=retention_days)
    else:
        # 2. Evaluar y rankear oportunidades (filtro anti-pozos activo)
        print("\n[Evaluador] Analizando y calculando scores de oportunidad en Zonaprop...")
        ranked_properties = evaluate_and_rank_properties(raw_properties, config)

        # 3. Procesar y sincronizar con el histórico de los últimos 10 días
        print(f"[Historial] Sincronizando cartera acumulada de los últimos {retention_days} días...")
        processed_properties, new_count = merge_and_sync_history(ranked_properties, retention_days=retention_days)

    # 4. Calcular Inteligencia de Mercado y Métricas Avanzadas
    print("[Market Intelligence] Generando mapas de calor, matrices y radar de insights...")
    history_data = load_history()
    past_snapshots = history_data.get("daily_snapshots", [])
    
    analytics = compute_market_analytics(processed_properties, config, historical_snapshots=past_snapshots)
    
    # Registrar snapshot diario en el acumulador histórico
    record_daily_market_snapshot(analytics.get("macro", {}))

    # 5. Generar Reporte HTML (en output/ y en index.html para Vercel)
    print(f"[Reporte] Generando dashboard interactivo en: {output_file}")
    generated_path = generate_html_report(processed_properties, analytics, output_file)
    
    try:
        shutil.copyfile(output_file, ROOT_INDEX_HTML)
        print(f"[Vercel] Actualizado index.html en la raíz del proyecto.")
    except Exception as e:
        print(f"[Aviso] No se pudo copiar a index.html: {e}")

    # 6. Resumen de resultados en consola
    macro = analytics.get("macro", {})
    print("\n" + "=" * 68)
    print(f" 📊 RESUMEN EJECUTIVO (CARTERA ACTIVA {retention_days} DÍAS)")
    print("=" * 68)
    print(f" ✅ Total avisos rastreados en esta corrida: {len(raw_properties)}")
    print(f" ✨ Nuevas oportunidades detectadas hoy:     {new_count}")
    print(f" 💎 Total oportunidades activas en cartera: {len(processed_properties)}")
    print(f" 📐 Valor medio metro cuadrado:             USD {macro.get('avg_usd_m2', 0):,}/m²")
    print(f" 🏷️ Descuento medio vs barrio:              {macro.get('avg_discount_pct', 0)}%")
    print(f" 🚪 Mediana de precio en oferta:            USD {macro.get('median_price', 0):,}")

    if processed_properties:
        top_deal = processed_properties[0]
        days_ago = top_deal.get("days_ago", 0)
        age_str = "Hoy" if days_ago == 0 else f"Hace {days_ago} días"
        print(f"\n 🔥 TOP OPORTUNIDAD EN CARTERA:")
        print(f"    - Barrio:      {top_deal['barrio']} ({top_deal.get('address', 'Sin calle')})")
        print(f"    - Precio:      {top_deal['price_usd_formatted']} ({top_deal['usd_m2_formatted']})")
        print(f"    - Detección:   {top_deal.get('first_seen_date', 'Hoy')} ({age_str})")
        print(f"    - Descuento:   {top_deal['discount_pct']}% vs promedio del barrio")
        print(f"    - Link:        {top_deal['link']}")

    insights = analytics.get("insights", [])
    if insights:
        print(f"\n 🎯 INSIGHTS DEL RADAR:")
        for ins in insights[:3]:
            print(f"    • {ins['title']}: {ins['desc']}")

    print("\n[OK] Dashboard y reporte HTML generado exitosamente.")
    
    # 7. Abrir en navegador
    if not args.no_browser:
        abs_path = os.path.abspath(generated_path)
        print(f"[Navegador] Abriendo {abs_path}...")
        webbrowser.open(f"file:///{abs_path.replace(os.sep, '/')}")

if __name__ == "__main__":
    main()
