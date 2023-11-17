def calculate_overhead(cost: float, profit_margin: float = 0.3, overhead_percentage: float = 0.18, max_iterations: int = 10):
    """
    This function calculates the unit price of a product based on its cost, profit margin, overhead
    percentage, and maximum iterations.

    Args:
      cost (float): The cost of producing one unit of the product.
      profit_margin (float): The profit margin is the percentage of profit that a company expects to
    make on a product or service. In this function, it is set to a default value of 0.3, which means
    that the company expects to make a profit of 30% on each unit sold.
      overhead_percentage (float): The percentage of overhead cost to be added to the cost of the
    product. In the given code, it is set to 0.18 or 18%.
      max_iterations (int): The maximum number of iterations the function will run to calculate the unit
    price. Defaults to 10

    Returns:
      the unit price that should be charged for a product in order to cover the cost, overhead, and
    profit margin.
    """
    unit_price = 0
    for _ in range(max_iterations):
        try:
            unit_price = (cost + (unit_price * overhead_percentage)) / (1 - profit_margin)
        except ZeroDivisionError:
            unit_price = cost + (unit_price * overhead_percentage) / 0.00000001
    return unit_price


def calculate_scrap_percentage(nest_name: str, quote_nest_information: dict):
    sheet_dim_x, sheet_dim_y = quote_nest_information[nest_name]["sheet_dim"].replace(" x ", "x").split("x")
    sheet_surface_area: float = float(sheet_dim_x) * float(sheet_dim_y)

    nest_name = nest_name.split("/")[-1]
    if "CUSTOM NEST" in nest_name:
        nest_name = f"/{nest_name}"
    # Because of workspace inconsistent item types
    try:
        total_item_surface_area: float = sum(
            item_data["surface_area"] * item_data["quantity"] for _, item_data in quote_nest_information[nest_name].items()
        )
    except TypeError:
        return 0.0
    try:
        return (1 - (total_item_surface_area / sheet_surface_area)) * 100
    except ZeroDivisionError:
        return 0.0
