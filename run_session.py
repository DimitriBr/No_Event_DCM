from pathlib import Path

from experiment import  Experiment
from misc import Parameters, Participant

sbj = Participant(sbj_id="testych", age=100, gender="m", handedness="r")

parameters = Parameters(
    screen_params_file=Path("parameters_screen.json"),
    visual_params_file=Path("parameters_visual.json"),
    exp_trial_params_file=Path("parameters_exp_trial.json"),
    calibration_params_file=Path("parameters_calibration.json"),
    contrast_practise_params_file=Path("parameters_contrast_practise.json"),
    detection_report_params_file=Path("parameters_detection_report.json"),
    discrimination_report_params_file=Path("parameters_discrimination_report.json"),
    reds_values_file=Path("red_values.xlsx"),
    green_values_file=Path("green_values.xlsx"),
)

exp = Experiment(participant=sbj, params=parameters)
# exp.run_color_contrast_calibration(save_results = True)
# exp.run_contrast_adaptation_block()
exp.run_experimental_block(
    block_code="block_1",
    n_trials=3,
    contrast_levels=[7] * 3,
    color_modes=["fusion"] * 3,
)


#
#
# add full trial, but same color

# add staircase
# instead of termination by "left", "right" --> trial lasts until max duration is over, and then TWO responses

# when we split the screen, we ALWAYS have square frames and fixation cross

# duration of the trial: 5-6 seconds
# for appearence of the stimuli, uniform within the trial expept the first and the last
# 15% (or 50%?) of the trials - there really is nothing (or what is the minimum percent of blanks so that we can compute d-prime)
