#!/usr/local/bin/bash

EVENT_PATH="$1"

PREFIX="/usr/local/www/zoneminder-h264/events"

# libx264, libx265
CODEC=libx264

# remove any stale movie
find "$EVENT_PATH" -name '*.mp4' -empty -delete

# generate the new movie from the event frames
/usr/local/bin/ffmpeg -n -f image2 -framerate 7 -pattern_type glob -i "$EVENT_PATH"/'*-capture.jpg' -c:v "$CODEC" "$EVENT_PATH"/event.mp4

# call push-flickr to upload the movie
"$PREFIX"/venv/bin/python "$PREFIX"/push-flickr.py -c "$PREFIX"/push-flickr.ini -p "$PREFIX" "$EVENT_PATH"

# remove the movie
rm -f "$EVENT_PATH"/event.mp4
