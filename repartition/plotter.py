import matplotlib.pyplot as plt
import pandas as pd
import os

from .cost_analysis import CostAnalysis


class Plotter:
    """
    Contains all the plotting methods to report results.
    """

    def __init__(self, analysis: CostAnalysis = None, data_path: str = None):
        # Class variables
        if analysis:
            self._min_ssr_user = analysis.min_ssr_user

            # Variables to plot
            self._cost_users_no_deviation = analysis.cost_users_no_deviation
            self._cost_users = analysis.cost_users
            self._ssr_users = pd.read_csv(os.path.join(data_path, 'ssr_user.csv'))

        if data_path:
            self._inputs_path = data_path
            self._output_path = os.path.join(data_path, 'plots')
            os.makedirs(self._output_path, exist_ok=True)

    def plot_online_series(self):
        """
        Reports the results of one single run.
        """
        self._plot_series(self._cost_users_no_deviation, 'Costs without energy deviation', self._output_path,
                          'costs_users_no_deviation')
        self._plot_series(self._cost_users, 'Costs', self._output_path, 'costs_users')
        self._plot_series(self._ssr_users, 'SSR', self._output_path, 'ssr_users', ssr_plot=float(self._min_ssr_user))

    def plot_offline_series(self, plot_name: str, ssr: bool = False, costs: bool = False):
        """
        Reports results stored in csv files from previous runs.
        """
        if ssr:
            file = 'ssr_user.csv'
            file2 = 'ssr_rec.csv'
            sr = pd.read_csv(os.path.join(self._inputs_path, file), index_col=0, squeeze=True).drop(['SOLAR'])
            ssr_rec = pd.read_csv(os.path.join(self._inputs_path, file2), index_col=0, squeeze=True)
            self._plot_series(
                sr, self._output_path, plot_name, ssr_plot=float(self._min_ssr_user), ssr_rec=ssr_rec.mean()
            )
        if costs:
            file = 'costs_users_no_deviations.csv'
            sr = pd.read_csv(os.path.join(self._inputs_path, file), index_col=0, squeeze=True) / 250000
            self._plot_series(sr, self._output_path, plot_name)

    def plot_offline_difference(self, data_to_plot: list, y_label: str, plot_name: str):
        """
        Reports the difference between two series stored in csv files from previous runs.
        """
        sr1 = pd.read_csv(f'{self._inputs_path}/{data_to_plot[0]}.csv', index_col=0, squeeze=True)
        sr2 = pd.read_csv(f'{self._inputs_path}/{data_to_plot[1]}.csv', index_col=0, squeeze=True)
        self._plot_offline_series_difference([sr1, sr2], y_label, self._output_path, plot_name)

    @staticmethod
    def plot_offline_costs(costs: pd.Series, average_ssr: pd.Series, output_path: str):
        """
        Plots the costs alongside the average ssr of the users for several experiments
        """
        figure, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 8))
        costs.plot(ax=ax, kind='bar', color='b', alpha=0.5, grid=True)
        ax.set_xlabel('Min enforced SSR', fontsize=15)
        ax.set_ylabel('Total costs [EUR]', fontsize=15)
        plt.savefig(os.path.join(output_path, 'total_costs.pdf'))
        plt.close(figure)

        costs_to_plot = pd.Series((((costs / costs[0]) - 1) * 100))
        average_ssr_to_plot = pd.Series(average_ssr)
        width = 0.4
        # Figure
        figure, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 8))
        ax2 = ax.twinx()
        costs_to_plot.plot(
            ax=ax,
            kind='bar',
            rot=0,
            color=['blue'],
            alpha=0.5,
            width=width,
            position=1,
            grid=True,
            label='Costs evolution [%]'
        )
        average_ssr_to_plot.plot(
            ax=ax2,
            kind='bar',
            rot=0,
            color=['red'],
            alpha=0.5,
            width=width,
            position=0,
            ylim=[0.5, 0.6],
            label='Average SSR [%]'
        )
        ax.set_xlabel('Minimum SSR', fontsize=15)
        ax.set_ylabel('Costs evolution [%]', fontsize=15)
        ax2.set_ylabel('Average SSR of all AMRs [%]', fontsize=15)
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, loc=2, fontsize=15)
        ax2.legend().remove()
        ax.tick_params(which='both', labelsize=15)
        ax2.tick_params(which='both', labelsize=15)
        plt.savefig(os.path.join(output_path, 'costs_ssr.pdf'))
        plt.close(figure)

    @staticmethod
    def _plot_series(series: pd.Series, output_path: str, plot_name: str, ssr_plot: float = None,
                     ssr_rec: float = None, series_2: pd.Series = None):
        """
        Creates a bar plot.
        """
        figure, axes = plt.subplots(nrows=1, ncols=1, figsize=(10, 8))
        if series_2 is not None:
            df_to_plot = pd.DataFrame({'Costs with REC [EUR]': series, 'Costs without REC [EUR]': series_2})
            df_to_plot.plot(kind='bar', ax=axes, color=['b', 'g'], alpha=0.5, width=0.8, grid=True)
        else:
            series.plot(kind='bar', ax=axes, position=1, color='b', alpha=0.5, ylim=(0.0, 1.0), grid=True)

        if ssr_plot:
            axes.annotate(str(ssr_plot), xy=(23, ssr_plot), color='r', alpha=0.7, size=14, annotation_clip=False)
            axes.axhline(y=ssr_plot, color='r', linestyle='--', alpha=0.7)
        if ssr_rec:
            axes.annotate(str(round(ssr_rec, 2)), xy=(23, ssr_rec + 0.02), color='orange', alpha=0.7, size=14, annotation_clip=False)
            axes.axhline(y=ssr_rec, color='orange', linestyle='--', alpha=0.7)
            axes.annotate(str(round(series.mean(), 2)), xy=(23, series.mean()), color='g', alpha=0.7, size=14, annotation_clip=False)
            axes.axhline(y=series.mean(), color='g', linestyle='--', alpha=0.7)
        if not ssr_plot and not ssr_rec:
            plt.xlabel('Members of the REC')
            plt.ylabel('Costs [EUR]', fontsize=15)
        if ssr_plot and ssr_rec:
            plt.legend(['Minimum enforced SSR', 'SSR of the REC', 'Average SSR of the AMRs', 'SSR [%]'], fontsize=16,
                       loc='lower left')
        elif ssr_rec:
            plt.legend(['SSR of the REC', 'Average SSR of the AMRs', 'SSR [%]'], fontsize=16, loc='lower left')
        elif series_2 is not None:
            plt.legend(fontsize=16)
        plt.xticks(fontsize=15)
        plt.yticks(fontsize=15)
        if ssr_rec:
            figure.savefig(f'{output_path}/{plot_name}_{ssr_plot}.pdf')
        else:
            figure.savefig(f'{output_path}/{plot_name}.pdf')
        plt.tight_layout()
        plt.close(figure)

    @staticmethod
    def _plot_offline_series_difference(data_to_plot: pd.Series, output_path: str, plot_name: str):
        """
        Plots the difference between two series.
        """
        figure, axes = plt.subplots(nrows=1, ncols=1, figsize=(10, 8))
        data_to_plot.plot(kind='bar', ax=axes, color='b', alpha=0.5, label='Cost difference [%]', grid=True)
        plt.xlabel('Members of the REC', fontsize=15)
        plt.ylabel('Cost difference [%]', fontsize=15)
        plt.xticks(fontsize=15)
        plt.yticks(fontsize=15)
        plt.legend(fontsize=15)
        figure.savefig(f'{output_path}/{plot_name}.pdf')
        plt.close(figure)

    @staticmethod
    def plot_bar_three_cases(df1: pd.DataFrame, df2: pd.DataFrame, df3: pd.DataFrame, y_label: str, output_path: str,
                             plot_name: str, sales: bool = False, third_plot: bool = True):
        """
        Plots three dataframes in one figure.
        """
        if sales:
            width = 0.7
        else:
            width = 0.9
        if third_plot:
            titles = ['Uniform initial keys', 'Proportional static initial keys', 'Proportional dynamic initial keys']
            figure, axes = plt.subplots(nrows=3, ncols=1, figsize=(10, 9))
            df3.plot(kind='bar', ax=axes[2], colormap='Paired', alpha=0.9, width=width, rot=0, sharex=True, grid=True, ylim=(-16, 0))
        else:
            titles = ['Uniform initial keys', 'Proportional static initial keys']
            figure, axes = plt.subplots(nrows=2, ncols=1, figsize=(9, 5))
        df1.plot(kind='bar', ax=axes[0], colormap='Paired', alpha=0.9, width=width, rot=0, sharex=True, grid=True, ylim=(0, 105))
        df2.plot(kind='bar', ax=axes[1], colormap='Paired', alpha=0.9, width=width, rot=0, sharex=True, grid=True, ylim=(0, 105))
        [axes[i].legend(loc='lower left', fontsize=12) for i in range(len(axes))]
        [axes[i].set_title(titles[i], fontsize=16) for i in range(len(axes))]
        axes[-1].set_xlabel('Maximum key deviation allowed [%]', fontsize=16)
        [axes[i].set_ylabel(y_label, fontsize=16) for i in range(len(axes))]
        [axes[i].set_xticklabels([0, 1, 3, 5, 10, 20, 30, 50, 100], fontsize=16) for i in range(len(axes))]
        # [axes[i].set_ylim(-10, 18) for i in range(len(axes))]
        plt.tight_layout()
        figure.savefig(f'{output_path}/{plot_name}.pdf')
        plt.close(figure)

    @staticmethod
    def covered_consumption(cons: pd.Series, prod: pd.Series, loc1: pd.Series, loc2: pd.Series, loc3: pd.Series,
                            output_path: str, plot_name: str):
        """
        Covered consumption.
        """
        figure, axes = plt.subplots(nrows=1, ncols=1, figsize=(10, 8))
        cons.sort_values(ascending=False).plot(ax=axes, label='Total Consumption', alpha=0.5, linewidth=2.5, use_index=False)
        prod.sort_values(ascending=False).plot(ax=axes, label='Total Production', alpha=1., linewidth=2.5, use_index=False)
        loc1.sort_values(ascending=False).plot(ax=axes, label='Allocated Production Uniform', alpha=0.7, linestyle='--', use_index=False)
        loc2.sort_values(ascending=False).plot(ax=axes, label='Allocated Production Static', alpha=0.7, linestyle='--', use_index=False)
        loc3.sort_values(ascending=False).plot(ax=axes, label='Allocated Production Dynamic', alpha=0.7, linestyle='--',
                                               grid=True, use_index=False)
        plt.legend()
        figure.savefig(f'{output_path}/{plot_name}.pdf')
        plt.close(figure)

    @property
    def min_ssr_user(self):
        return self._min_ssr_user

    @min_ssr_user.setter
    def min_ssr_user(self, value):
        self._min_ssr_user = value
