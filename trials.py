import random
from abc import ABC, abstractmethod
from pathlib import Path
import json
from copy import copy

from psychopy import visual, colors, event
import pandas as pd
import numpy as np
from PIL import Image

from image_processing import prepare_image


class Dichoptic_Trial(ABC):
    """
    A parent class for the experimental and practise trials
    """

    def __init__(
        self,
        index: str,
        window: visual.Window,
        data_folder: Path,
        square_size: int,
        inter_square_distance: int,
        frame_color: colors.Color,
        frame_thickness: float,
        fixation_cross_size: int,
        max_trial_duration: int,
        stimulus_source: Path | list | None,
        stimulus_duration: int,
        stimulus_onset: int,
        detection_judgement_routine: dict | None,
        discrimination_judgement_routine: dict | None,
        termination_buttons: list | None,
    ):
        """
        Parameters
        ----------
        window : psychopy.visual.Window
            Window to display the stimuli
        data_folder: Path
            Folder to save the data generated in the trial

        """
        self.index = index
        self.window = window
        self.data_folder = data_folder
        self.data_folder.mkdir(exist_ok=True)
        self.square_size = square_size
        self.inter_square_distance = inter_square_distance
        self.max_trial_duration = max_trial_duration
        self.stimulus_source = stimulus_source
        self.stimulus_duration = stimulus_duration
        self.stimulus_onset = stimulus_onset
        self.termination_buttons = termination_buttons

        self.stimuli = []
        self.supporting_visuals = []
        self.dichoptic_canvas = generate_dichoptic_canvas(
            window=window,
            inter_square_distance=inter_square_distance,
            square_size=square_size,
            frame_color=frame_color,
            frame_thickness=frame_thickness,
            fixation_cross_size=fixation_cross_size,
        )

        self.detection_report = None
        if detection_judgement_routine is not None:
            self.detection_params = detection_judgement_routine
            self.detection_response_button_pressed = "No_Pressed_Button"  # default
            self.detection_report = "No_Report_Made"  # default

        self.discrimination_report = None 
        if discrimination_judgement_routine is not None:
            self.discrimination_params = discrimination_judgement_routine
            self.discrimination_report_button_pressed = "No_Pressed_Button"
            self.discrimination_report = "No_Report_Made"

        self.info = {}
        self.info["trial_id"] = index
        self.info["terminated_by"] = "time_out"  # default trial termination

    def run(self):
        event.clearEvents(eventType="keyboard")

        frame_mapping = {iframe: None for iframe in range(self.max_trial_duration)}

        # inserting stimuli to canvas for the relevant frames
        frame_visual_stimuli_off = self.supporting_visuals + self.dichoptic_canvas
        frame_visual_stimuli_on = (
            self.supporting_visuals + self.stimuli + self.dichoptic_canvas
        )

        for iframe in range(self.max_trial_duration):
            # frame_visual_stimuli_on[-2:-2] = copy(self.stimuli)
            if (iframe > self.stimulus_onset) and (
                iframe < (self.stimulus_onset + self.stimulus_duration)
            ):
                frame_mapping[iframe] = frame_visual_stimuli_on
            else:
                frame_mapping[iframe] = frame_visual_stimuli_off

        last_frame = self.max_trial_duration
        for iframe in range(last_frame):
            for visual_object in frame_mapping[iframe]:
                visual_object.draw()
            self.window.flip()

            if self.termination_buttons is not None:
                keys_pressed = event.getKeys()
                if any([button in keys_pressed for button in self.termination_buttons]):
                    self.info["terminated_by"] = keys_pressed[0]
                    last_frame = iframe + 1
                    frame_mapping[last_frame] = self.supporting_visuals + self.stimuli + [obj for iobj, obj in enumerate(self.dichoptic_canvas) if iobj%2==0]
            if iframe == last_frame:
                break
        self.info["terminated_at"] = last_frame

    def save_data(self):
        with open((self.data_folder / f"{self.index}.json"), "w") as f:
            json.dump(self.info, f, indent=4)

    @abstractmethod
    def process_stimuli(self):
        pass

    @abstractmethod
    def collect_responses(self):
        pass


