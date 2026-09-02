# 🏢 Zonaprop Hunter & Market Intelligence CABA

Plataforma en Python que rastrea automáticamente avisos de propiedades baratas en venta en la Ciudad Autónoma de Buenos Aires (CABA) desde **Zonaprop**, detecta oportunidades reales según el valor del metro cuadrado ($\text{USD/m}^2$) respecto a los valores zonales, y genera un **Dashboard interactivo en HTML** con listado diario de oportunidades y un **módulo completo de Market Intelligence y Analytics Inmobiliario**.

---

## 🌟 Dos Módulos en una Sola Plataforma

El reporte generado (`index.html` y `output/zonaprop_oportunidades.html`) incluye un menú de navegación superior con dos áreas clave:

### 1. 🔥 Pestaña: Oportunidades & Avisos
- **Listado y Tarjetas con fotos:** Explorador interactivo con fotos en alta resolución, insignias de oportunidad, características (m², ambientes, expensas) y botón de acceso directo a Zonaprop.
- **Filtros en tiempo real:**
  - Selector de Antigüedad: **🕒 Sólo Publicados Hoy** / **Últimas 48 horas** / Todas.
  - Buscador por texto, calle y palabras clave.
  - Filtro por Barrio con conteo dinámico.
  - Sliders de precio máximo y valor máximo de $\text{USD/m}^2$.
  - Selector de Ambientes (Monoambientes, 2 amb, 3+ amb).
  - Toggles rápidos: 🔥 *Sólo Super Oportunidades*, ✨ *Sólo Nuevas de Hoy*, ⭐ *Sólo Favoritos*.
- **Vistas:** Alterna con 1 clic entre **Vista de Tarjetas** y **Vista de Tabla** tipo planilla.
- **Exportación:** Exporta a **Excel/CSV** o **JSON**.

### 2. 📈 Pestaña: Mercado & Analytics CABA
- **Métricas Macroeconómicas:** Valor medio del $\text{USD/m}^2$ en CABA, mediana de precios, superficie media ofertada y porcentaje de descuento zonal.
- **🎯 Radar del Experto (Live Market Insights):** Conclusiones generadas por el motor analítico:
  - *Barrio más accesible para comprar hoy.*
  - *Barrio con mayor margen de arbitraje / descuento.*
  - *Piso de entrada por tipología.*
  - *Oportunidades destacadas en zonas de alta liquidez (Palermo, Recoleta, Belgrano, Caballito).*
- **Gráficos Interactivos (Chart.js):**
  - Gráfico de barras comparativo: $\text{USD/m}^2$ de oportunidad vs Benchmark de mercado por barrio.
  - Gráfico de dona: Distribución de la oferta por rangos de precio ($<\$45\text{k}$, $\$45\text{k}-\$60\text{k}$, $\$60\text{k}-\$75\text{k}$, $>\$75\text{k}$).
- **🏢 Matriz por Tipología:** Comparativa de tickets mínimos, precios medios, medianas y $\text{USD/m}^2$ para **Monoambientes**, **2 Ambientes** y **3+ Ambientes**.
- **🗺️ Mapa de Calor y Ranking de Barrios:** Tabla con barra de scoring visual por barrio, cantidad de avisos, valor de metro cuadrado, descuento medio y precios de entrada.

---

## 🚀 Inicio Rápido

### 1. Ejecutar con 1 clic en Windows
Haz doble clic en el archivo:
```
run_daily.bat
```
El scraper descargará los avisos más recientes, actualizará las estadísticas de mercado y abrirá automáticamente el dashboard en tu navegador.

---

### 2. Ejecutar desde Consola (CLI)
```bash
python scraper_main.py
```

#### Comandos y Filtros Útiles:
- **Filtrar estrictamente publicaciones de hoy:**
  ```bash
  python scraper_main.py --only-today
  ```

- **Buscar propiedades hasta USD 65.000 explorando 6 páginas:**
  ```bash
  python scraper_main.py --max-price 65000 --pages 6
  ```

- **Filtrar únicamente barrios específicos (ej: Palermo, Recoleta, Caballito):**
  ```bash
  python scraper_main.py --barrios palermo,recoleta,caballito --max-price 90000
  ```

- **Fijar un tope de USD/m²:**
  ```bash
  python scraper_main.py --max-usd-m2 1600
  ```

- **Ejecución silenciosa en segundo plano (sin abrir el navegador):**
  ```bash
  python scraper_main.py --no-browser
  ```

---

## ⚙️ Configuración Personalizada (`config.json`)

Puedes modificar los parámetros y los benchmarks de precio promedio por barrio en `config.json`:

```json
{
  "search": {
    "property_type": "departamentos",
    "location": "capital-federal",
    "max_price_usd": 80000,
    "min_price_usd": 18000,
    "min_m2": 18,
    "max_usd_m2": 2200,
    "sort_by": "orden-publicado-descendente",
    "pages_to_scrape": 5,
    "only_published_today": false,
    "include_developments": false,
    "filter_barrios": []
  },
  "neighborhood_benchmarks_usd_m2": {
    "Palermo": 3000,
    "Recoleta": 2600,
    "Belgrano": 2650,
    "Caballito": 2150,
    "Villa Crespo": 2100,
    "Almagro": 1850,
    "Once": 1400,
    "Constitucion": 1300,
    "Default_CABA": 1900
  }
}
```

---

## ⏰ Programación Automática Diaria

- **En la nube (GitHub Actions):** Se ejecuta solo todos los días a las **23:59 hora Argentina** y actualiza Vercel.
- **En Windows local (opcional):** Ejecuta `setup_daily_task.ps1` como Administrador.
