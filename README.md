# Project Name

No_Event_Dichoptic_Color_Masking

**work in progress**

## Requirements

Windows 10 or Windows 11

## Installation

To run the stimuli code, you may re-create the environment `psych` from the `psych.yml` file included in this project.
In this case, you could run `conda env create -f environment.yml` in your terminal

Further important steps on how to launch the stimuli code:

1. Modify `parameters_screen.json` with the parameters of your screen
(so far, the code has been tested and works stably with 60Hz, so it is recommended to keep the resolution of your screen at 60Hz)
2. Modify `run_session.py` if you want to change the block components of the experiment
3. Run `run_session.py` from `psych` conda environment

## Project Structure

1. `run_session.py` is used as a high-level runner for organizing experimental blocks into a particular experiment
2. `experiment.py` is the module with class `Experiment` that contains defined experimental blocks for DCM
3. `trials.py` is the module with classes that correspond to trial types needed for the DCM experiment
4. `misc.py` is the module with miscellaneous helper classes and functions for other modules
5. `image_processing.py` is the module containing the `prepare_image` function that transforms the image on a white or transparent background into the format required for DCF

## Current Experiment Structure

1. Demographical Info Filling
2. Welcome text
3. Calibration Instruction text
4. Background Color Calibration (red and grey)
5. Fusion Color Calibration (red and green)
6. Fusion Instruction
7. Stereo-E block (until 3 successes in a row)
8. Adaptation (same color, high contrast) with no report
9. Adaptation (same color, low contrast) with no report
10. Demo Trial (same color, variable constasts) with reports
11. Demo Trials (different colors, variable contrasts) with reports
12. Adjustment Instructions
13. Adjustment Block (searching for alpha-prime: estimated alpha-threshold)
14. Staircase Instructions
15. Double-Staircase with a small step size in the area around alpha-prime
16. Rest (self-paced)
17. Stereo-E block
18. Simple Experimental Block (Gabor orientation judgement; 50% of catch trials)
-- after every 30 trials: rest (self-paced) + stereo-E block
19. Rest (self-paced)
20. Stereo-E block
21. 2I2AFC Block (15% of catch trials )
-- after every 30 trials: rest (self-paced) + stereo-E block
22. Thank you message
