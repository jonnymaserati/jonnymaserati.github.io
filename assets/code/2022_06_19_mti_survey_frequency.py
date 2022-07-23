from copy import deepcopy
import json
from unicodedata import name
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import welleng as we


def figure_survey_frequency_overview(dls):
    """
    Create a figure with three trajectories, one vertical, one with
    intermediate tortuosity and another with extreme tortuosity.
    """

    # initiate figure
    fig = go.Figure()

    # start with the extreme tortuosity
    radius = we.utils.radius_from_dls(dls)

    fig.add_shape(
        type="circle",
        xref="x", yref="y",
        x0=0, y0=radius, x1=2*radius, y1=-radius,
        line_color="LightGrey",
    )

    fig.add_shape(
        type="circle",
        xref="x", yref="y",
        x0=0, y0=3*radius, x1=2*radius, y1=radius,
        line_color="LightGrey",
    )

    fig.add_trace(
        go.Scatter(
            x=[0, 0],
            y=[0, radius*np.pi],
            mode='lines',
            line=dict(
                color='blue',
                width=10
            ),
            name='path_0'
        )
    )

    fig.update_layout(
        yaxis=dict(
            autorange='reversed',
            scaleanchor = "x",
            scaleratio = 1,
        ),
        title="Two Possible Paths from a Two Station Survey"
    )

    survey = we.survey.Survey(
        md=[0, radius*np.pi/2, radius*np.pi],
        inc=[0, 90, 0],
        azi=[90, 90, 90]
    ).interpolate_survey(step=1)

    fig.add_trace(
        go.Scatter(
            x=survey.x,
            y=survey.z,
            mode='lines',
            line=dict(
                color='red',
                width=10
            ),
            name='path_1'
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[0, 0, survey.x[-1]],
            y=[0, np.pi*radius, survey.z[-1]],
            mode='markers+text',
            marker=dict(
                color=['green', 'red', 'red'],
                size=20
            ),
            text=['A', 'B1', 'B2'],
            textposition='middle right',
            textfont=dict(
                size=20
            ),
            showlegend=False
        )
    )

    arrow_length = 200

    fig.add_trace(
        go.Scatter(
            x=[0, 0, None, survey.x[-1], survey.x[-1]],
            y=[
                np.pi*radius, np.pi*radius + arrow_length,
                None, 
                survey.z[-1], survey.z[-1] + arrow_length],
            mode='markers+lines',
            marker=dict(
                color='red',
                size=20,
                symbol=['0', 'arrow-down', '0', '0', 'arrow-down']
            ),
            showlegend=False
        )
    )

    return fig


