class Config:
    def __init__(self):
        self.same_level_bound = 1.5
        self.width_lower_bound = 25
        self.width_upper_bound = 40
        self.walls_stroke_widths = list(map(str, range(7, 11)))
        self.walls_markers_widths = list(map(str, range(1, 3)))
        self.wall_color = "rgb(0%, 0%, 0%)"
        self.wall_marker_color = "rgb(0%, 0%, 0%)"
        self.wall_marker_min_length = 24
        self.needed_markers_count = 10

        self.red_color = "rgb(100%, 0%, 0%)"
        self.blue_color = "rgb(0%, 0%, 100%)"
        self.green_color = "rgb(0%, 100%, 0%)"
        self.gray_lower = 45
        self.gray_upper = 55
        self.draw_width = "10"
        self.no_transformation_draw_width = "1.2"
        self.gray_width_lower_bound = 2.5

config = Config()