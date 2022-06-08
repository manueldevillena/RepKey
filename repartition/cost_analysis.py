import pandas as pd

from typing import Dict

from .repartition_keys_inputs import RepartitionKeysInputs


class CostAnalysis:
    """
    Performs the cost analysis of the results.
    """

    def __init__(self, inputs: RepartitionKeysInputs, results_optimization: Dict[str, pd.DataFrame],
                 local_discount: float = 0.40):

        self.local_discount = local_discount
        self.delta_costs = None
        self.ssr_user_no_production = None
        self.global_sales = None
        self.self_consumption = None
        self.cost_users = None
        self.cost_users_no_deviation = None
        self.costs_users_no_rec = None
        self.min_ssr_user = pd.Series(inputs.minimum_ssr_user)[0]

        # Auxiliary variables
        self._users = inputs.users
        self._output_path = inputs.output_path
        self._initial_consumption = inputs.data_consumption
        self._net_consumption = inputs.consumption
        self._net_production = inputs.production
        self._locally_sold_production = results_optimization['locally_sold_production']
        self._allocated_production = results_optimization['allocated_production']
        self._verified_allocated_production = results_optimization['verified_allocated_production']
        self._ssr_user = results_optimization['ssr_user']
        self._costs_rec = results_optimization['objective']

        # Electricity prices
        self._price_retailer_in = inputs.price_retailer_in
        self._price_local_in = inputs.price_local_in
        self._price_retailer_out = inputs.price_retailer_out
        self._price_local_out = inputs.price_local_out

    def analyze(self):
        """
        Performs the cost analysis.
        """
        self._compute_costs_comparison()
        self._compute_coverage_rate()
        self._compute_globally_sold_production()
        self._compute_self_consumption()
        self._compute_costs()

        self._save_result(self.delta_costs, 'delta_costs', self._output_path)
        self._save_result(self.ssr_user_no_production, 'ssr_user_no_production', self._output_path)
        self._save_result(self.cost_users_no_deviation, 'costs_users_no_deviations', self._output_path)
        self._save_result(self.cost_users, 'costs_users', self._output_path)
        self._save_result(self.costs_users_no_rec, 'costs_users', self._output_path)

    def _compute_costs_comparison(self):
        """
        Compares the costs with and without REC for each user.
        """
        self.delta_costs = (
            (1 - self.local_discount) * self._ssr_user
        )

    def _compute_coverage_rate(self):
        """
        Computes the coverage rate of the users.
        """
        self.ssr_user_no_production = (
            self._verified_allocated_production.sum(axis=0) / self._initial_consumption.sum(axis=0)
        ).fillna(0.0)  # Self-sufficiency rate without taking into account the production

    def _compute_globally_sold_production(self):
        """
        Computes the global sales of the producers.
        """
        self.global_sales = (
            self._net_production - self._locally_sold_production
        )

    def _compute_self_consumption(self):
        """
        Computes the self-consumption of prosumers.
        """
        self.self_consumption = (
            self._initial_consumption - self._net_consumption
        )

    def _compute_costs(self):
        """
        Computes the costs of each consumer or prosumer independently.
        """
        self.cost_users_no_deviation = (
                pd.Series(self._price_retailer_in) * (self._net_consumption - self._verified_allocated_production).sum(axis=0) +
                pd.Series(self._price_local_in) * self._verified_allocated_production.sum(axis=0) -
                pd.Series(self._price_retailer_out) * (self._net_production - self._locally_sold_production).sum(axis=0) -
                pd.Series(self._price_local_out) * self._locally_sold_production.sum(axis=0)
        )
        costs_deviations = (self._costs_rec - self.cost_users_no_deviation.sum()) / len(self._users)
        self.cost_users = self.cost_users_no_deviation + costs_deviations.values
        self.costs_users_no_rec = (
                pd.Series(self._price_retailer_in) * self._net_consumption.sum(axis=0) -
                pd.Series(self._price_retailer_out) * self._net_production.sum(axis=0)
        )

    @staticmethod
    def _save_result(which_data: pd.DataFrame, name: str, output_path: str):
        """
        Saves the cost-comparison result.
        """
        df_to_save = pd.DataFrame(data=which_data)
        df_to_save.to_csv(f'{output_path}/{name}.csv', header=[name])
