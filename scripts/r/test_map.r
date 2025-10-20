library(sf)
library(ggplot2)
library(leaflet) 
library(tmap)


xx <- read_sf("/Users/benatkinson/Library/Mobile Documents/com~apple~CloudDocs/Obsidian Vault/projects/ohia/fha.geojson")

tm_shape(xx) +
  tm_polygons("PERCENT_AFFECTED", 
              fill.scale = 'tm_scale_intervals(jenks)', 
              fill.legend = tm_legend('Rapid Ohia Death by Percentage'))
