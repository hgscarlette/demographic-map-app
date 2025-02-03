import streamlit as st
import leafmap.foliumap as leafmap
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
# import altair as alt
from src.dynamic_filters import DynamicFilters

# import numpy as np

#######################
# Page configuration
st.set_page_config(
    page_title="Location Analytics Dashboard",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="expanded")

# alt.themes.enable("dark")


#######################
# CSS styling
st.write(
    """
    <style>

    [data-testid="stMetric"] {
        text-align: center;
        padding: 15px 0;
    }

    [data-testid="stMetricLabel"] {
        display: flex;
        justify-content: center;
        align-items: center;
    }

    [data-testid="stMetricDelta"] svg {
        display: none;
    }
    
    </style>
    """,
    unsafe_allow_html=True,
)

#######################
## PREPARE DATA

def insert_space(word):
    result = ""
    num = "0123456789-"
    for i in word:
        if i.isupper():
            # Concatenate a space and the uppercase version of the character to the result
            result = result + " " + i.upper()
        elif i in num:
            # Concatenate the character to the result if the previous character was also a number
            if result[-1] in num:
                result = result + i
            # Concatenate a space only if the previous character was not a number
            else:
                result = result + " " + i
        else:
            # Concatenate the character to the result
            result = result + i
    # Remove the leading space from the result and return
    return result[1:]

@st.cache_data
def get_data():
    """
    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """

    # Load GeoJSON of Vietnam's boundaries (Ward level)
    geojson_file = "https://raw.githubusercontent.com/hgscarlette/vn-demographic/main/VN_Boundaries_Ward.json"
    gdf = gpd.read_file(geojson_file, encoding="utf8")
    gdf["city"] = gdf["city"].apply(insert_space)
    gdf["district"] = gdf["dist_title"] + gdf["district"]
    gdf["district"] = gdf["district"].apply(insert_space)
    gdf["ward"] = gdf["ward_title"] + gdf["ward"]
    gdf["ward"] = gdf["ward"].apply(insert_space)

    # Load GeoJSON of Vietnam's boundaries (Dist level)
    geojson_dist_file = "https://raw.githubusercontent.com/hgscarlette/vn-demographic/main/VN_Boundaries_District.json"
    gdf_dist = gpd.read_file(geojson_dist_file, encoding="utf8")
    gdf_dist["city"] = gdf_dist["city"].apply(insert_space)
    gdf_dist["district"] = gdf_dist["dist_title"] + gdf_dist["district"]
    gdf_dist["district"] = gdf_dist["district"].apply(insert_space)

    # # Read cafe location data
    # store_filename = Path(__file__).parent/'data/WCM stores_ext.csv'
    # df = pd.read_csv(store_filename, encoding="utf8")
    # df = pd.merge(gdf[["ward_id","dist_id"]], df, how="inner", on="ward_id")

    # Read Vietnam's population data
    df_pop = pd.read_csv("https://github.com/hgscarlette/vn-demographic/blob/main/VN_Population_ward.csv?raw=true")
    df_pop = df_pop[df_pop.ward_id.isna()==False][["ward_id","area_sqm","total","pop_density","urban","rural"]]
    df_pop = pd.merge(gdf[["ward_id","dist_id"]], df_pop, how="inner", on="ward_id")

    df_pop_dist = df_pop.groupby("dist_id", as_index=False)[["area_sqm","total","urban","rural"]].sum()
    df_pop_dist["pop_density"] = round(df_pop_dist["total"] / df_pop_dist["area_sqm"] * 1e6)

    df_pop["urban_pcnt"] = round(df_pop["urban"] / df_pop["total"], 2) * 100
    df_pop["urban_pcnt"] = df_pop["urban_pcnt"].fillna(0)
    df_pop_dist["urban_pcnt"] = round(df_pop_dist["urban"] / df_pop_dist["total"], 2) * 100
    df_pop_dist["urban_pcnt"] = df_pop_dist["urban_pcnt"].fillna(0)

    df_youngpop = pd.read_csv("https://github.com/hgscarlette/vn-demographic/blob/main/VN_YoungPop_dist.csv?raw=true")
    df_youngpop = df_youngpop[df_youngpop.dist_id.isna()==False][["dist_id","total_15_34","dense_15_34","urban_15_34","rural_15_34"]]
    df_pop_dist = pd.merge(df_pop_dist, df_youngpop, how="inner", on="dist_id")

    # Add population to boundaries
    gdf_pop = pd.merge(df_pop, gdf, how="inner")
    gdf_pop = gpd.GeoDataFrame(gdf_pop, crs="EPSG:4326")

    gdf_pop_dist = pd.merge(df_pop_dist, gdf_dist, how="inner")
    gdf_pop_dist = gpd.GeoDataFrame(gdf_pop_dist, crs="EPSG:4326")

    return gdf, gdf_pop, gdf_pop_dist, df_pop, df_pop_dist, df_youngpop


