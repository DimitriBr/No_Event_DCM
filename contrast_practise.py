import random 

from psychopy import visual, colors
import numpy as np 

class Contrast_Practise_Trial():
    def __init__(self, window, contrast_level, main_color, red_colors, green_colors, inter_square_distance, square_size, grating_resolution):
        self.window = window
        self.inter_square_distance = inter_square_distance
        self.square_size = square_size
        self.grating_res = grating_resolution
        self.texture = None
        if main_color == "red":
            self.main_color =  colors.Color(list(red_colors.loc[contrast_level,:]), space = "rgb1")
            self.inner_color = colors.Color(list(green_colors.loc[contrast_level,:]), space = "rgb1")
        elif main_color == "green":
            self.main_color = colors.Color(list(green_colors.loc[contrast_level,:]), space = "rgb1")
            self.inner_color = colors.Color(list(red_colors.loc[contrast_level,:]), space = "rgb1")

        if grating_resolution not in [2**i for i in range(10)]:
            raise ValueError("grating_resolution should be a power of 2")

    def generate_texture(self): 

        sin_waves = [
            [(np.sin(val)+1)/2 for val in np.linspace(-np.pi, np.pi, self.grating_res)],
            [(np.sin(val)+1)/2 for val in np.linspace(np.pi, -np.pi, self.grating_res)]
        ]

        random.shuffle(sin_waves)

        green_space = [(val * np.abs(self.main_color.rgb[0] - self.inner_color.rgb[0])) + np.min([self.main_color.rgb[0], self.inner_color.rgb[0]]) for val in sin_waves[0]]
        red_space = [(val * np.abs(self.main_color.rgb[1] - self.inner_color.rgb[1])) + np.min([self.main_color.rgb[1], self.inner_color.rgb[1]]) for val in sin_waves[1]]

        one_cycle_grating = np.ones((self.grating_res, self.grating_res, 3)) 
        for i in range(self.grating_res):
            one_cycle_grating[:,i] = [green_space[i], red_space[i], -1]
        print(one_cycle_grating)

        self.texture = one_cycle_grating

    def get_visuals(self):
        square_positions = {
            "left" : (-int(self.inter_square_distance/2 + self.square_size/2), 0),
            "right" : (int(self.inter_square_distance/2 + self.square_size/2), 0)
        }

        for side in ["left", "right"]:
        
            square= visual.Rect(
                units  = "pix",
                win = self.window, 
                width=self.square_size,
                height = self.square_size,
                pos = square_positions[side],
                fillColor = self.main_color)
            square.draw()

            gabor = visual.GratingStim(
                units = "pix",
                win = self.window,
                size = [self.square_size, self.square_size],
                pos = square_positions[side],
                tex=self.texture,
                mask='gauss', 
                sf = 5/self.square_size,
                ori = 45,
                texRes = 128,
            )
            gabor.draw()

        self.window.flip()

        