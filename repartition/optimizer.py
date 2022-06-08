import pandas as pd
import time

from typing import Dict, List
from logging import getLogger, ERROR

import pyomo.environ as pyo
import numpy as np

from .repartition_keys_inputs import RepartitionKeysInputs

EPS = 1e-6


class SolverException(Exception):
    pass


class Optimizer:
    """
    Contains the optimization programs, processes the output and saves it.
    """

    def __init__(self, solver_name: str = 'cbc', is_debug: bool = False):
        self.solver_name = solver_name
        self.is_debug = is_debug

    def optimization_keys(self, inputs: RepartitionKeysInputs) -> Dict[str, pd.DataFrame]:
        """
        Optimizes the repartition keys.

        @param inputs: Input data structure.
        @return Result dictionary.
        """
        tic = time.time()
        # Remove pyomo warnings
        getLogger('pyomo.core').setLevel(ERROR)

        # Parameters pre-processing
        min_production_demand = pd.concat([inputs.data_consumption, -inputs.data_production]).min(level=0).sum(axis=0)
        total_users_consumption = inputs.data_consumption.sum(axis=0)
        total_community_production = inputs.production.sum(axis=1)

        # Bounds generators
        def _bounds_verified_allocated_production(m, t, u):
            """
            Defines the bounds of the verified allocated production.
            """
            return 0, inputs.consumption.loc[t, u]

        def _locally_sold_production_limit(m, t, u):
            """
            Sets the limit to the locally sold production.
            """
            return 0, inputs.production.loc[t, u]

        # LINEAR PROGRAM
        m = pyo.ConcreteModel()

        # SETS
        m.times = pyo.Set(initialize=[t for t in inputs.data_net_consumption.index])
        m.users = pyo.Set(initialize=[u for u in inputs.data_net_consumption.columns])

        # DECISION VARIABLES
        m.optimized_keys = pyo.Var(m.times, m.users, bounds=(0, 1))
        m.key_deviation_positive = pyo.Var(m.times, m.users, bounds=(0, 1))
        m.key_deviation_negative = pyo.Var(m.times, m.users, bounds=(0, 1))
        m.locally_sold_production = pyo.Var(m.times, m.users, bounds=_locally_sold_production_limit)
        m.allocated_production = pyo.Var(m.times, m.users, within=pyo.NonNegativeReals)
        m.verified_allocated_production = pyo.Var(m.times, m.users, bounds=_bounds_verified_allocated_production)
        m.positive_allocated_deviation = pyo.Var(m.times, within=pyo.NonNegativeReals)
        m.negative_allocated_deviation = pyo.Var(m.times, within=pyo.NonNegativeReals)
        m.ssr_user = pyo.Var(m.users, within=pyo.NonNegativeReals)
        m.ssr_rec = pyo.Var(within=pyo.NonNegativeReals)

        # SLACK VARIABLES
        m.slack_ssr_user = pyo.Var(m.users, within=pyo.NonNegativeReals)
        m.max_slack_ssr_user = pyo.Var(within=pyo.NonNegativeReals)
        m.slack_ssr_rec = pyo.Var(within=pyo.NonNegativeReals)

        # Auxiliary variables
        verified_allocated_production = dict()

        # Objective function
        def _objective_function(m):
            """
            Minimizes the costs of deviating from the assigned keys to maximise the energy use.
            """
            return (
                    pyo.quicksum(
                        pyo.quicksum(
                            (
                                inputs.price_retailer_in[u] * (inputs.consumption.loc[t, u] - m.verified_allocated_production[t, u])
                                + inputs.price_local_in[u] * m.verified_allocated_production[t, u]
                                - inputs.price_local_out[u] * m.locally_sold_production[t, u]
                                - inputs.price_retailer_out[u] * (inputs.production.loc[t, u] - m.locally_sold_production[t, u])
                                + inputs.price_deviation_energy[u] * (m.positive_allocated_deviation[t] + m.negative_allocated_deviation[t])
                                + inputs.price_allocated_energy[u] * m.allocated_production[t, u]
                            )
                            for t in m.times
                        ) for u in m.users
                    )
                    + ((m.max_slack_ssr_user + m.slack_ssr_rec) * inputs.slack_costs * inputs.consumption.sum().sum())
            )

        # Constraints
        def _allocated_production(m, t, u):
            """
            Computes the covered consumption of each user.
            """
            if total_community_production[t] <= EPS:
                return m.allocated_production[t, u] == 0.0
            else:
                return m.allocated_production[t, u] == m.optimized_keys[t, u] * total_community_production[t]

        def _allocated_production_limit(m, t):
            """
            Sets the total allocated production equal to the total locally sold production.
            """
            return (
                    sum(m.verified_allocated_production[t, u] for u in m.users) ==
                    sum(m.locally_sold_production[t, u] for u in m.users)
            )

        def _allocation_positive_deviation(m, t, u):
            """
            Computes the positive deviation from the initially allocated production.
            """
            return (
                    m.allocated_production[t, u] - inputs.initial_allocated_production.loc[t, u] <=
                    m.positive_allocated_deviation[t]
            )

        def _allocation_negative_deviation(m, t, u):
            """
            Computes the negative deviation from the initially allocated production.
            """
            return (
                    inputs.initial_allocated_production.loc[t, u] - m.allocated_production[t, u] <=
                    m.negative_allocated_deviation[t]
            )

        def _verified_allocated_production(m, t, u):
            """
            Computes the energy balance.
            """
            return m.verified_allocated_production[t, u] <= m.allocated_production[t, u]

        def _key_limits(m, t):
            """
            Ensures the the sum of all keys equals to 1.
            """
            return sum(m.optimized_keys[t, u] for u in m.users) <= 1

        def _key_deviation(m, t, u):
            """
            Computes the deviation from the original keys.
            """
            return (
                    m.key_deviation_positive[t, u] - m.key_deviation_negative[t, u] ==
                    m.optimized_keys[t, u] - inputs.initial_keys.loc[t, u]
            )

        def _compute_self_sufficiency_rate_user(m, u):
            """
            Computes the self-sufficiency rate (i.e. the coverage rate) of the users.
            """
            if total_users_consumption[u] <= EPS:
                return m.ssr_user[u] == 1.0  # Filter pure producers

            verified_allocated_production[u] = sum(m.verified_allocated_production[t, u] for t in m.times)

            return m.ssr_user[u] == (
                    (min_production_demand[u] + verified_allocated_production[u]) / total_users_consumption[u]
            )

        def _compute_self_sufficiency_rate_rec(m):
            """
            Computes the self-sufficiency rate (i.e. the coverage rate) of the users.
            """
            min_production_demand_rec = sum(min_production_demand[u] for u in m.users)
            verified_allocated_production_rec = sum(
                sum(m.verified_allocated_production[t, u] for t in m.times)
                for u in m.users)
            total_users_consumption_rec = sum(total_users_consumption[u] for u in m.users)

            return m.ssr_rec == (
                    (min_production_demand_rec + verified_allocated_production_rec) / total_users_consumption_rec
            )

        def _min_self_sufficiency_rate_user(m, u):
            """
            Ensures a minimum self-sufficiency rate (i.e. the coverage rate) of the users.
            """
            if total_users_consumption[u] <= EPS:
                return pyo.Constraint.Skip
            return m.ssr_user[u] + m.slack_ssr_user[u] >= inputs.minimum_ssr_user[u]

        def _compute_max_slack_ssr_user(m, u):
            """
            Computes the value of max_slack_ssr_user.
            """
            return m.max_slack_ssr_user >= m.slack_ssr_user[u]

        def _min_self_sufficiency_rate_rec(m):
            """
            Ensures a minimum self-sufficiency rate (i.e. the coverage rate) of the rec.
            """
            return m.ssr_rec + m.slack_ssr_rec >= inputs.minimum_ssr_rec

        # Max deviation constraints
        m.max_key_deviation_positive_allowed_eqn = pyo.ConstraintList()
        m.max_key_deviation_negative_allowed_eqn = pyo.ConstraintList()
        for u, max_deviation_value in inputs.max_deviations.items():
            for t in m.times:
                m.max_key_deviation_positive_allowed_eqn.add(
                    m.key_deviation_positive[t, u] <= max_deviation_value
                )
                m.max_key_deviation_negative_allowed_eqn.add(
                    m.key_deviation_negative[t, u] <= max_deviation_value
                )

        # CALL THE CONSTRAINTS
        m.objective_eqn = pyo.Objective(rule=_objective_function, sense=pyo.minimize)
        m._allocated_production_eqn = pyo.Constraint(m.times, m.users, rule=_allocated_production)
        m._allocated_production_limit_eqn = pyo.Constraint(m.times, rule=_allocated_production_limit)
        m._allocation_positive_deviation_eqn = pyo.Constraint(m.times, m.users, rule=_allocation_positive_deviation)
        m._allocation_negative_deviation_eqn = pyo.Constraint(m.times, m.users, rule=_allocation_negative_deviation)
        m._verified_allocated_production_eqn = pyo.Constraint(m.times, m.users, rule=_verified_allocated_production)
        m.key_limits_eqn = pyo.Constraint(m.times, rule=_key_limits)
        m._key_deviation_eqn = pyo.Constraint(m.times, m.users, rule=_key_deviation)
        m._compute_self_sufficiency_rate_user_eqn = pyo.Constraint(m.users, rule=_compute_self_sufficiency_rate_user)
        m._compute_self_sufficiency_rate_rec_eqn = pyo.Constraint(rule=_compute_self_sufficiency_rate_rec)
        m._min_self_sufficiency_rate_user_eqn = pyo.Constraint(m.users, rule=_min_self_sufficiency_rate_user)
        m._min_self_sufficiency_rate_rec_eqn = pyo.Constraint(rule=_min_self_sufficiency_rate_rec)
        m._compute_max_slack_ssr_user_eqn = pyo.Constraint(m.users, rule=_compute_max_slack_ssr_user)

        # SOLVE THE PROBLEM
        if self.is_debug:
            print(f"Optimization model built in {time.time() - tic:.2f} seconds.")
            m.write('optim.lp', io_options={'symbolic_solver_labels': True})
        opt = pyo.SolverFactory(self.solver_name)
        tic = time.time()
        results = opt.solve(m, tee=self.is_debug, keepfiles=False)
        print(f"Optimization model solved in {time.time() - tic:.2f} seconds")
        if (results.solver.status != pyo.SolverStatus.ok
                or results.solver.termination_condition not in {
                    pyo.TerminationCondition.optimal,
                    pyo.TerminationCondition.feasible
                }
        ):
            m.write("debug.lp", io_options={'symbolic_solver_labels': True})
            raise ValueError(f"""Problem not properly solved (status: {results.solver.status}, 
                termination condition: {results.solver.termination_condition}).""")

        min_ssr_rec_given = inputs.minimum_ssr_rec
        max_ssr_rec_feasible = m.ssr_rec.value
        slack_rec = m.slack_ssr_rec.value

        slack_users = {u: m.slack_ssr_user[u].value for u in m.users}
        unfeasible_users = {u: v for u, v in slack_users.items() if v > EPS}

        if len(unfeasible_users) > 0:
            raise SolverException(f"""The problem is infeasible for the given input value of min_ssr_user (or
            default_min_ssr_user) for users {', '.join(map(str, unfeasible_users))}. 
            The given value was {', '.join([f'{inputs.minimum_ssr_user[u]:.3f}' for u in unfeasible_users])}. 
            Try with a value <= {', '.join([f'{m.ssr_user[u].value:.3f}' for u in unfeasible_users])}.""")

        if slack_rec > EPS:
            raise SolverException(f"""The problem is infeasible for the given input value of min_ssr_rec. The given
            value was {min_ssr_rec_given}, however, the maximum feasible value for this variable is
            {max_ssr_rec_feasible}. Try with a value <= {max_ssr_rec_feasible}.""")

        # Output results
        return self._process_results(m)

    @classmethod
    def _process_results(cls, model: pyo.ConcreteModel) -> Dict[str, pd.DataFrame]:
        """
        Retrieves the results of the optimization.
        """
        # Extract from model
        output = cls._retrieve_data(
            model,
            ['optimized_keys', 'allocated_production', 'verified_allocated_production', 'locally_sold_production',
             'ssr_user', 'ssr_rec', 'objective']
        )

        return output

    @staticmethod
    def _retrieve_data(model: pyo.ConcreteModel, attributes: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Retrieves the optimised keys.

        :param model: LP model with the data.
        :param attributes: List of attributes to extract.
        :return: Dictionary with the desired date.
        """

        output = dict()
        for variable_name in attributes:
            if variable_name == 'objective':
                output_data = pd.Series(model.objective_eqn.expr())
            else:
                try:
                    data = getattr(model,
                                   variable_name).get_values()  # Get the value of the variable with the same name
                except AttributeError:
                    raise AttributeError(
                        """The argument "variable" only accepts "optimized_keys", "allocated_consumption",
                        "verified_allocated_consumption", "locally_sold_production", "ssr_user" or "ssr_rec",
                        otherwise leave it empty."""
                    )
                output_data = pd.Series(data)
                if type(output_data.index) == pd.core.indexes.multi.MultiIndex:
                    output_data = output_data.unstack()

            output[f'{variable_name}'] = output_data

        return output
