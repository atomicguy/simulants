import os
import random
import datetime
import subprocess

from argparse import ArgumentParser

color_list = ['Accent', 'Accent_r', 'Blues', 'Blues_r', 'BrBG', 'BrBG_r', 'BuGn', 'BuGn_r', 'BuPu', 'BuPu_r', 'CMRmap',
             'CMRmap_r', 'Dark2', 'Dark2_r', 'GnBu', 'GnBu_r', 'Greens', 'Greens_r', 'Greys', 'Greys_r', 'OrRd', 'OrRd_r',
             'Oranges', 'Oranges_r', 'PRGn', 'PRGn_r', 'Paired', 'Paired_r', 'Pastel1', 'Pastel1_r', 'Pastel2', 'Pastel2_r',
             'PiYG', 'PiYG_r', 'PuBu', 'PuBuGn', 'PuBuGn_r', 'PuBu_r', 'PuOr', 'PuOr_r', 'PuRd', 'PuRd_r', 'Purples',
             'Purples_r', 'RdBu', 'RdBu_r', 'RdGy', 'RdGy_r', 'RdPu', 'RdPu_r', 'RdYlBu', 'RdYlBu_r', 'RdYlGn', 'RdYlGn_r',
             'Reds', 'Reds_r', 'Set1', 'Set1_r', 'Set2', 'Set2_r', 'Set3', 'Set3_r', 'Spectral', 'Spectral_r', 'Wistia',
             'Wistia_r', 'YlGn', 'YlGnBu', 'YlGnBu_r', 'YlGn_r', 'YlOrBr', 'YlOrBr_r', 'YlOrRd', 'YlOrRd_r', 'afmhot',
             'afmhot_r', 'autumn', 'autumn_r', 'bone', 'bone_r', 'brg', 'brg_r', 'bwr', 'bwr_r',
             'cool', 'cool_r', 'coolwarm', 'coolwarm_r', 'copper', 'copper_r', 'cubehelix', 'cubehelix_r', 'flag', 'flag_r',
             'gist_earth', 'gist_earth_r', 'gist_gray', 'gist_gray_r', 'gist_heat', 'gist_heat_r', 'gist_ncar', 'gist_ncar_r',
             'gist_rainbow', 'gist_rainbow_r', 'gist_stern', 'gist_stern_r', 'gist_yarg', 'gist_yarg_r', 'gnuplot', 'gnuplot2',
             'gnuplot2_r', 'gnuplot_r', 'gray', 'gray_r', 'hot', 'hot_r', 'hsv', 'hsv_r', 'inferno', 'inferno_r', 'jet', 'jet_r',
             'magma', 'magma_r', 'nipy_spectral', 'nipy_spectral_r', 'ocean', 'ocean_r', 'pink', 'pink_r', 'plasma', 'plasma_r',
             'prism', 'prism_r', 'rainbow', 'rainbow_r', 'seismic', 'seismic_r', 'spectral', 'spectral_r', 'spring', 'spring_r',
             'summer', 'summer_r', 'terrain', 'terrain_r', 'viridis', 'viridis_r', 'winter', 'winter_r']

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--number', '-n', type=int, help='how many fractals to generate', required=True)
    parser.add_argument('--out', '-o', type=str, help='output path', required=True)
    args, _ = parser.parse_known_args()

    for _ in range(args.number):
        real = random.uniform(-1, 1)
        imag = random.uniform(0, 1)
        depth = random.randint(512, 1024)
        zoom = random.uniform(0.1, 0.75)
        x = random.uniform(-0.5, 0.5)
        y = random.uniform(-0.5, 0.5)
        colormap = random.choice(color_list)

        image_id = '{}_{}_z{:.2f}_{}'.format(datetime.datetime.now().strftime('%Y%m%d%H%M'), str(depth), zoom, colormap)
        image_path = os.path.join(args.out, image_id + '.png')

        cmd = ['python', '-m', 'fractal', 'julia', str(real), '+' + str(imag), 'j', '--size=1024x1024', '--depth=' + str(depth),
               '--zoom=' + str(zoom), '--center=' + str(x) + 'x' + str(y), '--output=' + image_path, '--cmap=' + colormap]

        print(cmd)
        subprocess.check_call(cmd)