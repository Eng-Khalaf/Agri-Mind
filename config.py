# Configuration Module for Agri-Mind Dashboard
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# ==================== API CONFIGURATION ====================
SENTINELHUB_CLIENT_ID = os.getenv("SENTINELHUB_CLIENT_ID", "")
SENTINELHUB_CLIENT_SECRET = os.getenv("SENTINELHUB_CLIENT_SECRET", "")
SENTINELHUB_SH_CLIENT_ID = os.getenv("SENTINELHUB_SH_CLIENT_ID", "")
SENTINELHUB_SH_CLIENT_SECRET = os.getenv("SENTINELHUB_SH_CLIENT_SECRET", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# ==================== APPLICATION SETTINGS ====================
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
API_RATE_LIMIT = float(os.getenv("API_RATE_LIMIT", "1"))  # requests per second
CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "6"))

# ==================== LOCATION DEFAULTS ====================
DEFAULT_LAT = float(os.getenv("DEFAULT_LAT", "30.3869"))
DEFAULT_LON = float(os.getenv("DEFAULT_LON", "30.3419"))
DEFAULT_ZOOM = int(os.getenv("DEFAULT_ZOOM", "14"))
DEFAULT_LOCATION_NAME = "Wadi El Natrun, Egypt"

# ==================== EGYPT BOUNDARIES ====================
EGYPT_BOUNDS = {
    "north": 32.0,
    "south": 22.0,
    "east": 37.0,
    "west": 25.0
}

# ==================== CROP CONFIGURATION ====================
CROPS_CONFIG = {
    "قمح": {  # Wheat
        "en_name": "Wheat",
        "optimal_ndvi": (0.5, 0.8),
        "optimal_water": (-0.1, 0.2),
        "growing_season": (90, 150),  # days
        "irrigation_interval": 10,  # days
        "fertilizer_schedule": ["Planting", "Tillering", "Boot", "Grain Fill"],
        "pest_risks": ["Aphids", "Hessian Flies", "Armyworms"]
    },
    "برتقال": {  # Citrus
        "en_name": "Citrus",
        "optimal_ndvi": (0.6, 0.75),
        "optimal_water": (0.0, 0.3),
        "growing_season": (365, 365),  # perennial
        "irrigation_interval": 7,  # days
        "fertilizer_schedule": ["Spring Growth", "Flowering", "Fruit Dev", "Pre-Harvest"],
        "pest_risks": ["Scale Insects", "Whiteflies", "Citrus Leaf Miners"]
    },
    "طماطم": {  # Tomato
        "en_name": "Tomato",
        "optimal_ndvi": (0.55, 0.75),
        "optimal_water": (-0.1, 0.2),
        "growing_season": (60, 90),  # days
        "irrigation_interval": 3,  # days
        "fertilizer_schedule": ["Flowering", "Fruit Set", "Fruit Dev", "Ripening"],
        "pest_risks": ["Whiteflies", "Spider Mites", "Tomato Hornworms", "Fusarium Wilt"]
    },
    "ذرة": {  # Corn
        "en_name": "Corn",
        "optimal_ndvi": (0.6, 0.85),
        "optimal_water": (-0.05, 0.25),
        "growing_season": (110, 140),  # days
        "irrigation_interval": 8,  # days
        "fertilizer_schedule": ["V4 Stage", "V12 Stage", "Tasseling", "Silking"],
        "pest_risks": ["European Corn Borers", "Armyworms", "Cutworms"]
    }
}

# ==================== IRRIGATION TYPES ====================
IRRIGATION_TYPES = {
    "تنقيط": "Drip",  # Most efficient
    "غمر": "Flood",   # Traditional
    "محوري": "Pivot"  # Center pivot
}

# ==================== SPECTRAL INDICES THRESHOLDS ====================
NDVI_THRESHOLDS = {
    "healthy_min": 0.6,
    "attention_max": 0.6,
    "attention_min": 0.3,
    "critical_max": 0.3
}

NDWI_THRESHOLDS = {
    "healthy_min": -0.2,
    "attention_max": -0.2,
    "attention_min": -0.4,
    "critical_max": -0.4
}

# ==================== SUSTAINABILITY METRICS ====================
WATER_EFFICIENCY = {
    "flood": 0.6,    # 60% efficiency
    "pivot": 0.85,   # 85% efficiency
    "drip": 0.95     # 95% efficiency
}

CARBON_SEQUESTRATION = {
    "rate_per_hectare": 0.5,  # tonnes CO2 per hectare per season
    "co2_price_per_tonne": 25  # EGP equivalent
}

ELECTRICITY_RATES = {
    "diesel": 2.5,   # EGP per liter
    "electric": 3.5  # EGP per kWh
}

# ==================== SENTINEL HUB SETTINGS ====================
SENTINEL_BANDS = {
    "B1": "Coastal aerosol",
    "B2": "Blue",
    "B3": "Green",
    "B4": "Red",
    "B5": "Vegetation Red Edge",
    "B6": "Vegetation Red Edge",
    "B7": "Vegetation Red Edge",
    "B8": "NIR",
    "B8A": "Vegetation Red Edge",
    "B11": "SWIR",
    "B12": "SWIR"
}

# TRUE Color RGB composition
TRUE_COLOR_SCRIPT = """
//VERSION=3
function setup() {
  return {
    input: [{
      bands: ["B04", "B03", "B02"]
    }],
    output: {
      bands: 3,
      sampleType: "UINT8"
    }
  };
}

function evaluatePixel(sample) {
  return [sample.B04, sample.B03, sample.B02].map(function(v){return 2.5 * v;});
}
"""

# NDVI Script
NDVI_SCRIPT = """
//VERSION=3
function setup() {
  return {
    input: [{
      bands: ["B04", "B08"]
    }],
    output: {
      bands: 1,
      sampleType: "FLOAT32"
    }
  };
}

function evaluatePixel(sample) {
  var nir = sample.B08;
  var red = sample.B04;
  return [(nir - red) / (nir + red)];
}
"""

# NDWI Script
NDWI_SCRIPT = """
//VERSION=3
function setup() {
  return {
    input: [{
      bands: ["B03", "B08"]
    }],
    output: {
      bands: 1,
      sampleType: "FLOAT32"
    }
  };
}

function evaluatePixel(sample) {
  var green = sample.B03;
  var nir = sample.B08;
  return [(green - nir) / (green + nir)];
}
"""

# ==================== TIME RANGES ====================
HISTORICAL_DAYS = 30
FORECAST_DAYS = 7
ANOMALY_THRESHOLD = 0.15  # 15% change in NDVI

# ==================== CACHE SETTINGS ====================
CACHE_VERSION = "v1"
DEMO_DATA_PATH = "demo_data/wadi_el_natrun_demo.tif"

# ==================== UI THEME ====================
THEME_CONFIG = {
    "primaryColor": "#2E7D32",      # Green
    "backgroundColor": "#F1F8E9",   # Light eco-green
    "secondaryBackgroundColor": "#C5E1A5",
    "textColor": "#1B5E20"
}
