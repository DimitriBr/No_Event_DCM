# Project Name

No_Event_Dichoptic_Color_Masking (**work in progress**)

## Requirements

Windows 10 or Windows 11

## Installation

To run the stimuli code, you may re-create the environment `psych` from the `psych.yml` file included in this project.
In this case, psychopy (2023.2.3) with no dependecies should be manually added to the environment from pip due to compatibility issues.

For this, run the following commands in your **conda** terminal:

1) `conda env create -f psych.yml` 
2) `activate psych`
3) `pip install psychopy==2023.2.3 --no-deps`

Further important steps on how to launch the stimuli code:

1. Modify `parameters_screen.json` with the parameters of your screen
(so far, the code has been tested and works stably with 60Hz, so it is recommended to keep the resolution of your screen at 60Hz)
2. Modify `run_session.py` if you want to change the block components of the experiment
3. Run `python run_session.py` from `psych` conda environment

## Project Structure

1. `run_session.py` is used as a high-level runner for organizing experimental blocks into a particular experiment
2. `experiment.py` is the module with class `Experiment` that contains defined experimental blocks for DCM
3. `trials.py` is the module with classes that correspond to trial types needed for the DCM experiment
4. `misc.py` is the module with miscellaneous helper classes and functions for other modules
5. `image_processing.py` is the module containing the `prepare_image` function that transforms the image on a white or transparent background into the format required for DCF

## Current Experiment Structure

Current Structure of the experiment from the `run_session.py`

1. Demographical Info Filling 
2. Welcome text -- *SPACE to proceed*
3. Calibration Instruction text -- *SPACE* to proceed
4. Background Color Calibration (red and grey) -- *UP* to increase beta; *DOWN* to decrease beta; *SPACE* to confirm subjective isoluminance (flickering sensation stopped) 
5. Fusion Color Calibration (red and green) -- *UP* to increase beta; *DOWN* to decrease beta; *SPACE* to confirm subjective isoluminance (flickering sensation stopped) 
6. Fusion Instruction -- *SPACE to proceed*
7. Stereo-E block (until 3 successes in a row) -- *LEFT*, *RIGHT*, *UP*, or *DOWN* to indicate orientation of the character
8. Adaptation (same color, high contrast) with no report -- *LEFT* or *RIGHT* to indicate orientation of the stimulus
9. Adaptation (same color, low contrast) with no report  -- *LEFT* or *RIGHT* to indicate orientation of the stimulus
10. Demo Trial (same color, variable constasts) with reports -- reports buttons are listed on the screen
11. Demo Trials (different colors, variable contrasts) with reports -- reports buttons are listed on the screen
12. Adjustment Instructions -- *SPACE* to proceed
13. Adjustment Block (searching for alpha-prime: estimated alpha-threshold) -  -- *UP* to increase contrast; *DOWN* to decrease contrast *SPACE* to confirm the estimated threshold
14. Staircase Instructions -- *SPACE* to proceed
15. Double-Staircase with a small step size in the area around alpha-prime -- reports buttons are listed on the screen
16. Rest (self-paced) -- *SPACE* to proceed
17. Stereo-E block (until 3 successes in a row) -- *LEFT*, *RIGHT*, *UP*, or *DOWN* to indicate orientation of the character
18. Simple Experimental Block (Gabor orientation judgement; 50% of catch trials) -- reports buttons are listed on the screen
-- after every 30 trials: rest (self-paced) + stereo-E block 
19. Rest (self-paced) -- *SPACE* to proceed
20. Stereo-E block (until 3 successes in a row) -- *LEFT*, *RIGHT*, *UP*, or *DOWN* to indicate orientation of the character
21. 2I2AFC Block (15% of catch trials )  -- reports buttons are listed on the screen
-- after every 30 trials: rest (self-paced) + stereo-E block
22. Thank you message -- *SPACE* to proceed
