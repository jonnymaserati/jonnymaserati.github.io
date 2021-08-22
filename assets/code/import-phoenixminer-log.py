import pandas as pd
from datetime import datetime
from copy import copy
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import re
import os


def get_time_stamp(row):
    time_stamp = row.split(': ')[0]
    return time_stamp


def get_gpu_hash_rates(row):
    time_stamp = get_time_stamp(row)
    gpus_data = row.split('GPUs: ')[1:][0]
    data = {
        time_stamp: {}
    }
    for n in range(N_GPUS):
        rate, unit = gpus_data.split(f"{n+1}:")[1].split(" ")[1:3]
        data[time_stamp][n + 1] = dict(
            rate = float(rate),
            unit = unit
        )
    if bool(data[time_stamp]):
        return data
    else:
        return


def split_units(string):
    value, unit = re.findall(r"[^\W\d_]+|\d+", string)
    value = float(value)
    return (value, unit)


def get_gpu_data(row):
    time_stamp = get_time_stamp(row)
    gpus_data = row.split('main ')[1:][0]
    data = {
        time_stamp: {}
    }
    for n in range(N_GPUS):
        temp, fan, power = gpus_data.split(f"GPU{n+1}:")[1].split(" ")[1:4]
        temp, temp_unit = split_units(temp)
        fan = float(fan.strip("%"))
        power, _ = split_units(power)
        data[time_stamp][n + 1] = dict(
            temp = temp,
            temp_unit = temp_unit,
            fan = fan,
            power = power
        )
    if bool(data[time_stamp]):
        return data
    else:
        return


def get_headers(data):
    headers = set(['time', 'gpu'])
    for time, gpus in data.items():
        for _, values in gpus.items():
            for k in values.keys():
                headers.add(k)
    return headers


def data_to_df(data):
    headers = list(get_headers(data))
    arr = []
    for time, gpus in data.items():
        temp = [None] * len(headers)
        for gpu, values in gpus.items():
            for k, v in values.items():
                temp[headers.index(k)] = v
            temp[headers.index('gpu')] = gpu
            temp[headers.index('time')] = convert_to_datetime(time)
            arr.append(copy(temp))
    
    df = pd.DataFrame(
        data=arr,
        columns=headers
    )

    df['time'] = pd.to_datetime(df['time'])

    return df


def convert_to_datetime(time):
    time_new = list(time.replace(".", "-"))
    time_new[-4] = "."
    time_new[10] = " "
    time_new = "".join(time_new)
    return time_new


def import_data(filename):
    counting_gpus = False
    global N_GPUS
    with open(filename) as f:
        content = []
        data = {}
        for row in f:
            row = row.strip("\n")

            if counting_gpus:
                if "GPU" in row:
                    N_GPUS += 1
                    continue
                else:
                    counting_gpus = False

            if "Available GPUs for mining" in row:
                counting_gpus = True
                continue

            if "main" in row:
                if "GPUs" in row:
                    data.update(get_gpu_hash_rates(row))
                else:
                    try:
                        data.update(get_gpu_data(row))
                    except (IndexError, NameError, TypeError, ValueError):
                        continue

            content.append(row)

    df = data_to_df(data)

    return df


def plot(df):
    gpus = df['gpu'].unique()
    subplot_titles = [f"GPU{gpu}" for gpu in gpus]

    fig = make_subplots(
        rows=N_GPUS, cols=1,
        subplot_titles=subplot_titles
    )

    traces = {
        'temp': 'red',
        'power': 'green',
        'fan': 'blue',
        'rate': 'magenta'
    }

    for trace, color in traces.items():
        for i, gpu in enumerate(gpus):
            legendgroup = f"GPU{gpu}"
            temp = df.loc[(df['gpu'] == gpu) & (df[trace].notnull())]
            fig.add_trace(
                go.Scatter(
                    x=temp['time'],
                    y=temp[trace],
                    name=trace,
                    mode='lines',
                    line=dict(
                        color=color
                    ),
                    legendgroup=legendgroup,
                ),
                row=i + 1, col=1
            )

    fig.update_layout(
        height=N_GPUS * 300,
        legend_tracegroupgap=300 - 90,
        template='plotly_dark'
    )

    yaxis_range = [min(df['power'])-10, max(df['power'])+10]

    for i, gpu in enumerate(gpus):
        yaxis_label = "yaxis" if i == 0 else f"yaxis{i + 1}"
        fig.layout[yaxis_label]['range'] = yaxis_range

    return fig


if __name__ == '__main__':
    PATH = os.path.dirname(os.path.realpath(__file__))

    filename = os.path.join(PATH, *("../data", "log20210819_074306.txt"))

    N_GPUS = 0

    df = import_data(filename)

    fig = plot(df)

    fig.show()



print("Done")
