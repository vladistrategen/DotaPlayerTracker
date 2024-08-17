from . import image_plotter
from . import video_plotter
from . import rank_plotter
from args_store import ARGS

class PlotterFactory:
    """Factory class to create appropriate plotter based on input."""
    
    @staticmethod
    def create_plotter(data) -> rank_plotter:
        """Create the appropriate plotter (ImagePlotter or VideoPlotter)."""

        if ARGS.CLIArgs.video:
            return video_plotter(data)
        else:
            return image_plotter(data)