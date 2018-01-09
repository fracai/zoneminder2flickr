#!/usr/bin/env python

import flickrapi
import os

api_key = u'your_flickr_api_key'
api_secret = u'your_flickr_api_secret'
access_level = u'write'

flickr = flickrapi.FlickrAPI(api_key, api_secret, token_cache_location="./flickr-token-cache")

# Only do this if we don't have a valid token already
if not flickr.token_valid(perms=access_level):

    # Get a request token
    flickr.get_request_token(oauth_callback='oob')

    # Open a browser at the authentication URL. Do this however
    # you want, as long as the user visits that URL.
    authorize_url = flickr.auth_url(perms=access_level)
    print authorize_url

    # Get the verifier code from the user. Do this however you
    # want, as long as the user gives the application the code.
    input_txt = raw_input('Verifier code: ')
    print 'i ', input_txt
    verifier = unicode(input_txt)
    print 'v ', verifier

    # Trade the request token for an access token
    flickr.get_access_token(verifier)

