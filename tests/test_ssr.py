import os
import unittest

from repartition.repartition_keys_inputs import RepartitionKeysInputs
from repartition.optimizer import Optimizer, SolverException
from repartition.cost_analysis import CostAnalysis
from repartition.plotter import Plotter
from repartition.utils import save_df_dict


class TestSSR(unittest.TestCase):

    def setUp(self):
        # Set the working directory to the root
        os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.solver = 'cbc'
        self.debug = False
        self.working_path = 'tests/test_output'

    def test_ssr_user_default(self):
        # Required inputs
        test_data_folder = "tests/data/ssr_user_default"  # Data corresponding to 1 week.
        path_consumption = f'{test_data_folder}/consumption.csv'
        path_production = f'{test_data_folder}/production.csv'
        input_options = f'{test_data_folder}/inputs.json'
        initial_keys = 'proportional_static'

        # Create output folder
        os.makedirs(self.working_path, exist_ok=True)

        # Create inputs
        inputs = RepartitionKeysInputs(
            consumption_path=path_consumption,
            production_path=path_production,
            initial_keys_path=initial_keys,
            output_path=self.working_path,
            input_options_path=input_options
        )

        # Optimize
        optimizer = Optimizer(solver_name=self.solver, is_debug=self.debug)
        results = optimizer.optimization_keys(inputs)

        # Cost analysis
        analysis = CostAnalysis(inputs, results)
        analysis.analyze()

        # Plot results
        plotter = Plotter(analysis, self.working_path)
        plotter.plot_online_series()

        # Save results
        save_df_dict(results, self.working_path)
        save_df_dict(
            {
                f'initial_keys': inputs.initial_keys,
                f'initial_allocated_production': inputs.initial_allocated_production,
                f'consumption': inputs.consumption_total,
                f'production': inputs.production_total,
                f'self_consumption': analysis.self_consumption,
                f'global_sales': analysis.global_sales
            },
            self.working_path
        )

    def test_ssr_user_individual(self):
        # Required inputs
        test_data_folder = "tests/data/ssr_user_individual"  # Data corresponding to 1 week.
        path_consumption = f'{test_data_folder}/consumption.csv'
        path_production = f'{test_data_folder}/production.csv'
        input_options = f'{test_data_folder}/inputs.json'
        initial_keys = 'proportional_static'

        # Create output folder
        os.makedirs(self.working_path, exist_ok=True)

        # Create inputs
        inputs = RepartitionKeysInputs(
            consumption_path=path_consumption,
            production_path=path_production,
            initial_keys_path=initial_keys,
            output_path=self.working_path,
            input_options_path=input_options
        )

        # Optimize
        optimizer = Optimizer(solver_name=self.solver, is_debug=self.debug)
        results = optimizer.optimization_keys(inputs)

        # Cost analysis
        analysis = CostAnalysis(inputs, results)
        analysis.analyze()

        # Plot results
        plotter = Plotter(analysis, self.working_path)
        plotter.plot_online_series()

        # Save results
        save_df_dict(results, self.working_path)
        save_df_dict(
            {
                f'initial_keys': inputs.initial_keys,
                f'initial_allocated_production': inputs.initial_allocated_production,
                f'consumption': inputs.consumption_total,
                f'production': inputs.production_total,
                f'self_consumption': analysis.self_consumption,
                f'global_sales': analysis.global_sales
            },
            self.working_path
        )

    def test_ssr_rec(self):
        # Required inputs
        test_data_folder = "tests/data/ssr_rec"  # Data corresponding to 1 week.
        path_consumption = f'{test_data_folder}/consumption.csv'
        path_production = f'{test_data_folder}/production.csv'
        input_options = f'{test_data_folder}/inputs.json'
        initial_keys = 'proportional_static'

        # Create output folder
        os.makedirs(self.working_path, exist_ok=True)

        # Create inputs
        inputs = RepartitionKeysInputs(
            consumption_path=path_consumption,
            production_path=path_production,
            initial_keys_path=initial_keys,
            output_path=self.working_path,
            input_options_path=input_options
        )

        # Optimize
        optimizer = Optimizer(solver_name=self.solver, is_debug=self.debug)
        self.assertRaises(SolverException, optimizer.optimization_keys, inputs)

    def test_price_retailer_out_individual(self):
        # Required inputs
        test_data_folder = "tests/data/price_local_out_individual"  # Data corresponding to 1 week.
        path_consumption = f'{test_data_folder}/consumption.csv'
        path_production = f'{test_data_folder}/production.csv'
        input_options = f'{test_data_folder}/inputs.json'
        initial_keys = 'proportional_static'

        # Create output folder
        os.makedirs(self.working_path, exist_ok=True)

        # Create inputs
        inputs = RepartitionKeysInputs(
            consumption_path=path_consumption,
            production_path=path_production,
            initial_keys_path=initial_keys,
            output_path=self.working_path,
            input_options_path=input_options
        )

        # Optimize
        optimizer = Optimizer(solver_name=self.solver, is_debug=self.debug)
        results = optimizer.optimization_keys(inputs)

        # Cost analysis
        analysis = CostAnalysis(inputs, results)
        analysis.analyze()

        # Plot results
        plotter = Plotter(analysis, self.working_path)
        plotter.plot_online_series()

        # Save results
        save_df_dict(results, self.working_path)
        save_df_dict(
            {
                f'initial_keys': inputs.initial_keys,
                f'initial_allocated_production': inputs.initial_allocated_production,
                f'consumption': inputs.consumption_total,
                f'production': inputs.production_total,
                f'self_consumption': analysis.self_consumption,
                f'global_sales': analysis.global_sales
            },
            self.working_path
        )

    def test_ssr_rec_check(self):
        # Required inputs
        test_data_folder = "tests/data/ssr_rec_check"
        path_consumption = f'{test_data_folder}/consumption.csv'
        path_production = f'{test_data_folder}/production.csv'
        input_options = f'{test_data_folder}/inputs.json'
        initial_keys = 'proportional_static'

        # Create output folder
        os.makedirs(self.working_path, exist_ok=True)

        # Create inputs
        inputs = RepartitionKeysInputs(
            consumption_path=path_consumption,
            production_path=path_production,
            initial_keys_path=initial_keys,
            output_path=self.working_path,
            input_options_path=input_options
        )

        # Optimize
        optimizer = Optimizer(solver_name=self.solver, is_debug=self.debug)
        results = optimizer.optimization_keys(inputs)

        # Cost analysis
        analysis = CostAnalysis(inputs, results)
        analysis.analyze()

        # Plot results
        plotter = Plotter(analysis, self.working_path)
        plotter.plot_online_series()

        # Save results
        save_df_dict(results, self.working_path)
        save_df_dict(
            {
                f'initial_keys': inputs.initial_keys,
                f'initial_allocated_production': inputs.initial_allocated_production,
                f'consumption': inputs.consumption_total,
                f'production': inputs.production_total,
                f'self_consumption': analysis.self_consumption,
                f'global_sales': analysis.global_sales
            },
            self.working_path
        )

    def test_four_users(self):
        # Required inputs
        test_data_folder = "tests/data/four_users"  # Data corresponding to 2 time-steps.
        path_consumption = f'{test_data_folder}/consumption.csv'
        path_production = f'{test_data_folder}/production.csv'
        input_options = f'{test_data_folder}/inputs.json'
        initial_keys = 'proportional_static'

        # Create output folder
        if not os.path.exists(self.working_path):
            os.makedirs(self.working_path, exist_ok=True)

        # Create inputs
        inputs = RepartitionKeysInputs(
            consumption_path=path_consumption,
            production_path=path_production,
            initial_keys_path=initial_keys,
            output_path=self.working_path,
            input_options_path=input_options
        )

        # Optimize
        optimizer = Optimizer(solver_name=self.solver, is_debug=self.debug)
        results = optimizer.optimization_keys(inputs)

        # Cost analysis
        analysis = CostAnalysis(inputs, results)
        analysis.analyze()

        # Save results
        save_df_dict(results, self.working_path)
        save_df_dict(
            {
                'initial_keys': inputs.initial_keys,
                'initial_allocated_production': inputs.initial_allocated_production,
                'consumption': inputs.consumption_total,
                'production': inputs.production_total,
                'self_consumption': analysis.self_consumption,
                'global_sales': analysis.global_sales
            },
            self.working_path
        )

    def test_three_users(self):
        # Required inputs
        test_data_folder = "tests/data/three_users"  # Data corresponding to 2 time-steps.
        path_consumption = f'{test_data_folder}/consumption.csv'
        path_production = f'{test_data_folder}/production.csv'
        input_options = f'{test_data_folder}/inputs.json'
        initial_keys = 'proportional_static'

        # Create output folder
        if not os.path.exists(self.working_path):
            os.makedirs(self.working_path, exist_ok=True)

        # Create inputs
        inputs = RepartitionKeysInputs(
            consumption_path=path_consumption,
            production_path=path_production,
            initial_keys_path=initial_keys,
            output_path=self.working_path,
            input_options_path=input_options
        )

        # Optimize
        optimizer = Optimizer(solver_name=self.solver, is_debug=self.debug)
        results = optimizer.optimization_keys(inputs)

        # Cost analysis
        analysis = CostAnalysis(inputs, results)
        analysis.analyze()

        # Save results
        save_df_dict(results, self.working_path)
        save_df_dict(
            {
                'initial_keys': inputs.initial_keys,
                'initial_allocated_production': inputs.initial_allocated_production,
                'consumption': inputs.consumption_total,
                'production': inputs.production_total,
                'self_consumption': analysis.self_consumption,
                'global_sales': analysis.global_sales
            },
            self.working_path
        )
