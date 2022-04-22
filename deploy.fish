#!/usr/bin/env fish

set -l options (fish_opt --short d --long directory --required-val)
set -a options (fish_opt --short h --long help)

argparse --max-args 0 $options -- $argv
or exit

if set -q _flag_help
    echo "deploy.fish [-d|--directory /run/media/$USER/CIRCUITPY] [-h|--help]"
    exit 0
end

set -l directory /run/media/$USER/CIRCUITPY
if set -q _flag_directory
    set directory $_flag_directory
end

set -l script_directory (dirname (status --current-filename))
set -l requirements (cat $script_directory/requirements.txt)
set -l tmp_dir (mktemp tmp.XXXXXXXXXX -ut)

mkdir -p $directory/lib
or exit

# Install the font bitmap, font5x8.bin, from the framebuf library.
string match -qr 'framebuf>=(?<framebuf_version>[0-9].[0-9].[0-9])' $requirements
wget -qO - https://api.github.com/repos/adafruit/Adafruit_CircuitPython_framebuf/releases/tags/$framebuf_version \
    | string match --quiet --regex '"browser_download_url": "(?<download_url>.*-examples-[0-9]+\.[0-9]+\.[0-9]\.zip)"'
wget -qLP $tmp_dir $download_url
or exit
unzip -q -o -j -d $directory $tmp_dir/*framebuf-examples*.zip '*font5x8.bin'
or exit

rm -rf $tmp_dir

cp $script_directory/code.py $directory
or exit
