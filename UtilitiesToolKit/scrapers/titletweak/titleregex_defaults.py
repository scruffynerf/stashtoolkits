## Title Regex defaults - DO NOT EDIT THIS FILE
## edit the config.py copy created on the first run

# edit as desired, you can use all the regex-y things like
#    r'replaced': 'REPLACED',    # simple replacement
#    r'(.*?)is(.*?)ing(.*?)ch': r'\3-\2-\1',   #backreferences and captures
#    r'\d\d((\d)(\d)-(\d)(\d))\d\d': r'__\5\4__\3\2__'

regex_dict = {
   r'\.(mp4|mkv|avi|mpg|mpeg)$': '',
   r'(1080|720|480|2160)p': '',
   r'_[0-9]$': '',
   r'[\+_ ]+': ' ',
}
