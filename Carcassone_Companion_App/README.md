# Carcassonne Companion (Streamlit App)

An interactive Streamlit companion app for Carcassonne base game scoring, computer vision board analysis, and ML tile segmentation review.

---

## Features

1. **Final Scoring Calculator**:
   - Manage players with custom names and classic meeple colors.
   - Record incomplete constructions according to Carcassonne base game rules:
     - **Cities**: 1 pt per tile + 1 pt per pennant/shield.
     - **Roads**: 1 pt per tile.
     - **Monasteries**: 1 pt for the monastery + 1 pt for each adjacent tile (0–8).
     - **Farms**: 3 pts per adjacent completed city.
   - Dynamic real-time scoreboard, leader highlight, and construction breakdown list.

2. **Board Photo & Computer Vision**:
   - Upload board photos (JPEG, PNG, or HEIC format via `pillow-heif`).
   - Sobel edge filtering and automatic square reference tile detection.
   - Overlay perspective boundaries and mapped tiles.

3. **Tile Catalog & AI Segmentation Review**:
   - Browse the 72 tiles from the Z-Man Games 2014 edition.
   - Inspect cropped tile images side-by-side with ML segmentation masks.
   - View 12 edge segments with terrain classifications and confidence scores.
   - Examine connectivity graphs and special detected features (Monasteries, Shields, Gardens).

---

## How to Run

1. Navigate to the companion app directory:
   ```bash
   cd Carcassone_Companion_App
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Launch the Streamlit application:
   ```bash
   streamlit run app.py
   ```
