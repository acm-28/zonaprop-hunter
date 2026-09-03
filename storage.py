"""
Módulo de almacenamiento e historial de oportunidades inmobiliarias y métricas de mercado.
Mantiene un histórico acumulativo de los últimos N días (por defecto 10 días) para que
la cartera de oportunidades no se reinicie a cero cada día, sino que acumule las mejores
opciones de compra detectadas recientemente.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")

def load_history() -> Dict[str, Any]:
    """Carga el historial desde el archivo JSON."""
    if not os.path.exists(HISTORY_FILE):
        return {"active_deals": {}, "properties": {}, "daily_snapshots": [], "last_run": None}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "active_deals" not in data:
                data["active_deals"] = {}
            if "daily_snapshots" not in data:
                data["daily_snapshots"] = []
            if "properties" not in data:
                data["properties"] = {}
            return data
    except Exception as e:
        print(f"[Aviso] Error al leer {HISTORY_FILE}: {e}. Iniciando historial nuevo.")
        return {"active_deals": {}, "properties": {}, "daily_snapshots": [], "last_run": None}

def save_history(history: Dict[str, Any]) -> None:
    """Guarda el historial actualizado con formato legible."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Error] No se pudo guardar el historial: {e}")

def merge_and_sync_history(today_properties: List[Dict[str, Any]], retention_days: int = 10) -> Tuple[List[Dict[str, Any]], int]:
    """
    Combina las propiedades recolectadas hoy con el histórico de oportunidades activas
    de los últimos N días (por defecto 10 días).
    
    1. Elimina automáticamente propiedades con más de retention_days de antigüedad.
    2. Agrega las oportunidades detectadas hoy asignando first_seen_date y is_new=True.
    3. Si una propiedad ya existía, actualiza su precio o datos conservando su fecha original.
    4. Calcula days_ago para cada propiedad para filtrado dinámico en la interfaz.
    5. Retorna la lista consolidada de los últimos 10 días y la cantidad de novedades de hoy.
    """
    history = load_history()
    active_deals = history.get("active_deals", {})
    seen_legacy = history.get("properties", {})
    
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    cutoff_date = now - timedelta(days=retention_days)
    new_today_count = 0

    # 1. Purgar oportunidades con más de retention_days de antigüedad
    purged_deals = {}
    for prop_id, prop_data in active_deals.items():
        first_seen_str = prop_data.get("first_seen_date", today_str)
        try:
            first_seen_dt = datetime.strptime(first_seen_str, "%Y-%m-%d")
            if first_seen_dt >= cutoff_date:
                days_diff = (now - first_seen_dt).days
                prop_data["days_ago"] = max(0, days_diff)
                prop_data["is_new"] = (first_seen_str == today_str)
                purged_deals[prop_id] = prop_data
        except Exception:
            purged_deals[prop_id] = prop_data

    active_deals = purged_deals

    # 2. Incorporar oportunidades detectadas hoy
    for prop in today_properties:
        prop_id = str(prop.get("id"))
        if not prop_id:
            continue

        if prop_id in active_deals:
            # Ya existía en los últimos 10 días: actualizar valores conservando first_seen_date
            orig_date = active_deals[prop_id].get("first_seen_date", today_str)
            first_seen_dt = datetime.strptime(orig_date, "%Y-%m-%d") if orig_date else now
            days_diff = (now - first_seen_dt).days
            
            prop_copy = dict(prop)
            prop_copy["first_seen_date"] = orig_date
            prop_copy["days_ago"] = max(0, days_diff)
            prop_copy["is_new"] = (orig_date == today_str)
            prop_copy["last_synced"] = now.isoformat()
            active_deals[prop_id] = prop_copy
        else:
            # Nueva oportunidad detectada hoy
            prop_copy = dict(prop)
            prop_copy["first_seen_date"] = today_str
            prop_copy["days_ago"] = 0
            prop_copy["is_new"] = True
            prop_copy["last_synced"] = now.isoformat()
            active_deals[prop_id] = prop_copy
            new_today_count += 1

        # Mantener registro de vistos para deduplicación histórica
        seen_legacy[prop_id] = {
            "first_seen": active_deals[prop_id].get("first_seen_date", today_str),
            "last_price": prop.get("price_val"),
            "barrio": prop.get("barrio")
        }

    history["active_deals"] = active_deals
    history["properties"] = seen_legacy
    history["last_run"] = now.isoformat()
    save_history(history)

    # Convertir a lista y ordenar por Score de Oportunidad de mayor a menor
    consolidated_list = list(active_deals.values())
    consolidated_list.sort(key=lambda x: (x.get("opportunity_score", 0), -x.get("usd_m2", 99999)), reverse=True)

    return consolidated_list, new_today_count

# Compatibilidad con código anterior
def process_properties_history(properties: list) -> Tuple[list, int]:
    return merge_and_sync_history(properties, retention_days=10)

def record_daily_market_snapshot(market_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Registra un snapshot diario de métricas agregadas del mercado."""
    history = load_history()
    snapshots = history.get("daily_snapshots", [])
    today_str = datetime.now().strftime("%Y-%m-%d")

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

    existing_idx = next((i for i, s in enumerate(snapshots) if s.get("date") == today_str), None)
    if existing_idx is not None:
        snapshots[existing_idx] = snapshot_entry
    else:
        snapshots.append(snapshot_entry)

    snapshots = sorted(snapshots, key=lambda x: x["date"])[-90:]
    history["daily_snapshots"] = snapshots
    save_history(history)

    return snapshots
