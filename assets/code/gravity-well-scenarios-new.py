"""
References to 'report' are references to Imperial College London Consultants
'Levelised Cost of Storage for energy-designed Gravitricity storage systems'
issued 30th July 2019 and available from Gravitricity on request.
"""

import math
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os

os.environ['DISPLAY'] = ':1'

params = {
    'G': 9.81,
    'density': 7800. - 830.,  # assume well diesel filled and take net density kg/m3
    'costs': {
        'casing_20': 800.,  # $/m
        'casing_13': 400.,  # $/m
        'casing_9': 250.,  # $/m
        'steel': 650.,  # $/tonne
        'rig_rate': 40_000.,  # $/day
        'location_construction': 100_000.,  # cemented, run-off collection, cellar
        'surface_equipment': 100_000.,  # winch, variable speed drive and switch gear
        # 'replacement': 40_000.,  # cost of replacing variable speed drive after 25 years
        'replacement': 0.,  # if life of VSD is 25 years and lifetime is 25 years
        'operating': 10_000.,  # estimate of annual operating cost
        'disposal': 100_000.,  # abandon well and location
        'power': 50.,  # $/MWh taken from report $/MWh
    },
    'depth_of_discharge': 1.,  # able to utilise all stored energy
    'discount_rate': 0.07,
    'lifetime': 25,  # years
    'cycles_per_year': 730,  # same assumption as report
    'annual_degredation': 0.,  # it's mechanical so assume no degredation
    'round_trip_efficiency': 0.85,  # same assumptions as report
    'peak_power_duration': 2.5,  # same assumption as report
}

scenarios = dict(
    big_bore_shallow = {
        'mass_diameter': 17.5 * 2.54 / 100,  # meters
        'mass_length': 250.,  # meters
        'well_length': 500.,  # meters
        'casings': ['casing_20'],
        'casing_shoe_depths': [500.],  # meters
        'time': 5  # time to drill and case the well in days
    },
    average_joe = {
        'mass_diameter': 12.25 * 2.54 / 100,
        'mass_length': 500.,
        'well_length': 1000.,
        'casings': ['casing_20', 'casing_13'],
        'casing_shoe_depths': [500., 1000.],
        'time': 10
    },
    deep = {
        'mass_diameter': 8.5 * 2.54 / 100,
        'mass_length': 1000.,
        'well_length': 2000.,
        'casings': ['casing_20', 'casing_13', 'casing_9'],
        'casing_shoe_depths': [500., 1000., 2000.],
        'time': 20
    },
    big_bore_deep = {
        'mass_diameter': 17.5 * 2.54 / 100,
        'mass_length': 500.,
        'well_length': 1000.,
        'casings': ['casing_20'],
        'casing_shoe_depths': [1000.],
        'time': 7
    },
)

class Result:
    def __init__(self, name, params, **well_params):
        self.name = name
        self.__unpack_dicts(params, well_params)
        self._get_mass()
        self._get_cost()
        self._get_power()
        self._calculate_lcos()
    
    def __unpack_dicts(self, *dicts):
        for d in dicts:
            for k, v in d.items():
                setattr(self, k, v)
    
    def _get_mass(self):
        self.mass_area = (math.pi * self.mass_diameter ** 2) / 4
        self.mass_per_meter = self.density * self.mass_area
        self.mass_mass = self.mass_per_meter * self.mass_length
    
    def _get_cost(self):
        self.total_cost = 0
        self.fixed_cost = (
            self.costs['location_construction']
            + self.costs['surface_equipment']
        )
        self.total_cost += self.fixed_cost

        self.rig_cost = (
            self.time * self.costs['rig_rate']
        )
        self.total_cost += self.rig_cost

        self.octg_cost = sum([
            (length * self.costs[casing])
            for length, casing in zip(self.casing_shoe_depths, self.casings)
        ])
        self.total_cost += self.octg_cost

        self.mass_cost = self.mass_mass * self.costs['steel'] / 1000
        self.total_cost += self.mass_cost
    
    def _get_power(self):
        # total potential energy in MJ
        self.total_energy = (
            self.mass_mass
            * (self.well_length - self.mass_length)
            * self.G
        ) * 1e-6
        # total power in MWh
        self.total_power = (
            self.total_energy
            / (60 * 60)
        )
        self.peak_power = self.total_power / self.peak_power_duration

    def _calculate_lcos(self):
        self.lcos = ((
            self.total_cost
            + self.costs['replacement']
            + self._get_operating_cost()
            + self._get_disposal_cost()
        ) / self._get_electricity_discharged()) + self._get_charging_cost()

    def _get_operating_cost(self):
        time = np.arange(self.lifetime)
        cost = np.sum([
            self.costs['operating']
            / (1 + self.discount_rate) ** n
            for n in time
        ])
        return cost

    def _get_disposal_cost(self):
        cost = (
            self.costs['disposal']
            / (1 + self.discount_rate) ** (self.lifetime + 1)
        )
        return cost
    
    def _get_degredation_cost(self):
        time = np.arange(self.lifetime)
        cost = np.sum([
            (1 + self.annual_degredation) ** n
            / (1 + self.discount_rate) ** n
            for n in time
        ])
        return cost

    def _get_charging_cost(self):
        cost = (
            self.costs['power'] * self.total_power
            / self.round_trip_efficiency
        )
        return cost

    def _get_electricity_discharged(self):
        electricity = (
            self.cycles_per_year
            * self.depth_of_discharge
            * self.total_power
            * self.round_trip_efficiency
            * self._get_degredation_cost()
        )
        return electricity

if __name__ == '__main__':
    results = [Result(s, params, **scenarios[s]) for s in scenarios]

    data = []
    x = ['Charging', 'Replacement', 'O&M', 'Investment'][::-1]
    temp = []
    names = []
    for r in results:
        names.append(r.name)
        temp.append([
            r._get_charging_cost(),
            r.costs['replacement'] / r._get_electricity_discharged(),
            r._get_operating_cost() / r._get_electricity_discharged(),
            r.total_cost / r._get_electricity_discharged()
        ])
    
    y = np.vstack(temp).T[::-1]
    colors = ['rgb(8,81,156)', 'rgb(33,113,181)', 'rgb(66,146,198)', 'rgb(158,202,225)']

    for i, cost in enumerate(x):
        data.append(
            go.Bar(
                name=cost,
                x=names,
                y=y[i],
                marker_color=colors[i]
            )
        )
    
    data[-1]['text'] = [f"${r.lcos:.0f}" for r in results]
    data[-1]['textposition'] = 'outside'
    
    fig = go.Figure(
        data=data
    )
    fig.update_layout(
        barmode='stack',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        )
    )
    fig.show()


print("Done")
