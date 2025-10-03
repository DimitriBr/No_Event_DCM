from pathlib import Path
import random

import tkinter as tk

from experiment import Experiment
from misc import Parameters, Participant, get_gui_inputs

# sbj_info = get_gui_inputs(["UEID", "Age", "Gender", "Handedness", "Vision"], "Demographics")
# sbj = Participant(
#     sbj_id=sbj_info["UEID"],
#     age=sbj_info["Age"],
#     gender=sbj_info["Gender"],
#     handedness=sbj_info["Handedness"],
#     vision=sbj_info["Vision"],
# )
sbj = Participant(sbj_id="testiq", age=111, gender="f", handedness="a", vision=1) ###temporal line
sbj.create_participant_repo()
sbj.save_demographical_info()

parameters = Parameters(
    screen_params_file=Path("parameters_screen.json"),
    visual_params_file=Path("parameters_visual.json"),
    exp_trial_params_file=Path("parameters_exp_trial.json"),
    calibration_params_file=Path("parameters_calibration.json"),
    contrast_practise_params_file=Path("parameters_contrast_practise.json"),
    detection_report_params_file=Path("parameters_detection_report.json"),
    discrimination_report_params_file=Path("parameters_discrimination_report.json"),
    stimuli_codes_file=Path("stimuli_codes.json"),
    reds_values_file=Path("red_values.xlsx"),
    green_values_file=Path("green_values.xlsx"),
)

exp = Experiment(participant=sbj, params=parameters)
# exp.display_text(
#     "Welcome!", text_mode="default", termination_buttons=["space", "enter"]
# )
# exp.display_text(
#     "Calibration Instructions",
#     text_mode="default",
#     termination_buttons=["space", "enter"],
# )
# exp.run_color_contrast_calibration(save_results=True)
exp.display_text(
    "Fusion Instruction", text_mode="default", termination_buttons=["space", "enter"]
)
exp.run_stereo_adaptation_block(block_code="block_E", n_trials_max=50)
exp.display_text("High Contrast", text_mode="fusion", termination_buttons=["space", "enter"])
exp.run_experimental_block(
    block_code="adaptation_high",
    n_trials=9,
    contrast_levels=([14] * 3) + ([13] * 3) + ([12] * 3),
    color_modes=[random.choice(["red", "green"]) for _i in range(9)],
    detection_collection = False,
    discrimination_collection = False,
    forced_termination_buttons=["left", "right"],
    is_iti_included=False,
    is_constant_stim=True
)
exp.display_text("Low Contrast", text_mode="fusion", termination_buttons=["space", "enter"])
exp.run_experimental_block(
    block_code="adaptation_low",
    n_trials=9,
    contrast_levels=([14] * 3) + ([13] * 3) + ([12] * 3),
    color_modes=[random.choice(["red", "green"]) for _i in range(9)],
    detection_collection = False,
    discrimination_collection = False,
    forced_termination_buttons=["left", "right"],
    is_iti_included=False,
    is_constant_stim=True
)
# exp.run_contrast_adaptation_block(block_code = "adaptation")

# exp.run_experimental_block(
#     block_code="practise",
#     n_trials=9,
#     contrast_levels=([14] * 3) + ([13] * 3) + ([12] * 3),
#     color_modes=[random.choice(["red", "green"]) for _i in range(9)],
#     detection_collection = False,
#     discrimination_collection = True
# )

# exp.run_experimental_block(
#     block_code="block_1",
#     n_trials=3,
#     contrast_levels=[7] * 3,
#     color_modes=["fusion"] * 3,
# )
# exp.run_stereo_adaptation_block(block_code="block_E", n_trials_max=50)


#
#
# add full trial, but same color

# add staircase
# instead of termination by "left", "right" --> trial lasts until max duration is over, and then TWO responses

# when we split the screen, we ALWAYS have square frames and fixation cross

# duration of the trial: 5-6 seconds
# for appearence of the stimuli, uniform within the trial expept the first and the last
# 15% (or 50%?) of the trials - there really is nothing (or what is the minimum percent of blanks so that we can compute d-prime)

# contrast-to-be-used -- one staircase step down from the point of convergence
# two-interval (5 seconds) two-alternative forced choice in the second block


# 0. Fill demographical info --U
# 1. Welcome text --U
# 2. Calibration Instucture text --U
# 3. Color Calibration --U
# 4. Fusion Instruction --U
# 5. Stereo-E block (untill 3 successes in a row) --M
# 6. Adaptation (same color, high contrast) with no report
# 7. Adaptation (same color, low contrast) with no report
# 8. Adaptation (same color, different constasts) with reports,
# 9. Instructions for Slider + Staircase
# 10. SLider with contrast "find the lowest where it's visible" --M
# 11. Double-Staircase with a small step size in the area of the lowest visibility report from slider
# 12. Rest (self-paced)
# 13. Stereo-E block
# 14. Simlex Experimental Block (gabor orientation judgement; 50% we have nothing) -- 45 stimuli + 45 empty (?)
# ### --> if waiting_time > 15 sec:
# ### ### Stereo_E block before the next trial
# 15. Rest (self-pasced)
# 16. Stereo-E block
# 17. Complex Experimental Block (2-interval 2-alternative forced choice trials; ?) - 45 + 45 (?)
# ### --> if waiting_time > 15 sec:
# ### ### Stereo_E block before the next trial
# 18. Thank-you Message
