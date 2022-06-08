from typing import Dict

import numpy as np
import pandas as pd


class ParsingException(Exception):
    def __init__(self, indexes: list):
        super().__init__()
        self.indexes = indexes

    def __str__(self):
        return "Invalid values at indexes:\n\t" + '\n\t'.join(map(str, self.indexes))


def read_data(path: str) -> pd.DataFrame:
    """
    Reads the data needed to compute the repartition of keys.

    @param path: Path with the data to read.
    @return Data frame with the read data.
    """
    df = pd.read_csv(path, header=0, index_col=0, parse_dates=True, infer_datetime_format=True, dtype=float)
    null_loc, _ = np.where(df.isna())
    if len(null_loc) != 0:
        raise ParsingException(indexes=df.index[null_loc])
    return df


def save_df_dict(d: Dict[str, pd.DataFrame], path_prefix: str = '.'):
    """
    Save each data frame of the dictionary into separate csv files named after their key.

    @param d: Dictionary of data frames.
    @param path_prefix: Path prefix to the output path.
    """
    for key, item in d.items():
        if key == 'production_total':
            item.to_csv(f'{path_prefix}/{key}.csv', header=['Total Production'])
        elif key == 'ssr':
            item.to_csv(f'{path_prefix}/{key}.csv', header=['Self-sufficiency rate'])
        else:
            item.to_csv(f'{path_prefix}/{key}.csv', header=True)


def multiply_data_frames(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """
    Multiplies two data frames column by column.

    @param df1: Data frame 1.
    @param df2: Data frame 2.
    """
    return df1.multiply(df2, axis=0)


def divide_data_frames(df1: pd.DataFrame, df2: pd.DataFrame, clipping: bool = False) -> pd.DataFrame:
    """
    Divides two data frames replacing infinite values and NaN by zeroes.

    @param df1: Data frame acting as numerator.
    @param df2: Data frame acting as denominator.
    @param clipping: Boolean true to clip with an upper bound of 1.0.
    @return: Data frame.
    """
    df1_post_processed = df1.replace(0, int(0))
    df2_post_processed = df2.replace(0, np.nan)
    if clipping:
        return df1_post_processed.divide(df2_post_processed, fill_value=0.0, axis=0).replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(upper=1.0)
    else:
        return df1_post_processed.divide(df2_post_processed, fill_value=0.0, axis=0).fillna(0.0)


def compute_spillage(served_energy: pd.DataFrame, total_demand: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the spilled production due to incorrect assignment of keys.

    @param served_energy: Served energy data frame, one column per client and row per time period.
    @param total_demand: Total demand data frame, one column per client and row per time period.
    """
    spilled_production = divide_data_frames(served_energy, total_demand, clipping=False)
    spilled_production[spilled_production <= 1] = 0
    spilled_production[spilled_production == np.inf] = 1

    for col in total_demand.columns:
        indices = spilled_production[col][spilled_production[col] > 1].index
        for ind in indices:
            spilled_production[col][ind] = 1 - (1 / spilled_production[col][ind])

    return spilled_production
