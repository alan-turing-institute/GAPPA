"""
Utility functions needed to create a plotly map of the PM2.5 air pollution
summarized by country.
"""


import os

import json
import requests
import tempfile
import tiledb

import pandas as pd
import geopandas as gpd

import plotly.express as px

# copy the azure_config_template.py file to azure_config.py
# and fill in details of your Azure storage account
from azure_config import azconfig

def get_azure_ctx():
    """
    Construct context object to allow tiledb to access Azure container.
    """
    config = tiledb.Config()
    config["vfs.azure.storage_account_name"] = azconfig["account_name"]
    config["vfs.azure.storage_account_key"] = azconfig["account_key"]
    config["vfs.azure.blob_endpoint"] = "{}.blob.core.windows.net".format(
        azconfig["account_name"]
    )
    ctx = tiledb.Ctx(config=config)
    return ctx


def read_shapefile(base_url):
    td = tempfile.TemporaryDirectory()
    for suffix in [".shp",".dbf",".prj",".sbn",".sbx",".shx"]:
        shapefile_url = base_url + suffix
        shapefile_url += azconfig["sas_token"]
        r = requests.get(shapefile_url)
        if r.status_code != 200:
            raise RuntimeError("error getting URL {}".format(shapefile_url))
        outfilename = os.path.join(td.name, "shapes"+suffix)
        with open(outfilename, "wb") as outfile:
            outfile.write(r.content)
    gdf = gpd.read_file(os.path.join(td.name, "shapes.shp"))
    return json.loads(gdf.to_json())


def read_who_map(url):
    url += azconfig["sas_token"]
    df = pd.read_csv(url)
    return df


shapefile_url = "https://dimaqdata.blob.core.windows.net/who2021-raw/Shapefiles/detailed_2013"
who_map_url = "https://dimaqdata.blob.core.windows.net/who2021-processed/Shapefiles/WHO_map.csv"
tiledb_url = "azure://who2021-tiledb/PMSummariesCountry"

shape_json = read_shapefile(shapefile_url)
map_df = read_who_map(who_map_url)


def read_country_summary(tiledb_url, year, weight_type="Population-weighted"):
    """
    Make a simple plot of (roughly) the UK, for specified year
    For datasets on Azure, the url will be something like
    azure://{container_name}/{dir_path}
    """
    if tiledb_url.startswith("azure://"):
        ctx = get_azure_ctx()
    else:
        ctx = None
    A = tiledb.open(tiledb_url, ctx=ctx)
    df = A.df[:, year, weight_type]
    return df


def merge_dfs(pm_summary, who_map):

    df = pd.merge(pm_summary,
                  who_map,
                  left_on="CountryCode",
                  right_on="CountryCode")
    return df

def get_country_map(year, weight_type="Population-weighted"):

    pm_df = read_country_summary(tiledb_url, year, weight_type)

    df = merge_dfs(pm_df, map_df)

    fig = px.choropleth(df,
                        geojson=shape_json,
                        locations='ISO3',
                        featureidkey="properties.ISO_3_CODE",
                        color='Mean',
                        hover_data = ["LowerCI", "UpperCI", "Type","Year"],
                        color_continuous_scale="Viridis",
                        range_color=(0, 100),
                        scope="world",
                        labels={'Mean':'Mean PM2.5'}
    )
    return fig
#fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
#fig.show()
