from pathlib import Path
import random

import tkinter as tk
import numpy as np

from experiment import Experiment
from misc import Parameters, Participant, get_gui_inputs

IS_TESTING_REGIME_ON = True 

if IS_TESTING_REGIME_ON:
    sbj = Participant(
    sbj_id="test", age=0, gender="X", handedness="X"
) 
else:
    sbj_info = get_gui_inputs(["UEID", "Age", "Gender", "Handedness"], "Demographics")
    sbj = Participant(
        sbj_id=sbj_info["UEID"],
        age=sbj_info["Age"],
        gender=sbj_info["Gender"],
        handedness=sbj_info["Handedness"],
    )
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
    interval_probe_prarms_file=Path("parameters_interval_probe.json"),
    stimuli_codes_file=Path("stimuli_codes.json"),
)
exp = Experiment(participant=sbj, params=parameters)
exp.display_text(
    "Welcome!", text_mode="default", termination_buttons=["space", "enter"]
)
exp.display_text(
    "Calibration Instructions",
    text_mode="default",
    termination_buttons=["space", "enter"],
)

# CALIBRATION BLOCK 
if IS_TESTING_REGIME_ON:
    try:
        exp.load_calibration() 
    except FileNotFoundError:
        exp.run_color_contrast_calibration(calibration_type="background", n_calibration_contrasts=15, save_results = True)
        exp.run_color_contrast_calibration(calibration_type="DCF_colors", n_calibration_contrasts=15, save_results = True)
    except Exception as e:
        print(f"Error occured:\n{e}")
else:
    exp.run_color_contrast_calibration(calibration_type="background", n_calibration_contrasts=15, save_results = True)
    exp.run_color_contrast_calibration(calibration_type="DCF_colors", n_calibration_contrasts=15, save_results = True)


exp.display_text(
    "Fusion Instruction", text_mode="default", termination_buttons=["space", "enter"]
)
exp.run_stereo_adaptation_block(block_code="block_E_1", n_trials_max=100)
exp.display_text("Ready?", text_mode="fusion", termination_buttons=["space", "enter"])

exp.display_text("High Contrast", text_mode="fusion", termination_buttons=["space", "enter"])
exp.display_text("Ready?", text_mode="fusion", termination_buttons=["space", "enter"])
exp.run_experimental_block(
    block_code="adaptation_high",
    n_trials=9,
    alphas =([0.2] * 3) + ([0.22] * 3) + ([0.24] * 3),
    color_modes=[random.choice(["red", "green"]) for _i in range(9)],
    detection_collection = False,
    discrimination_collection = False,
    forced_termination_buttons=["left", "right"],
    is_iti_included=False,
    is_constant_stim=True
)

exp.display_text("Low Contrast", text_mode="fusion", termination_buttons=["space", "enter"])
exp.display_text("Ready?", text_mode="fusion", termination_buttons=["space", "enter"])
exp.run_experimental_block(
    block_code="adaptation_low",
    n_trials=9,
    alphas =([0.35] * 3) + ([0.37] * 3) + ([0.39] * 3),
    color_modes=[random.choice(["red", "green"]) for _i in range(9)],
    detection_collection = False,
    discrimination_collection = False,
    forced_termination_buttons=["left", "right"],
    is_iti_included=False,
    is_constant_stim=True
)

# alphas_for_demo = np.linspace(0.26, 0.4, 10)
# random.shuffle(alphas_for_demo)
# exp.display_text("Demo Trials Instrucitions", text_mode="fusion", termination_buttons=["space", "enter"])
# exp.display_text("Ready?", text_mode="fusion", termination_buttons=["space", "enter"])
# exp.run_experimental_block(
#     block_code="adaptation_final_samecolor",
#     n_trials=10,
#     alphas = alphas_for_demo,
#     color_modes=[random.choice(["red", "green"]) for _i in range(10)],
#     detection_collection = True,
#     discrimination_collection = True,
#     forced_termination_buttons=["left", "right"],
#     is_iti_included=False,
#     is_constant_stim=False
# )
# exp.display_text("Fusion Demo Instrucitions", text_mode="fusion", termination_buttons=["space", "enter"])
# exp.display_text("Ready?", text_mode="fusion", termination_buttons=["space", "enter"])
# exp.run_experimental_block(
#     block_code="adaptation_final_fused",
#     n_trials=10,
#     alphas = alphas_for_demo,
#     color_modes=["fusion" for _i in range(10)],
#     detection_collection = True,
#     discrimination_collection = True,
#     forced_termination_buttons=["left", "right"],
#     is_iti_included=False,
#     is_constant_stim=False
# )

