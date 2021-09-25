"""
A quick bit of code to demonstrate how to import a large .csv file with
realtime drilling parameters, resample the data to reduce the number of points
and then to plot the traces with a shared time axis.

author: jonny corcutt
email: jonnycorcutt@gmail.com
date: 25-09-2021
"""

import pandas as pd
import os
from plotly.subplots import make_subplots
import plotly.graph_objects as go

PATH = os.path.dirname(os.path.realpath(__file__))

# Assume that the data file is located in a subfolder called data
data_filename = os.path.join(
    PATH, *['data', 'Norway-Statoil-NO 15_$47$_9-F-1 C 0 time.csv']
)

# I cheated here and took a look at the data in a spreadsheet - below is a
# list of headers that have data and I've commented out the ones that I do not
# want to plot in the figure.
headers = [
    'The mnemonic of the index curve ',
    'Block/Topdrive Position Compensated m',
    # 'Annular Velocity Monitor Maximum m/s',
    'Mud Flow In m3/s',
    # 'Cementing Flow In (measured) m3/s',
    # 'Cementing Fluid Density In kg/m3',
    # 'Cementing Stage Number unitless',
    # 'Cementing Fluid Temperature In K',
    # 'ECD at Casing Shoe kg/m3',
    # 'Cementing Individual Volume Pumped m3',
    # 'Cementing Cumulative Returns m3',
    # 'Pump Total Cumulative Stroke Sum unitless',
    # 'Mud Flow Out Percent Euc',
    # 'Cementing Flow In (calculated) m3/s',
    'Hookload N',
    # 'Pump 3 Stroke Rate Hz',
    # 'NoMonitor[0] Drilling[1] Reaming[2] OffBottom[3] InSlips[4] Connection[5] TrippingIn[6] TrippingOut[7] TripInSlips[8] ShutIn[9] Circulating (10) Rotating (100) -  112 means rotating, circulating, reaming, 013 means not rotating, circulating, off bottom . unitless',
    # 'Pump 2 Stroke Rate Hz',
    # 'Cementing Pump Pressure Pa',
    # 'Cementing Flow Out (measured) m3/s',
    # 'Cementing Total Volume Pumped m3',
    # 'Cementing Fluid Density Out kg/m3',
    'The mnemonic of the Hole depth m',
    # 'Cementing Fluid Temperature Out K',
    'Pump Pressure - Stand Pipe Pa',
    # 'RawData[0] unitless',
    # 'Pump 1 Stroke Rate Hz',
    # 'Cementing Cement Volume Pumped m3',
    # 'nameWellbore',
    # 'name'
]

# import the data - assign the first column as the index
df = pd.read_csv(
    data_filename, skipinitialspace=True, usecols=headers, low_memory=False,
    index_col=0
)

# change the index and depth names to something more intuitive and make the
# index datetime
df.index.names = ['Time']
df.index = pd.to_datetime(df.index)
df.rename(
    columns={
        'The mnemonic of the Hole depth m': 'Depth m'
    },
    inplace=True
)

# there's a whole bunch of data... too much to plot. Resample the taking the
# rolling 15 min average values
df_resample = df.resample('15T').mean()

# generate the figure
traces = list(df.columns.values)

fig = make_subplots(
    rows=1, cols=len(traces),
    shared_yaxes=True,
    subplot_titles=traces
)

for i, t in enumerate(traces):
    fig.add_trace(
        go.Scattergl(
            x=df_resample[t], y=df_resample.index,
            name=t
        ),
        col=i+1, row=1,
    )

fig.update_layout(
    showlegend=False,
    yaxis=dict(
        autorange='reversed'
    ),
    title_text="realtime_dd by jonny corcutt",
)

# there's some rogue data in the hookload - manually set the range of the
# axis so it plots nicely
fig.layout[f"xaxis{traces.index('Hookload N')+1}"]['range'] = (
    [-200, 4e6]
)

fig.show()

print("Done")
