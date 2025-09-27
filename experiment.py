import json
import random

from psychopy import visual, colors, event, core

from trials import DCF_Trial
from misc import Participant, Parameters, Calibrator


class Experiment:
    def __init__(self, participant: Participant, params: Parameters):
        self.participant = participant
        self.participant.path.mkdir(exist_ok=True)

        self.params = params

        self.window = visual.Window(fullscr=True, color=params.background_color)
        self.mouse = event.Mouse(visible=False)
        self.mouse.setExclusive(True)

        self.betas_calibration = {}
        self.betas_fitted = {i: 0.9 for i in range(15)}  # CHANGE TO OTHER DEFAULT TODO

        # Special block for generating DCF canvas: fixation cross and empty square frames:
        self.canvas_DCF = []
        square__center_positions = {
            "left": (
                -int(
                    params.visual_params["inter_square_distance__degrees"]
                    * params.px_per_deg
                    / 2
                    + params.visual_params["square_size__degrees"]
                    * params.px_per_deg
                    / 2
                ),
                0,
            ),
            "right": (
                int(
                    params.visual_params["inter_square_distance__degrees"]
                    * params.px_per_deg
                    / 2
                    + params.visual_params["square_size__degrees"]
                    * params.px_per_deg
                    / 2
                ),
                0,
            ),
        }
        for side in ["left", "right"]:
            square_frame = visual.Rect(
                units="pix",
                win=self.window,
                width=params.visual_params["square_size__degrees"] * params.px_per_deg,
                height=params.visual_params["square_size__degrees"] * params.px_per_deg,
                pos=square__center_positions[side],
                lineColor=params.frame_color,
                lineWidth=params.visual_params["square_size__degrees"]
                * 0.01
                * params.visual_params["frame_thickness__percent"]
                * params.px_per_deg,
                interpolate=True,
            )
            self.canvas_DCF.append(square_frame)

            fixation_cross = visual.TextBox2(
                units="pix",
                win=self.window,
                alignment="center",
                text="+",
                letterHeight=int(
                    params.visual_params["fixation_cross_size__degrees"]
                    * params.px_per_deg
                ),
                pos=square__center_positions[side],
                color=params.frame_color,
            )
            self.canvas_DCF.append(fixation_cross)

    def _insert_inter_trial_interval(self, inter_trial_interval):
        for visual in self.canvas_DCF:
            visual.draw()
        self.window.flip()
        core.wait(inter_trial_interval)

    def run_color_contrast_calibration(self, save_results: bool):
        is_calibration_approved = False
        contrast_levels = [i for i in range(self.params.green_colors.shape[0])]
        random.shuffle(contrast_levels)

        while is_calibration_approved is False:
            self.betas_calibration = {}

            for icontrast in contrast_levels:
                calibrator = Calibrator(
                    window=self.window,
                    refresh_rate=self.params.screen_params["refresh_rate__hz"],
                    mouse=self.mouse,
                    beta_0=self.params.calibration_params["beta_0"],
                    beta_increment=self.params.calibration_params["beta_increment"],
                    calibration_type=self.params.calibration_params["calibration_type"],
                    red_color_rgb1=colors.Color(
                        list(self.params.red_colors.loc[icontrast, :]), space="rgb1"
                    ),
                    green_color_rgb1=colors.Color(
                        list(self.params.green_colors.loc[icontrast, :]), space="rgb1"
                    ),
                    field_size=3
                    * int(
                        self.params.visual_params["square_size__degrees"]
                        * self.params.px_per_deg
                    ),
                    background_color=self.params.background_color,
                )
                beta = calibrator.run_calibration_trial()

                self.window.flip()
                core.wait(self.params.calibration_params["inter_round_waiting__s"])

                self.betas_calibration[icontrast] = beta

            is_calibration_approved, betas_fit = calibrator.check_beta_plot(
                betas=self.betas_calibration
            )

        self.betas_fitted = betas_fit

        if save_results:
            calibration_data_path = self.participant.path / "calibration"
            calibration_data_path.mkdir(exist_ok=True)

            for beta in self.betas_calibration.values():
                if beta > 1:
                    raise RuntimeError(
                        "Betas cannot exceed 1. Recalibration is required."
                    )

            for beta in self.betas_fitted.values():
                if beta > 1:
                    raise RuntimeError("Betas cannot exceed 1.")

            with open((calibration_data_path / f"betas_calibrated.json"), "w") as f:
                json.dump(self.betas_calibration, f, indent=4)

            with open((calibration_data_path / f"betas_fitted.json"), "w") as f:
                json.dump(self.betas_fitted, f, indent=4)

    def run_contrast_adaptation_block(self):
        trial_indexer = 0
        for contrast_level in self.params.contrast_practise_params["contrast_levels"]:
            for _itrial in range(
                self.params.contrast_practise_params["trials_per_level"]
            ):
                con_prac_trial = DCF_Trial(
                    index=str(f"Practice_{trial_indexer}"),
                    window=self.window,
                    data_folder=self.participant.path / "practice_trials",
                    max_duration=self.params.contrast_practise_params[
                        "max_trial_duration__frames"
                    ],
                    termination_buttons=["left", "right"],
                    detection_judgement_routine=False,
                    discrimination_judgement_routine=False,
                    contrast_level=contrast_level,
                    gabor_orientation=random.choice(["left", "right"]),
                    red_colors=self.params.red_colors,
                    green_colors=self.params.green_colors,
                    betas=self.betas_fitted,
                    color_mode=random.choice(["red", "green"]),
                    stimulus_mode="gabor",
                    square_size=int(
                        self.params.visual_params["square_size__degrees"]
                        * self.params.px_per_deg
                    ),
                    inter_square_distance=int(
                        self.params.visual_params["inter_square_distance__degrees"]
                        * self.params.px_per_deg
                    ),
                    grating_resolution=128,
                    canvas_DCF=self.canvas_DCF,
                )

                con_prac_trial.generate_visuals()
                con_prac_trial.run()
                con_prac_trial.save_data()
                trial_indexer += 1

                self._insert_inter_trial_interval(
                    self.params.contrast_practise_params["inter_trial_interval__s"]
                )

    def run_experimental_block(
        self, block_code, n_trials, contrast_levels, color_modes
    ):
        if len(color_modes) != n_trials:
            raise ValueError(
                "the length of color mode specification list is not the same as the number of trials"
            )
        if len(contrast_levels) != n_trials:
            raise ValueError(
                "the length of contrast_level specification list is not the same as the number of trials"
            )

        for itrial in range(n_trials):
            trial = DCF_Trial(
                index=str(f"{block_code}_{itrial}"),
                window=self.window,
                data_folder=self.participant.path / block_code,
                max_trial_duration=self.params.exp_trial_params["trial_duration__frames"],
                termination_buttons=None,
                stimulus_duration=self.params.exp_trial_params[
                    "stimulus_duration__frames"
                ],
                stimulus_onset=random.randint(
                    self.params.exp_trial_params["no_stimulus_interval_front__frames"],
                    self.params.exp_trial_params["trial_duration__frames"]
                    - self.params.exp_trial_params["no_stimulus_interval_back__frames"],
                ),
                contrast_level=contrast_levels[itrial],
                detection_judgement_routine=self.params.detection_report_params,
                discrimination_judgement_routine=self.params.discrimination_report_params,
                gabor_orientation=random.choice(["left", "right"]),
                red_colors=self.params.red_colors,
                green_colors=self.params.green_colors,
                betas=self.betas_fitted,
                color_mode=color_modes[itrial],
                stimulus_mode="gabor",
                square_size=int(
                    self.params.visual_params["square_size__degrees"]
                    * self.params.px_per_deg
                ),
                inter_square_distance=int(
                    self.params.visual_params["inter_square_distance__degrees"]
                    * self.params.px_per_deg
                ),
                grating_resolution=128,
                canvas_DCF=self.canvas_DCF,
            )

            trial.generate_visuals()
            trial.run()
            trial.collect_responses()
            trial.save_data()

            self._insert_inter_trial_interval(
                self.params.exp_trial_params["inter_trial_interval__s"]
            )
