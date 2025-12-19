import copy
from dataclasses import dataclass
from pathlib import Path
import math
import json

import matplotlib
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from psychopy import visual, event, colors
import numpy as np


@dataclass
class Participant:
    sbj_id: str
    age: str
    gender: str
    handedness: str

    @property
    def path(self):
        return Path("data") / self.sbj_id

    def create_participant_repo(self):
        self.path.mkdir(exist_ok=True)

    def save_demographical_info(self):
        demographics = {
            "id": self.sbj_id,
            "age": self.age,
            "gender": self.gender,
            "handedness": self.handedness,
        }

        try:
            age = int(self.age)
        except:
            raise ValueError("Age should be numeric")

        with open((self.path / f"demographics.json"), "w") as f:
            json.dump(demographics, f, indent=4)


class Parameters:
    def __init__(
        self,
        screen_params_file: Path,
        visual_params_file: Path,
        exp_trial_params_file: Path,
        calibration_params_file: Path,
        contrast_practise_params_file: Path,
        detection_report_params_file: Path,
        discrimination_report_params_file: Path,
        interval_probe_prarms_file : Path,
        stimuli_codes_file: Path,
    ):
        params_folder = Path("params")

        with open(params_folder / screen_params_file, "rb") as file:
            self.screen_params = json.load(file)

        with open(params_folder / visual_params_file, "rb") as file:
            self.visual_params = json.load(file)

        with open(params_folder / exp_trial_params_file, "rb") as file:
            self.exp_trial_params = json.load(file)

        with open(params_folder / calibration_params_file, "rb") as file:
            self.calibration_params = json.load(file)

        with open(params_folder / contrast_practise_params_file, "rb") as file:
            self.contrast_practise_params = json.load(file)

        with open(params_folder / detection_report_params_file, "rb") as file:
            self.detection_report_params = json.load(file)

        with open(params_folder / discrimination_report_params_file, "rb") as file:
            self.discrimination_report_params = json.load(file)

        with open(params_folder / interval_probe_prarms_file, "rb") as file:
            self.interval_probe_params = json.load(file)

        with open(params_folder / stimuli_codes_file, "rb") as file:
            self.stimuli_codes = json.load(file)

        # self.red_colors = pd.read_excel(params_folder / reds_values_file, header=None)
        # self.green_colors = pd.read_excel(
        #     params_folder / green_values_file, header=None
        # )

    @property
    def px_per_deg(self):
        cm_per_degree = self.screen_params["distance_to_screen__cm"] * math.tan(
            math.radians(1)
        )
        y_px_per_cm = (
            self.screen_params["resolution_y__px"]
            / self.screen_params["screen_height__cm"]
        )
        x_px_per_cm = (
            self.screen_params["resolution_x__px"]
            / self.screen_params["screen_width__cm"]
        )
        px_per_cm = (y_px_per_cm + x_px_per_cm) / 2
        return px_per_cm * cm_per_degree

    @property
    def background_color_0(self):
        backgroup_rgb1 = self.visual_params["background_0_rgb1"]
        return colors.Color(backgroup_rgb1, space="rgb1")

    @property
    def frame_color(self):
        frame_color_rgb1 = self.visual_params["frame_rgb1"]
        return colors.Color(frame_color_rgb1, space="rgb1")