def figure_maximum_curvature(dls=2, inc=60, dls_noise=1):
    """
    Create a figure with three trajectories, one vertical, one with
    intermediate tortuosity and another with extreme tortuosity.
    """
    survey = we.survey.Survey(
        md=[0, inc/dls*30],
        inc=[0, inc],
        azi=[0, 0]
    )

    survey_maxc = maximum_curvature(survey, dls_noise)

    # initiate figure
    fig = go.Figure()

    survey = survey.interpolate_survey(step=1)
    survey_maxc = survey_maxc.interpolate_survey(step=1)

    # start with the extreme tortuosity
    radius = we.utils.radius_from_dls(dls)

    fig.add_shape(
        type="circle",
        xref="x", yref="y",
        x0=0, y0=radius, x1=2*radius, y1=-radius,
        line_color="LightGrey",
    )

    radius = we.utils.radius_from_dls(dls + dls_noise)

    fig.add_shape(
        type="circle",
        xref="x", yref="y",
        x0=0, y0=radius, x1=2*radius, y1=-radius,
        line_color="LightGrey",
    )

    index = np.where(~np.array(survey_maxc.interpolated))[0][1]
    radius = survey_maxc.curve_radius[index+1]
    center = (
        survey_maxc.pos_xyz[index]
        + we.utils.get_xyz(survey_maxc.vec_radius_nev[index])[0] * radius
    )

    fig.add_shape(
        type="circle",
        xref="x", yref="y",
        x0=(
            center[1] - radius
        ),
        y0=(
            center[2] - radius
        ),
        x1=(
            center[1] + radius
        ),
        y1=(
            center[2] + radius
        ),
        line_color="LightGrey",

    )

    fig.update_layout(
        yaxis=dict(
            autorange='reversed',
            scaleanchor = "x",
            scaleratio = 1,
        ),
        title=(
            f"Maximum versus Minimum Curvature"
            f"<br><sup>dls_noise: 1 deg/30m</sup>"
        )
    )

    # survey = we.survey.Survey(
    #     md=[0, radius*np.pi/2, radius*np.pi],
    #     inc=[0, 90, 0],
    #     azi=[90, 90, 90]
    # ).interpolate_survey(step=1)

    fig.add_trace(
        go.Scatter(
            x=survey.y,
            y=survey.z,
            mode='lines',
            line=dict(
                color='blue',
                width=10
            ),
            name='min_curve'
        )
    )

    fig.add_trace(
        go.Scatter(
            x=survey_maxc.y,
            y=survey_maxc.z,
            mode='lines',
            line=dict(
                color='red',
                width=10
            ),
            name='max_curve'
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[0, survey.y[-1], survey_maxc.y[-1], survey_maxc.y[index]],
            y=[0, survey.z[-1], survey_maxc.z[-1], survey_maxc.z[index]],
            mode='markers+text',
            marker=dict(
                color=['green', 'red', 'red', 'blue'],
                size=20
            ),
            text=['A', 'B1', 'B2', 'mid point'],
            textposition='middle right',
            textfont=dict(
                size=20
            ),
            showlegend=False
        )
    )

    arrow_length = 200

    for s in (survey, survey_maxc):
        fig.add_annotation(
            x=(s.pos_xyz[-1] + s.vec_xyz[-1] * arrow_length)[1],
            y=(s.pos_xyz[-1] + s.vec_xyz[-1] * arrow_length)[-1],
            ax=s.y[-1],
            ay=s.z[-1],
            xref='x',
            yref='y',
            axref='x',
            ayref='y',
            text='',  # if you want only the arrow
            showarrow=True,
            arrowhead=1,
            arrowsize=2,
            arrowwidth=2,
            arrowcolor='red'
        )

    fig.add_trace(
        go.Scatter(
            x=[800, 800, 1220],
            y=[550, 790, 800],
            mode='text',
            text=['3 deg/30m', '1 deg/30', '2 deg/30m'],
            textposition='middle right',
            textfont=dict(
                size=20,
                color='LightGrey'
            ),
            showlegend=False
        )
    )

    # fig.add_trace(
    #     go.Scatter(
    #         x=[
    #             survey.y[-1], survey.y[-1],
    #             None,
    #             survey_maxc.y[-1],
    #             (survey_maxc.pos_xyz[-1] + survey_maxc.vec_xyz[-1] * arrow_length)[1]
    #         ],
    #         y=[
    #             survey.z[-1], survey.z[-1] + arrow_length,
    #             None, 
    #             survey_maxc.z[-1], 
    #             (survey_maxc.pos_xyz[-1] + survey_maxc.vec_xyz[-1] * arrow_length)[-1]
    #         ],
    #         mode='markers+lines',
    #         marker=dict(
    #             color='red',
    #             size=20,
    #             symbol=['0', 'arrow-down', '0', '0', 'arrow-down']
    #         ),
    #         showlegend=False
    #     )
    # )

    return fig


def get_iscwsa_example_2():
    # ISCWSA No. 2
    # survey header data
    header = we.survey.SurveyHeader(
        name="ISCWSA No. 2: Gulf of Mexico fish-hook well",
        latitude=28,
        longitude=-90,
        G=9.80665,
        b_total=48_000,
        dip=58,
        declination=2,
        vertical_section_azimuth=21,
        azi_reference='true'
    )

    # generate survey array - these are in feet
    md, inc, azi = np.array([
        [0.0, 0.0, 0.0],
        [2000.0, 0.0, 0.0],
        [3600.0, 32.0, 2.0],
        [5000.0, 32.0, 2.0],
        [5525.54, 32.0, 32.0],
        [6051.08, 32.0, 62.0],
        [6576.62, 32.0, 92.0],
        [7102.16, 32.0, 122.0],
        [9398.5, 60.0, 220.0],
        [12500.0, 60.0, 220.0]
    ]).T

    # initiate Survey instance
    survey = we.survey.Survey(
        md * 0.3048,  # convert to meters
        inc, azi,
        header=header
    )
    return survey


def vec_radius_to_toolface(vec):
    # transform vec to HLA
    vec_hla = we.utils.NEV_to_HLA(vec, cov=False)


def _maximum_curvature(md1, md_total, dls, dls_tortuosity, vec1, vec2):
    radius1 = we.utils.radius_from_dls(dls + dls_tortuosity)
    dogleg1 = md1 / radius1
    vec_normal = np.cross(vec1, vec2)
    vec_radius = np.cross(vec_normal, vec1)
    # toolface = 
    arc_0 = we.utils.get_arc()


