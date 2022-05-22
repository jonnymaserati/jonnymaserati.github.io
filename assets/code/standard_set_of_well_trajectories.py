import math
import numpy as np
import welleng as we
from typing import Union, List
import time

def tortuosity_index(survey, data=False):
    sections = survey._get_sections()
    sections_upper, sections_lower = sections[1:-1], sections[2:]
    n_sections = len(sections_upper)

    # assume that Survey object is in meters
    l_c = (sections[-1].md - sections[1].md) / 0.3048

    l_cs, l_xs = np.vstack([
        [
            l.md - u.md,
            np.linalg.norm(np.array(l.location) - np.array(u.location))
        ]
        for u, l in zip(sections_upper, sections_lower)
    ]).T

    ti = np.hstack((
        np.array([0.0]),
        (
            (n_sections / (n_sections + 1)) * (1 / l_c) * (
                np.cumsum(
                    (l_cs / l_xs) - 1
                )
            )
        ) * 1e7
    ))

    # if data:
    #     md = np.array([tp.md for tp in sections])[1:]
    #     delta_md = np.hstack(
    #         (
    #             0.0,
    #             md[1:] - md[0:-1]
    #         )
    #     )
    #     result = {}
    #     result['data'] = {}
    #     for i, (_ti, tp, d) in enumerate(zip(ti, sections[1:], delta_md)):
    #         tp.ti = _ti
    #         tp.delta_md = d
    #         tp.build_section = False if tp.dls < 1e-8 else True

    #         result['data'][i] = tp.__dict__
    #     mask = np.array([v['build_section'] for k, v in result['data'].items()])
    #     continuity = np.array([
    #         np.sum(arr)
    #         for arr in np.split(delta_md, 1 + np.where(np.diff(mask))[0])
    #     ])
    #     continuity_builds = np.array([
    #         np.all(arr)
    #         for arr in np.split(mask, 1 + np.where(np.diff(mask))[0])
    #     ])

    #     result['longest_build_section'] = np.max(delta_md[mask])
    #     result['longest_hold_section'] = np.max(delta_md[~mask])
    #     result['longest_cum_build_section'] = (
    #         np.max(continuity[continuity_builds])
    #     )
    #     result['longest_cum_hold_section'] = (
    #         np.max(continuity[~continuity_builds])
    #     )
    #     return (ti[-1], result)

    # else:
    return ti[-1]

def modified_tortuosity_index(self):
    sections = self._get_sections()
    sections_upper, sections_lower = sections[1:-1], sections[2:]
    n_sections = len(sections_upper)

    l_c = (sections[-1].md - sections[1].md) / 0.3048

    l_cs, u_loc, l_loc = [], [], []
    for u, l in zip(sections_upper, sections_lower): 
        l_cs.append(l.md - u.md)
        u_loc.append(u.location)
        l_loc.append(l.location)
    
    l_cs = np.array(l_cs)
    l_xs = np.linalg.norm(np.array(l_loc) - np.array(u_loc), axis=1)

    ti = np.hstack((
        np.array([0.0]),
        (
            (n_sections / (n_sections + 1)) * (1 / l_c) * (
                np.cumsum(
                    (l_cs / l_xs) - 1
                )
            )
        ) * 1e7
    ))

    return ti

    


M_TO_FT = 1/0.3048
FT_TO_M = 0.3048

def dist(pos1: Union[List[float], np.ndarray], pos2: Union[List[float], np.ndarray])->float:
    vec = [p1i - p2i for p1i, p2i in zip(pos1, pos2)]
    return math.sqrt(sum([v1 * v2 for v1, v2 in zip(vec, vec)]))

def cumsum(iterable: Union[List[float], np.ndarray])->List[float]:
    result = iterable.copy()
    for i,el in enumerate(iterable):
        if i != 0:
            result[i] += result[i-1]
    return result

def tortuosity_py(survey):
    sections = survey._get_sections()
    sections_upper, sections_lower = sections[1:-1], sections[2:]
    n_sections = len(sections_upper)

    l_c = (sections[-1].md - sections[1].md) * M_TO_FT

    factor = (n_sections / (n_sections + 1)) / l_c * 1e7

    return cumsum([factor*((l.md - u.md) / dist(l.location, u.location)-1) for u,l in zip(sections_upper, sections_lower)])


