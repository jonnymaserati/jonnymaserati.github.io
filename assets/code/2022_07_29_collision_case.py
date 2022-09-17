import numpy as np
import welleng as we


def get_meshes(surveys):
    meshes = []
    for survey in surveys:
        meshes.append(
            we.mesh.WellMesh(survey).mesh
        )

    return meshes


md, inc, azi = np.array([
    [0, 0, 0],
    [500, 0, 0],
    [2000, 90, 90],
    [3000, 90, 90]
]).T

reference_survey = we.survey.Survey(
    md=md, inc=inc, azi=azi,
).interpolate_survey(step=30)

md, inc, azi = np.vstack(
    (
        reference_survey.survey_deg[:83],
        reference_survey.survey_deg[-14:]
    )
).T

reference_survey = we.survey.Survey(
    md=md, inc=inc, azi=azi,
    start_nev=[0, -500 - 954.9296585513719, 0],
    error_model='ISCWSA MWD Rev5'
)

md, inc, azi = np.array([
    [0, 0, 0],
    [500, 0, 0],
    [2000, 90, 0],
    [3000, 90, 0]
]).T

offset_survey = we.survey.Survey(
    md=md, inc=inc, azi=azi,
    start_nev=[-500 - 954.9296585513719, 0, 0],
).interpolate_survey(step=30).get_error(error_model='ISCWSA MWD Rev5')

clearance = we.clearance.Clearance(reference_survey, offset_survey)

result = we.clearance.ISCWSA(clearance).SF

meshes = get_meshes([reference_survey, offset_survey])

we.visual.plot(meshes, colors=['red', 'blue'])

print("Done")