class DCM_Trial(Dichoptic_Trial):
    def __init__(
        self,
        index: str,
        window: visual.Window,
        data_folder: Path,
        square_size: int,
        inter_square_distance: int,
        frame_color: colors.Color,
        frame_thickness: float,
        fixation_cross_size: float,
        max_trial_duration: int,
        stimulus_source: Path | None,
        stimulus_duration: int,
        stimulus_onset: int,
        detection_judgement_routine: dict | None,
        discrimination_judgement_routine: dict | None,
        termination_buttons: list | None,
        color_mode: str,
        stimulus_orientation: str,
        contrast_level: int,
        red_colors: pd.DataFrame,
        green_colors: pd.DataFrame,
        betas: dict,
    ):
        super().__init__(
            index,
            window,
            data_folder,
            square_size,
            inter_square_distance,
            frame_color,
            frame_thickness,
            fixation_cross_size,
            max_trial_duration,
            stimulus_source,
            stimulus_duration,
            stimulus_onset,
            detection_judgement_routine,
            discrimination_judgement_routine,
            termination_buttons,
        )

        self.color_mode = color_mode
        if color_mode not in ["fusion", "red", "green"]:
            raise ValueError("color mode can be either fusion, red, or green")

        if stimulus_orientation == "left":
            self.ori = 45
        elif stimulus_orientation == "right":
            self.ori = 135
        else:
            raise ValueError("Oritentation can be either left or right")

        beta = betas[contrast_level]
        red_color = colors.Color(
            np.array(red_colors.loc[contrast_level, :]), space="rgb1"
        )
        green_color = colors.Color(
            beta * np.array(green_colors.loc[contrast_level, :]), space="rgb1"
        )
        self.colors = {"red": red_color, "green": green_color}

        self.info["color_mode"] = color_mode
        self.info["stimulus_orientation"] = stimulus_orientation
        self.info["contrast"] = contrast_level

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

        for visual_object in self.dichoptic_canvas:
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

    def process_stimuli(self):
        SIDES = ["left", "right"]

        square_positions = {
            "left": (-int(self.inter_square_distance / 2 + self.square_size / 2), 0),
            "right": (int(self.inter_square_distance / 2 + self.square_size / 2), 0),
        }

        square_colors = {side: None for side in SIDES}
        if self.color_mode == "fusion":
            color_set = ["red", "green"]
            random.shuffle(color_set)
            square_colors = {SIDES[i]: color_set[i] for i in range(len(SIDES))}
        elif self.color_mode == "red":
            square_colors = {side: "red" for side in SIDES}
        elif self.color_mode == "green":
            square_colors = {side: "green" for side in SIDES}

        processed_images = prepare_image(
            input_path=self.stimulus_source,
            m=self.square_size,
            red_rgb255=self.colors["red"].rgb255,
            green_rgb255=self.colors["green"].rgb255,
            ori=self.ori,
        )

        for side in SIDES:
            square_color = square_colors[side]
            background_square = visual.Rect(
                units="pix",
                win=self.window,
                width=self.square_size,
                height=self.square_size,
                pos=square_positions[side],
                fillColor=self.colors[square_color],
            )
            self.supporting_visuals.append(background_square)

            image_stimulus = visual.ImageStim(
                image=processed_images[square_color],
                units="pix",
                colorSpace="rgb",
                win=self.window,
                pos=square_positions[side],
            )
            self.stimuli.append(image_stimulus)

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


