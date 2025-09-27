import random
from abc import ABC, abstractmethod
from pathlib import Path
import json
from copy import copy

from psychopy import visual, colors, event
import pandas as pd
import numpy as np


class Trial(ABC):
    """
    A parent class for the experimental and practise trials
    """

    def __init__(
        self,
        index: str,
        window: visual.Window,
        data_folder: Path,
        max_trial_duration: int,
        termination_buttons: list,
    ):
        self.index = index
        self.window = window
        self.data_folder = data_folder
        self.data_folder.mkdir(exist_ok=True)
        self.max_trial_duration = max_trial_duration
        self.termination_buttons = termination_buttons

        self.support_visuals = []
        self.stimuli = []

        self.info = {}
        self.info["trial_id"] = index
        self.info["terminated_by"] = "time_out"  # default trial termination

    def save_data(self):
        with open((self.data_folder / f"{self.index}.json"), "w") as f:
            json.dump(self.info, f, indent=4)

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def generate_visuals(self):
        pass

    @abstractmethod
    def collect_responses(self):
        pass


class DCF_Trial(Trial):
    def __init__(
        self,
        index: str,
        window: visual.Window,
        data_folder: Path,
        max_trial_duration: int,
        termination_buttons: list | None,
        stimuli : list,
        stimulus_duration: int,
        stimulus_onset: int,
        detection_judgement_routine: bool,
        discrimination_judgement_routine: bool,
        contrast_level: int,
        stimulus_mode: str,
        red_colors: pd.DataFrame,
        green_colors: pd.DataFrame,
        betas: dict,
        color_mode: str,
        inter_square_distance: int,
        square_size: int,
        grating_resolution: int,
        canvas_DCF: int,
    ):
        super().__init__(
            index, window, data_folder, max_trial_duration, termination_buttons
        )

        self.stimulus_duration = stimulus_duration
        self.stimulus_onset = stimulus_onset
        self.inter_square_distance = inter_square_distance
        self.square_size = square_size
        self.grating_res = grating_resolution
        self.color_mode = color_mode
        self.stimulus_mode = stimulus_mode

        self.canvas = canvas_DCF
        for visual in canvas_DCF:
            self.support_visuals.append(visual)

        beta = betas[contrast_level]

        self.red_color = colors.Color(
            np.array(red_colors.loc[contrast_level, :]), space="rgb1"
        )
        self.green_color = colors.Color(
            beta * np.array(green_colors.loc[contrast_level, :]), space="rgb1"
        )

        if detection_judgement_routine is not None:
            self.detection_params = detection_judgement_routine
            self.detection_response_button_pressed = "No_Pressed_Button"  # default
            self.detection_report = "No_Report_Made"  # default
        if discrimination_judgement_routine is not None:
            self.discrimination_params = discrimination_judgement_routine
            self.discrimination_report_button_pressed = "No_Pressed_Button"
            self.discrimination_report = "No_Report_Made"

        if grating_resolution not in [2**i for i in range(10)]:
            raise ValueError("grating_resolution should be a power of 2")
        if color_mode not in ["fusion", "red", "green"]:
            raise ValueError("color mode can be either fusion, red, or green")
        if stimulus_mode not in ["orientation", "which_one_out_of_two", "empty"]:
            raise ValueError(f"stimulus_mode {stimulus_mode} is not defined")
        
        self.info["stimulus_mode"] = stimulus_mode
        self.info["contrast"] = contrast_level
        self.info["color_mode"] = color_mode

        if stimulus_mode == "orientation":
            orientation = random.choice(["left", "right"])
            if orientation == "left":
                self.ori = 315
            elif orientation == "right":
                self.ori = 45
            self.info["stimulus_orientation"] = orientation
        
        if stimulus_mode == "which_one":
            chosen_stimulus = random.choice(stimuli)
            

    def _generate_gaborlike_texture(self):
        sin_waves = [
            [
                (np.sin(val) + 1) / 2
                for val in np.linspace(-np.pi, np.pi, self.grating_res)
            ],
            [
                (np.sin(val) + 1) / 2
                for val in np.linspace(np.pi, -np.pi, self.grating_res)
            ],
        ]

        random.shuffle(sin_waves)

        red_space__rgb = [
            (val * np.abs(self.red_color.rgb[0] - self.green_color.rgb[0]))
            + np.min([self.red_color.rgb[0], self.green_color.rgb[0]])
            for val in sin_waves[0]
        ]
        green_space__rgb = [
            (val * np.abs(self.red_color.rgb[1] - self.green_color.rgb[1]))
            + np.min([self.red_color.rgb[1], self.green_color.rgb[1]])
            for val in sin_waves[1]
        ]

        one_cycle_grating = np.ones((self.grating_res, self.grating_res, 3))
        for i in range(self.grating_res):
            one_cycle_grating[:, i] = [green_space__rgb[i], red_space__rgb[i], -1]

        texture = one_cycle_grating
        return texture

    def _get_individual_response(
        self, response_params: dict, is_mapping_to_shuffle: bool
    ) -> tuple[str, str]:
        is_response_made = False

        labels = copy(response_params["response_labels"])
        if is_mapping_to_shuffle is True:
            random.shuffle(labels)
        response_mapping = {
            response_params["response_buttons"][i]: labels[i]
            for i in range(len(response_params["response_labels"]))
        }
        response_visuals = []

        upper_square_lining_positions = {
            "left": (
                -int(self.inter_square_distance / 2 + self.square_size / 2),
                int(self.square_size / 4),
            ),
            "right": (
                int(self.inter_square_distance / 2 + self.square_size / 2),
                int(self.square_size / 4),
            ),
        }

        lower_square_lining_positions = {
            "left": (
                -int(self.inter_square_distance / 2 + self.square_size / 2),
                -int(self.square_size / 4),
            ),
            "right": (
                int(self.inter_square_distance / 2 + self.square_size / 2),
                -int(self.square_size / 4),
            ),
        }

        for side in ["left", "right"]:
            question_icon = visual.TextBox2(
                units="pix",
                win=self.window,
                alignment="center",
                text=response_params["question_icon_text"],
                letterHeight=int(self.square_size / 8),
                pos=upper_square_lining_positions[side],
                color="black",
            )
            response_visuals.append(question_icon)

            mapping_visual_info = visual.TextBox2(
                units="pix",
                win=self.window,
                alignment="center",
                text=response_params["response_buttons"][0]
                + f" if {response_mapping[response_params['response_buttons'][0]]}"
                + "\n"
                + response_params["response_buttons"][1]
                + f" if {response_mapping[response_params['response_buttons'][1]]}",
                letterHeight=int(self.square_size / 8),
                pos=lower_square_lining_positions[side],
                color="black",
            )
            response_visuals.append(mapping_visual_info)

        for visual_object in self.canvas:
            response_visuals.append(visual_object)

        # waiting for the button press
        event.clearEvents(eventType="keyboard")
        while is_response_made is False:
            for visual_object in response_visuals:
                visual_object.draw()
            self.window.flip()

            keys_pressed = event.getKeys()
            if any(
                [
                    button in keys_pressed
                    for button in response_params["response_buttons"]
                ]
            ):
                is_response_made = True
                response_button_pressed = keys_pressed[0]
                response = response_mapping[response_button_pressed]

        return response_button_pressed, response

    def generate_visuals(self):
        SIDES = ["left", "right"]

        square_positions = {
            "left": (-int(self.inter_square_distance / 2 + self.square_size / 2), 0),
            "right": (int(self.inter_square_distance / 2 + self.square_size / 2), 0),
        }

        square_colors = {side: None for side in SIDES}
        if self.color_mode == "fusion":
            color_set = [self.red_color, self.green_color]
            random.shuffle(color_set)
            square_colors = {SIDES[i]: color_set[i] for i in range(len(SIDES))}
        elif self.color_mode == "red":
            square_colors = {side: self.red_color for side in SIDES}
        elif self.color_mode == "green":
            square_colors = {side: self.green_color for side in SIDES}

        if self.stimulus_mode == "gabor":
            texture = self._generate_gaborlike_texture()

        for side in SIDES:
            if self.stimulus_mode == "gabor":
                gabor = visual.GratingStim(
                    units="pix",
                    win=self.window,
                    size=[self.square_size, self.square_size],
                    pos=square_positions[side],
                    tex=texture,
                    mask="gauss",
                    sf=5 / self.square_size,
                    ori=self.gabor_ori,
                    texRes=128,
                )
                self.stimuli.append(gabor)

            background_square = visual.Rect(
                units="pix",
                win=self.window,
                width=self.square_size,
                height=self.square_size,
                pos=square_positions[side],
                fillColor=square_colors[side],
            )
            self.support_visuals.append(background_square)

    def collect_responses(self):
        if self.detection_report == "No_Report_Made":
            detection_response_button_pressed, detection_response = (
                self._get_individual_response(
                    response_params=copy(self.detection_params),
                    is_mapping_to_shuffle=True,
                )
            )
            self.info["detection_response_button_pressed"] = (
                detection_response_button_pressed
            )
            self.info["detection_response"] = detection_response
        else:
            pass

        if self.discrimination_report == "No_Report_Made":
            discrimination_response_button_pressed, discrimination_response = (
                self._get_individual_response(
                    response_params=copy(self.discrimination_params),
                    is_mapping_to_shuffle=True,
                )
            )
            self.info["discrimination_response_button_pressed"] = (
                discrimination_response_button_pressed
            )
            self.info["discrimination_response"] = discrimination_response
        else:
            pass

    def run(self):
        event.clearEvents(eventType="keyboard")
        is_stimulus_shown = False

        for iframe in range(self.max_trial_duration):
            for visual_object in reversed(self.support_visuals):
                    visual_object.draw()

            if (iframe > self.stimulus_onset) and (
                iframe < (self.stimulus_onset + self.stimulus_duration)
            ):
                for visual_object in self.stimuli:
                    visual_object.draw()
            self.window.flip()

            if self.termination_buttons is not None:
                keys_pressed = event.getKeys()
                if any([button in keys_pressed for button in self.termination_buttons]):
                    self.info["terminated_by"] = keys_pressed[0]
                    break
