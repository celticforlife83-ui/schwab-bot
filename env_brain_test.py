from pprint import pprint
from env_brain import get_environment

if __name__ == "__main__":
    env = get_environment("SPX")
    pprint(env)