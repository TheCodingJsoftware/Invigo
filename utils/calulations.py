# NOTE Deprecated in favor of job_price_calculator.py


def calculate_overhead(
    cost: float,
    profit_margin: float = 0.3,
    overhead_percentage: float = 0.18,
    max_iterations: int = 10,
):
    unit_price = 0
    for _ in range(max_iterations):
        try:
            unit_price = (cost + (unit_price * overhead_percentage)) / (
                1 - profit_margin
            )
        except ZeroDivisionError:
            unit_price = cost + (unit_price * overhead_percentage) / 0.00000001
    return unit_price


def calculate_scrap_percentage(nest_name: str, quote_nest_information: dict):
    sheet_dim_x, sheet_dim_y = (
        quote_nest_information[nest_name]["sheet_dim"].replace(" x ", "x").split("x")
    )
    sheet_surface_area: float = float(sheet_dim_x) * float(sheet_dim_y)

    nest_name = nest_name.split("/")[-1]
    if "CUSTOM NEST" in nest_name:
        nest_name = f"/{nest_name}"
    # Because of workspace inconsistent item types
    try:
        total_item_surface_area: float = sum(
            item_data["surface_area"] * item_data["quantity"]
            for _, item_data in quote_nest_information[nest_name].items()
        )
    except TypeError:
        return 0.0
    try:
        return (1 - (total_item_surface_area / sheet_surface_area)) * 100
    except ZeroDivisionError:
        return 0.0
