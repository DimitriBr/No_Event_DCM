import json
import random
import pickle

import numpy as np
from psychopy import visual, colors, event, core

from trials import (
    DCM_Trial,
    Stereo_Trial,
    Inter_Trial_Interval,
    Dichoptic_Text,
    Dichoptic_Slider,
    Adjustment_DCM_Trial,
)
from misc import Participant, Parameters, Calibrator, check_beta_plot


class Experiment:
    def __init__(self, participant: Participant, params: Parameters):
        self.participant = participant

        self.params = params

        self.window = visual.Window(fullscr=True, color=params.background_color_0)
        self.mouse = event.Mouse(visible=False)
        self.mouse.setExclusive(True)

        self.betas_calibration = {}

        def default_beta_function(_anything):
            return 1.0

        self.beta_polynomial = default_beta_function # default polynomial;
        self.kappa_polynomial = default_beta_function 

    def _insert_inter_trial_interval(self, inter_trial_interval):
        for visual in self.canvas_DCF:
            visual.draw()
        self.window.flip()
        core.wait(inter_trial_interval)

    def run_color_contrast_calibration(
        self, calibration_type : str, n_calibration_contrasts: int, save_results: bool, 
    ):
        if calibration_type not in ["DCF_colors", "background"]:
            raise ValueError("Calibration type should be either 'DCF_colors' or 'background'")
        
        contrast_levels = [i for i in range(n_calibration_contrasts)]
        random.shuffle(contrast_levels)

        gamma = self.params.visual_params["full_saturation_value"]

        is_calibration_approved = False
        while is_calibration_approved is False:
            self.betas_calibration = {}

            for icontrast in contrast_levels:
                alpha = (
                    gamma
                    - self.params.calibration_params["alpha_decrement"] * icontrast
                )
                if calibration_type == "DCF_colors":
                    color_A = colors.Color([gamma, alpha, 0], space="rgb1") #red
                    color_B = colors.Color([alpha, gamma, 0], space="rgb1") #green
                if calibration_type == "background":
                    color_A = colors.Color([gamma, alpha, 0], space="rgb1") #red
                    color_B = colors.Color([gamma, gamma, gamma], space="rgb1") #blue

                calibrator = Calibrator(
                    window=self.window,
                    refresh_rate=self.params.screen_params["refresh_rate__hz"],
                    mouse=self.mouse,
                    beta_0=self.params.calibration_params["beta_0"],
                    beta_increment=self.params.calibration_params["beta_increment"],
                    calibration_type=self.params.calibration_params["calibration_type"],
                    A_color_rgb1=color_A,
                    B_color_rgb1=color_B,
                    field_size=3
                    * int(
                        self.params.visual_params["square_size__degrees"]
                        * self.params.px_per_deg
                    ),
                    background_color=self.params.background_color_0,
                )
                beta = calibrator.run_calibration_trial()

                self.window.flip()
                core.wait(self.params.calibration_params["inter_round_waiting__s"])

                self.betas_calibration[icontrast] = beta

            is_calibration_approved, polynomial = check_beta_plot(
                window=self.window,
                mouse=self.mouse,
                field_size=3
                * int(
                    self.params.visual_params["square_size__degrees"]
                    * self.params.px_per_deg
                ),
                gamma=gamma,
                alpha_decrement=self.params.calibration_params["alpha_decrement"],
                betas=self.betas_calibration,
            )

        if calibration_type == "DCF_colors":
            self.beta_polynomial = polynomial
        if calibration_type == "background":
            self.kappa_polynomial = polynomial #changing notation to kappa to separate from red-and-green calibration

        if save_results:
            calibration_data_path = self.participant.path / f"calibration_{calibration_type}"
            calibration_data_path.mkdir(exist_ok=True)

            if calibration_type == "DCF_colors":
                for beta in self.betas_calibration.values():
                    if beta > 1:
                        raise RuntimeError(
                            "Betas cannot exceed 1. Recalibration is required."
                        )

            with open((calibration_data_path / f"calibration_{calibration_type}.json"), "w") as f:
                json.dump(self.betas_calibration, f, indent=4)

            with open(calibration_data_path / f"polynomial_{calibration_type}.pickle", "wb") as f:
                pickle.dump(polynomial, f)

    def load_calibration(self):
        # DCF calibration
        calibration_data_path = self.participant.path / "calibration_DCF_colors"
        with open(calibration_data_path / f"polynomial_DCF_colors.pickle", "rb") as f:
            beta_polynomial = pickle.load(f)
        print(f"Calibration loaded from {calibration_data_path}")
        self.beta_polynomial = beta_polynomial

        # Background calibration
        calibration_data_path = self.participant.path / "calibration_background"
        with open(calibration_data_path / f"polynomial_background.pickle", "rb") as f:
            kappa_polynomial = pickle.load(f)
        print(f"Calibration loaded from {calibration_data_path}")
        self.kappa_polynomial = kappa_polynomial

    def _set_background_color(self, alpha):
        kappa = self.kappa_polynomial(alpha)
        gamma = self.params.visual_params["full_saturation_value"]
        background_color = colors.Color(kappa * np.array([gamma, gamma, gamma]), space="rgb1")
        self.window.setColor(background_color)

    def run_experimental_block(
        self,
        block_code: str,
        n_trials: int,
        alphas: list,
        color_modes: list,
        detection_collection: bool,
        discrimination_collection: bool,
        forced_termination_buttons: list | None = None,
        is_iti_included: bool = True,
        is_constant_stim: bool = False,
        hidden_trial_ratio: float = 0.0,
    ):
        if len(color_modes) != n_trials:
            raise ValueError(
                "the length of color mode specification list is not the same as the number of trials"
            )
        if len(alphas) != n_trials:
            raise ValueError(
                "the length of contrast_level specification list is not the same as the number of trials"
            )

        if detection_collection is True:
            detection_info = self.params.detection_report_params
        else:
            detection_info = None

        if discrimination_collection is True:
            discrimination_info = self.params.discrimination_report_params
        else:
            discrimination_info = None

        # Setting stimulus duration
        stimulus_duration = None
        stimulus_onset = None
        if is_constant_stim:
            stimulus_duration = self.params.exp_trial_params["trial_duration__frames"]
            stimulus_onset = 0
        else:
            stimulus_duration = self.params.exp_trial_params[
                "stimulus_duration__frames"
            ]
            stimulus_onset = random.randint(
                self.params.exp_trial_params["no_stimulus_interval_front__frames"],
                self.params.exp_trial_params["trial_duration__frames"]
                - self.params.exp_trial_params["no_stimulus_interval_back__frames"],
            )

        for itrial in range(n_trials):

            self._set_background_color(alphas[itrial])
            trial = DCM_Trial(
                index=str(f"{block_code}_{itrial}"),
                window=self.window,
                data_folder=self.participant.path / block_code,
                square_size=int(
                    self.params.visual_params["square_size__degrees"]
                    * self.params.px_per_deg
                ),
                inter_square_distance=int(
                    self.params.visual_params["inter_square_distance__degrees"]
                    * self.params.px_per_deg
                ),
                frame_color=self.params.frame_color,
                frame_thickness=self.params.visual_params["frame_thickness__percent"],
                fixation_cross_size=int(
                    self.params.visual_params["fixation_cross_size__degrees"]
                    * self.params.px_per_deg
                ),
                max_trial_duration=self.params.exp_trial_params[
                    "trial_duration__frames"
                ],
                stimulus_source=self.params.stimuli_codes["gabor"],
                stimulus_duration=stimulus_duration,
                stimulus_onset=stimulus_onset,
                detection_judgement_routine=detection_info,
                discrimination_judgement_routine=discrimination_info,
                termination_buttons=forced_termination_buttons,
                color_mode=color_modes[itrial],
                stimulus_orientation=random.choice(["left", "right"]), ##### DEBUGGING
                gamma=self.params.visual_params["full_saturation_value"],
                alpha=alphas[itrial],
                beta_polynomial=self.beta_polynomial,
            )

            iti = Inter_Trial_Interval(
                index=str(f"{block_code}_{itrial}"),
                data_folder=self.participant.path / "inter_trial_intervals",
                window=self.window,
                duration=random.randint(
                    self.params.exp_trial_params[
                        "inter_trial_interval_lower_limit__frames"
                    ],
                    self.params.exp_trial_params[
                        "inter_trial_interval_higher_limit__frames"
                    ],
                ),
                square_size=int(
                    self.params.visual_params["square_size__degrees"]
                    * self.params.px_per_deg
                ),
                inter_square_distance=int(
                    self.params.visual_params["inter_square_distance__degrees"]
                    * self.params.px_per_deg
                ),
                frame_color=self.params.frame_color,
                frame_thickness=self.params.visual_params["frame_thickness__percent"],
                fixation_cross_size=int(
                    self.params.visual_params["fixation_cross_size__degrees"]
                    * self.params.px_per_deg
                ),
            )

            ###### block sequence #####
            trial.process_stimuli()
            random_number = random.random()

            if random_number > hidden_trial_ratio:
                trial.run()
            else:
                trial.run(hide_stimulus=True)

            trial.collect_responses()
            trial.save_data()
            if is_iti_included:
                iti.wait()
                iti.save_data()

    def run_2I2AFC_block(
        self,
        block_code: str,
        n_trials: int,
        alphas: list,
        color_modes: list,
        detection_collection: bool,
        discrimination_collection: bool,
        forced_termination_buttons: list | None = None,
        is_iti_included: bool = True,
        is_constant_stim: bool = False,
    ):
        if len(color_modes) != n_trials:
            raise ValueError(
                "the length of color mode specification list is not the same as the number of trials"
            )
        if len(alphas) != n_trials:
            raise ValueError(
                "the length of contrast_level specification list is not the same as the number of trials"
            )

        if detection_collection is True:
            detection_info = self.params.detection_report_params
        else:
            detection_info = None

        if discrimination_collection is True:
            discrimination_info = self.params.discrimination_report_params
        else:
            discrimination_info = None

        # Setting stimulus duration
        stimulus_duration = None
        stimulus_onset = None
        if is_constant_stim:
            stimulus_duration = self.params.exp_trial_params["trial_duration__frames"]
            stimulus_onset = 0
        else:
            stimulus_duration = self.params.exp_trial_params[
                "stimulus_duration__frames"
            ]
            stimulus_onset = random.randint(
                self.params.exp_trial_params["no_stimulus_interval_front__frames"],
                self.params.exp_trial_params["trial_duration__frames"]
                - self.params.exp_trial_params["no_stimulus_interval_back__frames"],
            )

        for itrial in range(n_trials):

            trial = DCM_Trial(
                index=str(f"{block_code}_{itrial}"),
                window=self.window,
                data_folder=self.participant.path / block_code,
                square_size=int(
                    self.params.visual_params["square_size__degrees"]
                    * self.params.px_per_deg
                ),
                inter_square_distance=int(
                    self.params.visual_params["inter_square_distance__degrees"]
                    * self.params.px_per_deg
                ),
                frame_color=self.params.frame_color,
                frame_thickness=self.params.visual_params["frame_thickness__percent"],
                fixation_cross_size=int(
                    self.params.visual_params["fixation_cross_size__degrees"]
                    * self.params.px_per_deg
                ),
                max_trial_duration=self.params.exp_trial_params[
                    "trial_duration__frames"
                ],
                stimulus_source=self.params.stimuli_codes["gabor"],
                stimulus_duration=stimulus_duration,
                stimulus_onset=stimulus_onset,
                detection_judgement_routine=detection_info,
                discrimination_judgement_routine=discrimination_info,
                termination_buttons=forced_termination_buttons,
                color_mode=color_modes[itrial],
                stimulus_orientation=random.choice(["left", "right"]),
                gamma=self.params.visual_params["full_saturation_value"],
                alpha=alphas[itrial],
                beta_polynomial=self.beta_polynomial,
            )

            iti = Inter_Trial_Interval(
                index=str(f"{block_code}_{itrial}"),
                data_folder=self.participant.path / "inter_trial_intervals",
                window=self.window,
                duration=random.randint(
                    self.params.exp_trial_params[
                        "inter_trial_interval_lower_limit__frames"
                    ],
                    self.params.exp_trial_params[
                        "inter_trial_interval_higher_limit__frames"
                    ],
                ),
                square_size=int(
                    self.params.visual_params["square_size__degrees"]
                    * self.params.px_per_deg
                ),
                inter_square_distance=int(
                    self.params.visual_params["inter_square_distance__degrees"]
                    * self.params.px_per_deg
                ),
                frame_color=self.params.frame_color,
                frame_thickness=self.params.visual_params["frame_thickness__percent"],
                fixation_cross_size=int(
                    self.params.visual_params["fixation_cross_size__degrees"]
                    * self.params.px_per_deg
                ),
            )

            iii = Inter_Trial_Interval(
                index=str(f"{block_code}_{itrial}"),
                data_folder=self.participant.path / "inter_trial_intervals",
                window=self.window,
                duration=60,
                square_size=int(
                    self.params.visual_params["square_size__degrees"]
                    * self.params.px_per_deg
                ),
                inter_square_distance=int(
                    self.params.visual_params["inter_square_distance__degrees"]
                    * self.params.px_per_deg
                ),
                frame_color=self.params.frame_color,
                frame_thickness=self.params.visual_params["frame_thickness__percent"],
                fixation_cross_size=int(
                    self.params.visual_params["fixation_cross_size__degrees"]
                    * self.params.px_per_deg
                ),
            )

            ###### block sequence #####
            configuration_2IFC = random.choice([1, 2])
            trial.process_stimuli()
            if configuration_2IFC == 1:
                trial.index = str(trial.index)  + "_stim"
                trial.run()
                trial.save_data() 
                iii.wait()
                trial.index = str(trial.index) + "_empty"
                trial.run(hide_stimulus=True)
                trial.save_data()
                trial.collect_interval_response(interval_probe_params=self.params.interval_probe_params)
                trial.collect_responses()
                trial.save_data()
                if is_iti_included:
                    iti.wait()
                    iti.save_data()
            elif configuration_2IFC == 2:
                trial.index = str(trial.index)  + "_empty"
                trial.run(hide_stimulus=True)
                trial.save_data() 
                trial.index = str(trial.index) + "_stim"
                iii.wait()
                trial.run()
                trial.save_data()
                trial.collect_interval_response(interval_probe_params=self.params.interval_probe_params)
                trial.collect_responses()
                trial.save_data()
                if is_iti_included:
                    iti.wait()
                    iti.save_data()
            

    def run_stereo_adaptation_block(self, block_code, n_trials_max):
        progress_tracker = []
        for itrial in range(n_trials_max):
            stimulus_direction = random.choice(["left", "right", "up", "down"])
            stimuli = [
                self.params.stimuli_codes[f"E_{stimulus_direction}_{side}"]
                for side in ["left", "right"]
            ]
            trial = Stereo_Trial(
                index=str(f"{block_code}_{itrial}"),
                stimulus_index=stimulus_direction,
                window=self.window,
                data_folder=self.participant.path / block_code,
                square_size=int(
                    self.params.visual_params["square_size__degrees"]
                    * self.params.px_per_deg
                ),
                inter_square_distance=int(
                    self.params.visual_params["inter_square_distance__degrees"]
                    * self.params.px_per_deg
                ),
                frame_color=self.params.frame_color,
                frame_thickness=self.params.visual_params["frame_thickness__percent"],
                fixation_cross_size=int(
                    self.params.visual_params["fixation_cross_size__degrees"]
                    * self.params.px_per_deg
                ),
                max_trial_duration=self.params.exp_trial_params[
                    "trial_duration__frames"
                ],
                stimulus_source=stimuli,
                termination_buttons=["left", "right", "up", "down"],
            )

            ###### block sequence #####
            trial.process_stimuli()
            trial.run()
            if trial.info["direction"] == trial.info["terminated_by"]:
                progress_tracker.append(True)
            else:
                progress_tracker.append(False)
            trial.save_data()

            if len(progress_tracker) > 3:
                if all(progress_tracker[-3:]):
                    break

    def display_text(self, text: str, text_mode: str, termination_buttons: list):
        if text_mode not in ["fusion", "default"]:
            raise ValueError("text mode can be either fusion or default")

        stimuli = []
        if text_mode == "default":
            text_stim = visual.TextBox2(
                units="pix",
                win=self.window,
                alignment="center",
                text=text,
                size=[
                    self.params.screen_params["resolution_x__px"],
                    self.params.screen_params["resolution_y__px"],
                ],
                letterHeight=int(
                    0.2
                    * self.params.visual_params["square_size__degrees"]
                    * self.params.px_per_deg
                ),
                pos=(0, 0),
                color=self.params.frame_color,
            )
            stimuli.append(text_stim)
        elif text_mode == "fusion":
            text_builder = Dichoptic_Text(
                window=self.window,
                square_size=int(
                    self.params.visual_params["square_size__degrees"]
                    * self.params.px_per_deg
                ),
                inter_square_distance=int(
                    self.params.visual_params["inter_square_distance__degrees"]
                    * self.params.px_per_deg
                ),
                frame_color=self.params.frame_color,
                frame_thickness=self.params.visual_params["frame_thickness__percent"],
                fixation_cross_size=int(
                    self.params.visual_params["fixation_cross_size__degrees"]
                    * self.params.px_per_deg
                ),
                termination_buttons=termination_buttons,
            )
            text_builder.process_stimuli(text=text)
            stimuli = text_builder.stimuli + text_builder.dichoptic_canvas

        while True:
            for stim in stimuli:
                stim.draw()
            self.window.flip()
            keys_pressed = event.getKeys()
            if any([button in keys_pressed for button in termination_buttons]):
                break

    def run_slider_based_adjustment_block(
        self,
        block_code: str,
    ) -> float:

        gamma = self.params.visual_params["full_saturation_value"]
        alpha = (
            self.params.visual_params["full_saturation_value"]
            - 0.2 * self.params.visual_params["full_saturation_value"]
        )

        trial_index = -1
        while True:
            trial_index += 1
            trial = DCM_Trial(
                index=str(f"{block_code}_{trial_index}"),
                window=self.window,
                data_folder=self.participant.path / block_code,
                square_size=int(
                    self.params.visual_params["square_size__degrees"]
                    * self.params.px_per_deg
                ),
                inter_square_distance=int(
                    self.params.visual_params["inter_square_distance__degrees"]
                    * self.params.px_per_deg
                ),
                frame_color=self.params.frame_color,
                frame_thickness=self.params.visual_params["frame_thickness__percent"],
                fixation_cross_size=int(
                    self.params.visual_params["fixation_cross_size__degrees"]
                    * self.params.px_per_deg
                ),
                max_trial_duration=self.params.exp_trial_params[
                    "trial_duration__frames"
                ],
                stimulus_source=self.params.stimuli_codes["gabor"],
                stimulus_duration=self.params.exp_trial_params[
                    "stimulus_duration__frames"
                ],
                stimulus_onset=random.randint(
                    self.params.exp_trial_params["no_stimulus_interval_front__frames"],
                    self.params.exp_trial_params["trial_duration__frames"]
                    - self.params.exp_trial_params["no_stimulus_interval_back__frames"],
                ),
                detection_judgement_routine=self.params.detection_report_params,
                discrimination_judgement_routine=None,
                termination_buttons=None,
                color_mode="fusion",
                stimulus_orientation=random.choice(["left", "right"]),
                gamma=gamma,
                alpha=alpha,
                beta_polynomial=self.beta_polynomial,
            )

            iti = Inter_Trial_Interval(
                index=str(f"{block_code}_{trial_index}"),
                data_folder=self.participant.path
                / f"{block_code}_inter_trial_intervals",
                window=self.window,
                duration=random.randint(
                    self.params.exp_trial_params[
                        "inter_trial_interval_lower_limit__frames"
                    ],
                    self.params.exp_trial_params[
                        "inter_trial_interval_higher_limit__frames"
                    ],
                ),
                square_size=int(
                    self.params.visual_params["square_size__degrees"]
                    * self.params.px_per_deg
                ),
                inter_square_distance=int(
                    self.params.visual_params["inter_square_distance__degrees"]
                    * self.params.px_per_deg
                ),
                frame_color=self.params.frame_color,
                frame_thickness=self.params.visual_params["frame_thickness__percent"],
                fixation_cross_size=int(
                    self.params.visual_params["fixation_cross_size__degrees"]
                    * self.params.px_per_deg
                ),
            )

            slider_menu = Dichoptic_Slider(
                window=self.window,
                scale=[int(0.625 * 100 * gamma), int(100 * gamma)],
                current_value=alpha * 100,
                square_size=int(
                    self.params.visual_params["square_size__degrees"]
                    * self.params.px_per_deg
                ),
                inter_square_distance=int(
                    self.params.visual_params["inter_square_distance__degrees"]
                    * self.params.px_per_deg
                ),
                frame_color=self.params.frame_color,
                frame_thickness=self.params.visual_params["frame_thickness__percent"],
                fixation_cross_size=int(
                    self.params.visual_params["fixation_cross_size__degrees"]
                    * self.params.px_per_deg
                ),
                termination_buttons=["space"],
                block_finish_buttons=["q"],
                increase_buttons=["o"],
                decrease_buttons=["m"],
            )

            ###### block sequence #####
            trial.process_stimuli()
            slider_menu.process_stimuli()

            trial.run()
            trial.collect_responses()

            alpha = slider_menu.run() / 100

            info = slider_menu.get_data()
            trial.save_data()

            if info["block_finish_called"] == "yes":
                break
            iti.wait()

        return alpha

    def run_adjustment_block(self, block_code: str, adjustment_buttons: list) -> float:

        random.seed(random.randint(1, 99999))
        gamma = self.params.visual_params["full_saturation_value"]
        alpha = (
            self.params.visual_params["full_saturation_value"]
            - 0.2 * self.params.visual_params["full_saturation_value"]
        )

        adj_trial = Adjustment_DCM_Trial(
            index=str(f"{block_code}_results"),
            window=self.window,
            data_folder=self.participant.path / block_code,
            square_size=int(
                self.params.visual_params["square_size__degrees"]
                * self.params.px_per_deg
            ),
            inter_square_distance=int(
                self.params.visual_params["inter_square_distance__degrees"]
                * self.params.px_per_deg
            ),
            frame_color=self.params.frame_color,
            frame_thickness=self.params.visual_params["frame_thickness__percent"],
            fixation_cross_size=int(
                self.params.visual_params["fixation_cross_size__degrees"]
                * self.params.px_per_deg
            ),
            max_trial_duration=99999,
            stimulus_source=self.params.stimuli_codes["gabor"],
            stimulus_duration=99999,
            stimulus_onset=0,
            detection_judgement_routine=None,
            discrimination_judgement_routine=None,
            termination_buttons=["space"],
            color_mode="fusion",
            stimulus_orientation=random.choice(["left", "right"]), #DEBUGGING
            gamma=gamma,
            alpha=alpha,
            beta_polynomial=self.beta_polynomial,
        )

        ###### block sequence #####
        adj_trial.process_stimuli()
        alpha = adj_trial.run(
            adjustment_buttons=adjustment_buttons, adjustment_value=0.002, kappa_polynomial=self.kappa_polynomial
        )

        random.seed(None)
        return alpha

    def run_adapted_staircase(
        self,
        block_code: str,
        n_reversals: int,
        suggested_alpha: float,
        alpha_increment: float,
        exploration_range: float,
    ) -> float:
        STAIRCASES = ["Swiss", "Dutch"]
        gamma = self.params.visual_params["full_saturation_value"]

        staircase_history = {staircase: [] for staircase in STAIRCASES}
        staircase_history["Swiss"].append(suggested_alpha + exploration_range / 2)
        staircase_history["Dutch"].append(suggested_alpha - exploration_range / 2)

        trial_index = -1
        while True:
            trial_index += 1
            staircase = random.choice(STAIRCASES)
            current_alpha = staircase_history[staircase][-1]
            trial = DCM_Trial(
                index=str(f"{block_code}_{trial_index}"),
                window=self.window,
                data_folder=self.participant.path / block_code,
                square_size=int(
                    self.params.visual_params["square_size__degrees"]
                    * self.params.px_per_deg
                ),
                inter_square_distance=int(
                    self.params.visual_params["inter_square_distance__degrees"]
                    * self.params.px_per_deg
                ),
                frame_color=self.params.frame_color,
                frame_thickness=self.params.visual_params["frame_thickness__percent"],
                fixation_cross_size=int(
                    self.params.visual_params["fixation_cross_size__degrees"]
                    * self.params.px_per_deg
                ),
                max_trial_duration=self.params.exp_trial_params[
                    "trial_duration__frames"
                ],
                stimulus_source=self.params.stimuli_codes["gabor"],
                stimulus_duration=self.params.exp_trial_params[
                    "stimulus_duration__frames"
                ],
                stimulus_onset=random.randint(
                    self.params.exp_trial_params["no_stimulus_interval_front__frames"],
                    self.params.exp_trial_params["trial_duration__frames"]
                    - self.params.exp_trial_params["no_stimulus_interval_back__frames"],
                ),
                detection_judgement_routine=self.params.detection_report_params,
                discrimination_judgement_routine=None,
                termination_buttons=None,
                color_mode="fusion",
                stimulus_orientation=random.choice(["left", "right"]),
                gamma=gamma,
                alpha=current_alpha,
                beta_polynomial=self.beta_polynomial,
            )

            iti = Inter_Trial_Interval(
                index=str(f"{block_code}_{trial_index}"),
                data_folder=self.participant.path
                / f"{block_code}_inter_trial_intervals",
                window=self.window,
                duration=random.randint(
                    self.params.exp_trial_params[
                        "inter_trial_interval_lower_limit__frames"
                    ],
                    self.params.exp_trial_params[
                        "inter_trial_interval_higher_limit__frames"
                    ],
                ),
                square_size=int(
                    self.params.visual_params["square_size__degrees"]
                    * self.params.px_per_deg
                ),
                inter_square_distance=int(
                    self.params.visual_params["inter_square_distance__degrees"]
                    * self.params.px_per_deg
                ),
                frame_color=self.params.frame_color,
                frame_thickness=self.params.visual_params["frame_thickness__percent"],
                fixation_cross_size=int(
                    self.params.visual_params["fixation_cross_size__degrees"]
                    * self.params.px_per_deg
                ),
            )

            ###### block sequence #####
            trial.process_stimuli()
            trial.run()
            trial.collect_responses()
            trial.save_data()
            info = trial.get_data()
            if info["detection_response"] == "yes":
                alpha_updated = current_alpha + alpha_increment
            elif info["detection_response"] == "no":
                alpha_updated = current_alpha - alpha_increment

            if alpha_updated > trial.gamma:
                alpha_updated = trial.gamma 
            if alpha_updated < 0:
                alpha_updated = 0

            print(staircase, alpha_updated)

            staircase_history[staircase].append(alpha_updated)
            iti.wait()

            converged_alpha = _get_staircase_covnergence(
                staircase_history=staircase_history, n_reversals=n_reversals
            )
            if converged_alpha is not None:
                break

        return converged_alpha


def _get_staircase_covnergence(staircase_history: dict, n_reversals: int):
    staircase_convergence = None
    keys = [key for key in staircase_history.keys()]
    individual_convergences = {staircase_name: None for staircase_name in keys}

    for staircase_name in keys:
        staircase = staircase_history[staircase_name]
        if len(staircase) > n_reversals:
            reversals_found = _get_number_of_reversals(staircase)
            if reversals_found >= n_reversals:
                individual_convergences[staircase_name] = np.mean(staircase[-5:])

    if all([result is not None for result in individual_convergences.values()]):
        staircase_convergence = np.mean(
            [[result for result in individual_convergences.values()]]
        )
    return staircase_convergence


def _get_number_of_reversals(staircase: list) -> int:
    n = len(staircase)
    counter = 0
    for i in range(n - 2):
        if staircase[i] == staircase[i + 2]:
            counter += 1
    return counter
