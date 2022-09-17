"""
A couple of Torque and Drag examples referencing the paper "Torque and Drag in
Directional Wells--Prediction and Measurement (SPE 11380-PA) by C.A. Johancsik
et al.

author: jonny corcutt
email: jonnycorcutt@gmail.com
date: 22-05-2022
"""

import welleng as we

ureg = we.units.ureg


def example_1():
    node0 = we.node.Node(pos=[0, 0, 0], md=0, inc=0, azi=0)
    node1 = we.node.Node(md=305, inc=0, azi=0)
    node2 = we.node.Node(md=2984, inc=37, azi=0)
    connectors = []
    connectors.append(
        we.connector.Connector(node0, node1)
    )
    connectors.append(
        we.connector.Connector(connectors[-1].node_end, node2, dls_design=6)
    )
    survey_example1 = we.survey.from_connections(
        connectors
    ).interpolate_survey(step=30)

    bha = we.architecture.BHA('8 1/2" Drilling BHA', 0, 2984, method="bottom_up")
    bha.add_section(
        od=(7.75 * ureg.inches).to('meters').m,
        id=(4 * ureg.inches).to('meters').m,
        length=(124 * ureg.ft).to('meters').m,
        unit_weight=(146.90 * ureg('lbs / ft').to('kg / meters')).m * 9.81,
        name='7 3/4" DC'
    )

    bha.add_section(
        od=(4.5 * ureg.inches).to('meters').m,
        tooljoint_od=(6.375 * ureg.inches).to('meters').m,
        id=(4 * ureg.inches).to('meters').m,
        length=(990 * ureg.ft).to('meters').m,
        unit_weight=(46.90 * ureg('lbs / ft').to('kg / meters')).m * 9.81,
        name='4 1/2" HWDP'
    )

    bha.add_section(
        od=(4.5 * ureg.inches).to('meters').m,
        tooljoint_od=(6.375 * ureg.inches).to('meters').m,
        id=(4 * ureg.inches).to('meters').m,
        length=None,
        unit_weight=(20 * ureg('lbs / ft').to('kg / meters')).m * 9.81,
        name='4 1/2" DP'
    )

    wellbore = we.architecture.WellBore(
        '8 1/2" Hole Section', 0, 2984, method='top_down'
    )

    wellbore.add_section(
        od=9+5/8, id=8.5,
        bottom=2984 * 0.7,
        coeff_friction_sliding=0.28,
        name='production 9 5/8" casing'
    )

    wellbore.add_section(
        od=None, id=8.5, bottom=2984, unit_weight=None,
        coeff_friction_sliding=0.28, name='8 1/2" OH'
    )

    t_and_d = we.torque_drag.TorqueDrag(
        survey_example1, wellbore, bha,
        fluid_density=11.6 / 8.33,
        wob=10_000, tob=(2_000 * 1.356), overpull=50_000,
        name='8 1/2" Hole Section'
    )

    hookload = we.torque_drag.HookLoad(
        survey_example1, wellbore, bha, fluid_density=11.6 / 8.33, step=30,
        name='8 1/2" Hole Section', ff_range=[0.1, 0.4, 0.1]
    )

    t_and_d.figure().show()
    hookload.figure().show()

    print("Done")


def example_2():
    """"""
    node0 = we.node.Node(pos=[0, 0, 0], md=0, inc=0, azi=0)
    node1 = we.node.Node(md=731.5, inc=0, azi=0)
    node2 = we.node.Node(md=1280, inc=44, azi=0)
    node3 = we.node.Node(md=3718, inc=44, azi=0)
    connectors = []
    connectors.append(
        we.connector.Connector(node0, node1)
    )
    connectors.append(
        we.connector.Connector(connectors[-1].node_end, node2, dls_design=2)
    )
    connectors.append(
        we.connector.Connector(connectors[-1].node_end, node3, dls_design=4)
    )
    survey_example_2 = we.survey.from_connections(
        connectors
    ).interpolate_survey(step=30)

    bha = we.architecture.BHA('8 1/2" Drilling BHA', 0, 3718, method="bottom_up")
    bha.add_section(
        od=(6.5 * ureg.inches).to('meters').m,
        id=(4 * ureg.inches).to('meters').m,
        length=(372 * ureg.ft).to('meters').m,
        unit_weight=(146.90 * ureg('lbs / ft').to('kg / meters')).m * 9.81,
        name='6 1/2" DC'
    )

    bha.add_section(
        od=(4.5 * ureg.inches).to('meters').m,
        tooljoint_od=(6.375 * ureg.inches).to('meters').m,
        id=(4 * ureg.inches).to('meters').m,
        length=(840 * ureg.ft).to('meters').m,
        unit_weight=(46.90 * ureg('lbs / ft').to('kg / meters')).m * 9.81,
        name='5" HWDP'
    )

    bha.add_section(
        od=(5.0 * ureg.inches).to('meters').m,
        tooljoint_od=(6.625 * ureg.inches).to('meters').m,
        id=(3.625 * ureg.inches).to('meters').m,
        length=None,
        unit_weight=(20 * ureg('lbs / ft').to('kg / meters')).m * 9.81,
        name='5" DP'
    )

    wellbore = we.architecture.WellBore(
        '8 1/2" Hole Section', 0, 3718, method='top_down'
    )

    wellbore.add_section(
        od=9+5/8, id=8.5,
        bottom=3688 * 0.7,
        unit_weight=(68 * ureg('lbs / ft').to('kg / meters')).m,
        coeff_friction_sliding=0.39,
        name='production 9 5/8" casing'
    )

    wellbore.add_section(
        od=None, id=8.5, bottom=3718, unit_weight=None,
        coeff_friction_sliding=0.39, name='8 1/2" OH'
    )

    t_and_d = we.torque_drag.TorqueDrag(
        survey_example_2, wellbore, bha,
        fluid_density=9.8 / 8.33,
        wob=10_000, tob=(2_000 * 1.356), overpull=50_000,
        name='8 1/2" Hole Section'
    )

    hookload = we.torque_drag.HookLoad(
        survey_example_2, wellbore, bha, fluid_density=11.6 / 8.33, step=30,
        name='8 1/2" Hole Section', ff_range=(0.1, 0.4, 0.1)
    )

    t_and_d.figure().show()
    hookload.figure().show()

    print("Done")


if __name__ == "__main__":
    example_2()