# def maximum_curvature(survey, dls_tortuosity):
#     curve_radius = np.full_like(
#         survey.delta_md, we.utils.radius_from_dls(dls_tortuosity)
#     )
#     curve_radius = np.where(
#         curve_radius * np.pi >= survey.delta_md,
#         curve_radius,
#         survey.delta_md / np.pi
#     )
#     _dls_tortuosity = we.utils.dls_from_radius(curve_radius)
#     dls_effective = survey.dls + dls_tortuosity
#     curve_radius_effective = we.utils.radius_from_dls(dls_effective)

#     curve_radius_effective = np.where(
#         curve_radius_effective * np.pi >= survey.delta_md,
#         curve_radius_effective,
#         survey.delta_md / np.pi
#     )

#     # toolface = []
#     # for i, (upper, lower) in enumerate(zip(
#     #     zip(survey.toolface[1:], survey.dls[1:]),
#     #     zip(survey.toolface[:-1], survey.dls[:-1])
#     # )):
#     #     if i == 0:
#     #         toolface.append(lower[0])
#     #     if upper[1] == 0:
#     #         toolface.append(toolface[-1])
#     #     else:
#     #         toolface.append(lower[0])

#     _, _toolface = we.utils.get_angles(we.utils.NEV_to_HLA(
#         survey.survey_rad, survey.vec_radius_nev, cov=False
#     ), nev=True).T

#     toolface = []
#     for i, t in enumerate(np.hstack((_toolface[1:], np.nan))):
#         if i == 0:
#             if np.isnan(t):
#                 toolface.append(0.0)
#             else:
#                 toolface.append(t)
#             continue

#         if np.isnan(t):
#             toolface.append(toolface[-1])
#         else:
#             toolface.append(t)



#     data = list(zip(
#         survey.delta_md, curve_radius_effective, survey.toolface,
#         survey.vec_nev
#     ))

#     arr = []
#     for i, (upper, lower) in enumerate(zip(data[1:], data[:-1])):
#         if i == 0:
#             arr.append([lower[0], *lower[3]])
#         pos, vec, md = we.utils.get_arc(
#             (upper[0] / upper[1]) / 2,
#             upper[1], lower[2], lower[3], target=True
#         )
#         arr.append([md + arr[-1][0], *vec])
#         arr.append([md + arr[-1][0], *upper[3]])
    
#     arr = np.array(arr)
    
#     inc, azi = np.degrees(we.utils.get_angles(arr[:, 1:], nev=True)).T

#     survey_new = we.survey.Survey(
#         md=arr[:, 0],
#         inc=inc,
#         azi=azi,
#         header=survey.header,
#         start_nev=survey.start_nev
#     )

#     return survey_new


