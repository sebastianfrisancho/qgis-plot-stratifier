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

* **Point allocation:** Aims to select one point inside each input polygon.
* **✅ Dynamic Biomass Stratification:** Dynamic categorization using raster percentiles.
* **Stochastic search:** Tests randomized candidate combinations up to a configurable iteration limit; runtime depends on the data and constraints.
* **Vegetation diversity constraint:** Avoids repeating vegetation types where the candidate pools and quotas allow it.
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

The optimizer searches for a selection that satisfies the following rules. Because it uses randomized greedy search, it may fail to find a feasible solution even when one exists:

* **Rule 1:** Select one sampling point inside every polygon that has a suitable candidate.
* **Rule 2:** Global biomass quotas must match user-defined targets (e.g., 5 High, 3 Medium, 2 Low).
* **Rule 3:** Prefer vegetation cover types not already selected.
* **Rule 4 (Fallback):** A repeated vegetation type is allowed only when its biomass class differs from the most recently selected occurrence of that type. This is not a guarantee that all repeated occurrences have distinct classes.

---

## Dynamic Biomass Classification

Unlike fixed-threshold approaches, biomass classes are calculated automatically from the sampled raster values using **tertiles**:

[Low Biomass]  <  33.33th Percentile  <  [Medium Biomass]  <  66.67th Percentile  <  [High Biomass]

Thresholds are calculated from valid raster values sampled among the generated candidate points, not from every pixel in the full raster. Results therefore depend on candidate generation and the input data.

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
The output is a new QGIS memory point layer containing the selected points and these fields:

poly_id: Unique identifier of the source polygon.

vegetation_type: Specific vegetation cover where the point landed.

biomass_value: Floating-point raster value, rounded to 2 decimal places.

biomass_class: Assigned dynamic category (High, Medium, Low).

---

## Requirements

* **QGIS 3.x**
* **Python 3**
* **NumPy**

---

## 👨‍💻 Developer & Author

**Sebastian Frisancho**  
*GIS Specialist & Forest Ecology Researcher*  
* **GitHub:** [@sebastianfrisancho](https://github.com/sebastianfrisancho)
* **LinkedIn:** [Sebastian Frisancho](https://www.linkedin.com/in/sebastianfrisancho/)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
