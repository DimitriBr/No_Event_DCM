import json
import math
import random
from pathlib import Path 

from psychopy import visual, core, colors, event
import pandas as pd
from matplotlib import pyplot as plt

from trial import Trial
from misc import Calibrator

# from contrast_practise import Contrast_Practise_Trial
from trials import Contrast_Practise_Trial

# Loading screen parameters and calculating pixels to degree
with open("parameters_screen.json", "rb") as file:
    params = json.load(file)
cm_per_degree = params["distance_to_screen_cm"] * math.tan(math.radians(1))
y_px_per_cm = params["resolution_y_px"] / params["screen_height_cm"]
x_px_per_cm = params["resolution_x_px"] / params["screen_width_cm"]
px_per_cm = (y_px_per_cm + x_px_per_cm) / 2
px_per_deg = px_per_cm * cm_per_degree

# Loading visual settings
with open("parameters_visual.json", "rb") as file:
    params = json.load(file)
isd_degrees = params[
    "inter_square_distance_degrees"
]  # inter square distance in visual degrees
ss_degrees = params["square_size_degrees"]  # square size in visual degrees
# TODO as calibration small square size
backgroup_blue_rgb1 = params[
    "background_blue_rgb1"
]  # every value normalized from 0 to 1

# Loading colors
red_colors = pd.read_excel("red_values.xlsx", header=None)
green_colors = pd.read_excel("green_values.xlsx", header=None)

backgroup_blue = colors.Color(backgroup_blue_rgb1, space="rgb1")
win = visual.Window(fullscr=True, color=backgroup_blue)

# betas = []
# for icolor in range(15):
#     calibrator = Calibrator(
#             window = win,
#             beta_0 = 0.9,
#             calibration_type = "checkerboard",
#             red_color_rgb1 = colors.Color(list(red_colors.loc[icolor,:]), space = "rgb1"),
#             green_color_rgb1 = colors.Color(list(green_colors.loc[icolor,:]), space = "rgb1"),
#             field_size = 3*int(ss_degrees*px_per_deg),
#             background_color = backgroup_blue)
#     calibrator.run_calibration_trial()
#     beta = calibrator.get_current_beta()
#     betas.append(beta)

# #TODO plot and GUI asking if it is good
# plt.plot(betas)
# plt.show()
# core.wait(4)
# TODO change green colors to match

SBJ_ID = "testique"
SBJ_FOLDER = Path("data", SBJ_ID)
SBJ_FOLDER.mkdir(exist_ok=True)

color_codes = ["red", "green"]
trial_indexer = 0
for contrast_level in [14, 12, 10, 8, 6, 4, 2]:
    for _ in range(1):
        con_prac_trial = Contrast_Practise_Trial(
            index=str(f"Practice_{trial_indexer}"),
            window=win,
            data_folder=SBJ_FOLDER,
            max_duration=500,
            termination_buttons=["left", "right"],
            gabor_orientation=random.choice(["left", "right"]),
            contrast_level=contrast_level,
            main_color=random.choice(color_codes),
            red_colors=red_colors,
            green_colors=green_colors,
            grating_resolution=128,
            square_size=int(ss_degrees * px_per_deg),
            inter_square_distance=int(isd_degrees * px_per_deg),
        )
        con_prac_trial.generate_visuals()
        con_prac_trial.run()
        con_prac_trial.save_data()
        trial_indexer += 1


# trial = Trial(window = win, square_size = int(ss_degrees*px_per_deg), inter_square_distance= int(isd_degrees*px_per_deg))
# trial.create_trial_visuals(color_left=(-1, 1, -1), color_right = (1, -1, -1))
# core.wait(5)