def export_data(
    self, deg=True, depth_unit='meters', surface_unit='meters',
    decimals=3
):
    header_angles = [
        'dip', 'convergence', 'declination', 'vertical_inc_limit',
        'vertical_section_azimuth', 'earth_rate'
    ]
    header_exclusions = ['mag_defaults']
    feet = ['ft', 'feet']
    data = {}

    # extract header data
    data['header'] = {
        k: v
        for k, v in vars(self.header).items()
        if k not in header_exclusions
    }

    # convert header angles
    if deg:
        data['header']['angles_unit'] = 'degrees'
        for k, v in data['header'].items():
            if k in header_angles:
                data['header'].update({k: math.degrees(v)})
    
    else:
        data['header']['angles_unit'] = 'radians'
    
    data['header']['error_model'] = self.error_model

    if depth_unit.lower() in feet:
        depth_coeff = 0.3048
        dls_coeff = (1 / (30 / 0.3048)) * 100
        data['header'].update({'depth_unit': 'feet'})
    else:
        depth_coeff, dls_coeff = 1, 1
    
    if surface_unit.lower() in feet:
        surface_coeff = 0.3048
        data['header'].update({'surface_unit': 'feet'})
    else:
        surface_coeff = 1
    
    # if there's no survey error data then make it all zeros
    errors = (
        np.zeros((len(self.md), 3, 3)) if not bool(self.cov_nev)
        else self.cov_nev
    ) * depth_coeff
    
    # extract well trajectory data
    angles = 'deg' if deg else 'rad'

    data['data'] = [
        {
            'md': md, 'inc': inc, 'azi': azi, 'northing': n, 'easting': e,
            'tvd': tvd, 'vs': vs, 'dls': dls, 'error': error
        }
        for i, (md, inc, azi, n, e, tvd, vs, dls, error) in enumerate(zip(
            self.md / depth_coeff, getattr(self, f"inc_{angles}"),
            getattr(
                self,
                f"azi_{self.azi_ref_lookup[self.header.azi_reference]}_{angles}"
            ),
            self.n / surface_coeff, self.e / surface_coeff,
            self.z / depth_coeff, self.vertical_section / surface_coeff,
            self.dls / dls_coeff,
            we.utils.errors_from_cov(errors, data=True).values()
        ))
    ]

    def round_the_numbers(data, decimals):
        """
        A little recursive function to round the numbers in a dict to the
        desired number of decimal places.
        """
        temp = {}
        for k, v in data.items():
            try:
                temp[k] = round(v, decimals)
            except TypeError:
                temp[k] = round_the_numbers(
                    data[k], decimals
                )
        return temp


    # Round the numbers to the desired number of decimals
    for i, row in enumerate(data['data']):
        data['data'][i] = round_the_numbers(row, decimals)
    
    return data


# ISCWSA No. 1

# survey header data
sh_1 = we.survey.SurveyHeader(
    name="ISCWSA No. 1: North Sea extended reach well",
    latitude=60,
    longitude=2,
    G=9.80665,
    b_total=50_000,
    dip=72,
    declination=-4,
    vertical_section_azimuth=75,
    azi_reference='magnetic'
)

# generate survey
md, inc, azi = np.array([
    [0.0, 0.0, 0.0],
    [1200.0, 0.0, 0.0],
    [2100.0, 60.0, 75.0],
    [5100.0, 60.0, 75.0],
    [5400.0, 90.0, 75.0],
    [8000.0, 90.0, 75.0]
]).T

survey_1 = we.survey.Survey(
    md, inc, azi,
    header=sh_1
).interpolate_survey(step=30)

data_1 = export_data(survey_1)

# ISCWSA No. 2

# survey header data
sh_2 = we.survey.SurveyHeader(
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

# generate survey
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

survey_2 = we.survey.Survey(
    md * 0.3048, inc, azi,
    header=sh_2
).interpolate_survey(step=100 * 0.3048)

data_2 = export_data(survey_2, depth_unit='ft', surface_unit='ft')

n = 10_000
start = time.time()
for i in range(n):
    ti0 = modified_tortuosity_index(survey_2)
finish = time.time()
print(f"modified_tortuosity_index = {finish - start} seconds")

start = time.time()
for i in range(n):
    ti1 = tortuosity_py(survey_2)
finish = time.time()
print(f"tortuosity_py = {finish - start} seconds")

start = time.time()
for i in range(n):
    ti2 = tortuosity_index(survey_2)
finish = time.time()
print(f"tortuosity_index = {finish - start} seconds")

print("Done")
