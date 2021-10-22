" Functions to fetch data paths and WRF parameters. "

import pkg_resources
import yaml


def fetch_yaml(yaml_file):
    """
    Lorem ipsum
    """
    # Check to see if the resource exists. If not, directly open the `yaml_file` 
    # (i.e., assume that it's the full path)
    if pkg_resources.resource_exists(__name__, yaml_file):
        file_name = pkg_resources.resource_filename(__name__, yaml_file)
    else:
        file_name = yaml_file
    # Open and return the contents of the yaml file. If there's a YAMLError, 
    # then an empty list will be returned.
    with open(file_name, 'r') as file:
        try:
            contents = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            print(exc)
            contents = []
    return contents