# # SLIDER & STAIRCASE
exp.display_text("Asjustment\nInstructions", text_mode="fusion", termination_buttons=["space", "enter"])
exp.display_text("Ready?", text_mode="fusion", termination_buttons=["space", "enter"])
suggested_alpha = exp.run_adjustment_block(block_code="adjustment", adjustment_buttons=["down", "up"])
print("Suggested alpha", suggested_alpha)
exp.display_text("Staircase\nInstructions", text_mode="fusion", termination_buttons=["space", "enter"])
exp.display_text("Ready?", text_mode="fusion", termination_buttons=["space", "enter"])
threshold_alpha = exp.run_adapted_staircase(
    block_code="staircase",
    n_reversals=5,
    suggested_alpha=suggested_alpha,
    alpha_increment=1 / 255,
    exploration_range = 5/255
)
print("Found alpha threshold is", threshold_alpha)

alpha_to_use = threshold_alpha + 0.05*threshold_alpha

# MAIN BLOCK WITH SAME COLOR
N = 3
exp.display_text("Resting", text_mode="fusion", termination_buttons=["space", "enter"])
exp.display_text("Ready?", text_mode="fusion", termination_buttons=["space", "enter"])
exp.run_stereo_adaptation_block(block_code=f"block_E_pre_simple_block_same_color", n_trials_max=50)
exp.display_text("Ready?", text_mode="fusion", termination_buttons=["space", "enter"])
exp.run_experimental_block(
    block_code=f"simple_block_same_color",
    n_trials=N,
    alphas = [alpha_to_use for _i in range(N)],
    color_modes=[random.choice(["green", "red"]) for _i in range(N)],
    detection_collection = True,
    discrimination_collection = True,
    forced_termination_buttons=None,
    is_iti_included=False,
    is_constant_stim=False,
    hidden_trial_ratio=0.5
)

## MAIN EXP BLOCK ("SIMPLE BLOCK")
N_SIMPLE_TRIALS = 3
if N_SIMPLE_TRIALS%3!=0:
    raise(ValueError, "Number of trials should divide on the number of the blocks!")
for iblock in range(3):
    exp.display_text("Resting", text_mode="fusion", termination_buttons=["space", "enter"])
    exp.display_text("Ready?", text_mode="fusion", termination_buttons=["space", "enter"])
    exp.run_stereo_adaptation_block(block_code=f"block_E_pre_simple_block_{iblock}", n_trials_max=50)
    exp.display_text("Ready?", text_mode="fusion", termination_buttons=["space", "enter"])
    exp.run_experimental_block(
        block_code=f"simple_block_{iblock}",
        n_trials=N_SIMPLE_TRIALS//3,
        alphas = [alpha_to_use for _i in range(N_SIMPLE_TRIALS//3)],
        color_modes=["fusion" for _i in range(N_SIMPLE_TRIALS//3)],
        detection_collection = True,
        discrimination_collection = True,
        forced_termination_buttons=None,
        is_iti_included=False,
        is_constant_stim=False,
        hidden_trial_ratio=0.5
    )


N_2IFC_TRIALS = 3
if N_2IFC_TRIALS%3!=0:
    raise(ValueError, "Number of trials should divide on the number of the blocks!")
exp.display_text("Resting", text_mode="fusion", termination_buttons=["space", "enter"])
for iblock in range(3):
    exp.display_text("Resting", text_mode="fusion", termination_buttons=["space", "enter"])
    exp.display_text("Ready?", text_mode="fusion", termination_buttons=["space", "enter"])
    exp.run_stereo_adaptation_block(block_code=f"block_E_pre_2IFC_block_{iblock}", n_trials_max=50)
    exp.display_text("Ready?", text_mode="fusion", termination_buttons=["space", "enter"])
    exp.run_2I2AFC_block(
        block_code = f"2IFC_block_{iblock}",
        n_trials = N_2IFC_TRIALS//3, 
        alphas = [alpha_to_use for _i in range(N_2IFC_TRIALS//3)],
        color_modes=["fusion" for _i in range(N_2IFC_TRIALS//3)],
        detection_collection = True,
        discrimination_collection = False,
        forced_termination_buttons=None,
        is_iti_included=False,
        is_constant_stim=False,
    )

exp.display_text("Fin", text_mode="fusion", termination_buttons=["space", "enter"])