class Calibrator:
    """
    color luminance calibration
    color A: reference luminance (lower)
    color B: luminance adjusted by multiplier < 1
    """

    def __init__(
        self,
        window: visual.Window,
        refresh_rate: int,
        mouse: event.Mouse,
        beta_0: int,
        beta_increment: int,
        calibration_type: str,
        A_color_rgb1: list,
        B_color_rgb1: list,
        field_size: int,
        background_color: colors.Color,
    ):
        self.window = window
        self.refresh_rate = refresh_rate
        self.mouse = mouse
        self.beta_0 = beta_0
        self.beta_increment = beta_increment
        self.calibration_type = calibration_type
        self.A_color_vals_0 = A_color_rgb1
        self.B_color_vals_0 = B_color_rgb1
        self.field_size = field_size
        self.window.color = background_color

        if calibration_type not in ["checkerboard", "single_square"]:
            raise ValueError(
                "Calibration is defined only for 'checkerboard' or 'single_square' types"
            )
        if refresh_rate % (15 * 2) != 0:
            raise ValueError("Refresh rate of the screen should be a multiple of 30")

    def _get_checkerboard(self, color_list):
        squares = []

        q = int(self.field_size / 6)  # scaler

        color_i = 0
        for x in np.linspace(-2.5, 2.5, 6):
            for y in np.linspace(-2.5, 2.5, 6):
                square = visual.Rect(
                    units="pix",
                    win=self.window,
                    width=int(q / 1.05),
                    height=int(q / 1.05),
                    pos=(x * q, y * q),
                    fillColor=color_list[color_i],
                )
                squares.append(square)
                color_i += 1
        
        return squares

    def run_calibration_trial(self) -> float:
        beta = self.beta_0
        A_color_vals = copy.copy(self.A_color_vals_0)
        B_color_vals = copy.copy(self.B_color_vals_0)
        B_color_vals.rgb1 = self.B_color_vals_0.rgb1 * beta

        event.clearEvents(eventType="keyboard")

        if self.calibration_type == "checkerboard":
            color_list_even = (
                [B_color_vals, A_color_vals] * 3
                + [A_color_vals, B_color_vals] * 3
            ) * 3
            color_list_odd = (
                [A_color_vals, B_color_vals] * 3
                + [B_color_vals, A_color_vals] * 3
            ) * 3
            colors = [color_list_even,  color_list_odd]
            boards = [self._get_checkerboard(color) for color in colors]
            #print("before", B_color_vals)

            i_frame = -1
            while True:
                i_frame += 1
                board = boards[(i_frame % 4)//2]

                for obj in board:
                    obj.draw()
                self.window.flip()

                current_keys = event.getKeys()
                if len(current_keys) > 0:
                    print("PRESSED", current_keys)
                    if "up" in current_keys:
                        beta += self.beta_increment
                    elif "down" in current_keys:
                        beta -= self.beta_increment 
                    elif "space" in current_keys:
                        break

                    B_color_vals.rgb1 = self.B_color_vals_0.rgb1 * beta
                    for board in boards:
                        green_squares = [obj for obj in board if obj.fillColor[0] < obj.fillColor[1]]
                        for obj in green_squares:
                            obj.setColor(B_color_vals)
                        #print("posle", obj.fillColor)           

        return beta


def check_beta_plot(
    window: visual.Window,
    mouse: event.Mouse,
    field_size: int,
    gamma: float,
    alpha_decrement: float,
    betas: dict,
) -> tuple[bool, dict]:
    is_judgement_made = False
    button_pressed_index = None
    experimenter_approved = False

    alphas_used = [gamma - (alpha_decrement * contrast) for contrast in range(len(betas))]
    betas_ordered = [betas[i] for i, alpha in enumerate(alphas_used)]

    polynomial = np.poly1d(np.polyfit(x=alphas_used, y=betas_ordered, deg=2))
    betas_fitted = polynomial(alphas_used)

    temporal_image_file = Path("temporal_image.png")
    matplotlib.use("Agg")
    matplotlib.rcParams["axes.edgecolor"] = "white"
    matplotlib.rcParams["xtick.color"] = "white"
    matplotlib.rcParams["ytick.color"] = "white"
    matplotlib.rcParams["axes.labelcolor"] = "white"
    plt.cla()
    plt.plot(
        alphas_used,
        betas_ordered,
        label="Calibration Data",
        color="yellow",
    )
    plt.plot(
        alphas_used,
        betas_fitted,
        label="Polynomial Fit",
        color="magenta",
    )
    plt.xlabel("Contrast Level")
    plt.ylabel("Beta")
    plt.savefig(temporal_image_file, transparent=True)
    plot = visual.ImageStim(
        units="pix",
        win=window,
        image=temporal_image_file,
        interpolate=True,
        texRes=1024,
    )
    judgement_text = visual.TextBox2(
        units="pix",
        win=window,
        size=(field_size, field_size / 8),
        text="Please, wait for the experimenter to continue",
        pos=(0, int(0.75 * field_size)),
        color="white",
    )

    button_xs = [-int(0.25 * field_size), int(0.25 * field_size)]
    button_labels = ["Aprove Calibration", "Repeat Calibration"]
    buttons = [
        visual.TextBox2(
            units="pix",
            win=window,
            size=(field_size / 2.5, field_size / 8),
            text=button_labels[i],
            pos=(button_xs[i], -int(0.7 * field_size)),
            color="black",
            fillColor="white",
        )
        for i in range(2)
    ]

    mouse.setExclusive(False)
    while not is_judgement_made:
        plot.draw()
        judgement_text.draw()
        for ibutton, button in enumerate(buttons):
            button.draw()
            if mouse.isPressedIn(shape=button, buttons=[0]):
                button_pressed_index = ibutton
                is_judgement_made = True

        window.flip()
    mouse.setExclusive(True)

    if button_pressed_index == 0:
        experimenter_approved = True
    elif button_pressed_index == 1:
        experimenter_approved == False

    temporal_image_file.unlink()

    return (
        experimenter_approved,
        polynomial,
    )


### old calibration version with tkinter
def check_beta_plot_2(betas: dict) -> tuple[bool, dict]:
    experimenter_approved = dict(value=None)

    contrast_list_ascending = [i for i in range(len(betas))]
    betas_ordered = [betas[i] for i in contrast_list_ascending]

    polynomial = np.poly1d(
        np.polyfit(x=contrast_list_ascending, y=betas_ordered, deg=2)
    )
    betas_fitted = polynomial(contrast_list_ascending)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(contrast_list_ascending, betas_ordered, label="Calibration Data")
    ax.plot(contrast_list_ascending, betas_fitted, label="Polynomial Fit")
    ax.set_xlabel("Contrast Level")
    ax.set_ylabel("Beta")

    root = tk.Tk()
    root.title("Color Contrast Calibration")
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    button_frame = tk.Frame(root)
    button_frame.pack(side=tk.BOTTOM, pady=10)

    yes_button = tk.Button(
        button_frame,
        text="Approve Calibration",
        width=20,
        command=lambda: (experimenter_approved.update(value=1), root.destroy()),
    )
    yes_button.pack(side=tk.LEFT, padx=10)

    no_button = tk.Button(
        button_frame,
        text="Repeat Calibration",
        width=20,
        command=lambda: (experimenter_approved.update(value=0), root.destroy()),
    )
    no_button.pack(side=tk.RIGHT, padx=10)

    root.mainloop()

    return (
        bool(experimenter_approved["value"]),
        {i: betas_fitted[i] for i in contrast_list_ascending},
    )


def get_gui_inputs(fields, gui_window_title):
    """
    Opens a tkinter window with text entry boxes for each field name.
    Returns a dict {field_name: entered_text}.
    """
    responses = {}

    def on_submit():
        for field, entry in entries.items():
            responses[field] = entry.get()
        root.destroy()

    root = tk.Tk()
    root.title(gui_window_title)

    entries = {}
    for i, field in enumerate(fields):
        label = tk.Label(root, text=field)
        label.grid(row=i, column=0, padx=5, pady=5, sticky="e")
        entry = tk.Entry(root, width=40)
        entry.grid(row=i, column=1, padx=5, pady=5)
        entries[field] = entry

    submit_btn = tk.Button(root, text="Submit", command=on_submit)
    submit_btn.grid(row=len(fields), column=0, columnspan=2, pady=10)

    root.mainloop()
    return responses