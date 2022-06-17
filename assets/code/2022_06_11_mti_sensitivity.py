from copy import deepcopy
import json
from unicodedata import name
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import welleng as we

with open('assets/data/2022_06_11_BK050073.json') as json_file:
    data = json.load(json_file)


def get_survey_mti(survey, rtol=1.0, dls_tol=None, **kwargs):
    mti = survey.modified_tortuosity_index(rtol, dls_tol=dls_tol, data=True)
    starts = np.hstack((deepcopy(mti['starts']), len(survey.md) - 1))

    # build up a trajectory from the mti control points
    connectors = []
    for i, (u, l) in enumerate(zip(starts[1:], starts[:-1])):
        if i == 0:
            connectors.append(
                we.connector.Connector(
                    md1=survey.md[l],
                    pos1=survey.pos_nev[l],
                    vec1=survey.vec_nev[l],
                    pos2=survey.pos_nev[u],
                    dls_design=1e-3
                )
            )
        else:
            connectors.append(
                we.connector.Connector(
                    node1=connectors[-1].node_end,
                    pos2=survey.pos_nev[u],
                    vec2=survey.vec_nev[u],
                    dls_design=1e-3
                )
            )
    survey_new = we.survey.from_connections(
        connectors, survey_header=survey.header, **kwargs
    )

    return survey_new, mti


def figure(survey, survey_mti, mti, rtol, dls_tol):
    # generate base figure
    fig = survey.figure()

    # remove survey points
    fig['data'][1].visible=False

    # add mti control points
    x, y, z = survey_mti.pos_xyz[~survey_mti.interpolated].T
    fig.add_trace(
        go.Scatter3d(
            x=x, y=y, z=z,
            name='survey_point_mti',
            mode='markers'
        )
    )

    # add mti path
    x, y, z = survey_mti.pos_xyz.T
    fig.add_trace(
        go.Scatter3d(
            x=x, y=y, z=z,
            name='path_mti',
            mode='lines'
        )
    )

    # add a title and set camera
    camera = dict(
        eye=dict(x=3.5, y=0., z=0.)
    )

    fig.update_layout(
        scene_camera=camera,
        title=(
            f"Well: {survey.header.name}"
            f"<br><sup>rtol: {rtol} mti: {mti['mti'][-1]:0.4f} "
            f"dls_tol: {dls_tol} "
            f"n: {mti['n_sections'][-1]}</sup>"
        )
    )

    return fig


def get_mti_figure(survey, rtol, dls_tol=None, step=30):
    survey_mti, mti = get_survey_mti(survey, rtol=rtol, dls_tol=dls_tol, step=step)
    fig = figure(survey, survey_mti, mti, rtol=rtol, dls_tol=dls_tol)

    return fig, mti


survey = we.survey.Survey(
    header=we.survey.SurveyHeader(name=data['header'].get('NITG_NR')),
    md=data['data']['AH_DEPTH'],
    inc=data['data']['DEV_ANGLE'],
    azi=data['data']['AZIMUTH']
)

rtols = [1.0, 0.9996, 0.999, 0.1]
dls_tol = 2.0

figs = []
for rtol in rtols:
    fig, mti = get_mti_figure(survey, rtol=rtol, dls_tol=dls_tol)
    figs.append(fig)

# construct a range of rtol values, weighted in the range 0.9 to 1.0
rtols = np.hstack((
    np.linspace(0.001, 0.9, 1000, endpoint=False),
    np.linspace(0.9, 1.0, 1000)
))

mtis = [
    survey.modified_tortuosity_index(rtol=rtol, dls_tol=dls_tol)[-1]
    for rtol in rtols
]

# construct a figure
fig_mtis = go.Figure()
fig_mtis.add_trace(
    go.Scattergl(
        x=rtols,
        y=mtis
    )
)

fig_mtis.add_vrect(
    x0=0.1, x1=0.4, line_width=0, fillcolor="red", opacity=0.2
)

fig_mtis.update_layout(
    title=(
        f"Well: {survey.header.name}"
        f"<br><sup>MTI versus rtol</sup>"
    ),
    xaxis=dict(
        type='log',
        title='rtol'
    ),
    yaxis=dict(
        title='MTI'
    )
)

rtol = 1.0
dls_tols = np.linspace(0, 10, 1000)
mtis = [
    survey.modified_tortuosity_index(rtol=rtol, dls_tol=dls_tol, data=True)
    for dls_tol in dls_tols
]

# construct a figure
fig_dls_tols = make_subplots(specs=[[{"secondary_y": True}]])
fig_dls_tols.add_trace(
    go.Scattergl(
        x=dls_tols,
        y=[mti['mti'][-1] for mti in mtis],
        name="MTI"
    )
)

fig_dls_tols.add_trace(
    go.Scattergl(
        x=dls_tols,
        y=[mti['n_sections'][-1] for mti in mtis],
        name='N_SECTIONS'
    ),
    secondary_y=True
)

# fig_dls_tols.add_vrect(
#     x0=0.1, x1=0.4, line_width=0, fillcolor="red", opacity=0.2
# )

fig_dls_tols.update_layout(
    title=(
        f"Well: {survey.header.name}"
        f"<br><sup>MTI and Number of Sections versus dls_tol</sup>"
    ),
    xaxis=dict(
        title='dls_tol (deg/30m)'
    ),
    yaxis=dict(
        title='MTI'
    )
)
fig_dls_tols.update_yaxes(
    title='Number of Sections',
    secondary_y=True
)
fig_dls_tols.add_vline(
    x=2.0, line_color="green", line_width=3, opacity=0.2
)

mtis_delta = np.hstack((
    [0],
    np.diff(survey.modified_tortuosity_index(rtol=0.01, dls_tol=2.0))
))

# construct a figure
fig_mti_delta = survey.figure()

# remove survey points
fig_mti_delta['data'][1].visible=False

# color the well trajectory with the mti values, make the line thicker and add
# a colobar to show the mti values
fig_mti_delta.data[0]['line']['color'] = survey.modified_tortuosity_index(rtol=0.01, dls_tol=2.0)
fig_mti_delta.data[0]['line']['width'] = 20
fig_mti_delta.data[0]['line']['colorbar'] = dict(
    thickness=40, title="MTI"
)

fig_mti_delta.update_layout(
    title=(
        f"Well: {survey.header.name}"
        f"<br><sup>MTI</sup>"
    )
)

fig_mti_delta.add_vrect(
    x0=0.1, x1=0.4, line_width=0, fillcolor="red", opacity=0.2
)

fig_mti_delta.update_layout(
    title=(
        f"Well: {survey.header.name}"
        f"<br><sup>MTI versus rtol</sup>"
    ),
    xaxis=dict(
        type='log',
        title='rtol'
    ),
    yaxis=dict(
        title='MTI'
    )
)

print("Done")


