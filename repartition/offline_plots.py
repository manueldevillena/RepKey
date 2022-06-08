import numpy as np
import os
import pandas as pd

from repartition.plotter import Plotter

if __name__ == "__main__":

    plot = Plotter()

    retailer_in = 220.
    retailer_out = 60.
    local_in = 100.
    local_out = 98.
    conversion_factor = 4000 # 250000

    consumption = pd.read_csv('data/one_year_paper/consumption.csv', index_col=0)
    production = -pd.read_csv('data/one_year_paper/production_2.csv', index_col=0)

    costs = pd.Series(dtype=np.float64)
    avg_ssr = pd.Series(dtype=np.float64)
    for ssr in ['0.00', '0.33', '0.34', '0.35', '0.38', '0.39', '0.40', '0.41', '0.42']:
        # COST RE-COMPUTATION
        output_path = f'results_paper/sensitivity_ssr_one_year_4/{ssr}/plots'
        verified_production = pd.read_csv(
            f'results_paper/sensitivity_ssr_one_year_4/{ssr}/verified_allocated_production.csv', index_col=0)
        local_sales = pd.read_csv(f'results_paper/sensitivity_ssr_one_year_4/{ssr}/locally_sold_production.csv',
                                  index_col=0)
        costs_retailer = (consumption - verified_production) * retailer_in
        costs_local = verified_production * local_in
        revenue_retailer = (production - local_sales).fillna(0.0) * retailer_out
        revenue_local = local_sales * local_out
        costs_users = costs_retailer + costs_local - revenue_retailer - revenue_local
        costs_users_to_plot = costs_users.sum(axis=0) / conversion_factor

        cost_retailer_no_rec = consumption * retailer_in
        revenue_retailer_no_rec = production * retailer_out
        cost_retailer_no_rec['SOLAR'] = -revenue_retailer_no_rec
        costs_users_no_rec_to_plot = cost_retailer_no_rec.sum(axis=0) / conversion_factor

        plot._plot_series(costs_users_to_plot, output_path, plot_name=f'costs_recomputed_{ssr}', ssr_rec=None,
                          series_2=costs_users_no_rec_to_plot)

        inputs_path = f'/Users/villena/bitbucket/repartition_keys/results_paper/sensitivity_ssr_one_year_4/{ssr}'
        output_path = f'/Users/villena/bitbucket/repartition_keys/results_paper/sensitivity_ssr_one_year_4/{ssr}/plots'
        min_ssr_user = float(ssr)
        # INDIVIDUAL SSR
        ssr_users = pd.read_csv(os.path.join(inputs_path, 'ssr_user.csv'), index_col=0, squeeze=True).drop(['SOLAR'])
        ssr_rec = pd.read_csv(os.path.join(inputs_path, 'ssr_rec.csv'), index_col=0, squeeze=True)
        plot._plot_series(
            ssr_users, output_path, plot_name='enforced_ssr', ssr_plot=float(min_ssr_user), ssr_rec=ssr_rec.mean()
        )

        # INDIVIDUAL COST
        costs_users = pd.read_csv(os.path.join(inputs_path, 'costs_users_no_deviations.csv'), index_col=0,
                                  squeeze=True) / conversion_factor
        plot._plot_series(costs_users, output_path, plot_name='costs')

        # REC's SSR and COSTS
        costs[ssr] = pd.read_csv(os.path.join(inputs_path, 'objective.csv'), index_col=0,
                                 squeeze=True).mean() / conversion_factor
        avg_ssr[ssr] = pd.read_csv(os.path.join(inputs_path, 'ssr_user.csv'), index_col=0,
                                   squeeze=True).drop(['SOLAR']).mean()

    plot.plot_offline_costs(costs, avg_ssr, output_path)

    # COST DIFFERENCE
    verified_production_1 = pd.read_csv(
        f'results_paper/sensitivity_ssr_one_year_4/0.00/verified_allocated_production.csv', index_col=0)
    local_sales_1 = pd.read_csv(f'results_paper/sensitivity_ssr_one_year_4/0.00/locally_sold_production.csv',
                              index_col=0)
    costs_1 = (((consumption.sum(axis=0) - verified_production_1.sum(axis=0)) * retailer_in) +
               ((verified_production_1.sum(axis=0)) * local_in) -
               ((production.sum(axis=0) - local_sales_1.sum(axis=0)).fillna(0.00) * retailer_out) -
               (local_sales_1.sum(axis=0) * local_out)
               ) / conversion_factor
    verified_production_2 = pd.read_csv(
        f'results_paper/sensitivity_ssr_one_year_4/0.42/verified_allocated_production.csv', index_col=0)
    local_sales_2 = pd.read_csv(f'results_paper/sensitivity_ssr_one_year_4/0.42/locally_sold_production.csv',
                                index_col=0)
    costs_2 = (((consumption.sum(axis=0) - verified_production_2.sum(axis=0)) * retailer_in) +
               ((verified_production_2.sum(axis=0)) * local_in) -
               ((production.sum(axis=0) - local_sales_2.sum(axis=0)).fillna(0.00) * retailer_out) -
               (local_sales_2.sum(axis=0) * local_out)
               ) / conversion_factor
    cost_difference = (costs_2 - costs_1) / costs_2 * 100
    plot._plot_offline_series_difference(cost_difference, output_path=output_path, plot_name='cost_difference')

    # CASE C
    folder = 'case_study_c_3'
    consumption = pd.read_csv('data/case_study_c/consumption.csv', index_col=0)
    production = pd.read_csv('data/case_study_c/production.csv', index_col=0)
    costs_users_deviations_uniform = pd.DataFrame()
    costs_users_deviations_static = pd.DataFrame()
    costs_users_deviations_dynamic = pd.DataFrame()
    key_deviations_uniform = pd.DataFrame()
    key_deviations_static = pd.DataFrame()
    key_deviations_dynamic = pd.DataFrame()
    allocated_production_uniform = pd.DataFrame()
    allocated_production_static = pd.DataFrame()
    allocated_production_dynamic = pd.DataFrame()
    verified_production_uniform = pd.DataFrame()
    verified_production_static = pd.DataFrame()
    verified_production_dynamic = pd.DataFrame()
    optimized_keys_uniform = pd.DataFrame()
    optimized_keys_static = pd.DataFrame()
    optimized_keys_dynamic = pd.DataFrame()
    sales_uniform = pd.DataFrame(index=['Local Sales', 'Global Sales'])
    sales_static = pd.DataFrame(index=['Local Sales', 'Global Sales'])
    sales_dynamic = pd.DataFrame(index=['Local Sales', 'Global Sales'])
    local_sales_uniform = pd.read_csv('results_paper/case_study_c_3/uniform/0.0/locally_sold_production.csv', index_col=0, squeeze=True)
    local_sales_static = pd.read_csv('results_paper/case_study_c_3/static/0.0/locally_sold_production.csv', index_col=0, squeeze=True)
    local_sales_dynamic = pd.read_csv('results_paper/case_study_c_3/dynamic/0.0/locally_sold_production.csv', index_col=0, squeeze=True)
    global_sales_uniform = pd.read_csv('results_paper/case_study_c_3/uniform/0.0/global_sales.csv', index_col=0, squeeze=True)
    global_sales_static = pd.read_csv('results_paper/case_study_c_3/static/0.0/global_sales.csv', index_col=0, squeeze=True)
    global_sales_dynamic = pd.read_csv('results_paper/case_study_c_3/dynamic/0.0/global_sales.csv', index_col=0, squeeze=True)
    for dev in [0.0, 0.01, 0.03, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0]:
        costs_users_deviations_uniform[dev] = pd.read_csv(
            f'results_paper/{folder}/uniform/{dev}/costs_users_no_deviations.csv', index_col=0, squeeze=True
        )
        costs_users_deviations_static[dev] = pd.read_csv(
            f'results_paper/{folder}/static/{dev}/costs_users_no_deviations.csv', index_col=0, squeeze=True
        )
        costs_users_deviations_dynamic[dev] = pd.read_csv(
            f'results_paper/{folder}/dynamic/{dev}/costs_users_no_deviations.csv', index_col=0, squeeze=True
        )
        key_deviations_uniform[dev] = ((
            pd.read_csv(
                f'results_paper/{folder}/uniform/{dev}/optimized_keys.csv', index_col=0
            ).mean(axis=0).divide(
                pd.read_csv(
                    f'results_paper/{folder}/uniform/{dev}/initial_keys.csv', index_col=0
                ).mean(axis=0), fill_value=0.0) - 1).fillna(0.0)
        ) * 100
        key_deviations_static[dev] = ((
            pd.read_csv(
                f'results_paper/{folder}/static/{dev}/optimized_keys.csv', index_col=0
            ).mean(axis=0).divide(
                pd.read_csv(
                    f'results_paper/{folder}/static/{dev}/initial_keys.csv', index_col=0
                ).mean(axis=0), fill_value=0.0) - 1).fillna(0.0)
        ) * 100
        key_deviations_dynamic[dev] = ((
            pd.read_csv(
                f'results_paper/{folder}/dynamic/{dev}/optimized_keys.csv', index_col=0
            ).mean(axis=0).divide(
                pd.read_csv(
                    f'results_paper/{folder}/dynamic/{dev}/initial_keys.csv', index_col=0
                ).mean(axis=0), fill_value=0.0) - 1).fillna(0.0)
        ) * 100
        allocated_production_uniform[dev] = ((
            pd.read_csv(
                f'results_paper/{folder}/uniform/{dev}/verified_allocated_production.csv', index_col=0
            ).sum(axis=0).divide(
                pd.read_csv(
                    f'results_paper/{folder}/uniform/{dev}/initial_allocated_production.csv', index_col=0
                ).sum(axis=0), fill_value=0.0
            ).fillna(0.0)
        ) - 1
                                             ) * 100
        allocated_production_static[dev] = ((
            pd.read_csv(
                f'results_paper/{folder}/static/{dev}/verified_allocated_production.csv', index_col=0
            ).sum(axis=0).divide(
                pd.read_csv(
                    f'results_paper/{folder}/static/{dev}/initial_allocated_production.csv', index_col=0
                ).sum(axis=0), fill_value=0.0
            ).fillna(0.0)
        ) - 1
                                             ) * 100
        allocated_production_dynamic[dev] = ((
            pd.read_csv(
                f'results_paper/{folder}/dynamic/{dev}/verified_allocated_production.csv', index_col=0
            ).sum(axis=0).divide(
                pd.read_csv(
                    f'results_paper/{folder}/dynamic/{dev}/initial_allocated_production.csv', index_col=0
                ).sum(axis=0), fill_value=0.0
            ).fillna(0.0)
        ) - 1
                                             ) * 100
        verified_production_uniform[dev] = (
            pd.read_csv(
                f'results_paper/{folder}/uniform/{dev}/verified_allocated_production.csv', index_col=0
            ).sum(axis=0)
        )
        verified_production_static[dev] = (
            pd.read_csv(
                f'results_paper/{folder}/static/{dev}/verified_allocated_production.csv', index_col=0
            ).sum(axis=0)
        )
        verified_production_dynamic[dev] = (
            pd.read_csv(
                f'results_paper/{folder}/dynamic/{dev}/verified_allocated_production.csv', index_col=0
            ).sum(axis=0)
        )
        optimized_keys_uniform[dev] = (
            pd.read_csv(
                f'results_paper/{folder}/uniform/{dev}/optimized_keys.csv', index_col=0
            ).mean(axis=0)
        )
        optimized_keys_static[dev] = (
            pd.read_csv(
                f'results_paper/{folder}/static/{dev}/optimized_keys.csv', index_col=0
            ).mean(axis=0)
        )
        optimized_keys_dynamic[dev] = (
            pd.read_csv(
                f'results_paper/{folder}/dynamic/{dev}/optimized_keys.csv', index_col=0
            ).mean(axis=0)
        )
        sales_uniform[dev] = (
            [
                pd.read_csv(
                    f'results_paper/{folder}/uniform/{dev}/locally_sold_production.csv', index_col=0
                ).sum(axis=0).sum(),
                pd.read_csv(
                    f'results_paper/{folder}/uniform/{dev}/global_sales.csv', index_col=0
                ).sum(axis=0).sum()
            ]
        )
        sales_static[dev] = (
            [
                pd.read_csv(
                    f'results_paper/{folder}/static/{dev}/locally_sold_production.csv', index_col=0
                ).sum(axis=0).sum(),
                pd.read_csv(
                    f'results_paper/{folder}/static/{dev}/global_sales.csv', index_col=0
                ).sum(axis=0).sum()
            ]
        )
        sales_dynamic[dev] = (
            [
                pd.read_csv(
                    f'results_paper/{folder}/dynamic/{dev}/locally_sold_production.csv', index_col=0
                ).sum(axis=0).sum(),
                pd.read_csv(
                    f'results_paper/{folder}/dynamic/{dev}/global_sales.csv', index_col=0
                ).sum(axis=0).sum()
            ]
        )

    plot.plot_bar_three_cases(
        ((costs_users_deviations_uniform.transpose() / costs_users_deviations_uniform.transpose().iloc[0]) - 1) * 100,
        ((costs_users_deviations_static.transpose() / costs_users_deviations_static.transpose().iloc[0]) - 1) * 100,
        ((costs_users_deviations_dynamic.transpose() / costs_users_deviations_dynamic.transpose().iloc[0]) - 1) * 100,
        'Cost evolution [%]',
        f'results_paper/{folder}',
        'costs_deviations',
        third_plot=False
    )
    plot.plot_bar_three_cases(
        key_deviations_uniform.transpose(),
        key_deviations_static.transpose(),
        key_deviations_dynamic.transpose(),
        'Key deviation [%]',
        f'results_paper/{folder}',
        'keys_deviations'
    )
    plot.plot_bar_three_cases(
        allocated_production_uniform.transpose(),
        allocated_production_static.transpose(),
        allocated_production_dynamic.transpose(),
        'Alloc. product. [%]',
        f'results_paper/{folder}',
        'allocated_production'
    )
    plot.plot_bar_three_cases(
        ((verified_production_uniform.transpose() / verified_production_uniform.transpose().iloc[0]) - 1) * 100,
        ((verified_production_static.transpose() / verified_production_static.transpose().iloc[0]) - 1) * 100,
        ((verified_production_dynamic.transpose() / verified_production_dynamic.transpose()) - 1) * 100,
        'Alloc. prod. [%]',
        f'results_paper/{folder}',
        'verified_production',
        third_plot=False
    )
    plot.plot_bar_three_cases(
        ((optimized_keys_uniform.transpose() - optimized_keys_uniform.transpose().loc[0]) * 100),
        ((optimized_keys_static.transpose() - optimized_keys_static.transpose().loc[0]) * 100),
        ((optimized_keys_dynamic.transpose() - optimized_keys_dynamic.transpose().loc[0]) * 100),
        'Key deviation [%]',
        f'results_paper/{folder}',
        'optimized_keys'
    )
    plot.plot_bar_three_cases(
        sales_uniform.transpose() / 4000,
        sales_static.transpose() / 4000,
        sales_dynamic.transpose() / 4000,
        'Electricity sales [MWh]',
        f'results_paper/{folder}',
        'sales',
        third_plot=False,
        sales=True
    )
    plot.covered_consumption(
        consumption.sum(axis=1),
        -production.sum(axis=1),
        local_sales_uniform.sum(axis=1),
        local_sales_static.sum(axis=1),
        local_sales_dynamic.sum(axis=1),
        f'results_paper/{folder}',
        'covered_consumption_ldc'
    )