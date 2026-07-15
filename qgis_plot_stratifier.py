"""
===============================================================================
QGIS Plot Stratifier (Spatially Constrained Optimization)
===============================================================================

Author:
    Sebastian Frisancho

Version:
    2.0.0

Description:
    Spatially constrained optimization algorithm for selecting one sampling 
    point per polygon while maximizing vegetation diversity and enforcing 
    global biomass quotas using dynamic raster percentiles.

Requirements:
    - QGIS 3.x
    - Python 3.x
    - numpy (For dynamic percentile calculation)

License:
    MIT License
===============================================================================
"""

__author__ = "Sebastian Frisancho"
__version__ = "2.0.0"

import random
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from PyQt5.QtCore import QVariant

from qgis.core import (
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsSpatialIndex,
    QgsVectorLayer,
    QgsMessageLog,
    Qgis
)

# Safe import for numpy
try:
    import numpy as np
except ImportError:
    QgsMessageLog.logMessage(
        "Numpy library missing. Please install numpy in your QGIS Python environment.",
        "Plot Stratifier",
        Qgis.Critical
    )
    raise ImportError("The 'numpy' library is required to run this script.")


@dataclass
class CandidatePoint:
    """Represents a candidate sampling point with its spatial attributes."""
    geometry: QgsGeometry
    vegetation_type: str
    biomass_value: float
    biomass_class: str = ""  # Assigned dynamically later


def log(message: str, level: Qgis.MessageLevel = Qgis.Info):
    """Helper function to log messages directly to QGIS Message Log panel."""
    QgsMessageLog.logMessage(message, "Plot Stratifier", level)
    print(message)  # Fallback for terminal users


def load_layers(poly_name: str, veg_name: str, raster_name: str) -> Tuple[QgsVectorLayer, QgsVectorLayer, QgsRasterLayer]:
    """Loads and validates required QGIS layers."""
    project = QgsProject.instance()
    try:
        poly = project.mapLayersByName(poly_name)[0]
        veg = project.mapLayersByName(veg_name)[0]
        raster = project.mapLayersByName(raster_name)[0]
        return poly, veg, raster
    except IndexError as e:
        raise FileNotFoundError(f"One or more layers were not found: {poly_name}, {veg_name}, {raster_name}. Error: {e}")


def generate_candidates(poly_layer: QgsVectorLayer, veg_layer: QgsVectorLayer, 
                        raster_layer: QgsVectorLayer, veg_column: str,
                        candidates_limit: int, max_attempts: int) -> Tuple[Dict[int, List[CandidatePoint]], List[float]]:
    """Generates random spatial candidate points within each polygon boundary."""
    veg_index = QgsSpatialIndex(veg_layer.getFeatures())
    raster_provider = raster_layer.dataProvider()
    
    candidates_by_poly = {}
    all_biomass_values = []
    
    for poly_feat in poly_layer.getFeatures():
        poly_id = poly_feat.id()
        poly_geom = poly_feat.geometry()
        bbox = poly_geom.boundingBox()
        
        candidates_by_poly[poly_id] = []
        attempts = 0
        
        while len(candidates_by_poly[poly_id]) < candidates_limit and attempts < max_attempts:
            attempts += 1
            x = random.uniform(bbox.xMinimum(), bbox.xMaximum())
            y = random.uniform(bbox.yMinimum(), bbox.yMaximum())
            point_geom = QgsGeometry.fromPointXY(QgsPointXY(x, y))
            
            if not point_geom.within(poly_geom):
                continue
                
            # Spatial Intersection with Vegetation Layer
            veg_ids = veg_index.intersects(point_geom.boundingBox())
            if not veg_ids:
                continue
            
            veg_feat = veg_layer.getFeature(veg_ids[0])
            veg_type = str(veg_feat[veg_column]).strip()
            
            # Sample raster value
            val, res = raster_provider.sample(QgsPointXY(x, y), 1)
            if not res or np.isnan(val):
                continue
            
            biomass_val = float(val)
            all_biomass_values.append(biomass_val)
            
            candidates_by_poly[poly_id].append(
                CandidatePoint(
                    geometry=point_geom,
                    vegetation_type=veg_type,
                    biomass_value=biomass_val
                )
            )
            
    return candidates_by_poly, all_biomass_values


def calculate_percentiles(biomass_values: List[float]) -> Tuple[float, float]:
    """Calculates tertile thresholds dynamically (33.33% and 66.67%)."""
    if not biomass_values:
        raise ValueError("No biomass values available for calculation.")
    p33 = np.percentile(biomass_values, 33.33)
    p66 = np.percentile(biomass_values, 66.67)
    return p33, p66


def classify_candidates(candidates_by_poly: Dict[int, List[CandidatePoint]], p33: float, p66: float):
    """Categorizes each candidate's biomass value based on dynamic thresholds."""
    for pid, candidates in candidates_by_poly.items():
        for candidate in candidates:
            if candidate.biomass_value > p66:
                candidate.biomass_class = "High"
            elif candidate.biomass_value >= p33:
                candidate.biomass_class = "Medium"
            else:
                candidate.biomass_class = "Low"


