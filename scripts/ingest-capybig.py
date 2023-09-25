#!/usr/bin/env python3
import sys
from pathlib import Path
import yaml
import csv

sanitize = str.maketrans('-() +', '_____')

def main():
    basedir = Path(sys.argv[1])
    strip_prefix = basedir
    while strip_prefix != Path('/'):
        if strip_prefix.is_mount():
            break
        strip_prefix = strip_prefix.parent
    else:
        raise ValueError("Why isn't there a mountpoint?")
    outdir = Path(__file__).absolute().parent.parent / 'input'
    try:
        max_file = max(int(fname.name.split('.')[0]) for fname in outdir.iterdir())
    except ValueError:
        max_file = 1
    with open(basedir / 'big.list') as fp:
        fp.readline()
        for brand, basename, suffix in csv.reader(fp, delimiter='\t'):
            fw_file = basedir / suffix

            out_file = outdir / f'{max_file + 1}.yaml'
            max_file += 1
            data = {
                "filename": str(fw_file.relative_to(strip_prefix)),
                "basename": basename,
                "brand": brand,
            }
            with open(out_file, 'w') as fp:
                yaml.dump(data, fp)

if __name__ == '__main__':
    main()
