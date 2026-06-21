from datetime import date

#! Helper function to calculate price
def calculate_total_price(price_per_night: int, nights: int):
    return price_per_night * nights


#! Helper function to calculate nights
def calculate_nights(check_in: date | None, check_out: date | None):
    if check_in is None or check_out is None:
        return 0

    return (check_out - check_in).days

#! Helper function to calculate starting price
def calculate_starting_price(rooms):
    if not rooms:
        return None

    return min(room.price_per_night for room in rooms)