def optimize_selection(candidates_by_poly: Dict[int, List[CandidatePoint]], 
                       quotas: Dict[str, int], max_iterations: int) -> Optional[List[Tuple[int, CandidatePoint]]]:
    """Solves the spatial constraints puzzle using a Monte Carlo Simulation."""
    poly_ids = list(candidates_by_poly.keys())
    best_selection = None
    
    for iteration in range(1, max_iterations + 1):
        # Progress reporting inside QGIS every 500 iterations
        if iteration % 500 == 0 or iteration == 1:
            log(f"Monte Carlo Optimization progress: Iteration {iteration}/{max_iterations}...")
            
        current_selection = []
        current_counts = {key: 0 for key in quotas.keys()}
        used_vegetation = {}  # {vegetation_type: biomass_class}
        
        random.shuffle(poly_ids)
        valid_iteration = True
        
        for pid in poly_ids:
            pool = candidates_by_poly[pid]
            random.shuffle(pool)
            
            point_selected = False
            for candidate in pool:
                b_class = candidate.biomass_class
                v_type = candidate.vegetation_type
                
                # Constraint 1: Global Quota Verification
                if b_class not in quotas or current_counts[b_class] >= quotas[b_class]:
                    continue
                    
                # Constraint 2: Unique Veg Cover & Fallback Logic
                if v_type not in used_vegetation:
                    point_selected = True
                else:
                    prev_b_class = used_vegetation[v_type]
                    # Enforce biomass category alternation if vegetation is reused
                    if prev_b_class != b_class:
                        point_selected = True
                
                if point_selected:
                    current_selection.append((pid, candidate))
                    current_counts[b_class] += 1
                    used_vegetation[v_type] = b_class
                    break
            
            if not point_selected:
                valid_iteration = False
                break
                
        if valid_iteration:
            best_selection = current_selection
            log(f"SUCCESS: Perfect combination solved at iteration {iteration}!", Qgis.Success)
            break
            
    return best_selection


def create_output_layer(poly_layer: QgsVectorLayer, selection: List[Tuple[int, CandidatePoint]], output_name: str):
    """Generates the final optimized virtual memory point layer in QGIS."""
    layer_crs = poly_layer.crs()
    out_layer = QgsVectorLayer(f"Point?crs={layer_crs.authid()}", output_name, "memory")
    provider = out_layer.dataProvider()

    # Clean standardized database fields
    fields = [
        QgsField("poly_id", QVariant.Int),
        QgsField("vegetation_type", QVariant.String),
        QgsField("biomass_value", QVariant.Double),
        QgsField("biomass_class", QVariant.String)
    ]
    provider.addAttributes(fields)
    out_layer.updateFields()

    new_features = []
    for pid, candidate in selection:
        new_feat = QgsFeature()
        new_feat.setGeometry(candidate.geometry)
        new_feat.setAttributes([
            pid, 
            candidate.vegetation_type, 
            round(candidate.biomass_value, 2), 
            candidate.biomass_class
        ])
        new_features.append(new_feat)

    provider.addFeatures(new_features)
    out_layer.updateExtents()
    QgsProject.instance().addMapLayer(out_layer)
    log(f"Output point layer '{output_name}' added to QGIS.", Qgis.Success)


def main():
    log("Initializing Spatial Sampling Optimization...")
    
    # =============================================================================
    # USER CONFIGURATION
    # =============================================================================
    STUDY_AREAS_LAYER = "study_areas"       # Input polygons layer (e.g., study areas, zones)
    VEGETATION_LAYER = "vegetation_cover"   # Input vegetation cover vector layer
    VEGETATION_COLUMN = "cover_type"        # Field name representing vegetation classes
    BIOMASS_RASTER = "biomass_raster"       # Biomass GeoTIFF raster layer
    OUTPUT_NAME = "Optimized_Sampling_Points"
    
    # Target quotas for each biomass class. 
    # IMPORTANT: The sum of these quotas must equal the total number of polygons!
    QUOTAS = {
        "High": 5, 
        "Medium": 3, 
        "Low": 2
    }
    
    MAX_ITERATIONS = 5000
    CANDIDATES_PER_POLY = 100
    MAX_ATTEMPTS_PER_POLY = 1000
    # =============================================================================

    try:
        poly_layer, veg_layer, raster_layer = load_layers(STUDY_AREAS_LAYER, VEGETATION_LAYER, BIOMASS_RASTER)
    except FileNotFoundError as e:
        log(str(e), Qgis.Critical)
        return

    # Pipeline execution
    candidates, biomass_values = generate_candidates(
        poly_layer, veg_layer, raster_layer, VEGETATION_COLUMN, 
        CANDIDATES_PER_POLY, MAX_ATTEMPTS_PER_POLY
    )
    
    try:
        p33, p66 = calculate_percentiles(biomass_values)
        log(f"Dynamic Thresholds: Low < {p33:.2f} | Med: {p33:.2f} - {p66:.2f} | High > {p66:.2f}")
    except ValueError as e:
        log(str(e), Qgis.Critical)
        return

    classify_candidates(candidates, p33, p66)
    
    selection = optimize_selection(candidates, QUOTAS, MAX_ITERATIONS)
    
    if not selection:
        log("ERROR: Optimization failed to satisfy all strict constraints. Try revising quotas.", Qgis.Warning)
        return
        
    create_output_layer(poly_layer, selection, OUTPUT_NAME)
    log("Optimization pipeline finished successfully!")


if __name__ == "__main__":
    main()