class Stereo_Trial(Dichoptic_Trial):
    def __init__(
        self,
        index: str,
        stimulus_index: str,
        window: visual.Window,
        data_folder: Path,
        square_size: int,
        inter_square_distance: int,
        frame_color: colors.Color,
        frame_thickness: float,
        fixation_cross_size: float,
        max_trial_duration: int,
        stimulus_source: list,
        termination_buttons: list,
    ):
        super().__init__(
            index,
            window,
            data_folder,
            square_size,
            inter_square_distance,
            frame_color,
            frame_thickness,
            fixation_cross_size,
            max_trial_duration,
            stimulus_source,
            termination_buttons=termination_buttons,
            stimulus_duration=max_trial_duration,
            stimulus_onset=0,
            detection_judgement_routine=False,
            discrimination_judgement_routine=False,
        )

        if type(stimulus_source) != list:
            raise ValueError(
                "For stereo trials, stimulus sourse should be a list of length 2"
            )
        if len(stimulus_source) != 2:
            raise ValueError(
                "For stereo trials, stimulus sourse should be a list of length 2"
            )

        self.info["direction"] = stimulus_index

    def process_stimuli(self):
        square_positions = {
            "left": (-int(self.inter_square_distance / 2 + self.square_size / 2), 0),
            "right": (int(self.inter_square_distance / 2 + self.square_size / 2), 0),
        }

        for iside, side in enumerate(["left", "right"]):
            image = Image.open(self.stimulus_source[iside])
            l1, l2 = image.size
            if l1 != l2:
                raise ValueError("Image input should be squared")
            l = l1
            m = self.square_size
            offset = (l - m) // 2
            image = image.crop((offset, offset, offset + m, offset + m))

            image_stimulus = visual.ImageStim(
                image=image,
                units="pix",
                win=self.window,
                # size=[self.square_size, self.square_size],
                pos=square_positions[side],
            )
            self.stimuli.append(image_stimulus)

    def collect_responses(self):
        super().collect_responses()


class Inter_Trial_Interval:
    def __init__(
        self,
        index: str,
        data_folder: Path,
        window: visual.Window,
        duration: int,
        square_size: int,
        inter_square_distance: int,
        frame_color: colors.Color,
        frame_thickness: float,
        fixation_cross_size: int,
    ):
        self.window = window
        self.index = index
        self.data_folder = data_folder
        self.duration = duration
        self.dichoptic_canvas = generate_dichoptic_canvas(
            window,
            square_size,
            inter_square_distance,
            frame_color,
            frame_thickness,
            fixation_cross_size,
        )

        self.info = {}
        self.info["preceding_trial"] = index
        self.info["waiting_time"] = duration

    def wait(self):
        for _iframe in range(self.duration):
            for visual_object in self.dichoptic_canvas:
                visual_object.draw()
            self.window.flip()

    def save_data(self):
        self.data_folder.mkdir(exist_ok=True)
        with open((self.data_folder / f"post_{self.index}.json"), "w") as f:
            json.dump(self.info, f, indent=4)


def generate_dichoptic_canvas(
    window: visual.Window,
    square_size: int,
    inter_square_distance: int,
    frame_color: colors.Color,
    frame_thickness: float,
    fixation_cross_size: int,
) -> list:
    dichoptic_canvas = []
    square_center_positions = {
        "left": (
            -int(inter_square_distance / 2 + square_size / 2),
            0,
        ),
        "right": (
            int(inter_square_distance / 2 + square_size / 2),
            0,
        ),
    }
    for side in ["left", "right"]:
        square_frame = visual.Rect(
            units="pix",
            win=window,
            width=square_size,
            height=square_size,
            pos=square_center_positions[side],
            lineColor=frame_color,
            lineWidth=square_size * 0.01 * frame_thickness,
            interpolate=True,
        )
        dichoptic_canvas.append(square_frame)

        fixation_cross = visual.TextBox2(
            units="pix",
            win=window,
            alignment="center",
            text="+",
            letterHeight=fixation_cross_size,
            pos=square_center_positions[side],
            color=frame_color,
        )
        dichoptic_canvas.append(fixation_cross)
    return dichoptic_canvas
