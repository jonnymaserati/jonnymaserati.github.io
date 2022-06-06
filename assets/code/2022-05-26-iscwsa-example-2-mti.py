import numpy as np
import welleng as we


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
).interpolate_survey(step=100 * 0.3048)  # convert per 100 ft to meters

# calculate the MTI using convenience method
mti = survey.modified_tortuosity_index(data=True)

# check the result
# generate a plot to show MTI
fig = survey.figure()

for i in range(1, 3):
    fig.data[i].visible = False

fig.data[0]['line']['color'] = mti['mti']
fig.data[0]['line']['width'] = 20
fig.data[0]['line']['colorbar'] = dict(
    thickness=40, title="MTI"
)
fig.update_layout(
    title="Modified Tortuosity Index (MTI)<br><sup>ISCWSA Example no. 2</sup>"
)

print("Done")
