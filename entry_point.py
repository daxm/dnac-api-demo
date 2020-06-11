from dnacentersdk import DNACenterAPI, AccessTokenError, ApiError
from ruamel.yaml import YAML
import urllib3
import typing
from pathlib import Path

urllib3.disable_warnings()


def main(config: typing.Dict):
    api = None
    try:
        api = DNACenterAPI(
            username=config['dnac']['username'],
            password=config['dnac']['password'],
            base_url=f"https://{config['dnac']['host']}:443",
            verify=False,
        )
    except AccessTokenError as e:
        print(f"Probably wrong host or bad credentials.  Error: {e}")
        exit(1)
    try:
        print(api.pnp.get_workflows()[0])
    except ApiError as e:
        print(f"Something wrong with your API query.  Error: {e}")


if __name__ == "__main__":
    yaml = YAML(typ='safe')
    path = Path('./config.yml')
    with open(path, 'r') as stream:
        try:
            main(config=yaml.load(stream))
        except OSError as e:
            print(f"Error trying to open {path}.  Error: {e}")
            exit(1)
