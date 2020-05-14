#!/usr/bin/env python3
import sys
import argparse
import yaml


def replace_path(path, target, patch):
    target = dict(target)
    if len(path) == 1:
        target[path[0]] = patch
        return target
    target[path[0]] = replace_path(path[1:], target.get(path[0], {}), patch)
    return target


def main():
    parser = argparse.ArgumentParser(description="Patch one YAML file with another. No templates necessary!")
    parser.add_argument("-b", "--base", required=True, help="Base YAML file.")
    parser.add_argument("-p", "--patch", nargs="+", required=True, help="One or more YAML files to patch into the main file.")
    parser.add_argument("-o", "--out", help="Output file to write to instead of stdout.")

    args = parser.parse_args()
    args = vars(args)
    base_filename = args["base"]
    patch_files = args["patch"]
    out_filename = args["out"]
    with open(base_filename, "r") as f:
        base = yaml.full_load(f)

    for patch_filename in patch_files:
        with open(patch_filename, "r") as f:
            patches = yaml.full_load_all(f)
            for patch in patches:
                if patch is None:
                    continue
                path = patch["path"].split(".")
                patch_dict = patch["patch"]
                base = replace_path(path, base, patch_dict)

    if out_filename is None:
        print(yaml.dump(base))
        return 0

    with open(out_filename, "w") as f:
        yaml.dump(base, f)


if __name__ == '__main__':
    main()
