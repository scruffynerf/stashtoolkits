## YTDLP defaults - DO NOT EDIT (could be overridden by later versions)
## Edit the config.py which copies this file on your first run (and stops)
#
# your editable config, uncomment anything you to set values on
#
# make sure your download directory is INSIDE your library
download_dir = "/put your/download/directory/here/"

# put your desired download urls into this file
urls_file = "urls.txt"

#type of file it is:  text list or json?
urls_type = "text"

#if json, what fieldname holds the url?
url_json_urlname = "videoUrl"

# a history of downloads is here, to avoid redownloading, even if you move or rename the original download
grabbed_urls_txt = "grabbed_urls.txt"

# a history of errors in downloads is here
error_urls_txt = "error_urls.txt"

# batch size, number of urls to fetch on one button push
batchsize = 5

# A list of options for use with the youtube_dl module
# You can find available options here:
# https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L194
ytdl_options = {}