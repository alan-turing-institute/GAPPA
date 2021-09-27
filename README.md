# GAPPA
Global Air Pollution using Pangeo on Azure

### What is GAPPA

GAPPA is a collaboration between the University of Exeter, the Alan Turing Institute, and the Met Office Informatics Lab, to improve accessibility of the DIMAQ air pollution model (itself a collaboration between Exeter and the WHO).

### Creating a conda environment 

Clone this repo, then run the command: `conda env create -f env.yaml`.   This will create a conda environment called "gappa", which can be activated with `conda activate gappa`.

## Contents so far:

### Scripts: Convert PM summary csv files to tileDB format

The output of the DIMAQ model can be saved as csv files.   There are three types of these csv:
* PM Samples:  For every grid cell (longitude and latitude) and year, there will be 100 values of PM2.5 air pollution, corresponding to 100 samples from the posterior of the model.
* PM Summaries Country:  For each country code, there are mean, median, and uncertainty values for PM2.5 pollution, both unweighted and weighted by population.
* PM Summaries Grid: For each 10km grid cell (longitude and latitude) there are mean, median, and quantile values for PM2.5 pollution levels.

The file `scripts/csv_to_tileDB.py` contains code to read these CSV files into a dataframe, create a TileDB schema for the appropriate type of output, and write the data.   Both the inputs and outputs can either be on the local filesystem or the Azure cloud.
To see the various options for running the script, do 
```
python csv_to_tileDB.py --help
```

### Notebooks: example of reading TileDB from Azure

The jupyter notebook `notebooks/Reading_from_tileDB.ipynb` shows a couple of examples of reading data from the TileDB datasets on Azure and making basic plots.

### Example dashboard

In the `dashboard/` directory there is an example using Plot.ly/Dash to show a dashboard of the mean PM2.5 estimates per country, including a slider to change the year, and a radio button to choose between population-weighted or unweighted values.  
There is also a Dockerfile which can be used to containerize this application, and [instructions](dashboard/DeployWebAppOnAzure.md) on how to do this and then deploy as an Azure WebApp.
