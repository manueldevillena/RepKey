import argparse
import os
import time
import sys

from .repartition_keys_inputs import RepartitionKeysInputs, UserInputException
from .optimizer import Optimizer, SolverException
from .cost_analysis import CostAnalysis
from .plotter import Plotter
from .utils import save_df_dict, ParsingException

import warnings
warnings.simplefilter(action='ignore', category=UserWarning)


if __name__ == "__main__":

    # Create variable inputs
    inputs = None

    # Argument parsing
    parser = argparse.ArgumentParser(description="Parses the inputs for the module to run.")
    parser.add_argument('data_consumption', help="Input consumption profiles.")
    parser.add_argument('-dp', '--data_production', dest='data_production', help="Input production profiles.")
    parser.add_argument('-k', '--initial_keys', dest='initial_keys',
                        help="Type of initial keys to use: uniform, proportional_static, or proportional_dynamic.",
                        default='uniform')
    parser.add_argument('-i', '--input_options', dest='input_options',
                        help="""json file with several options: price_retailer_in, price_retailer_out, price_local_in,
                        price_local_out, price_deviation_energy, max_deviation, default_max_deviation, min_ssr_user,
                        default_min_ssr_user, min_ssr_rec, scaling_factor, or slack_costs. More info can be found on the
                        README.""")
    parser.add_argument('-s', '--solver', dest='solver', help="Solver name (cbc, cplex ...)", default='cbc')
    parser.add_argument('-o', '--output', dest='output_path', default='.', type=str, help="Output path")
    parser.add_argument('-p', '--plot', dest='is_plot', action='store_true', help="Plot flag")
    parser.add_argument('-d', '--debug', dest='is_debug', action='store_true', help="Debug mode")
    parser.add_argument('-v', '--verbose', dest='is_verbose', action='store_true', help="Verbose mode")

    args = parser.parse_args()

    # Prepare output path
    os.makedirs(args.output_path, exist_ok=True)

    # Read input files
    tic = time.time()
    try:
        inputs = RepartitionKeysInputs(
            consumption_path=args.data_consumption,
            production_path=args.data_production,
            initial_keys_path=args.initial_keys,
            output_path=args.output_path,
            input_options_path=args.input_options
        )
    except (ParsingException, UserInputException) as e:
        print(e, file=sys.stderr)
        exit(1)

    if args.is_verbose:
        print(f"Input files read in {time.time() - tic:.2f} seconds.")

    # Optimize
    optimizer = Optimizer(solver_name=args.solver, is_debug=args.is_debug)
    tic = time.time()
    try:
        results = optimizer.optimization_keys(inputs)
    except SolverException as e:
        print(e, file=sys.stderr)
        exit(1)

    # Cost analysis
    analysis = CostAnalysis(inputs, results)
    analysis.analyze()

    if args.is_verbose:
        print(f"Repartition keys optimized in {time.time() - tic:.2f} seconds.")

    # Save results
    save_df_dict(results, args.output_path)
    save_df_dict(
        {
            'initial_keys': inputs.initial_keys,
            'initial_allocated_production': inputs.initial_allocated_production,
            'consumption': inputs.consumption_total,
            'production': inputs.production_total,
            'self_consumption': analysis.self_consumption,
            'global_sales': analysis.global_sales
         },
        args.output_path
    )

    if args.is_plot:
        plotter = Plotter(analysis, args.output_path)
        plotter.plot_online_series()

    if args.is_verbose:
        print(f'Results saved in "{args.output_path}".')
