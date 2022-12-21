# serenity (v0.1)

A music player, manager, streamer and downloader written in pure Python with a [mpv](https://mpv.io/) audio backend.

## setup

### installing python dependencies

In the root directory of this project, simply run ``` pip -r requirements.txt ``` to install the required python packages.

### installing other dependencies

#### ---the easy way (windows only)

A quick-install for dependencies on Windows PCs is to just extract this 7z file in the root directory:
https://www.dropbox.com/s/x4aoruzu8q922gm/subprograms.7z?dl=0

#### ---alternatively...
You will likely have to download a few files. 
(Note: if any of the following files happen to be on your PATH variable already, the following steps may be avoidable.)

Again, in the root directory, create a folder called *subprograms*.

Inside it, place an [ffmpeg](https://ffmpeg.org/) installation or executable. 
If on Windows, create a folder called *libmpv* and extract the contents of one of [these](https://sourceforge.net/projects/mpv-player-windows/files/libmpv/) (x86_64) archive files inside it.
Otherwise, place a [libmpv.so](https://pkgs.org/download/libmpv.so) file in the *subprograms* folder.

For MacOS/Linux, install [mpv](https://mpv.io/installation) as a last resort.

Such steps should allow Serenity to work cross-platform. 

## running serenity
In the root of this directory simply run: ```python main.py```.

Happy days.

Here is a video guide on current features (v0.1): https://www.youtube.com/watch?v=O3ltb8ARMsI

Enjoy!
