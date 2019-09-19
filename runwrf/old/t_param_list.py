import yaml
import random


with open("params.yml", 'r') as params_file:
    try:
        params = yaml.safe_load(params_file)

    except yaml.YAMLError as exc:
        print(exc)

mp = params.get("microphysics")
lw = params.get("lw radiation")

param_opts = [mp, lw]

param_list = []
for opt in param_opts:
    param_choice = random.choice(list(opt.keys()))
    param_list.append(str(param_choice))

print(param_list)

