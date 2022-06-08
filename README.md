# Repartition keys

This tool computes the optimal repartition of keys for the users of a renewable energy community (REC). The repartition keys distribute the locally generated electricity among the users by assigning a proportion of the production to each of them. The users' electricity needs will therefore be met primarily by their assigned local production, and then, if this is not enough, by importing electricity from the main grid the REC is connected to. The local producers will supply the demand in an orderly fashion, depending on their production costs, which are reflected on their selling price.

A set of initial keys is either given or precomputed. These keys are then optimized minimizing:

- sum of final customers' electricity bills, composed of four elements – imports from the main network, exports to the main network, imports from the REC, and exports to the REC;
- deviations from the initial keys – optimized keys should not significantly differ from the initial ones.

A set of constraints is taken into account when performing such a minimization:

- the local production must be partially or totally allocated to the final customers – if not all the production is allocated, the rest is sold to the main network;
- deviations from the initial keys are computed and can be bounded;
- the self-sufficiency rate is computed and a minimum self-sufficiency rate can be enforced.

## Setup

This tool is written and tested in python 3.7. The software and its dependencies can be installed in a python virtual environment.

Create a virtual environment called `venv`:

```bash
python -m venv venv
```

Activate the virtual environment:

```bash
source venv/bin/activate
```

Make sure that `pip` is up-to-date:

```bash
(venv) pip install --upgrade pip
```

Install the required packages with:

```bash
(venv) pip install -r requirements.txt
```

Then install a linear optimization solver and make sure it is available from the command-line. By default, `cbc` is used. This solver can be easily installed in most Unix based distributions. For example:

- on Ubuntu, the following command is used `sudo apt install coinor-cbc`;
- on Arch Linux, the following command is used `sudo pacman -S coin-or-cbc`;
- on macOS, the following command is used (requires HomeBrew) `brew tap coin-or-tools/coinor && brew install cbc`.

Faster simulation may be obtained using commercial solvers such as CPLEX or Gurobi. In that case, the solver name should be provided in the command line options.

## How to run the simulation

The simulator can be run as a python module. To run the simulation it is required: (1) data, (2) inputs file, and (3) other options.

### 1. Data

Only one data file is mandatory for the simulation to work:

- A `csv` file containing the time series of the users showing their power consumption or production as positive or negative values, respectively. Note that one user can present positive (consumption) and negative (production) power in the same file. An example is provided.

Additionally, a number of files can be introduced to run more detailed simulations:

- A `csv` file with the production profiles as negative values independent from the previous one. Note that if this file is introduced, the production profiles in the first `csv` file should be removed.
- A `csv` file containing the desired initial keys for the optimization.

Alternatively, instead of introducing the initial keys in a `csv` file, it is possible to compute them based on the time series containing consumption and production profiles. The simulator counts with three different built-in methods that can be called to compute them. To call this built-in methods, instead of introducing the `csv` file, it is possible to call with a string (`static`, `proportional_static`, `proportional_dynamic`) one of such methods.

#### Initial keys built-in methods

- ***Uniform*** (`static`): this method distributes the initial keys evenly among all the users of the simulation.
- ***Proportional Static*** (`proportional_static`): this method computes the initial keys based on the proportion of the total demand of one user over the simulation horizon (i.e. the length of the `csv` file containing the consumption/production profiles) with respect to the total consumption of the system over the same period.
- ***Proportional Dynamic*** (`proportional_dynamic`): this method computes the initial keys based on the proportion of the instantaneous demand of one user with respect to the total instantaneous demand of the system.

### 2. Inputs file

An inputs file can created in `json` format to introduce the following parameters:

