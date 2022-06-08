import matplotlib.pyplot as plt
import pandas as pd


def plot_ldc(data_raw, ldc_consumption, ldc_residual):
    """
    Plots load duration curves.

    :param data_raw: Raw data of consumption timeseries.
    :param ldc_consumption: Load duration curve of aggregated consumption.
    :param ldc_residual: Load duration curve of aggregated consumption minus production.
    """
    figure, axes = plt.subplots(nrows=1, ncols=1, figsize=(10, 7))
    axes.plot(ldc_consumption.values, linewidth=2, color='red', alpha=0.7)
    axes.plot(ldc_residual.values, linewidth=2, color='green', alpha=0.7)
    axes.plot(data_raw, linewidth=1.0, color='blue', alpha=0.2)
    axes.grid()
    axes.legend(['Aggregated consumption', 'Residual consumption', 'Raw consumption'])
    plt.xlabel('Time [quarter hours (15 min)]')
    plt.ylabel('Consumption [kWh]')
    figure.savefig('consumption_production.pdf')
    plt.close(figure)


def plot_consumption(data_raw, range_zoom=None):
    """
    Plots raw consumption data
    """
    df_to_plot = pd.DataFrame(columns=['User{}'.format(i) for i in range(1, 6)], index=data_raw.index,
                              data=data_raw.values)
    figure, axes = plt.subplots(nrows=1, ncols=1, figsize=(10, 8))
    if range_zoom is not None:
        df_to_plot[range_zoom:range_zoom+250].plot(ax=axes, linewidth=1, alpha=0.7, rot=10, grid=True)
    else:
        df_to_plot.plot(ax=axes, linewidth=0.3, alpha=0.7, rot=10, grid=True)
    plt.xlabel('Time [quarter hours (15 min)]')
    plt.ylabel('Consumption [kWh]')
    figure.savefig('consumption_raw.pdf')
    plt.close(figure)


if __name__ == "__main__":
    path_consumption = 'data/case_study_c/consumption.csv'
    path_production = 'data/case_study_c/production.csv'
    consumption = pd.read_csv(path_consumption).drop(['time', 'User6'], axis=1) / 4
    consumption_ts = pd.read_csv(path_consumption, index_col=0).drop(['User6'], axis=1) / 4
    consumption_sorted = consumption.sum(axis=1).sort_values(ascending=False)
    production = -pd.read_csv(path_production).drop(['time'], axis=1) / 4
    ldc_data = pd.concat([consumption_sorted, production], axis=1, join='inner')
    consumption_residual = (consumption.sum(axis=1).subtract(production.sum(axis=1))).clip(lower=0).sort_values(ascending=False)

    plot_ldc(consumption, consumption_sorted, consumption_residual)
    plot_consumption(consumption_ts)
    # plot_consumption(consumption_ts, range_zoom=20500)
