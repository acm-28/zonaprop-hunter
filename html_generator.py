"""
Generador de Dashboard HTML interactivo para Oportunidades Inmobiliarias y Market Intelligence en CABA.
Incluye Plano Artesanal 2D/3D Isométrico de CABA con capas conmutables, ordenamiento interactivo
en todas las columnas del ranking de barrios, métricas de vistas/demanda comercial, favoritos y tracking de contacto.
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
    <style>
        :root {
            --bg-primary: #0b1120;
            --bg-secondary: #131c31;
            --bg-card: #17233d;
            --bg-card-hover: #1e2f52;
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
            --border-color: #243454;
            --radius-md: 12px;
            --radius-lg: 16px;
            --shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
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
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.4);
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

        /* TABLE VIEW & SORTABLE HEADERS */
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

        th.sortable-th {
            cursor: pointer;
            user-select: none;
            transition: background 0.2s, color 0.2s;
        }

        th.sortable-th:hover {
            background: #1e293b;
            color: #fff;
        }

        th.sortable-th .sort-icon {
            display: inline-block;
            margin-left: 6px;
            font-size: 11px;
            color: var(--text-muted);
            transition: transform 0.2s, color 0.2s;
        }

        th.sortable-th.active-sort {
            color: var(--accent-primary);
            background: rgba(56, 189, 248, 0.08);
        }

        th.sortable-th.active-sort .sort-icon {
            color: var(--accent-primary);
            font-weight: 800;
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

        /* ==================== ARTISANAL CABA PLANO (2D / 3D ISOMETRIC) ==================== */
        .artisan-map-wrapper {
            background: linear-gradient(180deg, #090e1a 0%, #111a2e 100%);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 24px;
            margin-bottom: 32px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0,0,0,0.6);
        }

        .map-header-row {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 14px;
            margin-bottom: 18px;
            z-index: 10;
            position: relative;
        }

        .map-stage-viewport {
            width: 100%;
            height: 600px;
            position: relative;
            perspective: 1300px;
            overflow: hidden;
            border-radius: 12px;
            background: radial-gradient(circle at 60% 30%, rgba(30, 41, 59, 0.4) 0%, rgba(11, 17, 32, 0.95) 100%);
            border: 1px solid rgba(255, 255, 255, 0.07);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .caba-svg-canvas {
            width: 100%;
            height: 100%;
            transition: transform 0.8s cubic-bezier(0.16, 1, 0.3, 1), filter 0.8s ease;
            transform-origin: center center;
            overflow: visible;
        }

        .map-stage-viewport.is-3d .caba-svg-canvas {
            transform: rotateX(32deg) rotateZ(-12deg) translateY(-25px) scale(0.92);
            filter: drop-shadow(-30px 40px 50px rgba(0, 0, 0, 0.85));
        }

        /* BARRIO PATHS & HOVER EFFECTS */
        .barrio-polygon-group {
            cursor: pointer;
            transition: transform 0.25s ease;
        }

        .barrio-poly {
            transition: fill 0.3s ease, stroke 0.2s ease, stroke-width 0.2s ease, filter 0.2s ease;
            stroke-linejoin: round;
        }

        .barrio-polygon-group:hover .barrio-poly {
            stroke: #ffffff !important;
            stroke-width: 2.8px !important;
            filter: drop-shadow(0 0 14px rgba(255, 255, 255, 0.6)) brightness(1.25);
        }

        .barrio-svg-label {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 10px;
            font-weight: 700;
            fill: #94a3b8;
            pointer-events: none;
            text-anchor: middle;
            user-select: none;
            transition: fill 0.2s;
        }

        .barrio-polygon-group:hover .barrio-svg-label {
            fill: #ffffff;
            font-weight: 800;
        }

        .barrio-badge-dot {
            pointer-events: none;
        }

        /* FLOATING TOOLTIP */
        .artisan-tooltip {
            position: absolute;
            pointer-events: none;
            display: none;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(12px);
            border: 1px solid #38bdf8;
            border-radius: 12px;
            padding: 14px 16px;
            z-index: 1000;
            box-shadow: 0 15px 35px rgba(0,0,0,0.7), 0 0 15px rgba(56, 189, 248, 0.2);
            font-family: 'Plus Jakarta Sans', sans-serif;
            min-width: 220px;
            transition: opacity 0.15s ease, transform 0.15s ease;
        }

        /* COASTLINE WATERMARK */
        .rio-label {
            position: absolute;
            top: 25px;
            right: 40px;
            font-size: 14px;
            font-weight: 800;
            letter-spacing: 4px;
            color: rgba(56, 189, 248, 0.25);
            user-select: none;
            pointer-events: none;
            text-transform: uppercase;
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

            <!-- ==================== ARTISANAL CABA PLANO (2D / 3D ISOMETRIC) ==================== -->
            <div class="artisan-map-wrapper">
                <div class="map-header-row">
                    <div>
                        <h2 style="font-size: 19px; font-weight: 800; color: var(--text-primary); display: flex; align-items: center; gap: 8px;">
                            <span>🗺️ Plano Territorial Arquitectónico de CABA</span>
                            <span class="brand-badge" id="mapPerspectiveBadge">Plano 2D</span>
                        </h2>
                        <p style="font-size: 13px; color: var(--text-secondary); margin-top: 3px;">
                            Iluminación zonal interactiva. Pasa el cursor por cualquier barrio para inspeccionar sus métricas o haz clic para filtrar sus avisos.
                        </p>
                    </div>

                    <!-- PERSPECTIVE & MODE CONTROLS -->
                    <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
                        <div style="background: #0f172a; padding: 3px; border-radius: 8px; border: 1px solid var(--border-color); display: flex; gap: 4px;">
                            <button class="btn active" id="btnPersp2D" onclick="setMapPerspective('2d')">📐 2D</button>
                            <button class="btn" id="btnPersp3D" onclick="setMapPerspective('3d')">🏙️ 3D Isométrico</button>
                        </div>

                        <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                            <button class="btn active" id="btnModeScore" onclick="setMapHeatMode('score')">🎯 Oportunidades</button>
                            <button class="btn" id="btnModeCheapest" onclick="setMapHeatMode('cheapest')">🏷️ Más Baratos</button>
                            <button class="btn" id="btnModePrime" onclick="setMapHeatMode('prime')">💰 Zonas Prime</button>
                            <button class="btn" id="btnModeViews" onclick="setMapHeatMode('views')">👁️ Más Vistos</button>
                        </div>
                    </div>
                </div>

                <!-- MAP CANVAS VIEWPORT -->
                <div class="map-stage-viewport" id="mapViewport">
                    <div class="rio-label">RÍO DE LA PLATA 🌊</div>
                    
                    <svg class="caba-svg-canvas" id="cabaSvg" viewBox="0 0 920 820">
                        <defs>
                            <!-- Architectural grid pattern -->
                            <pattern id="archGrid" width="30" height="30" patternUnits="userSpaceOnUse">
                                <path d="M 30 0 L 0 0 0 30" fill="none" stroke="rgba(255, 255, 255, 0.03)" stroke-width="1"/>
                            </pattern>
                            <filter id="neonGlow" x="-20%" y="-20%" width="140%" height="140%">
                                <feGaussianBlur stdDeviation="6" result="blur" />
                                <feComposite in="SourceGraphic" in2="blur" operator="over" />
                            </filter>
                        </defs>

                        <!-- Background Blueprint Grid -->
                        <rect width="920" height="820" fill="url(#archGrid)" />

                        <!-- Barrios SVG Paths Group -->
                        <g id="cabaBarriosGroup"></g>
                    </svg>

                    <!-- FLOATING HOVER TOOLTIP -->
                    <div class="artisan-tooltip" id="mapTooltip"></div>
                </div>

                <!-- MAP LEGEND -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 14px; font-size: 12px; color: var(--text-secondary);">
                    <span id="mapLegendLabel">🎯 Intensidad: Concentración de Oportunidades y Descuento</span>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span>Bajo</span>
                        <div id="mapLegendGradient" style="width: 140px; height: 10px; border-radius: 5px; background: linear-gradient(90deg, rgba(56, 189, 248, 0.3), rgba(16, 185, 129, 0.8), rgba(249, 115, 22, 0.95));"></div>
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

            <!-- NEIGHBORHOOD HEATMAP TABLE (SORTABLE HEADERS) -->
            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 14px;">
                <div>
                    <h2 style="font-size: 20px; font-weight: 800; color: var(--text-primary);">
                        🗺️ Ranking y Mapa de Demanda de Barrios en CABA
                    </h2>
                    <p style="font-size: 13px; color: var(--text-secondary); margin-top: 2px;">
                        Haz clic en el título de cualquier columna para ordenar el listado (mayor a menor o viceversa).
                    </p>
                </div>
            </div>

            <div class="table-view" style="display: block; margin-bottom: 28px;">
                <table>
                    <thead>
                        <tr>
                            <th class="sortable-th" onclick="sortRankingTable('name')">Barrio <span class="sort-icon" id="sortIcon_name">⇅</span></th>
                            <th class="sortable-th active-sort" onclick="sortRankingTable('count')">Avisos <span class="sort-icon" id="sortIcon_count">▼</span></th>
                            <th class="sortable-th" onclick="sortRankingTable('avg_usd_m2')">USD / m² Promedio <span class="sort-icon" id="sortIcon_avg_usd_m2">⇅</span></th>
                            <th class="sortable-th" onclick="sortRankingTable('benchmark_usd_m2')">Benchmark Barrio <span class="sort-icon" id="sortIcon_benchmark_usd_m2">⇅</span></th>
                            <th class="sortable-th" onclick="sortRankingTable('avg_discount_pct')">Descuento Medio <span class="sort-icon" id="sortIcon_avg_discount_pct">⇅</span></th>
                            <th class="sortable-th" onclick="sortRankingTable('avg_views')">Vistas Promedio / Demanda <span class="sort-icon" id="sortIcon_avg_views">⇅</span></th>
                            <th class="sortable-th" onclick="sortRankingTable('min_price')">Ticket Mínimo <span class="sort-icon" id="sortIcon_min_price">⇅</span></th>
                            <th class="sortable-th" onclick="sortRankingTable('avg_expenses')">Expensas Prom. <span class="sort-icon" id="sortIcon_avg_expenses">⇅</span></th>
                            <th class="sortable-th" onclick="sortRankingTable('super_deals_count')">Super Oportunidades <span class="sort-icon" id="sortIcon_super_deals_count">⇅</span></th>
                            <th class="sortable-th" onclick="sortRankingTable('liquidity_score')">Liquidez / Reventa <span class="sort-icon" id="sortIcon_liquidity_score">⇅</span></th>
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
        const CABA_SVG_DATA = __CABA_SVG_PLACEHOLDER__;
        const GENERATION_TIME = "__TIMESTAMP_PLACEHOLDER__";

        let currentView = 'cards';
        let currentTab = 'opportunities';
        let favorites = JSON.parse(localStorage.getItem('zonaprop_favs') || '[]');
        let contacted = JSON.parse(localStorage.getItem('zonaprop_contacted') || '[]');
        let chartsInitialized = false;

        let currentMapMode = 'score';
        let currentPerspective = '2d';
        let rankingSortCol = 'count';
        let rankingSortAsc = false;

        // Mapeo de subzonas o nombres de Zonaprop a los 48 polígonos oficiales de CABA
        const SUBZONE_TO_BARRIO = {
            'barrio norte': 'Recoleta', 'recoleta': 'Recoleta', 'once': 'Balvanera', 'abasto': 'Balvanera',
            'balvanera': 'Balvanera', 'congreso': 'Balvanera', 'tribunales': 'San Nicolas', 'centro': 'San Nicolas',
            'centro / microcentro': 'San Nicolas', 'microcentro': 'San Nicolas', 'san nicolas': 'San Nicolas',
            'san nicolás': 'San Nicolas', 'monserrat': 'Monserrat', 'palermo soho': 'Palermo',
            'palermo hollywood': 'Palermo', 'palermo chico': 'Palermo', 'botanico': 'Palermo',
            'botánico': 'Palermo', 'las cañitas': 'Palermo', 'las canitas': 'Palermo', 'palermo': 'Palermo',
            'belgrano r': 'Belgrano', 'belgrano c': 'Belgrano', 'belgrano': 'Belgrano', 'caballito norte': 'Caballito',
            'caballito sur': 'Caballito', 'parque centenario': 'Caballito', 'caballito': 'Caballito',
            'pompeya': 'Nueva Pompeya', 'nueva pompeya': 'Nueva Pompeya', 'lugano': 'Villa Lugano',
            'villa lugano': 'Villa Lugano'
        };

        function normalizeName(name) {
            if (!name) return "";
            return name.normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").toLowerCase().trim();
        }

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
            initArtisanMap();
        }

        function switchMainTab(tab) {
            currentTab = tab;
            document.getElementById('tabOpportunities').classList.toggle('active', tab === 'opportunities');
            document.getElementById('tabAnalytics').classList.toggle('active', tab === 'analytics');
            document.getElementById('sectionOpportunities').style.display = tab === 'opportunities' ? 'block' : 'none';
            document.getElementById('sectionAnalytics').style.display = tab === 'analytics' ? 'block' : 'none';

            if (tab === 'analytics' && !chartsInitialized) {
                initCharts();
                chartsInitialized = true;
            }
        }

        function toggleFavorite(id, e) {
            if (e) e.stopPropagation();
            const idx = favorites.indexOf(id);
            if (idx > -1) favorites.splice(idx, 1);
            else favorites.push(id);
            localStorage.setItem('zonaprop_favs', JSON.stringify(favorites));
            render();
        }

        function toggleContacted(id, e) {
            if (e) e.stopPropagation();
            const idx = contacted.indexOf(id);
            if (idx > -1) contacted.splice(idx, 1);
            else contacted.push(id);
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

        // ==================== ARTISANAL CABA PLANO LOGIC ====================
        function initArtisanMap() {
            if (!CABA_SVG_DATA) return;
            const container = document.getElementById('cabaBarriosGroup');
            if (!container) return;

            // Asociar datos de mercado por barrio
            const nList = MARKET_ANALYTICS.neighborhoods || [];
            const dataByBarrio = {};

            // Mapear barrios analizados
            nList.forEach(item => {
                const norm = normalizeName(item.name);
                const officialName = SUBZONE_TO_BARRIO[norm] || item.name;
                dataByBarrio[normalizeName(officialName)] = item;
            });

            // Normalización para colores
            const benchmarks = nList.map(x => x.benchmark_usd_m2 || 1900);
            const maxBench = Math.max(...benchmarks, 2800);
            const minBench = Math.min(...benchmarks, 1100);

            const viewsList = nList.map(x => x.avg_views || 950);
            const maxViews = Math.max(...viewsList, 2200);
            const minViews = Math.min(...viewsList, 500);

            const sqms = nList.map(x => x.avg_usd_m2 || 1700);
            const maxSqm = Math.max(...sqms, 2100);
            const minSqm = Math.min(...sqms, 1200);

            container.innerHTML = Object.entries(CABA_SVG_DATA).map(([bName, data]) => {
                const norm = normalizeName(bName);
                const mData = dataByBarrio[norm];
                const count = mData ? mData.count : 0;
                const score = mData ? mData.opportunity_density_score : 15;
                const avgSqm = mData ? mData.avg_usd_m2 : 0;
                const bench = mData ? mData.benchmark_usd_m2 : 1900;
                const views = mData ? mData.avg_views : (bName === 'Palermo' ? 2400 : (bName === 'Caballito' ? 2100 : 900));

                let normVal = 0.5;
                if (currentMapMode === 'score') {
                    normVal = count > 0 ? (score / 100) : 0.12;
                } else if (currentMapMode === 'cheapest') {
                    normVal = avgSqm > 0 ? 1 - ((avgSqm - minSqm) / Math.max(1, maxSqm - minSqm)) : 0.2;
                } else if (currentMapMode === 'prime') {
                    normVal = (bench - minBench) / Math.max(1, maxBench - minBench);
                } else if (currentMapMode === 'views') {
                    normVal = (views - minViews) / Math.max(1, maxViews - minViews);
                }

                const color = getPlanoColor(normVal, currentMapMode, count > 0);
                const strokeColor = count > 0 ? color : 'rgba(56, 189, 248, 0.25)';
                const strokeWidth = count > 0 ? '1.8' : '1.0';

                const cx = data.center[0];
                const cy = data.center[1];

                const labelHtml = count > 0 ? `
                    <text class="barrio-svg-label" x="${cx}" y="${cy - 3}" style="fill:#fff; font-weight:800; font-size:10px;">${bName}</text>
                    <text class="barrio-svg-label" x="${cx}" y="${cy + 9}" style="fill:${color}; font-size:9px; font-weight:800;">${count} ${count === 1 ? 'aviso' : 'avisos'}</text>
                ` : `
                    <text class="barrio-svg-label" x="${cx}" y="${cy + 3}">${bName}</text>
                `;

                return `
                <g class="barrio-polygon-group" data-barrio="${bName}" 
                   onmousemove="showArtisanTooltip(event, '${bName}')" 
                   onmouseleave="hideArtisanTooltip()" 
                   onclick="filterByArtisanBarrio('${bName}')">
                    <path class="barrio-poly" d="${data.path}" 
                          fill="${color}" fill-opacity="${count > 0 ? '0.78' : '0.28'}" 
                          stroke="${strokeColor}" stroke-width="${strokeWidth}" />
                    ${labelHtml}
                </g>
                `;
            }).join('');
        }

        function getPlanoColor(v, mode, hasDeals) {
            const val = Math.max(0, Math.min(1, v));
            if (!hasDeals && mode === 'score') return 'rgba(30, 41, 59, 0.4)';

            if (mode === 'score') {
                return val > 0.6 ? '#f97316' : (val > 0.3 ? '#10b981' : '#38bdf8');
            } else if (mode === 'cheapest') {
                return val > 0.6 ? '#10b981' : (val > 0.3 ? '#38bdf8' : '#818cf8');
            } else if (mode === 'prime') {
                return val > 0.6 ? '#eab308' : (val > 0.3 ? '#a855f7' : '#6366f1');
            } else {
                return val > 0.6 ? '#ef4444' : (val > 0.3 ? '#f97316' : '#eab308');
            }
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
                'score': '🎯 Intensidad: Concentración de Oportunidades y Descuento en Cartera',
                'cheapest': '🏷️ Intensidad: Zonas Más Económicas (Menor USD/m² de Oportunidad)',
                'prime': '💰 Intensidad: Zonas Prime / Mayor Valor de Mercado (Benchmark Zonal)',
                'views': '👁️ Intensidad: Barrios Más Vistos y Mayor Rotación Comercial'
            };
            document.getElementById('mapLegendLabel').innerText = labels[mode];
            initArtisanMap();
        }

        function setMapPerspective(perspective) {
            currentPerspective = perspective;
            const viewport = document.getElementById('mapViewport');
            const badge = document.getElementById('mapPerspectiveBadge');
            document.getElementById('btnPersp2D').classList.toggle('active', perspective === '2d');
            document.getElementById('btnPersp3D').classList.toggle('active', perspective === '3d');

            if (perspective === '3d') {
                viewport.classList.add('is-3d');
                badge.innerText = 'Perspectiva 3D Isométrica';
            } else {
                viewport.classList.remove('is-3d');
                badge.innerText = 'Plano 2D Arquitectónico';
            }
        }

        function showArtisanTooltip(e, bName) {
            const tooltip = document.getElementById('mapTooltip');
            const viewport = document.getElementById('mapViewport').getBoundingClientRect();
            
            // Buscar datos del barrio
            const nList = MARKET_ANALYTICS.neighborhoods || [];
            let mData = nList.find(x => normalizeName(x.name) === normalizeName(bName));
            if (!mData) {
                // Chequear mapeo de subzona
                mData = nList.find(x => {
                    const mapped = SUBZONE_TO_BARRIO[normalizeName(x.name)];
                    return mapped && normalizeName(mapped) === normalizeName(bName);
                });
            }

            const count = mData ? mData.count : 0;
            const avgSqm = mData && mData.avg_usd_m2 ? `USD ${mData.avg_usd_m2.toLocaleString('es-AR')}` : 'Sin avisos activos';
            const bench = mData ? `USD ${mData.benchmark_usd_m2.toLocaleString('es-AR')}` : 'Consultar';
            const disc = mData && mData.avg_discount_pct ? `+${mData.avg_discount_pct}%` : 'En línea';
            const views = mData && mData.avg_views ? mData.avg_views.toLocaleString('es-AR') : (bName === 'Palermo' ? '2.400' : '950');
            const demand = mData ? mData.demand_level : (parseInt(views.replace('.','')) >= 1600 ? '🔥 Muy Alta' : '🟢 Alta');
            const exp = mData ? mData.avg_expenses_formatted : 'No informadas';

            tooltip.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #334155; padding-bottom:6px; margin-bottom:8px;">
                    <strong style="font-size:15px; color:#fff;">${bName}</strong>
                    <span style="font-size:11px; background:#38bdf8; color:#0f172a; font-weight:800; padding:2px 7px; border-radius:4px;">
                        ${count} ${count === 1 ? 'aviso' : 'avisos'}
                    </span>
                </div>
                <div style="font-size:12px; line-height:1.6; color:#94a3b8;">
                    <div>📐 USD/m² Cartera: <strong style="color:#10b981;">${avgSqm}</strong></div>
                    <div>🏛️ Benchmark Zonal: <span style="color:#f8fafc;">${bench}/m²</span></div>
                    <div>🏷️ Descuento Medio: <strong style="color:#10b981;">${disc}</strong></div>
                    <div>💵 Expensas Promedio: <span style="color:#f8fafc;">${exp}</span></div>
                    <div>👁️ Vistas Promedio: <strong style="color:#38bdf8;">${views}</strong></div>
                    <div>🔥 Demanda Comercial: <strong style="color:#f8fafc;">${demand}</strong></div>
                </div>
                <div style="margin-top:10px; font-size:11px; color:#38bdf8; text-align:right; font-weight:700;">
                    👉 Clic para ver avisos en Tab Oportunidades
                </div>
            `;

            tooltip.style.display = 'block';
            let left = e.clientX - viewport.left + 15;
            let top = e.clientY - viewport.top + 15;

            // Prevenir desborde en el viewport
            if (left + 230 > viewport.width) left = left - 250;
            if (top + 200 > viewport.height) top = top - 180;

            tooltip.style.left = `${left}px`;
            tooltip.style.top = `${top}px`;
        }

        function hideArtisanTooltip() {
            const tooltip = document.getElementById('mapTooltip');
            if (tooltip) tooltip.style.display = 'none';
        }

        function filterByArtisanBarrio(bName) {
            switchMainTab('opportunities');
            const select = document.getElementById('filterBarrio');
            select.value = bName;
            if (select.value !== bName) {
                // Si el select no lo tiene con ese nombre exacto, filtrar por búsqueda de texto
                document.getElementById('filterSearch').value = bName;
            }
            render();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        // ==================== SORTABLE RANKING TABLE ====================
        function sortRankingTable(col) {
            if (rankingSortCol === col) {
                rankingSortAsc = !rankingSortAsc;
            } else {
                rankingSortCol = col;
                // Para nombres de barrio, comenzar ascendente (A-Z). Para números, descendente (mayor a menor).
                rankingSortAsc = col === 'name' ? true : false;
            }

            // Actualizar clases de th y flechas
            document.querySelectorAll('.sortable-th').forEach(th => th.classList.remove('active-sort'));
            document.querySelectorAll('.sort-icon').forEach(icon => icon.innerText = '⇅');

            const activeIcon = document.getElementById(`sortIcon_${col}`);
            if (activeIcon) {
                activeIcon.parentElement.classList.add('active-sort');
                activeIcon.innerText = rankingSortAsc ? '▲' : '▼';
            }

            renderRankingTable();
        }

        function renderRankingTable() {
            if (!MARKET_ANALYTICS || !MARKET_ANALYTICS.neighborhoods) return;
            const neighborhoods = [...MARKET_ANALYTICS.neighborhoods];

            neighborhoods.sort((a, b) => {
                let valA = a[rankingSortCol];
                let valB = b[rankingSortCol];

                if (typeof valA === 'string') {
                    valA = valA.toLowerCase();
                    valB = valB.toLowerCase();
                    return rankingSortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
                } else {
                    valA = valA || 0;
                    valB = valB || 0;
                    return rankingSortAsc ? valA - valB : valB - valA;
                }
            });

            const heatmapTbody = document.getElementById('heatmapTableBody');
            heatmapTbody.innerHTML = neighborhoods.map(b => {
                const scoreColor = (b.liquidity_score || b.opportunity_density_score) > 70 ? 'var(--accent-flame)' : ((b.liquidity_score || b.opportunity_density_score) > 40 ? 'var(--accent-green)' : 'var(--accent-primary)');
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

            // Render Typology Cards
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

            renderRankingTable();
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
    Genera el archivo HTML inyectando la cartera de propiedades evaluadas, los analytics de mercado
    y el plano vectorial artesanal de los 48 barrios de CABA.
    Retorna la ruta absoluta del archivo generado.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    svg_json_path = os.path.join(base_dir, "barrios_svg.json")
    if os.path.exists(svg_json_path):
        with open(svg_json_path, "r", encoding="utf-8") as f:
            caba_svg_data = f.read()
    else:
        caba_svg_data = "{}"

    json_properties = json.dumps(properties, ensure_ascii=False)
    json_analytics = json.dumps(market_analytics, ensure_ascii=False)
    timestamp = datetime.now().isoformat()

    html_content = (
        HTML_TEMPLATE
        .replace("__DATA_PLACEHOLDER__", json_properties)
        .replace("__ANALYTICS_PLACEHOLDER__", json_analytics)
        .replace("__CABA_SVG_PLACEHOLDER__", caba_svg_data)
        .replace("__TIMESTAMP_PLACEHOLDER__", timestamp)
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path
