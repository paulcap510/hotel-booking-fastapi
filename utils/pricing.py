from datetime import date

#! Helper function to calculate price
def calculate_total_price(price_per_night: int, nights: int):
    return price_per_night * nights