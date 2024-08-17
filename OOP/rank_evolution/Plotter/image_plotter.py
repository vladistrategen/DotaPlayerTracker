from typing import override

from matplotlib import pyplot as plt

from ... import ARGS
from . import rank_plotter


class ImagePlotter(rank_plotter):
    def __init__(self, data):
        super().__init__(data)

    @property
    @override
    def _save_file_extension(self) -> str:
        return "png"

    @property
    @override
    def _save_file_directory(self) -> str:
        return "images"            

    @override
    def plot_and_save(self) -> None:
        plt.figure(figsize=(19.2, 10.8))
        
        plt.plot(self._data['DateTime'], self._data['Rank'], linestyle='-', marker='')

        # Highlight the first and last dates
        first_date = self._data['DateTime'].iloc[0]
        last_date = self._data['DateTime'].iloc[-1]
        plt.scatter([first_date, last_date], 
                    [self._data['Rank'].iloc[0], self._data['Rank'].iloc[-1]], 
                    color='orange')
        plt.text(first_date, self._data['Rank'].iloc[0], first_date.strftime('%Y-%m-%d'), verticalalignment='bottom', horizontalalignment='right', color='orange')
        plt.text(last_date, self._data['Rank'].iloc[-1], last_date.strftime('%Y-%m-%d'), verticalalignment='bottom', horizontalalignment='right', color='orange')

        if ARGS.CLIArgs.detailed:
            # Highlight local minimum and maximum for each month
            self._data['Month'] = self._data['DateTime'].dt.to_period('M').apply(lambda r: r.start_time)
            for month, group in self._data.groupby('Month'):
                if len(group) > 1:
                    max_rank = group.loc[group['Rank'].idxmin()]
                    min_rank = group.loc[group['Rank'].idxmax()]
                    plt.scatter([min_rank['DateTime']], [min_rank['Rank']], color='red')
                    plt.text(min_rank['DateTime'], min_rank['Rank'], f"{min_rank['Rank']}", verticalalignment='top', horizontalalignment='right', color='red')
                    plt.scatter([max_rank['DateTime']], [max_rank['Rank']], color='green')
                    plt.text(max_rank['DateTime'], max_rank['Rank'], f"{max_rank['Rank']}", verticalalignment='bottom', horizontalalignment='left', color='green')

        plt.xlabel('Date and Time')
        plt.ylabel('Rank')
        plt.title('Rank Evolution Over Time')
        plt.grid(True)
        plt.xticks(rotation=45)

        if ARGS.CLIArgs.zoomed_in: # TODO: fix for values close to factors of 25
            min_rank = self._data['Rank'].min()
            max_rank = self._data['Rank'].max()
            min_rank = 25 * (min_rank // 25)
            max_rank = 25 * (max_rank // 25 + 1)
            plt.ylim(min_rank, max_rank)
        else:
            plt.ylim(0, 1000)  # Set y-axis limits

        if ARGS.CLIArgs.inverted:
            plt.gca().invert_yaxis()
        
        plt.savefig(self.save_file_path, dpi=100)
        plt.close()
        