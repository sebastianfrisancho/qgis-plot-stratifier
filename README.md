# QGIS Plot Stratifier

### *Spatially constrained optimization for forest sampling design in QGIS*

---

## Overview

**QGIS Plot Stratifier** is a PyQGIS tool designed to optimize the selection of one sampling point inside each polygon while satisfying multiple spatial constraints.

Instead of selecting points independently, the algorithm searches for an optimized solution that simultaneously **maximizes vegetation diversity** and **enforces predefined biomass sampling quotas**.

The workflow was developed for forest inventory, LiDAR calibration, biomass estimation, and carbon monitoring projects, but can be easily adapted to any polygon-based environmental sampling workflow.

---

## Motivation

Many environmental monitoring projects require selecting sampling plots that satisfy several conditions simultaneously. Typical GIS random sampling tools cannot easily enforce concurrent constraints such as:
* Exactly one point per polygon.
* Predefined biomass class proportions.
* Maximization of vegetation diversity.
* Spatial consistency.

This tool addresses those limitations using a stochastic **Monte Carlo** optimization strategy.

---

## Key Features

* **✅ Spatial Autonomy:** Exactly one sampling point per polygon boundary.
* **✅ Dynamic Biomass Stratification:** Dynamic categorization using raster percentiles.
* **✅ Monte Carlo Optimization:** Exploring thousands of combinations in milliseconds.
* **✅ Automatic Vegetation Diversity Enforcement:** Prioritizes unique ecological zones.
* **✅ Modular Architecture:** Developed as a clean, structured Python data pipeline.

---

## Algorithm Workflow

The optimization pipeline consists of six stages:

[Start] ──> load_layers()

└──> generate_candidates()

└──> calculate_percentiles()

└──> classify_candidates()

└──> optimize_selection()

└──> create_output_layer() ──> [Success]

---

## Input Data Requirements

The algorithm requires three standard datasets loaded in QGIS:

| Layer | Type | Description |
| :--- | :--- | :--- |
| **Study Areas** | Polygon Vector | Target boundaries for point allocation |
| **Vegetation Cover** | Polygon Vector | Ecological attributes for diversity enforcement |
| **Biomass Raster** | GeoTIFF Raster | Pixel values ($t/ha$) for stratification |

---

## Optimization Constraints

The optimizer simultaneously satisfies the following four rules:

* **Rule 1:** Exactly one sampling point must be selected inside every polygon.
* **Rule 2:** Global biomass quotas must match user-defined targets (e.g., 5 High, 3 Medium, 2 Low).
* **Rule 3:** Vegetation cover types should not repeat across the selected points whenever possible.
* **Rule 4 (Fallback):** If vegetation repetition is unavoidable due to spatial availability, the biomass classes of those repeated covers must be different.

---

## Dynamic Biomass Classification

Unlike fixed-threshold approaches, biomass classes are calculated automatically from the sampled raster values using **tertiles**:

[Low Biomass]  <  33.33th Percentile  <  [Medium Biomass]  <  66.67th Percentile  <  [High Biomass]

This allows the algorithm to adapt to any biomass raster (e.g., rain forests vs. dry forests) without modifying thresholds manually.

---

## Configuration Example

Modify this block inside the `main()` function:

```python
# USER CONFIGURATION
STUDY_AREAS_LAYER = "study_areas"       # Input polygons layer
VEGETATION_LAYER = "vegetation_cover"   # Input vegetation layer
VEGETATION_COLUMN = "cover_type"        # Field name with vegetation attributes
BIOMASS_RASTER = "biomass_raster"       # Biomass Raster (GeoTIFF)

# The sum of quotas must equal the total number of input polygons!
QUOTAS = {
    "High": 5, 
    "Medium": 3, 
    "Low": 2
}
```
Attribute Output Schema
The output is a new QGIS virtual memory layer containing the optimized points and a clean database:

poly_id: Unique identifier of the source polygon.

vegetation_type: Specific vegetation cover where the point landed.

biomass_value: Floating-point raster value (rounded to 2 decimal places).

biomass_class: Assigned dynamic category (High, Medium, Low).

Requirements
QGIS 3.x

Python 3

NumPy

License
This project is licensed under the MIT License.
