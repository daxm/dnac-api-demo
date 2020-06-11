from dnacentersdk import DNACenterAPI
from ruamel.yaml import YAML
import typing
from pathlib import Path

print("hello world!")


def main(config: typing.Dict):
    api = DNACenterAPI(
        username=config['dnac']['username'],
        password=config['dnac']['password'],
        base_url=f"https://{config['dnac']['host']}:443",
    )


if __name__ == "__main__":
    yaml = YAML(typ='safe')
    path = Path('./config.yml')
    with open(path, 'r') as stream:
        try:
            main(config=yaml.load(stream))
        except OSError as e:
            print(f"Error trying to open {path}.  Error: {e}")
            exit(1)
