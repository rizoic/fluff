#!/usr/bin/env python
# Copyright (c) 2012-2013 Simon van Heeringen <s.vanheeringen@ncmls.ru.nl>
#
# This script is free software. You can redistribute it and/or modify it under 
# the terms of the MIT License

### Standard imports ###
from optparse import OptionParser,OptionGroup
import sys
import os

### External imports ###
from pylab import plot, show, ylim, yticks,savefig
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter,NullLocator
from matplotlib.font_manager import fontManager, FontProperties
from numpy import array,mean,amax,max,std,median,arange
from scipy.interpolate import splprep, splev
from scipy.stats import scoreatpercentile
import pybedtools

### My imports ###
from fluff.fluffio import *
from fluff.plot import *
from fluff.util import *
from fluff.color import DEFAULT_COLORS

######## EDIT CONSTANTS TO CHANGE BEHAVIOUR OF THE SCRIPT #############
# Sizes of the plots (in inches)
PLOTWIDTH = 0.6
PLOTHEIGHT = 0.6
PAD = 0.05
PADLEFT = 1.5						# For labels
PADTOP = 0.4 						# For labels
PADBOTTOM = 0.05
PADRIGHT = 0.05
FONTSIZE = 8
BINS = 21								# Number of bins for profile
RPKM = False						# If False, use absolute count
RMDUP = True				# Remove duplicate reads, if present
RMREPEATS = True				# Remove reads mapping to repeats, if mapped with bwa
#########################################################################
font = FontProperties(size=FONTSIZE / 1.25, family=["Nimbus Sans L", "Helvetica", "sans-serif"])

VERSION = "1.0"

usage = "Usage: %prog -c <bedfile> -d <file1>[,<file2>,...] -o <out> [options]"
version = "%prog " + str(VERSION)
parser = OptionParser(version=version, usage=usage)
group1 = OptionGroup(parser, 'Optional')
parser.add_option("-c", dest="clust_file", help="BED file with cluster in 4th column", metavar="FILE")
parser.add_option("-d", dest="datafiles", help="Data files (reads in BAM or BED format)", metavar="FILE(S)")
parser.add_option("-o", dest="outfile", help="Output file (type determined by extension)", metavar="FILE")
group1.add_option("-l", dest="colors", help="Colors", metavar="NAME(S)", default=DEFAULT_COLORS)
group1.add_option("-s", dest="scalegroups", help="Scale groups", metavar="GROUPS")

parser.add_option_group(group1)
(options, args) = parser.parse_args()

for opt in [options.clust_file, options.datafiles, options.outfile]:
	if not opt:
		parser.print_help()
		sys.exit()

clust_file = options.clust_file
datafiles = [x.strip() for x in options.datafiles.split(",")]
tracks = [os.path.basename(x) for x in datafiles]
colors = [x.strip() for x in options.colors.split(",")]
scalegroups = process_groups(options.scalegroups)

# Calculate the profile data
data = load_cluster_data(clust_file, datafiles, BINS, RPKM, RMDUP, RMREPEATS)
# Get cluster information
cluster_data = load_bed_clusters(clust_file)
clusters = [int(x) for x in cluster_data.keys()]

#Init x-axis
t = arange(BINS)

# Get a figure with a lot of subplots
fig, axes = create_grid_figure(len(tracks), len(clusters), plotwidth=PLOTWIDTH, plotheight=PLOTHEIGHT, padleft=PADLEFT, padtop=PADTOP, pad=PAD, padright=PADRIGHT, padbottom=PADBOTTOM) 

track_max = []
for track_num, track in enumerate(tracks):
	percentiles = [scoreatpercentile([data[track][x] for x in cluster_data[cluster]], 90) for cluster in clusters]
	track_max.append(max(percentiles))
	
for track_num, track in enumerate(tracks):
	for i,cluster in enumerate(clusters):
		# Retrieve axes
		ax = axes[track_num][i]
		
		# Get the data
		vals = array([data[track][x] for x in cluster_data[cluster]])
		
		# Make the plot
		coverage_plot(ax, t, vals, colors[track_num % len(colors)])
		
		# Get scale max
		maxscale = track_max[track_num]
		if scalegroups and len(scalegroups) > 0:
			for group in scalegroups:
				if (track_num + 1) in group:
					maxscale = max([track_max[j - 1] for j in group])
					break

		# Set scale	
		ax.set_ylim(0, maxscale)
		ax.set_xlim(0, BINS - 1)	
		
		# Cluster titles
		if track_num == 0:
			ax.set_title("%s\nn=%s" % (cluster, len(cluster_data[cluster])), font_properties=font)
		
		# Track title and scale
		if i == 0:
			
			pos = axes[track_num][0].get_position().get_points()
			text_y = (pos[1][1] + pos[0][1]) / 2
			text_x = pos[0][0] - (PAD / fig.get_figwidth())
			plt.figtext(text_x, text_y, track, clip_on=False, horizontalalignment="right", verticalalignment="center", font_properties=font)
			plt.figtext(text_x,  pos[1][1], maxscale, clip_on=False, horizontalalignment="right", verticalalignment="top", font_properties=font)
			plt.figtext(text_x,  pos[0][1], 0, clip_on=False, horizontalalignment="right", verticalalignment="bottom", font_properties=font)

print "Saving figure"
savefig(options.outfile)