# Load data
gdf, gdf_pop, gdf_pop_dist, df_pop, df_pop_dist, df_youngpop = get_data()
map_options = ["CartoDB","Google Map","OpenStreetMap","Bus Map","ESRI Street Map","Google Satellite","Google Satellite with POIs","Google Terrain"]


#######################
## SIDEBAR

with st.sidebar:
    st.title("📍Geospatial Analytics")
    # Main filters
    dynamic_filters = DynamicFilters(gdf_pop, filters=["city","district","ward"])
    dynamic_filters.display_filters(num_cols=1)

    # Option 1: population view
    base_population = st.selectbox("Population View", ["Total Population","Population Density"], 0)
    base_pop_col = "pop_density" if base_population=="Population Density" else "total"
    
    # Option 2: basemap
    basemap = st.selectbox("Basemap", map_options, 0)
    
    # About section
    markdown = """
    This interactive map dictates demographic* across every ward of Vietnam to support Location Analyses in Retail and F&B.

    *General Statistics Office of Vietnam as of 2019.
    
    Check out [GitHub repository](https://github.com/hgscarlette/demographic-map-app).
    """
    
    st.divider()
    st.title("About")
    st.info(markdown)


#######################
## FILTERED DATA & PARAMETERS FOR MAPS & CHARTS

if st.session_state["filters"]["city"] or st.session_state["filters"]["district"] or st.session_state["filters"]["ward"]:
    gdf_map = dynamic_filters.filter_df()
    admin_id_type = "ward_id"
    df_chart = df_pop
    
    # Find map's center point
    gdf_dissolve = gdf_map.dissolve(as_index=False)
    gdf_dissolve["center_point"] = gdf_dissolve.representative_point()
    map_center=(gdf_dissolve["center_point"].values[0].y, gdf_dissolve["center_point"].values[0].x)

    # Set map zoom level
    map_zoom = 13 if st.session_state["filters"]["ward"] else (12 if st.session_state["filters"]["district"] else 10)

    # Define tooltip cols
    tooltip_cols = ["city","district","ward"]

else:
    gdf_map = gdf_pop_dist
    admin_id_type = "dist_id"
    df_chart = df_pop_dist
    
    # Find map's center point
    map_center = (16.088850817930474, 107.82173235396314)

    # Set map zoom level
    map_zoom = 6

    # Define tooltip cols
    tooltip_cols = ["city","district"]


#######################
## MAP
map, data = st.columns([4, 3], gap="small")

with map:
    map = leafmap.Map(
        locate_control=True, draw_control=False, attribution_control=True, #latlon_control=True, #draw_export=True, #minimap_control=True,
        center=map_center, zoom=map_zoom, height="700px"
    )

    # Layer 1: Basemap
    basemap_tiles = {
        "CartoDB": "CartoDB.Positron", #light basemap
        "Google Map": "ROADMAP",
        "OpenStreetMap": "OpenStreetMap",
        "Bus Map": "OPNVKarte",
        "ESRI Street Map": "Esri.WorldStreetMap", #highlights of main streets
        "Google Satellite": "SATELLITE",
        "Google Satellite with POIs": "HYBRID",
        "Google Terrain": "TERRAIN" #height
    }
    map.add_basemap(basemap_tiles[basemap])

    # Layer 2: Population color coded
    pop = folium.Choropleth(
                geo_data=gdf_map,
                name="Population",
                fill_opacity=0.4,
                line_weight=1,
                data=gdf_map[base_pop_col],
                columns=[base_pop_col],
                key_on="feature.id",
                fill_color="YlGnBu",
                legend_name="Population (2019)",
                highlight=True,
            ).add_to(map)

    folium.GeoJsonTooltip(
            fields=tooltip_cols + [base_pop_col],
            aliases=tooltip_cols + [base_population],
            localize=True
            ).add_to(pop.geojson)

    # Add to page
    map_container = st_folium(map, height=800)  