- `default_price_retailer_in` *(floating number)*: this price will be associated to the electricity imports from the main network – it represents a cost for the users. It will be applied to all users.
- `price_retailer_in` *(dictionary {users: floating number})*: user wise version of the previous price – it will be applied to the users included in the dictionary, for the rest, the default value will by applied.
- `default_price_retailer_out` *(floating number)*: this price will be associated to the electricity exports to the main network – it represents a revenue for the users.
- `price_retailer_out` *(dictionary {users: floating number})*: user wise version of the previous price – it will be applied to the users included in the dictionary, for the rest, the default value will by applied.
- `default_price_local_in` *(floating number)*: this price will be associated to the electricity imports from the REC – it represents a cost for the users.
- `price_local_in` *(dictionary {users: floating number})*: user wise version of the previous price – it will be applied to the users included in the dictionary, for the rest, the default value will by applied.
- `default_price_local_out` *(floating number)*: this price will be associated to the electricity exports to the REC – it represents a revenue for the users. It will be applied to the users included in the dictionary, for the rest, the default value will by applied.
- `price_local_out` *(dictionary {users: floating number})*: user wise version of the previous price – it will be applied to the users included in the dictionary, for the rest, the default value will by applied.
- `default_price_deviation_energy` *(floating number)*: this price will be associated to the deviation from the initial allocated production, computed from the initial keys.
- `price_deviation_energy` *(floating number)*: user wise version of the previous price – it will be applied to the users included in the dictionary, for the rest, the default value will by applied.
- `default_price_allocated_production` *(floating number)*: this price will penalize the allocated production in the objective function, forcing it to be as close to the verified allocated production as possible.
- `price_allocated_production` *(floating number)*: user wise version of the previous price – it will be applied to the users included in the dictionary, for the rest, the default value will by applied.
- `default_max_deviation` *(floating number)*: this sets the maximum absolute deviation of the optimized repartition keys for all users at once.
- `max_deviation` *(dictionary {users: floating number})*: this sets the maximum allowed deviation of the optimized keys from the initial ones for every user of the simulation. The values can range from 0.0 to 1.0, allowing keys deviations of 0 -- 100% of the initial keys. It can be filled totally or partially (i.e. only for the relevant users). It will overwrite the `default_max_deviation` parameter for the relevant users.
- `default_min_ssr_user` *(floating number)*: this sets the minimum value of self-sufficiency rate desired for all users at once. Note that this may lead to an infeasible solution of the optimization problem.
- `min_ssr_user` *(dictionary {users: floating number})*: this sets the minimum value of self-sufficiency rate desired for every consumer. It can be filled totally or partially (i.e. only for the relevant users). It will overwrite the `default_min_ssr_user` parameter for the relevant users. Note that this may lead to an infeasible solution of the optimization problem.
- `min_ssr_rec` *(floating number)*: this sets the minimum value of self-sufficiency rate desired for the whole REC.
- `scaling_factor` *(dictionary {users: floating number})*: this limits the use of the available production of each user to a percentage of this production. The values can range from 0.0 to 1.0, limiting the available production to 0 - 100% of the initial production.

All the parameters in this file are optional. If they are not present, default parameters will be used.

### 3. Other options

Several arguments can be entered through the command to run – `data_consumption`, `data_production`, `initial_keys`, `input_options`, `solver`, `output`, `debug`, `verbose`. Only the first one is mandatory. More information can be obtained by running the help function:

```bash
python -m repartition -h
```

## Running Examples

One basic example can be run using the data included in the repository:

```bash
python -m repartition tests/data/four_users/consumption.csv -dp tests/data/four_users/production.csv -i tests/data/four_users/inputs.json -o ./results_four_users
```

A more advanced example case can be run with:

```bash
python -m repartition data/one_month/consumption.csv -dp data/one_month/production.csv -k proportional_static -i data/one_month/inputs.json -s cbc -o ./results_one_month -v
```

## Tests

Several tests are included with the simulator to showcase its functionalities.

### `test_ssr_user_default`

This test illustrates the capabilities of the simulator to enforce a minimum ssr for all users at once.

### `test_ssr_user_individual`

This test illustrates the capabilities of the simulator to enforce a minimum ssr for certain users.

### `test_ssr_rec`

This test illustrates the capabilities of the simulator to enforce a minimum ssr for the whole of the REC.

### `test_price_retailer_out_individual`

This test illustrates the capabilities of the simulator to rank the producers according to their generation costs. In this case, the `price_retailer_out` is applied to only one producer. When two producers have different `price_retailer_out`, keeping all the other prices equal, the one with a lower `price_retailer_out` tends to sell more locally (to the REC), and the one with a higher `price_retailer_out` tends to sell more globally (to the retailer).

### `test_three_users` and `test_four_users`

This tests illustrate the basic functioning of the simulator.
