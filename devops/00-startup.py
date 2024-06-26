# 00-startup.py

print('Loading default imports...')

from code.io.EventProcessor import EventProcessor
from code.io.TrackingProcessor import TrackingProcessor
from code.io.PossessionProcessor import PossessionProcessor
from code.io.ActionProcessor import ActionProcessor

from code.util.StatsUtil import StatsUtil
from code.util.ShotRegionUtil import ShotRegionUtil
from code.util.VisUtil import VisUtil
from code.util.FeatureUtil import FeatureUtil

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


# Verify ffmpeg path and set it for matplotlib
ffmpeg_path = '/usr/bin/ffmpeg'
plt.rcParams['animation.ffmpeg_path'] = ffmpeg_path
plt.rcParams['animation.writer'] = 'ffmpeg'

# Print a message to confirm the script has run
print("Default imports loaded.")