#!/usr/bin/env fish

set -l options (fish_opt --short d --long directory --required-val)
set -a options (fish_opt --short h --long help)
set -a options (fish_opt --short m --long major-version --required-val)

argparse --max-args 0 $options -- $argv
or exit

if set -q _flag_help
    echo "deploy.fish [-d|--directory /run/media/$USER/CIRCUITPY] [-h|--help] [-m|--major-version 7]"
    exit 0
end

set -l directory /run/media/$USER/CIRCUITPY
if set -q _flag_directory
    set directory $_flag_directory
end

set -l major_version 7
if set -q _flag_major-version
    set major_version $_flag_major-version
end

set -l script_directory (dirname (status --current-filename))
set -l ciruitpython_requirements (cat $script_directory/requirements-circuitpython.txt)
set -l tmp_dir (mktemp tmp.XXXXXXXXXX -ut)

mkdir -p $directory/lib
or exit

for requirement in $ciruitpython_requirements
    set -l pair (string split ' ' $requirement)
    set -l library $pair[1]
    set -l library_version $pair[2]
    wget -qO - https://api.github.com/repos/adafruit/Adafruit_CircuitPython_$library/releases/tags/$library_version \
        | string match --quiet --regex (string join "" '"browser_download_url": "(?<download_url>.*-' $major_version '\.x-mpy-[0-9]+\.[0-9]+\.[0-9]\.zip)"')
    wget -qLP $tmp_dir $download_url
    or exit
end

for zip_archive in $tmp_dir/*.zip
    unzip -q -d $tmp_dir $zip_archive '*.mpy'
    or exit
end

# Copy over all the subdirectories and files under the `lib` directory.
for lib_dir in (ls $tmp_dir/**.mpy | string match -r '.*/lib/' | sort -u)
    # for subdirectory in (find -mindepth 1 -type d $lib_dir)
    #     mv $subdirectory
    # end
    mv $lib_dir/* $directory/lib
    or exit
end

# Install the font bitmap, font5x8.bin, from the framebuf library.
string match -qr 'framebuf (?<framebuf_version>[0-9].[0-9].[0-9])' $ciruitpython_requirements
wget -qO - https://api.github.com/repos/adafruit/Adafruit_CircuitPython_framebuf/releases/tags/$framebuf_version \
    | string match --quiet --regex '"browser_download_url": "(?<download_url>.*-examples-[0-9]+\.[0-9]+\.[0-9]\.zip)"'
wget -qLP $tmp_dir $download_url
or exit
unzip -q -o -j -d $directory $tmp_dir/*framebuf-examples*.zip '*font5x8.bin'
or exit

rm -rf $tmp_dir

cp $script_directory/code.py $directory
or exit
