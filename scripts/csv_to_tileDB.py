import os
import numpy as np
import pandas as pd
import tiledb
import matplotlib.pyplot as plt

from azure_config import azconfig
from fsspec.registry import known_implementations
known_implementations['abfs'] = {'class': 'adlfs.AzureBlobFileSystem'}


def open_dataframe(container, filename):
    """
    Open CSV file on Azure storage as pandas dataframe
    """
    df = pd.read_csv(f"abfs://{container}/{filename}",
                     storage_options=azconfig)
    return df


def write_schema(output_url):
    """
    Call once, will create file/directory structure ready for data
    to be written to it.
    """
    schema = tiledb.ArraySchema(
        domain = tiledb.Domain(*[
            tiledb.Dim(name='Year', domain=(2010,2017),
                       tile=None, dtype='uint64'),
            tiledb.Dim(name='Longitude', domain=(-180., 180),
                       tile=None, dtype='float64'),
            tiledb.Dim(name='Latitude', domain=(-70., 70),
                       tile=None, dtype='float64'),
        ]),
        attrs=[

            tiledb.Attr(name='CountryCode', dtype='int64'),
            tiledb.Attr(name='Mean', dtype='float64'),
            tiledb.Attr(name='Median', dtype='float64'),
            tiledb.Attr(name='StdDev', dtype='float64'),
            tiledb.Attr(name='Upper95', dtype='float64'),
            tiledb.Attr(name='Lower95', dtype='float64'),
        ],
        cell_order='col-major',
        tile_order='col-major',
        sparse=True
    )
    tiledb.SparseArray.create(output_url, schema)


def write_data(df, output_url):
    """
    Call for each year's dataframe - write data to the Array
    """
    with tiledb.open(output_url, 'w') as A:
        df_dict = {k: v.values for k,v in df.items()}
        lat = df_dict.pop('Latitude')
        lon = df_dict.pop('Longitude')
        year = df_dict.pop('Year')
        _ = df_dict.pop('Unnamed: 0')
        A[year, lon, lat] = df_dict


def test_plot(tiledb_url, year):
    """
    Make a simple plot of (roughly) the UK, for specified year
    """
    A = tiledb.open(tiledb_url)
    gb = A.df[year, -5.:5.,50.:60.]
    p = gb.plot.scatter("Longitude", "Latitude", c="Mean")
    plt.show()



if __name__ == "__main__":
    container_name = "who2021-output"
    output_url = "PMSummariesGrid"
    write_schema(output_url)
    for year in range(2010,2017):
        print("Doing year {}".format(year))
        filename = "PMSummariesGrid_{}.csv".format(year)
        df = open_dataframe(container_name, filename)
        write_data(df, output_url)
    print("All done!")
