FROM continuumio/anaconda3:latest

RUN pip install dash==2.0.0
RUN pip install geopandas==0.9.0
RUN pip install matplotlib==3.3.4
RUN pip install plotly==5.3.1
RUN pip install pyarrow==5.0.0
RUN pip install tiledb==0.9.5


COPY . /dash_app

WORKDIR /dash_app

EXPOSE 8050:8050

ENTRYPOINT ["python","app.py"]