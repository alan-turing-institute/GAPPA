## Guide to notebooks in this repo

### Using the conda environment

One of the use-cases of these notebooks is to run in the cloud, e.g. on an Azure Machine Learning compute instance.
It is possible to use the `gappa` conda environment created following the instructions here, for Jupyter notebooks even in the cloud environment.  To do this:
* (if not already done) clone this repo on the machine/VM that you will be running Jupyter on (in Juypyterlab this is straightforward to do in a terminal).
* `cd` to the `GAPPA` directory and do
```
conda env create -f env.yaml
```
* Run the command
```
python -m ipykernel install --user --name gappa
```
in the terminal on this machine/VM
* Now, when you start a new Jupyter notebook tab, you should be able to click on the "Kernel" at the top right of the screen, and select "gappa".
