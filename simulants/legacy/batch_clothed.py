import subprocess

from argparse import ArgumentParser

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--number', '-n', type=int, help='number of renders to generate', required=True)
    parser.add_argument('--out_dir', '-o', type=str, help='output directory for blends', required=True)
    args, _ = parser.parse_known_args()

    i = 1
    for _ in range(args.number):
        print('{} of {}'.format(i, args.number))
        subprocess.check_call(['blender', '-b', '-P', 'make_clothed.py',
                               '--',
                               '--base_file', 'data/base_scene.blend',
                               '--clothing', 'data/clothes',
                               '--hair', 'data/hairs',
                               '--out_dir', args.out_dir])
        i += 1