# profiler.py

class Profiler:
    def __init__(self, gui):
        self.gui = gui
        self.execution_times = {}

    def profile(self, stmt, time_taken):
        if stmt not in self.execution_times:
            self.execution_times[stmt] = 0
        self.execution_times[stmt] += time_taken

    def display_profile(self):
        profile_data = "\n".join([f"{stmt}: {time:.6f} seconds" for stmt, time in self.execution_times.items()])
        self.gui.display_profiler_results(profile_data)