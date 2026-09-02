"""
Módulo de almacenamiento e historial de oportunidades inmobiliarias y métricas de mercado.
Permite persistir las propiedades vistas para identificar rápidamente novedades del día
y registrar snapshots diarios para análisis de tendencias de mercado.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Tuple, List

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")

def load_history() -> Dict[str, Any]:
    """Carga el historial de propiedades vistas y snapshots diarios desde el archivo JSON."""
    if not os.path.exists(HISTORY_FILE):
        return {"properties": {}, "daily_snapshots": [], "last_run": None}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "daily_snapshots" not in data:
                data["daily_snapshots"] = []
            if "properties" not in data:
                data["properties"] = {}
            return data
    except Exception as e:
        print(f"[Aviso] Error al leer {HISTORY_FILE}: {e}. Iniciando historial nuevo.")
        return {"properties": {}, "daily_snapshots": [], "last_run": None}

def save_history(history: Dict[str, Any]) -> None:
    """Guarda el historial actualizado."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Error] No se pudo guardar el historial: {e}")

def process_properties_history(properties: list) -> Tuple[list, int]:
    """
    Compara las propiedades encontradas con el historial.
    Marca `is_new=True` para avisos que nunca se habían visto antes o vistos hoy por primera vez.
    Retorna la lista de propiedades procesada y el total de propiedades nuevas detectadas.
    """
    history = load_history()
    seen_dict = history.get("properties", {})
    today_str = datetime.now().strftime("%Y-%m-%d")
    now_iso = datetime.now().isoformat()
    new_count = 0

    for prop in properties:
        prop_id = str(prop.get("id"))
        if not prop_id:
            prop["is_new"] = False
            prop["first_seen"] = today_str
            continue

        if prop_id not in seen_dict:
            # Propiedad totalmente nueva
            seen_dict[prop_id] = {
                "first_seen": today_str,
                "first_seen_timestamp": now_iso,
                "price": prop.get("price_val"),
                "usd_m2": prop.get("usd_m2"),
                "barrio": prop.get("barrio"),
                "ambientes": prop.get("ambientes"),
                "title": prop.get("title", "")
            }
            prop["is_new"] = True
            prop["first_seen"] = today_str
            new_count += 1
        else:
            # Ya existía en el historial
            first_seen_date = seen_dict[prop_id].get("first_seen", today_str)
            prop["is_new"] = (first_seen_date == today_str)
            prop["first_seen"] = first_seen_date
            seen_dict[prop_id]["last_seen_price"] = prop.get("price_val")
            seen_dict[prop_id]["last_seen_timestamp"] = now_iso

    history["properties"] = seen_dict
    history["last_run"] = now_iso
    save_history(history)

    return properties, new_count

def record_daily_market_snapshot(market_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Registra un snapshot diario de métricas agregadas del mercado para análisis de series temporales.
    Retorna la lista completa de snapshots históricos.
    """
    history = load_history()
    snapshots = history.get("daily_snapshots", [])
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Crear o actualizar el snapshot del día
    snapshot_entry = {
        "date": today_str,
        "timestamp": datetime.now().isoformat(),
        "total_properties": market_metrics.get("total_properties", 0),
        "new_today": market_metrics.get("new_today", 0),
        "avg_usd_m2": market_metrics.get("avg_usd_m2", 0),
        "min_price": market_metrics.get("min_price", 0),
        "median_price": market_metrics.get("median_price", 0),
        "super_deals_count": market_metrics.get("super_deals_count", 0),
        "top_neighborhoods": market_metrics.get("top_neighborhoods_summary", [])
    }

    # Reemplazar si ya existía hoy o agregar nuevo
    existing_idx = next((i for i, s in enumerate(snapshots) if s.get("date") == today_str), None)
    if existing_idx is not None:
        snapshots[existing_idx] = snapshot_entry
    else:
        snapshots.append(snapshot_entry)

    # Mantener orden cronológico y limitar a los últimos 90 días
    snapshots = sorted(snapshots, key=lambda x: x["date"])[-90:]
    history["daily_snapshots"] = snapshots
    save_history(history)

    return snapshots
