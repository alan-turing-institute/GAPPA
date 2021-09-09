"""
Script to convert csv files from running the DIMAQ model
(in particular the PMSummaryGrid outputs) into TileDB.
Both input and output can be either on local filesystem or on Azure.

Example (local):
python csv_to_tileDB.py --input_path /path/to/input_dir --output_path /path/to/output

Example (azure):
python csv_to_tileDB.py --input_path container/blob_path --input_location azure --output_path container/output_path --output_location azure

To see all options
python csv_to_tileDB.py --help

Note that to use Azure, you need a file `azure_config.py` in this directory.
Copy the file `azure_config_template.py` and fill in the storage account name
and other details (all available from the Azure portal).
"""

import os
import numpy as np
import pandas as pd
import tiledb
import matplotlib.pyplot as plt
import argparse
import re

from azure_config import azconfig
from fsspec.registry import known_implementations
known_implementations['abfs'] = {'class': 'adlfs.AzureBlobFileSystem'}
from azure.storage.blob import BlobServiceClient

def check_container_exists(container_name, bbs=None):
    """
    See if a container already exists for this account name.
    """
    if not bbs:
        bbs = BlobServiceClient.from_connection_string(
            azconfig["connection_string"]
        )
    container_list = list(bbs.list_containers())
    container_list = [c["name"] for c in container_list]
    return container_name in container_list


def create_container(container_name, bbs=None):
    print("Will create container {}".format(container_name))
    if not bbs:
        bbs = BlobServiceClient.from_connection_string(
            azconfig["connection_string"]
        )
    exists = check_container_exists(container_name, bbs)
    if not exists:
        bbs.create_container(container_name)


def open_dataframe(filepath, filename, local_or_azure):
    """
    Open CSV file on local Azure storage as pandas dataframe
    """

    if local_or_azure.lower() == "azure":
        container = filepath.split("/")[0]
        if len(filepath.split("/")) > 1:
            path = os.path.join(*filepath.split("/")[1:])
            filename = os.path.join(path, filename)
        csv_path = f"abfs://{container}/{filename}"
        print("Reading csv from {}".format(csv_path))
        df = pd.read_csv(csv_path,
                         storage_options=azconfig)
    else:
        df = pd.read_csv(os.path.join(filepath, filename))
    # if 'Year' isn't in the df, but is in filename, add it
    if not "Year" in df.columns:
        year_match = re.search("_([\d]{4}).csv", filename)
        if not year_match:
            raise RuntimeError("Unable to extract year from filename")
        year = int(year_match.groups()[0])
        df["Year"] = year
    return df


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


