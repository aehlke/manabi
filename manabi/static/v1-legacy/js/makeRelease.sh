#!/bin/sh

# Copy our current location to $HERE
#HERE=`dirname $(readlink -f $0)`
HERE='/Users/jehlke/workspace/manabi/site_media/static/js'

echo $HERE
# Move to the dojo buildscripts directory. You have to be here in order to run your build
cd $HERE/dojo-src/util/buildscripts

# Run the build (linux - use build.bat for Windows). Both just call build.js via Rhino (Java based Javascript environment)
# 
# The following options are used (details true as of v1.4.1):
# action=release: 
# optimize=shrinksafe: Minimize the Javascript code with shrinksafe
# layerOptimize=shrinksafe: Optimize the layers as well as the modules (I'm not sure why you'd ever *not* want to do this?)
# copyTests=false: Don't copy tests. This is your deployed application, you probably don't want them there
# stripConsole=all: Remove any console.log() lines. You can chose just to remove groups using e.g. stripConsole=warn
# releaseDir=$HERE: set the directory which contains this script as the directory to put the release of Dojo in. Feel free to change this
# profileFile: The location of your profile file
# version: A version number for this version of your built Dojo
# cssOptimize=comments: Remove all comments and whitespace from CSS files. Follow any @import links and add them inline to the CSS file too
# releaseName=dojo-ourRelease: The name of the directory created by the build system containing your build
./build.sh  action=release optimize=shrinksafe layerOptimize=shrinksafe copyTests=false stripConsole=all releaseDir=$HERE/  profileFile=$HERE/manabi.profile.js cssOptimize=comments releaseName=dojo-ourRelease

#version=manabi-0.0.0 

