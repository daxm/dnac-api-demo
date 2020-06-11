"""Using user info from config.yml establish connection to DNAC and run API call."""

from dnacentersdk import DNACenterAPI, AccessTokenError, ApiError
from ruamel.yaml import YAML
import urllib3
import typing
from pathlib import Path

urllib3.disable_warnings()


def main(config: typing.Dict):
    """Use dnac info from config Dict to establish a connection to DNAC and then run an API call."""
    api = None
    try:
        api = DNACenterAPI(
            username=config['dnac']['username'],
            password=config['dnac']['password'],
            base_url=f"https://{config['dnac']['host']}:443",
            verify=False,
        )
    except AccessTokenError as e1:
        print(f"Probably wrong host or bad credentials.  Error: {e1}")
        exit(1)
    try:
        print(api.devices.get_device_count())
    except ApiError as e2:
        print(f"Something wrong with your API query.  Error: {e2}")


if __name__ == "__main__":
    yaml = YAML(typ='safe')
    path = Path('./config.yml')
    with open(path, 'r') as stream:
        try:
            main(config=yaml.load(stream))
        except OSError as e:
            print(f"Error trying to open {path}.  Error: {e}")
            exit(1)
