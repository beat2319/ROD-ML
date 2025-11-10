library(sf)
library(ggplot2)

# --- 1. Load Your Data ---
# Replace with the actual file paths to your GeoJSON files
tryCatch({
  hakalau_boundary <- read_sf("/Users/benatkinson/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian Vault/Projects/ROD-ML/data/location/neatogeo_Hakalau Forest National Wildlife Refuge.geojson")
  rod_2016 <- read_sf("/Users/benatkinson/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian Vault/Projects/ROD-ML/data/response/ROD_geojson/masked_regions/2016ROD_masked.geojson")
}, error = function(e) {
  stop("Error loading files. Please double-check your file paths. \n", e)
})

# --- 2. Check and Match Projections (Crucial) ---
# Layers must have the same Coordinate Reference System (CRS) to align correctly.
if (st_crs(hakalau_boundary) != st_crs(rod_2016)) {
  message("Aligning projections (CRS)...")
  rod_2016 <- st_transform(rod_2016, st_crs(hakalau_boundary))
}

# --- 3. Prepare Data for Legend ---
# To make a legend, we must map an aesthetic (like 'fill') to a data column.
# We'll create a new column called 'status' in the ROD data.
rod_2016$status <- "Affected"

# --- 4. Create the Plot ---
ggplot() +
  
  # Layer 1: The Hakalau outline
  # 'fill = NA' makes the polygon transparent
  # 'color = "black"' draws the black outline
  geom_sf(data = hakalau_boundary, fill = NA, color = "black", linewidth = 0.5) +
  
  # Layer 2: The ROD affected area
  # We map the 'fill' aesthetic to our new 'status' column
  geom_sf(data = rod_2016, aes(fill = status), color = NA) + # 'color = NA' removes the polygon's own border
  
  # Layer 3: Manual Legend and Color Control
  # This is the key to matching your request
  scale_fill_manual(
    name = "ROD Status",  # This is the legend's title
    
    # Define the colors for all possible values
    values = c("Affected" = "red", "Not Affected" = "white"),
    
    # Define the labels for all possible values
    labels = c("Affected" = "Affected", "Not Affected" = "Not Affected"),
    
    # This is the trick:
    # 'limits' forces *both* "Affected" and "Not Affected" to appear in the legend,
    # even though "Not Affected" isn't in our plotted data.
    limits = c("Affected", "Not Affected"),
    
    # This adds a black border to the white swatch so it's visible
    guide = guide_legend(override.aes = list(color = c(NA, "black"))) 
  ) +
  
  # --- 5. Final Touches ---
  theme_bw() + # A clean plot theme
  ggtitle("2016 ROD") +
  labs(x = "Longitude", y = "Latitude")