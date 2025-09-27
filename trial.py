from psychopy import visual, core

class Trial(): 
    def __init__(self, window, inter_square_distance, square_size):
        self.window = window
        self.square_size = square_size 
        self.inter_square_distance = inter_square_distance

    def create_trial_visuals(self, color_left, color_right):
        square_left = visual.Rect(
            units  = "pix",
            win = self.window, 
            width=self.square_size,
            height = self.square_size,
            pos = (-int(self.inter_square_distance/2 + self.square_size/2), 0),
            fillColor = color_left)
        
        square_right = visual.Rect(
            units  = "pix",
            win = self.window, 
            width=self.square_size,
            height =self.square_size,
            pos = (int(self.inter_square_distance/2 + self.square_size/2), 0),
            fillColor = color_right)
        
        square_left.draw()
        square_right.draw()
        self.window.flip()
