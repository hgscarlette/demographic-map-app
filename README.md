# VN Demographic Map Webapp 

A webapp built in Python using Streamlit and deployed to [Streamlit Cloud](https://streamlit.io/cloud).

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://vn-demographic-map.streamlit.app/)

### To run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run Home.py
   ```

## Data sources
VN population data and boundaries are orginated from [vn-demographic project](https://github.com/hgscarlette/vn-demographic), which sourced from [Population and Housing Census 01/4/2019](http://portal.thongke.gov.vn/khodulieudanso2019), [GADM maps and data](https://gadm.org) and the CityScope project run by [City Science Lab @ Ho Chi Minh City](https://www.media.mit.edu/projects/city-science-lab-ho-chi-minh-city/overview/).

## Demo
The default map shows population distribution by District level across Vietnam.

To view by Ward level, select relevant filters from the sidebar. Multi selection is allowed in administrative filters (city/district/ward).

Click on anywhere of the map to see the stats for that particular administrative.

![](https://github.com/hgscarlette/demographic-map-app/blob/main/app_demo.png)
