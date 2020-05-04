"""
Test wrfparams functionality

"""

from optwrf.wrfparams import num2name


def test_num2name():
    param_ids = [13, 6, 7, 22, 51]
    physics_type = 'microphysics'
    param_names = num2name(param_ids, physics_type, in_yaml='params.yml')
    print(param_names)
    assert type(param_names[0]) is str
