#!/usr/bin/env python3
import sys
from pathlib import Path
import yaml

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
    for brand_dir in basedir.iterdir():
        try:
            brand_dir = brand_dir.readlink()
        except OSError:
            pass
        if not brand_dir.is_dir():
            continue
        for fw_file in brand_dir.iterdir():
            try:
                fw_file = fw_file.readlink()
            except OSError:
                pass
            if not fw_file.is_file():
                continue
            out_file = outdir / f'{max_file + 1}.yaml'
            max_file += 1
            data = {
                "filename": str(fw_file.relative_to(strip_prefix)),
                "basename": fw_file.name,
                "brand": brand_dir.name,
            }
            with open(out_file, 'w') as fp:
                yaml.dump(data, fp)

if __name__ == '__main__':
    main()
