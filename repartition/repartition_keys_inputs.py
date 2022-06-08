import json
import logging

import numpy as np
import pandas as pd

from .utils import read_data

EPS = 1e-4  # Numerical tolerance and minimum slack value.


class UserInputException(Exception):
    pass


class RepartitionKeysInputs:
    """
    Inputs of the repartition key problem
    """

    def __init__(self, consumption_path: str, initial_keys_path: str, output_path: str, input_options_path: str = None,
                 production_path: str = None):

        # Read data
        self.data_consumption: pd.DataFrame = read_data(consumption_path)
        self.users = self.data_consumption.columns

        if production_path is None:
            self.data_net_consumption: pd.DataFrame = self.data_consumption.copy(deep=False)
            self.data_production = pd.DataFrame()
        else:
            self.data_production: pd.DataFrame = read_data(production_path)
            self.data_net_consumption: pd.DataFrame = self.data_consumption.add(self.data_production, fill_value=0)

            # Fill with zeroes all the users not present in the production file
            users_already_present = self.data_production.columns
            users_to_add = [u for u in self.users if u not in users_already_present]
            for user in users_to_add:
                self.data_production.insert(0, user, 0.0)

        # Optional inputs
        if input_options_path:
            with open(input_options_path, 'r') as f:
                input_options = json.loads(f.read())
        else:
            input_options = {}

        _default_price_retailer_in = input_options.get('default_price_retailer_in', 220)
        self.price_retailer_in = self._retrieve_input_dict(
            input_options, 'price_retailer_in', _default_price_retailer_in, self.users, message=f"""The price of
"price_retailer_in" must be strictly positive, its given value has been replaced by {EPS}."""
        )
        _default_price_retailer_out = input_options.get('default_price_retailer_out', 60)
        self.price_retailer_out = self._retrieve_input_dict(
            input_options, 'price_retailer_out', _default_price_retailer_out, self.users, message=f"""The price of
"price_retailer_out" must be strictly positive, its given value has been replaced by {EPS}."""
        )
        _default_price_local_in = input_options.get('default_price_local_in', 172)
        self.price_local_in = self._retrieve_input_dict(
            input_options, 'price_local_in', _default_price_local_in, self.users, message=f"""The price of
"price_retailer_out" must be strictly positive, its given value has been replaced by {EPS}."""
        )
        _default_price_local_out = input_options.get('default_price_local_out', 100)
        self.price_local_out = self._retrieve_input_dict(
            input_options, 'price_local_out', _default_price_local_out, self.users, message=f"""The price of
"price_retailer_out" must be strictly positive, its given value has been replaced by {EPS}."""
        )
        _default_price_deviation_energy = input_options.get('default_price_deviation_energy', 0.1)
        self.price_deviation_energy = self._retrieve_input_dict(
            input_options, 'price_deviation_energy', _default_price_deviation_energy, self.users, message=f"""The price
of "price_deviation_energy" must be strictly positive, its given value has been replaced by {EPS}."""
        )
        _default_price_allocated_energy = input_options.get('default_price_allocated_energy', 0.1)
        self.price_allocated_energy = self._retrieve_input_dict(
            input_options, 'price_allocated_energy', _default_price_allocated_energy, self.users, message=f"""The price
of "price_allocated_energy" must be strictly positive, its given value has been replaced by {EPS}."""
        )

        # Slack costs
        self.slack_costs = input_options.get('slack_costs', 1e5)

        # Fill min_ssr_user and min_ssr_rec
        _default_min_ssr_user = input_options.get('default_min_ssr_user', 0.0)
        self.minimum_ssr_user = self._retrieve_input_dict(input_options, 'min_ssr_user', _default_min_ssr_user,
                                                          self.users)
        self.minimum_ssr_rec = input_options.get('min_ssr_rec', 0.0)

        # Fill max_deviation
        _default_max_deviation = input_options.get('default_max_deviation', 1.0)
        self.max_deviations = self._retrieve_input_dict(input_options, 'max_deviation', _default_max_deviation,
                                                        self.users)

        # Scaling
        try:
            for user_name, scaling_factor in input_options['scaling'].items():
                try:
                    self.data_net_consumption[user_name] *= scaling_factor
                except KeyError:
                    raise UserInputException(f'Unknown user {user_name} in scaling factors.')
                except:
                    raise UserInputException(f'Invalid scaling factor {scaling_factor} for user {user_name}.')
        except KeyError:
            pass

        # Consumption by-products
        self.consumption = self.data_net_consumption.clip(lower=0.0)
        self.production = -self.data_net_consumption.clip(upper=0.0)
        self.consumption_total = self.consumption.sum(axis=1)
        self.production_total = -self.production.sum(axis=1)
        self.consumption_local = self._compute_local_consumption()

        # Initial keys
        self.initial_keys_path = initial_keys_path
        self.initial_keys: pd.DataFrame = self._parse_initial_keys()

        # Initial allocation of production
        self.initial_allocated_production = self._compute_initial_allocated_production()
        # Output path
        self.output_path = output_path

        # Auxiliary variables
        self._keys = None

    def _parse_initial_keys(self, ) -> pd.DataFrame:
        """
        Parse the initial keys file. If the input file contains a single row, transform it into a time series of keys.

        :return: Initial keys.
        """
        if self.initial_keys_path == 'uniform':  # Create uniform keys
            keys = self._compute_uniform_keys()
        elif self.initial_keys_path == 'proportional_static':  # Create proportional static keys
            keys = self._compute_proportional_static_keys()
        elif self.initial_keys_path == 'proportional_dynamic':  # Create proportional dynamic keys
            keys = self._compute_proportional_dynamic_keys()
        else:
            # Try reading time series keys
            keys: pd.DataFrame = read_data(self.initial_keys_path)

            # If single row keys, transform it into a keys time series
            if len(keys.index) == 1:
                base_keys = pd.read_csv(self.initial_keys_path)
                base_key_users = list(base_keys.columns)
                keys = pd.DataFrame(index=self.consumption.index, columns=base_key_users)
                keys[base_key_users] = base_keys.values

        return keys

    def _compute_uniform_keys(self) -> pd.DataFrame:
        """
        Computes the initial keys according to the principle of uniformity among the participants of a renewable energy
        community.

        :return: Initial keys.
        """
        not_consumers = list()
        for name, value in (self.consumption.max()).iteritems():
            if value <= EPS:
                not_consumers.append(name)

        keys_aux = np.empty(self.consumption.shape)
        keys_aux[:] = 1 / (len(self.users) - len(not_consumers))
        self._keys = pd.DataFrame(index=self.data_net_consumption.index, columns=self.users, data=keys_aux)
        self._keys[not_consumers] = 0.0

        return self._keys

    def _compute_proportional_static_keys(self) -> pd.DataFrame:
        """
        Computes the initial keys according to the principle of yearly proportionality of a consumer's demand and the
        total demand of the renewable energy community.

        :return: Initial keys.
        """
        total_consumption_users = self.consumption.sum(axis=0)
        total_consumption_system = total_consumption_users.sum()
        self._keys = pd.DataFrame(index=self.data_net_consumption.index, columns=self.users)
        for user in self.users:
            self._keys[user] = total_consumption_users[user] / total_consumption_system

        return self._keys

    def _compute_proportional_dynamic_keys(self) -> pd.DataFrame:
        """
        Computes the initial keys according to the principle of quarterly proportionality of a consumer's demand and the
        total demand of the renewable energy community.

        :return: Initial keys.
        """
        total_consumption_system = self.consumption.sum(axis=1)
        self._keys = pd.DataFrame(index=self.data_net_consumption.index, columns=self.users)
        for timestamp, users in self.consumption.iterrows():
            if total_consumption_system[timestamp] <= EPS:
                value = EPS
            else:
                value = total_consumption_system[timestamp]
            self._keys.loc[timestamp] = users / value

        return self._keys

    def _compute_local_consumption(self) -> pd.DataFrame:
        """
        Computes the part of the consumption covered from locally produced energy.

        :return: Proportion of the consumption covered by the local generation.
        """
        net_consumption_production = self.consumption_total.subtract(self.production_total).clip(lower=0.0)
        consumption_local = self.consumption_total.subtract(net_consumption_production).clip(lower=0.0)

        return consumption_local

    def _compute_initial_allocated_production(self) -> pd.DataFrame:
        """
        Computes the initial allocation of the production given the initial keys.

        :return: Initial allocation of production.
        """
        index = self.initial_keys.index
        initial_allocated_production = pd.DataFrame(index=index, columns=self.users)
        production_sum = self.production.sum(axis=1)
        for u in self.users:
            initial_allocated_production.loc[:, u] = self.initial_keys.loc[:, u] * production_sum

        return initial_allocated_production

    @staticmethod
    def _retrieve_input_dict(inputs: dict, parameter: str, default_value: float, list_users: list,
                             message=None) -> dict:
        """
        Retrieves a dictionary of values.

        :return: Dictionary with values.
        """
        dict_values = {user: default_value for user in list_users}
        try:
            for _user_name, _value in inputs[parameter].items():
                if _user_name not in list_users:
                    raise UserInputException(f'Unknown user {_user_name} in {parameter}.')
                else:
                    dict_values[_user_name] = _value
        except:
            pass

        if message:
            for key, value in dict_values.items():
                if value <= 0.0:
                    logging.warning(message)
                    dict_values[key] = EPS

        return dict_values