def write_schema(output_url, schema_type="SummaryGrid"):
    """
    Call once, will create file/directory structure ready for data
    to be written to it.
    """
    print("Will write schema to {}".format(output_url))
    if output_url.startswith("azure://"):
        ctx = get_azure_ctx()
    else:
        ctx = None
    if schema_type == "SummaryGrid" or schema_type == "Samples":
        dom = tiledb.Domain(*[
            tiledb.Dim(name='Year', domain=(2010,2017),
                       tile=None, dtype='uint64'),
            tiledb.Dim(name='Longitude', domain=(-180., 180),
                       tile=None, dtype='float64'),
            tiledb.Dim(name='Latitude', domain=(-70., 70),
                       tile=None, dtype='float64'),
        ])
    elif schema_type == "SummaryCountry":
        dom = tiledb.Domain(*[
            tiledb.Dim(name="CountryCode", domain=(1,233),
                       tile=None, dtype='uint64'),
            tiledb.Dim(name='Year', domain=(2010,2017),
                       tile=None, dtype='uint64'),
            tiledb.Dim(name="Type", domain=(None,None),
                       tile=None, dtype=np.bytes_)
            ])
    else:
        raise RuntimeError("Unknown schema type {}".format(schema_type))

    if schema_type == "SummaryGrid":
        attributes = [
            tiledb.Attr(name='CountryCode', dtype='int64'),
            tiledb.Attr(name='Mean', dtype='float64'),
            tiledb.Attr(name='Median', dtype='float64'),
            tiledb.Attr(name='StdDev', dtype='float64'),
            tiledb.Attr(name='Upper95', dtype='float64'),
            tiledb.Attr(name='Lower95', dtype='float64'),
        ]
    elif schema_type == "SummaryCountry":
        attributes = [
            tiledb.Attr(name='Mean', dtype='float64'),
            tiledb.Attr(name='LowerCI', dtype='float64'),
            tiledb.Attr(name='UpperCI', dtype='float64'),
            tiledb.Attr(name='Median', dtype='float64'),
            tiledb.Attr(name='LowerPI', dtype='float64'),
            tiledb.Attr(name='UpperPI', dtype='float64'),
        ]
    elif schema_type == "Samples":
        attributes = [
            tiledb.Attr(name='POP', dtype='float64'),
            tiledb.Attr(name='CountryCode', dtype='int64'),
        ]
        for i in range(1,101):
            attributes.append(
                tiledb.Attr(name=f'pred_{i}', dtype='float64')
            )
    else:
        raise RuntimeError("Unknown schema_type {}".format(schema_type))


    schema = tiledb.ArraySchema(
        domain = dom,
        attrs = attributes,
        cell_order='col-major',
        tile_order='col-major',
        sparse=True
    )
    tiledb.SparseArray.create(output_url, schema, ctx=ctx)


def write_data(df, output_url, schema_type="SummaryGrid"):
    """
    Call for each year's dataframe - write data to the Array
    """
    if output_url.startswith("azure://"):
        ctx = get_azure_ctx()
    else:
        ctx = None
    with tiledb.open(output_url, 'w', ctx=ctx) as A:
        df_dict = {k: v.values for k,v in df.items()}
        year = df_dict.pop('Year')
        _ = df_dict.pop('Unnamed: 0')
        if schema_type in ["SummaryGrid", "Samples"]:
            lat = df_dict.pop('Latitude')
            lon = df_dict.pop('Longitude')
            A[year, lon, lat] = df_dict
        elif schema_type == "SummaryCountry":
            cc = df_dict.pop('CountryCode')
            weighted = df_dict.pop("Type")
            A[cc, year, weighted] = df_dict
        else:
            raise RuntimeError("Unknown schema type {}".format(schema_type))

def test_plot(tiledb_url, year):
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
    gb = A.df[year, -5.:5.,50.:60.]
    p = gb.plot.scatter("Longitude", "Latitude", c="Mean")
    plt.show()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="convert csv to TileDB")
    parser.add_argument("--input_path", help="path to csv file, including container if on Azure", required=True)
    parser.add_argument("--input_filebase", help="basename of csv file", default="PMSummariesGrid")
    parser.add_argument("--input_location", help="local or Azure", default="local")
    parser.add_argument("--output_path", help="path TileDB dataset, including container, if on Azure", required=True)
    parser.add_argument("--output_location", help="local or Azure", default="local")
    parser.add_argument("--schema_type", help="What type of CSV", choices=["SummaryGrid", "SummaryCountry", "Samples"], default="SummaryGrid")
    args = parser.parse_args()

    if args.output_location.lower() not in ["azure", "local"] or \
       args.input_location.lower() not in ["azure", "local"]:
        raise RuntimeError("Please specify 'azure' or 'local' for input_location and output_location")
    if args.output_location.lower() == "azure":
        container_name = args.output_path.split("/")[0]
        create_container(container_name)
        output_url = "azure://{}".format(args.output_path)
    else:
        output_url = args.output_path
    write_schema(output_url, args.schema_type)
    for year in range(2010,2017):
        print("Doing year {}".format(year))
        filename = "{}_{}.csv".format(args.input_filebase, year)
        df = open_dataframe(args.input_path, filename, args.input_location)
        write_data(df, output_url, args.schema_type)
    print("All done!")
