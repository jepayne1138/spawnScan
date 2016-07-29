import argparse
import sys

import spawnscan.multiscan as multiscan
import spawnscan.check as check


def parse_arguments(args):
    parser = argparse.ArgumentParser(
        description='A simple and fast spawnPoint finder for pokemon go'
    )
    parser.add_argument(
        '-c', '--check', action='store_true',
        help='Check estimated scan time.'
    )
    parser.add_argument(
        '-r', '--radius', type=float, default=100.0,
        help='Radius of each scan point (in meters).'
    )
    parser.add_argument(
        '-e', '--error', type=float, default=0.05,
        help='Percent to overlap values to correct for any error.'
    )
    # TODO: Add any command line arguments
    return parser.parse_args(args)


def main():
    args = parse_arguments(sys.argv[1:])

    if args.check:
        print(
            check.estimate_string(
                radius=args.radius,
                error=args.error,
            )
        )
    else:
        # Handle the console input
        multiscan.main()