def maximum_curvature(survey, dls_noise=1.0, figure=False):
    """
    Create a well trajectory using the Maximum Curvature method.

    Parameters
    ----------
    survey: welleng.Survey.survey object
    dls_noise: float
        The additional Dog Leg Severity (DLS) in deg/30m used to calculate the
        curvature for the initial section of the survey interval.
    
    Returns
    -------
    survey_new: welleng.Survey.survey object
        A revised survey object calculated using the Minimum Curvature method
        with updated survey positions and additional mid-point stations.
    """

    # Iterate through survey station pairs.
    for i, ((md2, vec2, dls), (md1, vec1, survey1)) in enumerate(zip(
        zip(survey.md[1:], survey.vec_nev[1:], survey.dls[1:]),
        zip(survey.md[:-1], survey.vec_nev[:-1], survey.survey_rad[:-1])
    )):
        # add the first survey station to the new survey
        if i == 0:
            _survey_new = [
                [md1, *np.degrees(we.utils.get_angles(vec1, nev=True))[0]]
            ]
        
        # Calculate the vector of the normal plane between of two stations or
        # set to NaN if the vectors are parallel.
        vec_normal = np.cross(vec1, vec2)
        vec_normal = np.nan if np.all(vec_normal==0.0) else vec_normal

        # Calculate the (minimum) curvature radius.
        vec_radius = (
            np.inf if np.all(np.isnan(vec_normal))
            else np.cross(vec_normal, vec1)
        )

        # Calculate the initial toolface - this is used to determine the
        # rotation angle which is used for a transform later. The welleng
        # library has a function for converting from the NEV to HLA domain.
        if np.all(vec_radius == np.inf):
            toolface1 = 0.0
        else:
            _, toolface1 = we.utils.get_angles(we.utils.NEV_to_HLA(
                survey1, vec_radius, cov=False
            ), nev=True).T

        # Calculate the new initial DLS and convert to a curvature radius.
        dls_effective = dls + dls_noise
        radius = we.utils.radius_from_dls(dls)
        radius_effective = we.utils.radius_from_dls(dls_effective)

        # Manage where the path is straight.
        if dls == 0:
            dogleg1 = ((md2 - md1) / radius_effective) / 2
        else:
            dogleg1 = ((md2 - md1) / radius_effective) / 2
        
        # For simplicity, limit the maximum dogleg to 90 degrees - this will
        # be fine for 99% of the time and where it isn't there's likely so
        # more pressing issues with the trajectory.
        if dogleg1 > np.pi:
            dogleg1 = np.pi
            radius_effective = (md2 - md1) * 4 / (2 * np.pi)

        # Use the welleng function to create the first half of the well path
        # as a simple arc and rotate and transform to the survey station.
        arc1 = we.utils.get_arc(dogleg1, radius_effective, toolface1, vec=vec1)

        # Add the new point (the end of the newly created arc) to the new
        # survey.
        _survey_new.append([
            _survey_new[-1][0] + arc1[-1],
            *np.degrees(we.utils.get_angles(arc1[1], nev=True))[0]
        ])

        # The survey station at the end of the section is simply the second
        # survey station, so append this to the list.
        _survey_new.append([
            md2, *np.degrees(we.utils.get_angles(vec2, nev=True))[0]
        ])
    
    # Transform array to Series of md, inc and azi
    md, inc, azi = np.vstack(_survey_new).T

    # Update the new survey header as the new azimuth reference is 'grid'.
    sh = survey.header
    sh.azi_reference = 'grid'

    # Create a new Survey instance
    survey_new = we.survey.Survey(
        md=md,
        inc=inc,
        azi=azi,
        radius=20,
        header=sh,
        start_xyz=survey.start_xyz,
        start_nev=survey.start_nev
    )

    if figure:
        fig = survey_new.interpolate_survey(step=30).figure()
        fig.data[1].visible = False
        fig.data[0].name = 'survey_max_curvature'

        _fig = survey.interpolate_survey(step=30).figure()
        _fig.data[1].visible = False
        _fig.data[0].name = 'survey_min_curvature'
        
        for i, trace in enumerate(_fig.data):
            fig.add_trace(trace)

        fig.data[-1]['marker']['color'] = 'black'
        fig.data[-3]['line']['color'] = 'black'

        mesh = we.mesh.WellMesh(survey_new.interpolate_survey(step=30), method='circle')
        plt = we.visual.Plotter([mesh.mesh])
        plt.show()
    
    return survey_new
        

# fig = figure_maximum_curvature()

survey = get_iscwsa_example_2()

# import ray
# ray.init()

# @ray.remote
# def get_mti(survey, step, dls_noise):
#     mti = maximum_curvature(
#         survey.interpolate_survey(step=step), dls_noise=1.0
#     ).modified_tortuosity_index()[-1]

#     return mti


# mti = ray.get([
#     get_mti.remote(survey, step, dls_noise=1.0)
#     for step in np.linspace(0.1, 1000.0, 1000)
# ])
# ray.shutdown()

# fig = go.Figure()
# fig.add_trace(
#     go.Scatter(
#         x=np.linspace(0.1, 1000.0, 1000),
#         y=mti
#     )
# )
# fig.update_layout(
#     title=(
#         f'Modified Tortuousity Index Versus Interpolated Step Length'
#         f'<br><sup>Using Maximum Curvature method with dls_noise: 1 deg/30m</sup>'
#     ),
#     xaxis=dict(
#         type='log',
#         showgrid=True,
#         title='Interpolation Step (meters)'
#     ),
#     yaxis=dict(
#         title='Modified Tortuosity Index'
#     )
# )
# fig.add_vline(
#     x=30, line_width=3, line_color='red'
# )
# fig.add_vline(
#     x=1, line_width=3, line_color='green'
# )


survey_maxc = maximum_curvature(survey.interpolate_survey(step=1), 1.0, figure=True)

# with open('assets/data/2022_06_11_BK050073.json') as json_file:
#     data = json.load(json_file)

# survey = we.survey.Survey(
#     header=we.survey.SurveyHeader(name=data['header'].get('NITG_NR')),
#     md=data['data']['AH_DEPTH'],
#     inc=data['data']['DEV_ANGLE'],
#     azi=data['data']['AZIMUTH']
# )

# fig = figure_survey_frequency_overview(4)

print("Done")


"""
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

"""
