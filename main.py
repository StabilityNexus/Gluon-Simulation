import random
import numpy as np

def initialize_simulator(initial_sp=100, initial_sn=100, initial_r=200, initial_balance=None):
    if initial_balance is None:
        initial_balance = [90, 90, 1000]
    return {
        "initial_sp": initial_sp,
        "initial_sn": initial_sn,
        "initial_r": initial_r,
        "initial_balance": initial_balance,
        "sp": initial_sp,
        "sn": initial_sn,
        "r": initial_r,
        "user_balance": initial_balance.copy()
    }

def reset(simulator):
    simulator["sp"] = simulator["initial_sp"]
    simulator["sn"] = simulator["initial_sn"]
    simulator["r"] = simulator["initial_r"]
    simulator["user_balance"] = simulator["initial_balance"].copy()

def illegal_state(simulator):
    return simulator["r"] <= 0 or simulator["sp"] <= 0 or simulator["sn"] <= 0

def execute_trade_minus(simulator, m):
    if simulator["user_balance"][0] < m:
        return False

    q = min(0.66, simulator["sn"] / simulator["r"])
    out_p = m * (simulator["sp"] / simulator["sn"]) * (q / (1 - q))

    if simulator["sn"] < m:
        return False

    simulator["user_balance"][0] -= m
    simulator["sp"] += out_p
    simulator["sn"] -= m
    simulator["user_balance"][1] += out_p

    return not illegal_state(simulator)

def execute_trade_plus(simulator, m):
    if simulator["user_balance"][1] < m:
        return False

    q = min(0.66, simulator["sn"] / simulator["r"])
    out_n = m * (simulator["sn"] / simulator["sp"]) * ((1 - q) / q)

    if simulator["sp"] < m:
        return False

    simulator["user_balance"][1] -= m
    simulator["sp"] -= m
    simulator["sn"] += out_n
    simulator["user_balance"][0] += out_n

    return not illegal_state(simulator)

def execute_fission(simulator, ru):
    if simulator["user_balance"][2] < ru:
        return False

    out_p = ru * simulator["sp"] / simulator["r"]
    out_n = ru * simulator["sn"] / simulator["r"]

    simulator["user_balance"][2] -= ru
    simulator["user_balance"][0] += out_n
    simulator["user_balance"][1] += out_p

    simulator["sn"] += out_n
    simulator["sp"] += out_p
    simulator["r"] += ru

    return not illegal_state(simulator)

def execute_fusion(simulator, ru):
    out_p = ru * simulator["sp"] / simulator["r"]
    out_n = ru * simulator["sn"] / simulator["r"]

    if out_p > simulator["user_balance"][1] or out_n > simulator["user_balance"][0]:
        return False

    simulator["user_balance"][2] += ru
    simulator["user_balance"][0] -= out_n
    simulator["user_balance"][1] -= out_p

    simulator["sn"] -= out_n
    simulator["sp"] -= out_p
    simulator["r"] -= ru

    return not illegal_state(simulator)

def random_trade_sequence(simulator, max_trades=30):
    trade_funcs = [
        (execute_trade_minus, lambda: random.uniform(10, 200)),
        (execute_trade_plus, lambda: random.uniform(10, 200)),
        (execute_fusion, lambda: random.uniform(100, 1000)),
        (execute_fission, lambda: random.uniform(100, 1000))
    ]

    trade_attempts = 0
    successful_trades = 0
    max_fails = 50

    # Initialize counters for tracking trade amounts
    total_minus = 0
    total_plus = 0
    total_fusioned = 0
    total_fissioned = 0

    while successful_trades < max_trades and trade_attempts - successful_trades < max_fails:
        func, amount_generator = random.choice(trade_funcs)
        amount = amount_generator()
        if func(simulator, amount):
            successful_trades += 1

            # Track the amount based on the trade function
            if func == execute_trade_minus:
                total_minus += amount
            elif func == execute_trade_plus:
                total_plus += amount
            elif func == execute_fusion:
                total_fusioned += amount
            elif func == execute_fission:
                total_fissioned += amount

            # Stop if in profit
            if all(final > initial for final, initial in zip(simulator["user_balance"], simulator["initial_balance"])):
                break
        trade_attempts += 1
    if simulator["user_balance"][0] > simulator["initial_balance"][0] and simulator["user_balance"][1] > simulator["initial_balance"][1]:
        execute_fusion(simulator, min(simulator["user_balance"][0],  simulator["user_balance"][1]) - simulator["initial_balance"][0] - 1)
    if simulator["user_balance"][0] > simulator["user_balance"][1]:
        execute_trade_minus(simulator, simulator["user_balance"][0] - simulator["user_balance"][1] - 1)
    if simulator["user_balance"][1] > simulator["user_balance"][0]:
        execute_trade_plus(simulator, simulator["user_balance"][1] - simulator["user_balance"][0] - 1)
    if simulator["user_balance"][2] < simulator["initial_balance"][2]:
        execute_fission(simulator, simulator["user_balance"][2] - simulator["initial_balance"][2] - 1)


def manual_trade_sequence(simulator):
    execute_trade_minus(simulator, 90)
    print(simulator)

def run_simulation(num_simulations=10000, verbose=False, manual=False):
    results = []
    simulator = initialize_simulator()
    if manual:
        manual_trade_sequence(simulator)

    for _ in range(num_simulations):
        reset(simulator)
        random_trade_sequence(simulator)

        is_profitable = all(
            final > initial
            for final, initial in zip(simulator["user_balance"], simulator["initial_balance"])
        )

        result = {
            'initial_balance': simulator["initial_balance"].copy(),
            'final_balance': simulator["user_balance"].copy(),
            'balance_changes': [
                final - initial
                for final, initial in zip(simulator["user_balance"], simulator["initial_balance"])
            ],
            'is_profitable': is_profitable
        }

        if is_profitable:
            results.append(result)

        if verbose and is_profitable:
            print(f"Successful Simulation: {result}")

    return results

def analyze_results(results):
    total_simulations = len(results)

    if not results:
        print("No profitable simulations found.")
        return []

    most_balanced_result = max(
        results,
        key=lambda r: min(r['balance_changes'])
    )

    print(f"Total Profitable Simulations: {total_simulations}")

    print("\nMost Balanced Profitable Scenario:")
    print("Initial Balance:  ", most_balanced_result['initial_balance'])
    print("Final Balance:    ", most_balanced_result['final_balance'])
    print("Absolute Changes: ", most_balanced_result['balance_changes'])
    print("Percentage Changes:")
    for initial, final in zip(
            most_balanced_result['initial_balance'],
            most_balanced_result['final_balance']
    ):
        print(f"  {((final - initial) / initial * 100):.2f}%")

    return results

# Demonstration
if __name__ == "__main__":
    results = run_simulation(num_simulations=100000, verbose=False, manual=False)
    analyze_results(results)
