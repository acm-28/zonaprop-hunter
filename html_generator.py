"""
Generador de Dashboard HTML interactivo para Oportunidades Inmobiliarias y Market Intelligence en CABA.
Crea un archivo HTML autónomo, moderno, responsivo, con gráficos interactivos, mapa geográfico de CABA con capas conmutables,
métricas de vistas y demanda comercial, favoritos, tracking de contacto y cartera acumulada de 10 días.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zonaprop Hunter CABA | Cartera & Market Intelligence</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
    <style>
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --bg-card-hover: #283548;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-primary: #38bdf8;
            --accent-green: #10b981;
            --accent-emerald: #059669;
            --accent-flame: #f97316;
            --accent-purple: #a855f7;
            --accent-indigo: #6366f1;
            --accent-yellow: #eab308;
            --border-color: #334155;
            --radius-md: 12px;
            --radius-lg: 16px;
            --shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
        }

        body {
            background-color: var(--bg-primary);
            color: var(--text-primary);
            padding: 24px 20px;
            min-height: 100vh;
        }

        .container {
            max-width: 1440px;
            margin: 0 auto;
        }

        /* HEADER */
        header {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            margin-bottom: 24px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
        }

        .brand-title {
            font-size: 26px;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 10px;
            background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .brand-badge {
            font-size: 12px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 999px;
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            -webkit-text-fill-color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }

        .header-meta {
            color: var(--text-secondary);
            font-size: 13px;
        }

        /* TOP NAV TABS */
        .nav-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 26px;
            background: var(--bg-secondary);
            padding: 6px;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
            width: fit-content;
        }

        .nav-tab {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .nav-tab.active {
            background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
            color: #fff;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
        }

        .nav-tab:hover:not(.active) {
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.05);
        }

        /* KPI CARDS */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 16px;
            margin-bottom: 26px;
        }

        .kpi-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 18px 20px;
            position: relative;
            overflow: hidden;
        }

        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--accent-primary);
        }

        .kpi-card.flame::before { background: var(--accent-flame); }
        .kpi-card.green::before { background: var(--accent-green); }
        .kpi-card.purple::before { background: var(--accent-purple); }
        .kpi-card.indigo::before { background: var(--accent-indigo); }

        .kpi-label {
            font-size: 12px;
            color: var(--text-secondary);
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }

        .kpi-value {
            font-size: 26px;
            font-weight: 800;
            color: var(--text-primary);
        }

        .kpi-sub {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 4px;
        }

        /* FILTERS TOOLBAR */
        .toolbar {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 20px;
            margin-bottom: 28px;
            box-shadow: var(--shadow);
        }

        .filters-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
            gap: 14px;
            align-items: end;
        }

        .filter-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .filter-group label {
            font-size: 12px;
            font-weight: 600;
            color: var(--text-secondary);
        }

        .input-control, select.input-control {
            background: #0f172a;
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 9px 12px;
            border-radius: 8px;
            font-size: 13px;
            outline: none;
            transition: border-color 0.2s;
        }

        .input-control:focus {
            border-color: var(--accent-primary);
        }

        .toggles-row {
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            margin-top: 16px;
            padding-top: 14px;
            border-top: 1px solid var(--border-color);
            align-items: center;
            justify-content: space-between;
        }

        .checkbox-label {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            cursor: pointer;
            user-select: none;
        }

        .checkbox-label input {
            cursor: pointer;
            accent-color: var(--accent-primary);
            width: 16px;
            height: 16px;
        }

        .action-buttons {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .btn {
            background: #0f172a;
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 8px 14px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            text-decoration: none;
        }

        .btn:hover {
            background: var(--border-color);
        }

        .btn.active {
            background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
            border-color: #38bdf8;
            color: #fff;
        }

        .btn-primary {
            background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
            border: none;
            color: #fff;
        }

        .btn-primary:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }

        /* VIEW CONTROLS */
        .view-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
        }

        .results-count {
            font-size: 15px;
            font-weight: 600;
            color: var(--text-secondary);
        }

        .view-toggle {
            display: flex;
            background: #0f172a;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 2px;
        }

        .view-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 13px;
            cursor: pointer;
            font-weight: 600;
        }

        .view-btn.active {
            background: var(--bg-secondary);
            color: var(--text-primary);
        }

        /* GRID CARDS */
        .property-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(330px, 1fr));
            gap: 20px;
        }

        .property-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
            position: relative;
        }

        .property-card:hover {
            transform: translateY(-3px);
            border-color: #475569;
            box-shadow: var(--shadow);
        }

        .property-card.is-contacted {
            border-color: rgba(16, 185, 129, 0.4);
            background: linear-gradient(180deg, rgba(16, 185, 129, 0.04) 0%, var(--bg-card) 100%);
        }

        .card-img-wrapper {
            position: relative;
            height: 190px;
            background: #0f172a;
            overflow: hidden;
        }

        .card-img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s;
        }

        .property-card:hover .card-img {
            transform: scale(1.04);
        }

        .badge-container {
            position: absolute;
            top: 12px;
            left: 12px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            z-index: 2;
        }

        .badge {
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            backdrop-filter: blur(8px);
            box-shadow: 0 2px 6px rgba(0,0,0,0.4);
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }

        .badge-super {
            background: rgba(249, 115, 22, 0.9);
            color: #fff;
        }

        .badge-great {
            background: rgba(16, 185, 129, 0.9);
            color: #fff;
        }

        .badge-good {
            background: rgba(56, 189, 248, 0.9);
            color: #0f172a;
        }

        .badge-new {
            background: rgba(168, 85, 247, 0.9);
            color: #fff;
        }

        .badge-date {
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #38bdf8;
        }

        .badge-contacted {
            background: rgba(16, 185, 129, 0.95);
            color: #fff;
            box-shadow: 0 2px 8px rgba(16, 185, 129, 0.4);
        }

        .score-pill {
            position: absolute;
            top: 12px;
            right: 12px;
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            color: #38bdf8;
            font-weight: 800;
            font-size: 13px;
            padding: 4px 8px;
            border-radius: 8px;
            z-index: 2;
        }

        .card-body {
            padding: 16px;
            display: flex;
            flex-direction: column;
            flex-grow: 1;
        }

        .card-price-row {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 4px;
        }

        .card-price {
            font-size: 22px;
            font-weight: 800;
            color: #fff;
        }

        .card-sqm-price {
            font-size: 14px;
            font-weight: 700;
            color: var(--accent-green);
        }

        .card-expenses {
            font-size: 12px;
            color: var(--text-muted);
            margin-bottom: 12px;
            min-height: 18px;
        }

        .card-features {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 14px;
        }

        .feature-chip {
            background: #0f172a;
            border: 1px solid var(--border-color);
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
            color: var(--text-secondary);
        }

        .card-location {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 4px;
        }

        .card-discount {
            font-size: 12px;
            color: var(--accent-flame);
            font-weight: 600;
            margin-bottom: 10px;
        }

        .card-views-row {
            font-size: 12px;
            color: var(--text-secondary);
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .card-actions {
            margin-top: auto;
            display: flex;
            gap: 8px;
            align-items: center;
        }

        .card-btn {
            flex-grow: 1;
            text-align: center;
            padding: 10px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 700;
            text-decoration: none;
            transition: all 0.2s;
        }

        .card-btn-view {
            background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
            color: #fff;
        }

        .card-btn-view:hover {
            opacity: 0.9;
        }

        .contact-btn {
            background: #0f172a;
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 10px 12px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
            white-space: nowrap;
        }

        .contact-btn:hover {
            background: var(--border-color);
            color: #fff;
        }

        .contact-btn.active {
            background: rgba(16, 185, 129, 0.15);
            border-color: var(--accent-green);
            color: var(--accent-green);
        }

        .fav-btn {
            background: #0f172a;
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            width: 40px;
            height: 38px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            flex-shrink: 0;
        }

        .fav-btn.active {
            color: #eab308;
            border-color: #eab308;
        }

        /* TABLE VIEW */
        .table-view {
            display: none;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            overflow-x: auto;
            box-shadow: var(--shadow);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            text-align: left;
        }

        th {
            background: #0f172a;
            padding: 14px 16px;
            color: var(--text-secondary);
            font-weight: 700;
            border-bottom: 1px solid var(--border-color);
            white-space: nowrap;
        }

        td {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-color);
            color: var(--text-primary);
            vertical-align: middle;
        }

        tr:hover td {
            background: var(--bg-card-hover);
        }

        tr.is-contacted td {
            background: rgba(16, 185, 129, 0.05);
        }

        .table-thumb {
            width: 54px;
            height: 40px;
            object-fit: cover;
            border-radius: 6px;
        }

        /* ANALYTICS SECTION STYLES */
        .analytics-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 28px;
        }

        @media (max-width: 992px) {
            .analytics-grid {
                grid-template-columns: 1fr;
            }
        }

        .chart-box {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 20px;
            box-shadow: var(--shadow);
        }

        .chart-title {
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            color: var(--text-primary);
        }

        .chart-container {
            position: relative;
            height: 300px;
            width: 100%;
        }

        /* INSIGHTS RADAR */
        .insights-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }

        .insight-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 18px 20px;
            position: relative;
            transition: transform 0.2s, border-color 0.2s;
        }

        .insight-card:hover {
            transform: translateY(-2px);
            border-color: #475569;
        }

        .insight-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }

        .insight-icon {
            font-size: 22px;
        }

        .insight-category {
            font-size: 11px;
            font-weight: 700;
            color: var(--accent-primary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .insight-title {
            font-size: 15px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 6px;
        }

        .insight-desc {
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.5;
        }

        /* TYPOLOGY CARDS */
        .typology-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }

        .typology-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 20px;
            position: relative;
        }

        .typology-title {
            font-size: 16px;
            font-weight: 700;
            color: var(--accent-primary);
            margin-bottom: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .typology-stat-row {
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            padding: 6px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .typology-stat-row:last-child {
            border-bottom: none;
        }

        .typology-stat-label {
            color: var(--text-secondary);
        }

        .typology-stat-val {
            font-weight: 700;
            color: var(--text-primary);
        }

        /* HEATMAP TABLE */
        .heatmap-bar-container {
            width: 100%;
            height: 8px;
            background: #0f172a;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 4px;
        }

        .heatmap-bar {
            height: 100%;
            border-radius: 4px;
        }

        /* LEAFLET DARK POPUPS & TOOLTIPS */
        .leaflet-popup-content-wrapper {
            background: #1e293b !important;
            color: #f8fafc !important;
            border: 1px solid #334155;
            border-radius: 12px;
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5);
        }
        .leaflet-popup-tip {
            background: #1e293b !important;
        }

        /* EMPTY STATE */
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-secondary);
        }

        .empty-icon {
            font-size: 48px;
            margin-bottom: 12px;
        }

        /* FOOTER */
        footer {
            margin-top: 48px;
            text-align: center;
            font-size: 13px;
            color: var(--text-muted);
            border-top: 1px solid var(--border-color);
            padding-top: 24px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <div class="brand-title">
                    <span>🏢 Zonaprop Hunter CABA</span>
                    <span class="brand-badge">Cartera 10 Días</span>
                </div>
                <div class="header-meta" id="headerMeta">Cartera Activa de Oportunidades Reales y Market Intelligence en CABA</div>
            </div>
            <div class="action-buttons">
                <button class="btn" onclick="exportToCSV()">📥 Exportar CSV</button>
                <button class="btn" onclick="exportToJSON()">📋 Exportar JSON</button>
            </div>
        </header>

        <!-- NAVIGATION TABS -->
        <div class="nav-tabs">
            <button class="nav-tab active" id="tabOpportunities" onclick="switchMainTab('opportunities')">
                🔥 Oportunidades en Cartera (<span id="tabCount">0</span>)
            </button>
            <button class="nav-tab" id="tabAnalytics" onclick="switchMainTab('analytics')">
                📈 Mercado & Analytics CABA
            </button>
        </div>

        <!-- ==================== TAB 1: OPPORTUNITIES ==================== -->
        <div id="sectionOpportunities">
            <!-- KPI METRICS -->
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-label">Oportunidades en Cartera</div>
                    <div class="kpi-value" id="kpiTotal">0</div>
                    <div class="kpi-sub" id="kpiNewSub">0 nuevas hoy</div>
                </div>
                <div class="kpi-card flame">
                    <div class="kpi-label">Super Oportunidades</div>
                    <div class="kpi-value" id="kpiSuper">0</div>
                    <div class="kpi-sub">> 25% descuento vs barrio</div>
                </div>
                <div class="kpi-card green">
                    <div class="kpi-label">Precio Mínimo</div>
                    <div class="kpi-value" id="kpiMinPrice">-</div>
                    <div class="kpi-sub" id="kpiContactedSub">0 ya contactadas</div>
                </div>
                <div class="kpi-card purple">
                    <div class="kpi-label">Promedio USD / m²</div>
                    <div class="kpi-value" id="kpiAvgSqm">-</div>
                    <div class="kpi-sub">En avisos filtrados</div>
                </div>
            </div>

            <!-- FILTERS -->
            <div class="toolbar">
                <div class="filters-grid">
                    <div class="filter-group">
                        <label>Buscar (Palabra clave / Calle)</label>
                        <input type="text" id="filterSearch" class="input-control" placeholder="Ej: Palermo, Balcón, Reciclado...">
                    </div>
                    <div class="filter-group">
                        <label>Antigüedad en Cartera</label>
                        <select id="filterAntiquity" class="input-control">
                            <option value="ALL">Todo el histórico (10 días)</option>
                            <option value="TODAY">🕒 Nuevas de Hoy</option>
                            <option value="2DAYS">📅 Últimas 48 horas (2 días)</option>
                            <option value="5DAYS">📅 Últimos 5 días</option>
                            <option value="7DAYS">📅 Últimos 7 días</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>Barrio</label>
                        <select id="filterBarrio" class="input-control">
                            <option value="ALL">Todos los barrios</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>Precio Máximo (USD)</label>
                        <input type="number" id="filterMaxPrice" class="input-control" placeholder="Ej: 75000" step="5000">
                    </div>
                    <div class="filter-group">
                        <label>Máximo USD / m²</label>
                        <input type="number" id="filterMaxSqm" class="input-control" placeholder="Ej: 1800" step="100">
                    </div>
                    <div class="filter-group">
                        <label>Ambientes Mínimos</label>
                        <select id="filterAmbientes" class="input-control">
                            <option value="0">Cualquiera</option>
                            <option value="1">1 Ambiente (Monoambiente)</option>
                            <option value="2">2 Ambientes</option>
                            <option value="3">3+ Ambientes</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>Ordenar Por</label>
                        <select id="sortBy" class="input-control">
                            <option value="score_desc">🏆 Mayor Oportunidad (Score)</option>
                            <option value="views_desc">👁️ Más Vistos (Mayor Demanda)</option>
                            <option value="newest_desc">🕒 Más Recientes Primero</option>
                            <option value="price_asc">💲 Precio: Menor a Mayor</option>
                            <option value="sqm_asc">📐 USD/m²: Menor a Mayor</option>
                            <option value="m2_desc">🏢 Superficie: Mayor a Menor</option>
                            <option value="discount_desc">🏷️ Mayor Descuento %</option>
                        </select>
                    </div>
                </div>

                <div class="toggles-row">
                    <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                        <label class="checkbox-label">
                            <input type="checkbox" id="chkOnlySuper"> 🔥 Sólo Super Oportunidades
                        </label>
                        <label class="checkbox-label">
                            <input type="checkbox" id="chkHideContacted"> 🙈 Ocultar ya contactadas
                        </label>
                        <label class="checkbox-label">
                            <input type="checkbox" id="chkOnlyContacted"> ✅ Sólo ya contactadas
                        </label>
                        <label class="checkbox-label">
                            <input type="checkbox" id="chkOnlyFavs"> ⭐ Sólo Favoritos
                        </label>
                    </div>
                    <div>
                        <button class="btn" onclick="resetFilters()">↺ Restablecer Filtros</button>
                    </div>
                </div>
            </div>

            <!-- VIEW CONTROLS -->
            <div class="view-controls">
                <div class="results-count" id="resultsCount">Mostrando 0 propiedades</div>
                <div class="view-toggle">
                    <button class="view-btn active" id="btnViewCards" onclick="switchView('cards')">⊞ Tarjetas</button>
                    <button class="view-btn" id="btnViewTable" onclick="switchView('table')">☰ Tabla</button>
                </div>
            </div>

            <!-- CARDS CONTAINER -->
            <div id="propertyGrid" class="property-grid"></div>

            <!-- TABLE CONTAINER -->
            <div id="tableView" class="table-view">
                <table>
                    <thead>
                        <tr>
                            <th>Foto</th>
                            <th>Estado</th>
                            <th>Barrio / Ubicación</th>
                            <th>Precio</th>
                            <th>USD / m²</th>
                            <th>Superficie</th>
                            <th>Amb.</th>
                            <th>Vistas / Demanda</th>
                            <th>Detección</th>
                            <th>Descuento</th>
                            <th>Score</th>
                            <th>Acción</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody"></tbody>
                </table>
            </div>

            <!-- EMPTY STATE -->
            <div id="emptyState" class="empty-state" style="display: none;">
                <div class="empty-icon">🔍</div>
                <h3>No se encontraron propiedades</h3>
                <p>Prueba ajustando o relajando los filtros de búsqueda.</p>
            </div>
        </div>

        <!-- ==================== TAB 2: MARKET ANALYTICS ==================== -->
        <div id="sectionAnalytics" style="display: none;">
            <!-- MACRO MARKET METRICS -->
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-label">M² Promedio Oportunidades</div>
                    <div class="kpi-value" id="macroAvgSqm">USD 0</div>
                    <div class="kpi-sub">En toda la muestra analizada</div>
                </div>
                <div class="kpi-card green">
                    <div class="kpi-label">Mediana de Precio CABA</div>
                    <div class="kpi-value" id="macroMedianPrice">USD 0</div>
                    <div class="kpi-sub">Precio central de la oferta</div>
                </div>
                <div class="kpi-card flame">
                    <div class="kpi-label">Descuento Promedio</div>
                    <div class="kpi-value" id="macroAvgDiscount">0%</div>
                    <div class="kpi-sub">Respecto a benchmarks de barrio</div>
                </div>
                <div class="kpi-card indigo">
                    <div class="kpi-label">Superficie Media</div>
                    <div class="kpi-value" id="macroAvgM2">0 m²</div>
                    <div class="kpi-sub">Tamaño promedio ofertado</div>
                </div>
            </div>

            <!-- EXPERT INSIGHTS RADAR -->
            <h2 style="font-size: 20px; font-weight: 800; margin-bottom: 16px; color: var(--text-primary); display: flex; align-items: center; gap: 8px;">
                <span>🎯 Radar del Experto Inmobiliario</span>
                <span class="brand-badge">Zonaprop Market Insights</span>
            </h2>
            <div id="insightsList" class="insights-list"></div>

            <!-- GEOGRAPHIC CABA HEATMAP (INTERACTIVE LEAFLET MAP) -->
            <div class="chart-box" style="margin-bottom: 28px;">
                <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 16px;">
                    <div>
                        <h2 style="font-size: 18px; font-weight: 800; color: var(--text-primary); display: flex; align-items: center; gap: 8px;">
                            <span>🗺️ Mapa de Calor Geográfico de CABA</span>
                            <span class="brand-badge">Explorador Territorial Interactivo</span>
                        </h2>
                        <p style="font-size: 13px; color: var(--text-secondary); margin-top: 2px;">
                            Selecciona una capa para iluminar los barrios de la Ciudad. Pasa el cursor para ver las métricas completas o haz clic para filtrar sus avisos.
                        </p>
                    </div>
                    <!-- HEATMAP LAYER TOGGLES -->
                    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                        <button class="btn active" id="btnModeScore" onclick="setMapHeatMode('score')">🎯 Oportunidades & Score</button>
                        <button class="btn" id="btnModeCheapest" onclick="setMapHeatMode('cheapest')">🏷️ Más Baratos (USD/m²)</button>
                        <button class="btn" id="btnModePrime" onclick="setMapHeatMode('prime')">💰 Zonas Prime (Benchmark)</button>
                        <button class="btn" id="btnModeViews" onclick="setMapHeatMode('views')">👁️ Más Vistos (Mayor Demanda)</button>
                    </div>
                </div>

                <!-- MAP CONTAINER -->
                <div id="cabaMap" style="height: 480px; width: 100%; border-radius: 12px; border: 1px solid var(--border-color); background: #0f172a; z-index: 1;"></div>

                <!-- MAP LEGEND -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px; font-size: 12px; color: var(--text-secondary);">
                    <span id="mapLegendLabel">🎯 Intensidad: Score de Oportunidades en Cartera</span>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span>Bajo</span>
                        <div id="mapLegendGradient" style="width: 140px; height: 10px; border-radius: 5px; background: linear-gradient(90deg, rgba(56, 189, 248, 0.4), rgba(16, 185, 129, 0.8), rgba(249, 115, 22, 0.95));"></div>
                        <span>Alto</span>
                    </div>
                </div>
            </div>

            <!-- CHARTS GRID -->
            <div class="analytics-grid">
                <div class="chart-box">
                    <div class="chart-title">
                        <span>📊 Comparativa USD / m² por Barrio (Oportunidad vs Benchmark)</span>
                        <small style="font-size:12px; color:var(--text-muted);">Top Barrios con Oferta</small>
                    </div>
                    <div class="chart-container">
                        <canvas id="chartBarrios"></canvas>
                    </div>
                </div>
                <div class="chart-box">
                    <div class="chart-title">
                        <span>🥧 Distribución de Oferta por Precio</span>
                        <small style="font-size:12px; color:var(--text-muted);">Porcentaje</small>
                    </div>
                    <div class="chart-container">
                        <canvas id="chartDistribution"></canvas>
                    </div>
                </div>
            </div>

            <!-- TYPOLOGY BREAKDOWN -->
            <h2 style="font-size: 20px; font-weight: 800; margin-bottom: 16px; color: var(--text-primary);">
                🏢 Análisis por Tipología de Inmueble (Demanda, Vistas y Velocidad de Venta)
            </h2>
            <div id="typologyGrid" class="typology-grid"></div>

            <!-- NEIGHBORHOOD HEATMAP TABLE -->
            <h2 style="font-size: 20px; font-weight: 800; margin-bottom: 16px; color: var(--text-primary);">
                🗺️ Ranking y Mapa de Demanda de Barrios en CABA
            </h2>
            <div class="table-view" style="display: block; margin-bottom: 28px;">
                <table>
                    <thead>
                        <tr>
                            <th>Barrio</th>
                            <th>Avisos</th>
                            <th>USD / m² Promedio</th>
                            <th>Benchmark Barrio</th>
                            <th>Descuento Medio</th>
                            <th>Vistas Promedio / Demanda</th>
                            <th>Ticket Mínimo</th>
                            <th>Expensas Prom.</th>
                            <th>Super Oportunidades</th>
                            <th>Liquidez / Reventa</th>
                        </tr>
                    </thead>
                    <tbody id="heatmapTableBody"></tbody>
                </table>
            </div>
        </div>

        <footer>
            <p>Zonaprop Hunter CABA &bull; Cartera Histórica 10 Días &bull; Generado el <span id="footerDate"></span></p>
        </footer>
    </div>

    <!-- DATA INJECTION -->
    <script>
        const RAW_DATA = __DATA_PLACEHOLDER__;
        const MARKET_ANALYTICS = __ANALYTICS_PLACEHOLDER__;
        const GENERATION_TIME = "__TIMESTAMP_PLACEHOLDER__";

        let currentView = 'cards';
        let currentTab = 'opportunities';
        let favorites = JSON.parse(localStorage.getItem('zonaprop_favs') || '[]');
        let contacted = JSON.parse(localStorage.getItem('zonaprop_contacted') || '[]');
        let chartsInitialized = false;
        let cabaMap = null;
        let mapMarkersLayer = null;
        let currentMapMode = 'score';

        // Coordenadas geográficas de los barrios de CABA
        const BARRIO_GEO = {
            "Palermo": [-34.588, -58.420], "Recoleta": [-34.587, -58.393], "Belgrano": [-34.562, -58.456],
            "Caballito": [-34.618, -58.443], "Almagro": [-34.610, -58.420], "Villa Urquiza": [-34.572, -58.495],
            "Colegiales": [-34.576, -58.448], "Villa Crespo": [-34.598, -58.440], "Chacarita": [-34.588, -58.455],
            "Villa Devoto": [-34.599, -58.513], "Nuñez": [-34.545, -58.465], "San Telmo": [-34.621, -58.373],
            "Retiro": [-34.592, -58.378], "Puerto Madero": [-34.610, -58.362], "Balvanera": [-34.610, -58.400],
            "Once": [-34.608, -58.406], "Congreso": [-34.609, -58.392], "Monserrat": [-34.613, -58.383],
            "San Nicolás": [-34.603, -58.380], "San Nicolas": [-34.603, -58.380], "San Cristóbal": [-34.624, -58.400],
            "San Cristobal": [-34.624, -58.400], "Constitución": [-34.627, -58.382], "Constitucion": [-34.627, -58.382],
            "Barracas": [-34.646, -58.380], "La Boca": [-34.636, -58.362], "Parque Patricios": [-34.637, -58.406],
            "Boedo": [-34.629, -58.419], "Parque Chacabuco": [-34.632, -58.443], "Flores": [-34.631, -58.465],
            "Floresta": [-34.631, -58.484], "Villa del Parque": [-34.605, -58.490], "Paternal": [-34.598, -58.468],
            "Agronomía": [-34.591, -58.487], "Agronomia": [-34.591, -58.487], "Villa Ortúzar": [-34.581, -58.471],
            "Villa Ortuzar": [-34.581, -58.471], "Parque Chas": [-34.582, -58.480], "Coghlan": [-34.565, -58.473],
            "Saavedra": [-34.550, -58.489], "Villa Santa Rita": [-34.614, -58.480], "Villa General Mitre": [-34.608, -58.470],
            "Villa Luro": [-34.638, -58.502], "Villa Pueyrredón": [-34.580, -58.505], "Villa Pueyrredon": [-34.580, -58.505],
            "Villa Real": [-34.615, -58.525], "Versalles": [-34.626, -58.522], "Monte Castro": [-34.620, -58.505],
            "Mataderos": [-34.656, -58.504], "Liniers": [-34.645, -58.520], "Parque Avellaneda": [-34.645, -58.478],
            "Nueva Pompeya": [-34.654, -58.420], "Villa Lugano": [-34.675, -58.470], "Villa Soldati": [-34.664, -58.445],
            "Villa Riachuelo": [-34.685, -58.460]
        };

        function init() {
            const todayCount = RAW_DATA.filter(p => (p.days_ago === 0 || p.is_new)).length;
            document.getElementById('headerMeta').innerText = `Actualizado el ${new Date(GENERATION_TIME).toLocaleString('es-AR')} • ${RAW_DATA.length} oportunidades activas en cartera (${todayCount} nuevas hoy)`;
            document.getElementById('footerDate').innerText = new Date(GENERATION_TIME).toLocaleString('es-AR');
            document.getElementById('tabCount').innerText = RAW_DATA.length;

            // Populate Barrios dropdown
            const barrioSelect = document.getElementById('filterBarrio');
            const barrios = [...new Set(RAW_DATA.map(p => p.barrio))].sort();
            barrios.forEach(b => {
                const opt = document.createElement('option');
                opt.value = b;
                const count = RAW_DATA.filter(p => p.barrio === b).length;
                opt.innerText = `${b} (${count})`;
                barrioSelect.appendChild(opt);
            });

            // Event Listeners
            ['filterSearch', 'filterAntiquity', 'filterBarrio', 'filterMaxPrice', 'filterMaxSqm', 'filterAmbientes', 'sortBy', 'chkOnlySuper', 'chkHideContacted', 'chkOnlyContacted', 'chkOnlyFavs'].forEach(id => {
                document.getElementById(id).addEventListener('input', render);
                document.getElementById(id).addEventListener('change', render);
            });

            // Mutual exclusion for contacted filters
            document.getElementById('chkHideContacted').addEventListener('change', function() {
                if (this.checked) document.getElementById('chkOnlyContacted').checked = false;
            });
            document.getElementById('chkOnlyContacted').addEventListener('change', function() {
                if (this.checked) document.getElementById('chkHideContacted').checked = false;
            });

            render();
            renderAnalytics();
        }

        function switchMainTab(tab) {
            currentTab = tab;
            document.getElementById('tabOpportunities').classList.toggle('active', tab === 'opportunities');
            document.getElementById('tabAnalytics').classList.toggle('active', tab === 'analytics');
            document.getElementById('sectionOpportunities').style.display = tab === 'opportunities' ? 'block' : 'none';
            document.getElementById('sectionAnalytics').style.display = tab === 'analytics' ? 'block' : 'none';

            if (tab === 'analytics') {
                if (!chartsInitialized) {
                    initCharts();
                    chartsInitialized = true;
                }
                setTimeout(() => {
                    if (!cabaMap) {
                        initCabaMap();
                    } else {
                        cabaMap.invalidateSize();
                    }
                }, 150);
            }
        }

        function toggleFavorite(id, e) {
            if (e) e.stopPropagation();
            const idx = favorites.indexOf(id);
            if (idx > -1) {
                favorites.splice(idx, 1);
            } else {
                favorites.push(id);
            }
            localStorage.setItem('zonaprop_favs', JSON.stringify(favorites));
            render();
        }

        function toggleContacted(id, e) {
            if (e) e.stopPropagation();
            const idx = contacted.indexOf(id);
            if (idx > -1) {
                contacted.splice(idx, 1);
            } else {
                contacted.push(id);
            }
            localStorage.setItem('zonaprop_contacted', JSON.stringify(contacted));
            render();
        }

        function switchView(view) {
            currentView = view;
            document.getElementById('btnViewCards').classList.toggle('active', view === 'cards');
            document.getElementById('btnViewTable').classList.toggle('active', view === 'table');
            document.getElementById('propertyGrid').style.display = view === 'cards' ? 'grid' : 'none';
            document.getElementById('tableView').style.display = view === 'table' ? 'block' : 'none';
        }

        function resetFilters() {
            document.getElementById('filterSearch').value = '';
            document.getElementById('filterAntiquity').value = 'ALL';
            document.getElementById('filterBarrio').value = 'ALL';
            document.getElementById('filterMaxPrice').value = '';
            document.getElementById('filterMaxSqm').value = '';
            document.getElementById('filterAmbientes').value = '0';
            document.getElementById('sortBy').value = 'score_desc';
            document.getElementById('chkOnlySuper').checked = false;
            document.getElementById('chkHideContacted').checked = false;
            document.getElementById('chkOnlyContacted').checked = false;
            document.getElementById('chkOnlyFavs').checked = false;
            render();
        }

        function filterData() {
            const query = document.getElementById('filterSearch').value.toLowerCase().trim();
            const antiquity = document.getElementById('filterAntiquity').value;
            const barrio = document.getElementById('filterBarrio').value;
            const maxPrice = parseFloat(document.getElementById('filterMaxPrice').value) || Infinity;
            const maxSqm = parseFloat(document.getElementById('filterMaxSqm').value) || Infinity;
            const minAmb = parseInt(document.getElementById('filterAmbientes').value) || 0;
            const onlySuper = document.getElementById('chkOnlySuper').checked;
            const hideContacted = document.getElementById('chkHideContacted').checked;
            const onlyContacted = document.getElementById('chkOnlyContacted').checked;
            const onlyFavs = document.getElementById('chkOnlyFavs').checked;
            const sortBy = document.getElementById('sortBy').value;

            return RAW_DATA.filter(p => {
                if (query && !`${p.title} ${p.location} ${p.barrio} ${p.address} ${p.features_raw}`.toLowerCase().includes(query)) return false;
                if (barrio !== 'ALL' && p.barrio !== barrio) return false;
                if (p.price_val > maxPrice) return false;
                if (p.usd_m2 > maxSqm) return false;
                if (minAmb > 0 && (p.ambientes || 0) < minAmb) return false;
                if (onlySuper && p.opportunity_score < 75 && !p.badge_text.includes('Super')) return false;
                
                const daysAgo = (typeof p.days_ago === 'number') ? p.days_ago : 0;
                if (antiquity === 'TODAY' && daysAgo !== 0 && !p.is_new) return false;
                if (antiquity === '2DAYS' && daysAgo > 1) return false;
                if (antiquity === '5DAYS' && daysAgo > 4) return false;
                if (antiquity === '7DAYS' && daysAgo > 6) return false;

                const isCont = contacted.includes(p.id);
                if (hideContacted && isCont) return false;
                if (onlyContacted && !isCont) return false;

                if (onlyFavs && !favorites.includes(p.id)) return false;
                return true;
            }).sort((a, b) => {
                if (sortBy === 'score_desc') return b.opportunity_score - a.opportunity_score;
                if (sortBy === 'views_desc') return (b.user_views || 0) - (a.user_views || 0);
                if (sortBy === 'newest_desc') return (a.days_ago || 0) - (b.days_ago || 0);
                if (sortBy === 'price_asc') return a.price_val - b.price_val;
                if (sortBy === 'sqm_asc') return a.usd_m2 - b.usd_m2;
                if (sortBy === 'm2_desc') return (b.m2_tot || 0) - (a.m2_tot || 0);
                if (sortBy === 'discount_desc') return (b.discount_pct || 0) - (a.discount_pct || 0);
                return 0;
            });
        }

        function render() {
            const data = filterData();

            // Update KPIs
            document.getElementById('kpiTotal').innerText = data.length;
            const newTodayCount = data.filter(p => p.days_ago === 0 || p.is_new).length;
            document.getElementById('kpiNewSub').innerText = `${newTodayCount} detectadas hoy`;
            const superCount = data.filter(p => p.opportunity_score >= 75 || p.badge_text.includes('Super')).length;
            document.getElementById('kpiSuper').innerText = superCount;

            const totalContactedInView = data.filter(p => contacted.includes(p.id)).length;
            document.getElementById('kpiContactedSub').innerText = `${totalContactedInView} ya contactadas`;

            if (data.length > 0) {
                const minP = Math.min(...data.map(p => p.price_val));
                document.getElementById('kpiMinPrice').innerText = `USD ${minP.toLocaleString('es-AR')}`;
                const avgSqm = Math.round(data.reduce((acc, p) => acc + p.usd_m2, 0) / data.length);
                document.getElementById('kpiAvgSqm').innerText = `USD ${avgSqm.toLocaleString('es-AR')}`;
            } else {
                document.getElementById('kpiMinPrice').innerText = '-';
                document.getElementById('kpiAvgSqm').innerText = '-';
            }

            document.getElementById('resultsCount').innerText = `Mostrando ${data.length} de ${RAW_DATA.length} oportunidades en cartera`;
            document.getElementById('emptyState').style.display = data.length === 0 ? 'block' : 'none';

            // Render Cards
            const grid = document.getElementById('propertyGrid');
            grid.innerHTML = data.map(p => {
                const isFav = favorites.includes(p.id);
                const isCont = contacted.includes(p.id);
                const defaultImg = "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=500&auto=format&fit=crop&q=60";
                const imgUrl = p.image || defaultImg;
                
                let ageBadge = '<span class="badge badge-new">✨ Nueva Hoy</span>';
                if (typeof p.days_ago === 'number' && p.days_ago > 0) {
                    ageBadge = `<span class="badge badge-date">📅 Hace ${p.days_ago} ${p.days_ago === 1 ? 'día' : 'días'}</span>`;
                }

                const viewsText = p.user_views_formatted ? `👁️ ${p.user_views_formatted} vistas estimadas` : '👁️ Alta demanda';
                
                return `
                <div class="property-card ${isCont ? 'is-contacted' : ''}">
                    <div class="card-img-wrapper">
                        <img src="${imgUrl}" alt="Foto propiedad" class="card-img" onerror="this.src='${defaultImg}'" loading="lazy">
                        <div class="badge-container">
                            <span class="badge ${p.badge_class}">${p.badge_text}</span>
                            ${isCont ? '<span class="badge badge-contacted">✅ Ya Contactada</span>' : ''}
                            ${ageBadge}
                        </div>
                        <div class="score-pill">Score: ${p.opportunity_score}/100</div>
                    </div>
                    <div class="card-body">
                        <div class="card-price-row">
                            <span class="card-price">${p.price_usd_formatted}</span>
                            <span class="card-sqm-price">${p.usd_m2_formatted}</span>
                        </div>
                        <div class="card-expenses">${p.expenses_raw || 'Expensas no especificadas'}</div>
                        
                        <div class="card-features">
                            ${p.m2_tot ? `<span class="feature-chip">📐 ${p.m2_tot} m²</span>` : ''}
                            ${p.ambientes ? `<span class="feature-chip">🚪 ${p.ambientes} amb</span>` : ''}
                            ${p.dormitorios ? `<span class="feature-chip">🛏️ ${p.dormitorios} dorm</span>` : ''}
                            ${p.banos ? `<span class="feature-chip">🚿 ${p.banos} baño</span>` : ''}
                            ${p.cocheras ? `<span class="feature-chip">🚗 Cochera</span>` : ''}
                        </div>

                        <div class="card-location">📍 ${p.barrio} ${p.address ? '• ' + p.address : ''}</div>
                        <div class="card-discount">
                            ${p.discount_pct > 0 ? `🟢 ${p.discount_pct}% más barato que el promedio de ${p.barrio} (${p.benchmark_formatted})` : `⚪ En línea con el promedio de ${p.barrio}`}
                        </div>

                        <div class="card-views-row">
                            <span>${viewsText}</span>
                        </div>

                        <div class="card-actions">
                            <a href="${p.link}" target="_blank" rel="noopener noreferrer" class="card-btn card-btn-view">Ver en Zonaprop ↗</a>
                            <button class="contact-btn ${isCont ? 'active' : ''}" onclick="toggleContacted('${p.id}', event)" title="${isCont ? 'Desmarcar contactada' : 'Marcar como ya contactada'}">
                                ${isCont ? '✅ Contactada' : '📞 Contactar'}
                            </button>
                            <button class="fav-btn ${isFav ? 'active' : ''}" onclick="toggleFavorite('${p.id}', event)" title="Guardar en favoritos">${isFav ? '★' : '☆'}</button>
                        </div>
                    </div>
                </div>
                `;
            }).join('');

            // Render Table
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = data.map(p => {
                const isFav = favorites.includes(p.id);
                const isCont = contacted.includes(p.id);
                const defaultImg = "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=100&auto=format&fit=crop&q=60";
                const imgUrl = p.image || defaultImg;
                const ageLabel = (p.days_ago === 0 || p.is_new) ? '✨ Hoy' : `Hace ${p.days_ago}d`;

                return `
                <tr class="${isCont ? 'is-contacted' : ''}">
                    <td><img src="${imgUrl}" class="table-thumb" onerror="this.src='${defaultImg}'"></td>
                    <td>
                        <button class="contact-btn ${isCont ? 'active' : ''}" style="padding:4px 8px; font-size:11px;" onclick="toggleContacted('${p.id}', event)">
                            ${isCont ? '✅ Contactada' : '📞 Marcar'}
                        </button>
                    </td>
                    <td>
                        <strong>${p.barrio}</strong><br>
                        <small style="color:var(--text-muted)">${p.address || p.location}</small>
                    </td>
                    <td><strong>${p.price_usd_formatted}</strong></td>
                    <td style="color:var(--accent-green)"><strong>${p.usd_m2_formatted}</strong></td>
                    <td>${p.m2_tot || '-'} m²</td>
                    <td>${p.ambientes || '-'} amb</td>
                    <td>
                        <span style="color:var(--accent-primary); font-weight:700;">👁️ ${p.user_views_formatted || 'Alta'}</span>
                    </td>
                    <td><small style="color:var(--accent-primary); font-weight:700;">${ageLabel}</small></td>
                    <td>
                        <span style="color:${p.discount_pct > 0 ? 'var(--accent-green)' : 'var(--text-muted)'}">
                            ${p.discount_pct > 0 ? '+' : ''}${p.discount_pct}%
                        </span>
                    </td>
                    <td><span class="badge ${p.badge_class}">${p.opportunity_score} pts</span></td>
                    <td>
                        <div style="display:flex; gap:6px;">
                            <a href="${p.link}" target="_blank" rel="noopener noreferrer" class="btn btn-primary" style="padding:4px 8px; font-size:11px;">Ver ↗</a>
                            <button class="fav-btn ${isFav ? 'active' : ''}" style="width:28px; height:28px; font-size:12px;" onclick="toggleFavorite('${p.id}', event)">${isFav ? '★' : '☆'}</button>
                        </div>
                    </td>
                </tr>
                `;
            }).join('');
        }

        function renderAnalytics() {
            if (!MARKET_ANALYTICS) return;
            const macro = MARKET_ANALYTICS.macro || {};

            document.getElementById('macroAvgSqm').innerText = `USD ${macro.avg_usd_m2?.toLocaleString('es-AR') || 0}`;
            document.getElementById('macroMedianPrice').innerText = `USD ${macro.median_price?.toLocaleString('es-AR') || 0}`;
            document.getElementById('macroAvgDiscount').innerText = `${macro.avg_discount_pct || 0}%`;
            document.getElementById('macroAvgM2').innerText = `${macro.avg_m2_size || 0} m²`;

            // Render Insights
            const insightsContainer = document.getElementById('insightsList');
            const insights = MARKET_ANALYTICS.insights || [];
            insightsContainer.innerHTML = insights.map(item => `
                <div class="insight-card">
                    <div class="insight-header">
                        <span class="insight-icon">${item.icon}</span>
                        <span class="insight-category">${item.category}</span>
                    </div>
                    <div class="insight-title">${item.title}</div>
                    <div class="insight-desc">${item.desc}</div>
                </div>
            `).join('');

            // Render Typology Cards (con Vistas y Velocidad de Venta)
            const typContainer = document.getElementById('typologyGrid');
            const typologies = MARKET_ANALYTICS.typologies || {};
            typContainer.innerHTML = Object.values(typologies).map(t => `
                <div class="typology-card">
                    <div class="typology-title">
                        <span>${t.label}</span>
                        <span class="brand-badge">${t.count} unidades</span>
                    </div>
                    <div class="typology-stat-row">
                        <span class="typology-stat-label">Vistas Promedio por Aviso:</span>
                        <span class="typology-stat-val" style="color:var(--accent-primary)">👁️ ${t.avg_views_formatted}</span>
                    </div>
                    <div class="typology-stat-row">
                        <span class="typology-stat-label">Participación en Consultas:</span>
                        <span class="typology-stat-val" style="color:var(--accent-yellow)">📊 ${t.demand_share}</span>
                    </div>
                    <div class="typology-stat-row">
                        <span class="typology-stat-label">Velocidad de Absorción:</span>
                        <span class="typology-stat-val" style="font-size:11px; color:#10b981;">${t.sales_speed}</span>
                    </div>
                    <div class="typology-stat-row">
                        <span class="typology-stat-label">Ticket de Entrada Mínimo:</span>
                        <span class="typology-stat-val" style="color:var(--accent-green)">USD ${t.min_price?.toLocaleString('es-AR')}</span>
                    </div>
                    <div class="typology-stat-row">
                        <span class="typology-stat-label">Precio Promedio:</span>
                        <span class="typology-stat-val">USD ${t.avg_price?.toLocaleString('es-AR')}</span>
                    </div>
                    <div class="typology-stat-row">
                        <span class="typology-stat-label">Valor Promedio USD/m²:</span>
                        <span class="typology-stat-val">USD ${t.avg_usd_m2?.toLocaleString('es-AR')}/m²</span>
                    </div>
                    <div class="typology-stat-row">
                        <span class="typology-stat-label">Superficie Promedio:</span>
                        <span class="typology-stat-val">${t.avg_m2} m²</span>
                    </div>
                </div>
            `).join('');

            // Render Heatmap Table (con Vistas y Expensas)
            const heatmapTbody = document.getElementById('heatmapTableBody');
            const neighborhoods = MARKET_ANALYTICS.neighborhoods || [];
            heatmapTbody.innerHTML = neighborhoods.map(b => {
                const scoreColor = b.opportunity_density_score > 70 ? 'var(--accent-flame)' : (b.opportunity_density_score > 40 ? 'var(--accent-green)' : 'var(--accent-primary)');
                return `
                <tr>
                    <td><strong>${b.name}</strong></td>
                    <td><span class="badge badge-date">${b.count} avisos</span></td>
                    <td style="color:var(--accent-green); font-weight:700;">USD ${b.avg_usd_m2?.toLocaleString('es-AR')}</td>
                    <td style="color:var(--text-muted);">USD ${b.benchmark_usd_m2?.toLocaleString('es-AR')}</td>
                    <td style="font-weight:700; color:${b.avg_discount_pct > 0 ? 'var(--accent-green)' : 'var(--text-muted)'};">
                        ${b.avg_discount_pct > 0 ? '+' : ''}${b.avg_discount_pct}%
                    </td>
                    <td>
                        <strong style="color:var(--accent-primary);">👁️ ${b.avg_views_formatted}</strong><br>
                        <small style="color:var(--text-muted); font-size:11px;">${b.demand_level}</small>
                    </td>
                    <td>USD ${b.min_price?.toLocaleString('es-AR')}</td>
                    <td>${b.avg_expenses_formatted}</td>
                    <td><strong>${b.super_deals_count}</strong></td>
                    <td style="min-width:140px;">
                        <div style="display:flex; justify-content:space-between; font-size:11px; margin-bottom:2px;">
                            <span>Liquidez</span>
                            <span style="font-weight:700; color:${scoreColor}">${b.liquidity_score || b.opportunity_density_score}/100</span>
                        </div>
                        <div class="heatmap-bar-container">
                            <div class="heatmap-bar" style="width:${b.liquidity_score || b.opportunity_density_score}%; background:${scoreColor};"></div>
                        </div>
                    </td>
                </tr>
                `;
            }).join('');
        }

        // ==================== CABA LEAFLET HEATMAP ====================
        function initCabaMap() {
            const mapContainer = document.getElementById('cabaMap');
            if (!mapContainer || cabaMap) return;

            // Centro geométrico de Capital Federal
            cabaMap = L.map('cabaMap', {
                center: [-34.615, -58.435],
                zoom: 12,
                minZoom: 11,
                maxZoom: 15,
                attributionControl: false
            });

            // CartoDB Dark Matter Tiles
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                maxZoom: 19,
                subdomains: 'abcd'
            }).addTo(cabaMap);

            mapMarkersLayer = L.layerGroup().addTo(cabaMap);
            renderMapLayer();
        }

        function setMapHeatMode(mode) {
            currentMapMode = mode;
            ['btnModeScore', 'btnModeCheapest', 'btnModePrime', 'btnModeViews'].forEach(id => {
                document.getElementById(id).classList.remove('active');
            });

            const modeBtnMap = {
                'score': 'btnModeScore',
                'cheapest': 'btnModeCheapest',
                'prime': 'btnModePrime',
                'views': 'btnModeViews'
            };
            document.getElementById(modeBtnMap[mode]).classList.add('active');

            const labels = {
                'score': '🎯 Intensidad: Score de Oportunidad y Descuento en Cartera',
                'cheapest': '🏷️ Intensidad: Zonas Más Económicas (Menor USD/m² Oportunidad)',
                'prime': '💰 Intensidad: Zonas Prime / Mayor Valor de Mercado (Benchmark USD/m²)',
                'views': '👁️ Intensidad: Barrios Más Vistos y Mayor Rotación Comercial'
            };
            document.getElementById('mapLegendLabel').innerText = labels[mode];

            renderMapLayer();
        }

        function getHeatColor(normVal, mode) {
            // normVal de 0.0 (mínimo) a 1.0 (máximo)
            const v = Math.max(0, Math.min(1, normVal));
            if (mode === 'score') {
                // Azul suave a Verde a Naranja brillante
                return v > 0.6 ? '#f97316' : (v > 0.3 ? '#10b981' : '#38bdf8');
            } else if (mode === 'cheapest') {
                // Invertido: más barato es más verde/cian
                return v > 0.6 ? '#10b981' : (v > 0.3 ? '#38bdf8' : '#818cf8');
            } else if (mode === 'prime') {
                // Dorado y violeta para zonas premium
                return v > 0.6 ? '#eab308' : (v > 0.3 ? '#a855f7' : '#6366f1');
            } else {
                // Vistas: rojo fuego a naranja a amarillo
                return v > 0.6 ? '#ef4444' : (v > 0.3 ? '#f97316' : '#eab308');
            }
        }

        function renderMapLayer() {
            if (!mapMarkersLayer || !MARKET_ANALYTICS) return;
            mapMarkersLayer.clearLayers();

            const nList = MARKET_ANALYTICS.neighborhoods || [];
            const nMap = {};
            nList.forEach(item => { nMap[item.name.toLowerCase()] = item; });

            // Calcular rangos min/max para normalizar
            const benchmarks = Object.values(nList).map(x => x.benchmark_usd_m2 || 1900);
            const maxBench = Math.max(...benchmarks, 3000);
            const minBench = Math.min(...benchmarks, 1000);

            const viewsList = Object.values(nList).map(x => x.avg_views || 950);
            const maxViews = Math.max(...viewsList, 2200);
            const minViews = Math.min(...viewsList, 500);

            const sqms = Object.values(nList).map(x => x.avg_usd_m2 || 1700);
            const maxSqm = Math.max(...sqms, 2100);
            const minSqm = Math.min(...sqms, 1200);

            // Iterar barrios de CABA
            Object.entries(BARRIO_GEO).forEach(([bName, coords]) => {
                const data = nMap[bName.toLowerCase()];
                const count = data ? data.count : 0;
                const avgSqm = data ? data.avg_usd_m2 : 0;
                const bench = data ? data.benchmark_usd_m2 : 1900;
                const disc = data ? data.avg_discount_pct : 0;
                const views = data ? data.avg_views : (bName === 'Palermo' ? 2400 : (bName === 'Caballito' ? 2100 : 1000));
                const demand = data ? data.demand_level : (views >= 1600 ? '🔥 Muy Alta' : '🟢 Alta');
                const expenses = data ? data.avg_expenses_formatted : 'No informadas';
                const score = data ? data.opportunity_density_score : 20;

                // Determinar valor de normalización según modo
                let norm = 0.5;
                let radius = 800;

                if (currentMapMode === 'score') {
                    norm = count > 0 ? (score / 100) : 0.15;
                    radius = count > 0 ? 850 + Math.min(count * 60, 450) : 650;
                } else if (currentMapMode === 'cheapest') {
                    norm = avgSqm > 0 ? 1 - ((avgSqm - minSqm) / Math.max(1, maxSqm - minSqm)) : 0.2;
                    radius = 850;
                } else if (currentMapMode === 'prime') {
                    norm = (bench - minBench) / Math.max(1, maxBench - minBench);
                    radius = 900;
                } else if (currentMapMode === 'views') {
                    norm = (views - minViews) / Math.max(1, maxViews - minViews);
                    radius = 800 + Math.round(norm * 400);
                }

                const color = getHeatColor(norm, currentMapMode);

                const circle = L.circle(coords, {
                    color: color,
                    fillColor: color,
                    fillOpacity: count > 0 ? 0.60 : 0.30,
                    weight: count > 0 ? 2 : 1,
                    radius: radius
                });

                // Tooltip enriquecido
                const tooltipHtml = `
                <div style="font-family:'Plus Jakarta Sans',sans-serif; min-width:180px; padding:4px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #334155; padding-bottom:4px; margin-bottom:6px;">
                        <strong style="font-size:14px; color:#fff;">${bName}</strong>
                        <span style="font-size:11px; background:${color}; color:#0f172a; font-weight:800; padding:2px 6px; border-radius:4px;">
                            ${count} avisos
                        </span>
                    </div>
                    <div style="font-size:12px; line-height:1.6; color:#94a3b8;">
                        <div>📐 USD/m² Cartera: <strong style="color:#10b981;">${avgSqm > 0 ? 'USD ' + avgSqm.toLocaleString('es-AR') : 'Sin oferta activa'}</strong></div>
                        <div>🏛️ Benchmark Zonal: <span style="color:#f8fafc;">USD ${bench.toLocaleString('es-AR')}/m²</span></div>
                        ${disc > 0 ? `<div>🏷️ Descuento Medio: <strong style="color:#10b981;">+${disc}%</strong></div>` : ''}
                        <div>💵 Expensas Promedio: <span style="color:#f8fafc;">${expenses}</span></div>
                        <div>👁️ Vistas Promedio: <strong style="color:#38bdf8;">${views.toLocaleString('es-AR')}</strong></div>
                        <div>🔥 Demanda Comercial: <strong style="color:#f8fafc;">${demand}</strong></div>
                    </div>
                    <div style="margin-top:8px; font-size:11px; color:#38bdf8; text-align:right; font-weight:600;">
                        👉 Clic para ver avisos del barrio
                    </div>
                </div>
                `;

                circle.bindPopup(tooltipHtml);
                circle.on('mouseover', function() { this.openPopup(); this.setStyle({ fillOpacity: 0.85, weight: 3 }); });
                circle.on('mouseout', function() { this.setStyle({ fillOpacity: count > 0 ? 0.60 : 0.30, weight: count > 0 ? 2 : 1 }); });

                // Al hacer clic, filtra las propiedades en Tab 1
                circle.on('click', function() {
                    switchMainTab('opportunities');
                    const select = document.getElementById('filterBarrio');
                    select.value = bName;
                    if (select.value !== bName) {
                        // Si no estaba en el select, buscar por texto
                        document.getElementById('filterSearch').value = bName;
                    }
                    render();
                });

                mapMarkersLayer.addLayer(circle);
            });
        }

        function initCharts() {
            if (!MARKET_ANALYTICS) return;

            // 1. Bar Chart: Barrios vs Benchmark
            const barriosData = (MARKET_ANALYTICS.neighborhoods || []).slice(0, 10);
            const ctxBarrios = document.getElementById('chartBarrios').getContext('2d');
            new Chart(ctxBarrios, {
                type: 'bar',
                data: {
                    labels: barriosData.map(b => b.name),
                    datasets: [
                        {
                            label: 'USD/m² Oportunidades Encontradas',
                            data: barriosData.map(b => b.avg_usd_m2),
                            backgroundColor: 'rgba(16, 185, 129, 0.85)',
                            borderRadius: 6
                        },
                        {
                            label: 'USD/m² Benchmark de Mercado',
                            data: barriosData.map(b => b.benchmark_usd_m2),
                            backgroundColor: 'rgba(100, 116, 139, 0.4)',
                            borderRadius: 6
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { ticks: { color: '#94a3b8', font: { size: 11 } }, grid: { display: false } },
                        y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255, 255, 255, 0.05)' } }
                    },
                    plugins: {
                        legend: { labels: { color: '#f8fafc', font: { size: 12, family: 'Plus Jakarta Sans' } } }
                    }
                }
            });

            // 2. Doughnut Chart: Price Distribution
            const dist = MARKET_ANALYTICS.price_distribution || {};
            const ctxDist = document.getElementById('chartDistribution').getContext('2d');
            new Chart(ctxDist, {
                type: 'doughnut',
                data: {
                    labels: Object.values(dist).map(d => d.label),
                    datasets: [{
                        data: Object.values(dist).map(d => d.count),
                        backgroundColor: Object.values(dist).map(d => d.color),
                        borderWidth: 2,
                        borderColor: '#1e293b'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { color: '#f8fafc', font: { size: 12 } } }
                    },
                    cutout: '65%'
                }
            });
        }

        function exportToCSV() {
            const data = filterData();
            if (data.length === 0) return alert('No hay datos para exportar.');

            const headers = ['ID', 'Barrio', 'Direccion', 'Precio_USD', 'USD_m2', 'M2_Tot', 'Ambientes', 'Dormitorios', 'Vistas_Estimadas', 'Expensas', 'Fecha_Deteccion', 'Dias_En_Cartera', 'Score_Oportunidad', 'Descuento_Pct', 'Contactada', 'Link'];
            const rows = data.map(p => {
                const isCont = contacted.includes(p.id) ? 'SI' : 'NO';
                return [
                    p.id,
                    `"${p.barrio}"`,
                    `"${(p.address || '').replace(/"/g, '""')}"`,
                    p.price_val,
                    p.usd_m2,
                    p.m2_tot || '',
                    p.ambientes || '',
                    p.dormitorios || '',
                    p.user_views || '',
                    `"${(p.expenses_raw || '').replace(/"/g, '""')}"`,
                    `"${p.first_seen_date || ''}"`,
                    p.days_ago ?? 0,
                    p.opportunity_score,
                    p.discount_pct,
                    `"${isCont}"`,
                    `"${p.link}"`
                ];
            });

            const csvContent = "data:text/csv;charset=utf-8," + [headers.join(','), ...rows.map(e => e.join(','))].join('\\n');
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement('a');
            link.setAttribute('href', encodedUri);
            link.setAttribute('download', `zonaprop_cartera_caba_${new Date().toISOString().slice(0,10)}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        function exportToJSON() {
            const data = filterData().map(p => ({
                ...p,
                contactada: contacted.includes(p.id)
            }));
            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
            const link = document.createElement('a');
            link.setAttribute('href', dataStr);
            link.setAttribute('download', `zonaprop_cartera_caba_${new Date().toISOString().slice(0,10)}.json`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        window.onload = init;
    </script>
</body>
</html>
"""

def generate_html_report(properties: List[Dict[str, Any]], market_analytics: Dict[str, Any], output_path: str) -> str:
    """
    Genera el archivo HTML inyectando la cartera de propiedades evaluadas y los analytics de mercado.
    Retorna la ruta absoluta del archivo generado.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    json_properties = json.dumps(properties, ensure_ascii=False)
    json_analytics = json.dumps(market_analytics, ensure_ascii=False)
    timestamp = datetime.now().isoformat()

    html_content = (
        HTML_TEMPLATE
        .replace("__DATA_PLACEHOLDER__", json_properties)
        .replace("__ANALYTICS_PLACEHOLDER__", json_analytics)
        .replace("__TIMESTAMP_PLACEHOLDER__", timestamp)
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path
