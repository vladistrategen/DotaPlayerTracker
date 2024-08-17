from typing import override

from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from tqdm import tqdm
from rank_evolution.Plotter.rank_plotter import RankPlotter
from args_store import ARGS


class VideoPlotter(RankPlotter):
    def __init__(self, data):
        super().__init__(data)

    @property
    @override
    def _save_file_extension(self) -> str:
        return "mp4"

    @property
    @override
    def _save_file_directory(self) -> str:
        return "videos"   

    @override
    def plot_and_save(self) -> None:
        fig, ax = plt.subplots(figsize=(19.2, 10.8))
        line, = ax.plot([], [], linestyle='-', marker='')
        text = ax.text(0.5, 1.05, '', transform=ax.transAxes, ha='center', fontsize=15)
        progress_bar = tqdm(total=len(self._data), desc="Creating animation frames")
        plotted_min_points = set()
        plotted_max_points = set()

        # Get the first and last date for annotations
        first_date = self._data['DateTime'].iloc[0]
        last_date = self._data['DateTime'].iloc[-1]

        def init():
            ax.set_xlim(self._data['DateTime'].min(), self._data['DateTime'].max())
            if ARGS.CLIArgs.zoomed_in: # TODO: fix for values close to factors of 25
                min_rank = self._data['Rank'].min()
                max_rank = self._data['Rank'].max()
                min_rank = 25 * (min_rank // 25)
                max_rank = 25 * (max_rank // 25 + 1)
                ax.set_ylim(min_rank, max_rank)
                pass
            else:
                ax.set_ylim(0, 1000)

            ax.grid(True)  # Add grid lines

            # Add annotations for the first and last dates
            ax.annotate(first_date.strftime('%d %B %Y'), xy=(first_date, 0), xycoords=('data', 'axes fraction'),
                        xytext=(0, -30), textcoords='offset points', ha='center', fontsize=10, color='blue')
            ax.annotate(last_date.strftime('%d %B %Y'), xy=(last_date, 0), xycoords=('data', 'axes fraction'),
                        xytext=(0, -30), textcoords='offset points', ha='center', fontsize=10, color='blue')

            if ARGS.CLIArgs.inverted:
                ax.invert_yaxis()
            return line, text

        def update(frame):
            # print(f"Processing frame {frame}/{len(self._data)}")  
            current_time = self._data['DateTime'].iloc[frame]
            current_rank = self._data['Rank'].iloc[frame]
            text.set_text(f"{current_time.strftime('%d %B %Y, %H:%M')}, Rank: {current_rank}")
            xdata = self._data['DateTime'].iloc[:frame + 1]
            ydata = self._data['Rank'].iloc[:frame + 1]
            line.set_data(xdata, ydata)

            if ARGS.CLIArgs.detailed: # TODO: add option to select min/max interval
                current_month = self._data['DateTime'].dt.to_period('M').iloc[frame]
                month_group = self._data[self._data['DateTime'].dt.to_period('M') == current_month]

                if not month_group.empty:
                    max_rank = month_group.loc[month_group['Rank'].idxmin()]
                    min_rank = month_group.loc[month_group['Rank'].idxmax()]

                    if (current_month, min_rank['DateTime']) not in plotted_min_points and current_time >= min_rank['DateTime']:
                        ax.scatter(min_rank['DateTime'], min_rank['Rank'], color='blue')
                        ax.text(min_rank['DateTime'], min_rank['Rank'], f"{min_rank['Rank']}", verticalalignment='top', horizontalalignment='right', color='red')
                        plotted_min_points.add((current_month, min_rank['DateTime']))

                    if (current_month, max_rank['DateTime']) not in plotted_max_points and current_time >= max_rank['DateTime']:
                        ax.scatter(max_rank['DateTime'], max_rank['Rank'], color='green')
                        ax.text(max_rank['DateTime'], max_rank['Rank'], f"{max_rank['Rank']}", verticalalignment='bottom', horizontalalignment='left', color='green')
                        plotted_max_points.add((current_month, max_rank['DateTime']))

            progress_bar.update(1)
            return line, text

        fps = len(self._data) / ARGS.CLIArgs.duration
        anim = FuncAnimation(fig, update, frames=len(self._data), init_func=init, blit=False, repeat=False)

        anim.save(self.save_file_path, writer='ffmpeg', fps=fps, dpi=100, extra_args=['-v', 'error'])
        progress_bar.close()
        plt.close(fig)