#######################
## CHARTS
with data:
    admin_ids = []

    ## HEADER
    # If a polygon is clicked
    if "last_active_drawing" in map_container:
        polygon_clicked = map_container["last_active_drawing"]
        if polygon_clicked:
            for key in polygon_clicked["properties"]:
                if key in ("city","district","ward"):
                    st.markdown("##### 📍" + key.title() + ": " + polygon_clicked["properties"][key])
            if admin_id_type in polygon_clicked["properties"]:
                clicked_admin_id = polygon_clicked["properties"][admin_id_type]
                admin_ids.insert(0, clicked_admin_id)
        # Show admin names as filters
        else:
            for param in ("city","district","ward"):
                if param in gdf_map.columns:
                    if gdf_map[param].nunique() <= 3:
                        st.markdown("##### 📍" + param.title() + ": " + ", ".join(value for value in set(gdf_map[param])))
                    else:
                        st.markdown("##### 📍" + str(gdf_map[param].nunique()) + " selected " + param.title() + "s")
            admin_ids = gdf_map[admin_id_type]

    ## FILTERED DATA
    df_chart = df_chart[df_chart[admin_id_type].isin(admin_ids)]

    st.markdown("##### 📊Population Distribution")

    ## <Data Cards>
    cols = st.columns(2)
    with cols[0]:
        # Card 1: Total Population
        sum_total = gdf_map["total"].sum()
        st.metric(label="Total Population", value="{:,}".format(sum_total), border=True)
        
        # Card 2: Urban Population
        urban_sum = int(gdf_map["urban"].sum())
        urban_pcnt = round(urban_sum / sum_total, 2)
        st.metric(label="Urban Population", value="{:,}".format(urban_sum), border=True, delta="{:.0%}".format(urban_pcnt)+" of total", delta_color="normal") #"inverse"

    with cols[1]:
        # Card 3: Average population density
        density_avg = int(gdf_map["pop_density"].median())
        st.metric(label="Median Density", value="{:,}/Km2".format(density_avg), border=True)

        # Card 4: Young Population
        dist_ids = df_chart[df_chart[admin_id_type].isin(admin_ids)].dist_id
        youngpop_sum = int(df_pop_dist[df_pop_dist.dist_id.isin(dist_ids)]["total_15_34"].sum())
        youngpop_pcnt = round(youngpop_sum / sum_total, 2)

        st.metric(label="Young Population", value="{:,}".format(youngpop_sum), border=True, delta="{:.0%}".format(youngpop_pcnt)+" of total", delta_color="normal")


    if st.session_state["filters"]["city"] or st.session_state["filters"]["district"] or st.session_state["filters"]["ward"]:
        for city in gdf_map["city"].unique():
            with st.expander(f"Summary of {city}", expanded=False):
                df_chart = df_chart.sort_values(["total","pop_density"], ascending=[False, False])
                st.dataframe(gdf_map,
                            column_order=(["city","district","ward","total","pop_density","urban_pcnt"]),
                            hide_index=True,
                            width=None,
                            height=200,
                            column_config={
                                "city": st.column_config.TextColumn(
                                    "City"
                                    ),
                                "district": st.column_config.TextColumn(
                                    "District"
                                    ),
                                "ward": st.column_config.TextColumn(
                                    "Ward"
                                    ),
                                "total": st.column_config.ProgressColumn(
                                    "Population",
                                    format="%f",
                                    min_value=0,
                                    max_value=max(gdf_map.total)
                                    ),
                                "pop_density": st.column_config.ProgressColumn(
                                    "Density",
                                    format="%f/Km2",
                                    min_value=0,
                                    max_value=max(gdf_map.pop_density)
                                    ),
                                "urban_pcnt": st.column_config.NumberColumn(
                                    "% Urban",
                                    format="%f%%",
                                    )}
                                )
