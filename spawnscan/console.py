import argparse
import sys

import spawnscan.spawn as spawn


def parse_arguments(args):
    parser = argparse.ArgumentParser(
        description='A simple and fast spawnPoint finder for pokemon go'
    )
    # TODO: Add any command line arguments
    return parser.parse_args(args)


def main():
    args = parse_arguments(sys.argv[1:])

    # Handle the console input
    spawn.main()
