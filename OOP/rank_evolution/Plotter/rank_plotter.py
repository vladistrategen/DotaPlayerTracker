from abc import ABC, abstractmethod
from datetime import datetime
from args_store import ARGS
from pandas import DataFrame

class RankPlotter(ABC):

    def __init__(self, data : DataFrame):
        self._data = data
        self._datetime_string = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    @property
    def __save_file_path_base(self) -> str:
        """Abstract property that each subclass must define for saving files."""
        start_end_part = "GENERAL"
        if ARGS.CLIArgs.start_date and ARGS.CLIArgs.end_date:
            start_end_part = f"{ARGS.CLIArgs.start_date}___{ARGS.CLIArgs.end_date}"
        elif ARGS.CLIArgs.start_date:
            start_end_part = f"FROM___{ARGS.CLIArgs.start_date}"
        elif ARGS.CLIArgs.end_date:
            start_end_part = f"UNTIL___{ARGS.CLIArgs.end_date}"

        inverted_part = "inverted_" if ARGS.CLIArgs.inverted else "normal_"
        detailed_part = "detailed_" if ARGS.CLIArgs.detailed else ""
        zoomed_in_part = "zoomed_in_" if ARGS.CLIArgs.zoomed_in else ""

        return f'{start_end_part}___{inverted_part}{detailed_part}{zoomed_in_part}rank_evolution'

    @property
    def save_file_path(self) -> str:
        return f"{self._save_file_directory}/{self.__save_file_path_base}.{self._save_file_extension}"

    @property
    @abstractmethod
    def _save_file_extension(self) -> str:
        """Method to get the save file's directory. Do not include the trailing '.' character"""
        pass

    @property
    @abstractmethod
    def _save_file_directory(self) -> str:
        """Method to get the save file's directory. Do not include the trailing directory separator charactre i.e., '/', '\ ', etc..."""
        pass

    @abstractmethod
    def plot_and_save(self) -> None:
        """Method to generate and save the plot."""
        pass

