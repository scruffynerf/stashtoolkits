# YTDLP downloader for use inside Stash

This allows you to use ytdlp to grab videos from many urls and directly import them into Stash

## Description

After putting your urls into a list, you can click on a single button, it'll download the videos, scan them into Stash, and then add metadata based on the downloaded info.

## Getting Started

### Dependencies

* Python 3.11
* [stashapp-tools](https://github.com/stg-annon/stashapp-tools)
* which installs [stashapi](https://github.com/stg-annon/stashapi)
* [ytdlp](https://github.com/yt-dlp/yt-dlp)

### Installing

* Install as a plugin in the plugin folder
* run `pip install -r requirements.txt` if needed.
* Reload plugins, and click the download button once to setup the config file so you can edit a fresh copy of it.
* Edit the config.py file

### Executing program

* Add urls to the url.txt file (or modify the path/name of the file if you wish)
* Click on the Download button.
* ????
* Profit! (ok, really, just watch some videos...)

## Help

* TBD, let me know if there are issues.

## Authors

Contributors names and contact info

* ScruffyNerf  
* based on code from Niemands

## Version History

* 3.0
    * Initial Release
* previous versions were different entirely, so I'm starting at 3.0

## License

This project is licensed under the Rules of Acquisition License - it is worth exactly what you paid for it, and if you paid anything, you got gyped.
Code is considered to be under whatever licenses various parts are, and no stronger.

## Acknowledgments

Inspiration, code snippets, etc.
* [Stash](https://github.com/stashapp/stash)
* Niemand for [previous versions](https://github.com/niemands/StashPlugins)
* with additional inspiration from Skier
* and thanks Stg-annon's StashAPI making it so much easier to do all of this.
