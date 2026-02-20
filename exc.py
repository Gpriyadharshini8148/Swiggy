from openpyxl import Workbook
from datetime import datetime
import random

# Create workbook
wb = Workbook()
ws = wb.active

# Define headers (based on your model)
headers = [
    "id", "created_at", "updated_at", "is_deleted",
    "created_by", "updated_by", "deleted_by",
    "name", "logo_image", "banner_image",
    "location", "address", "state", "city",
    "rating", "category", "user",
    "opening_time", "closing_time",
    "account_number", "ifsc_code",
    "gst_number", "pan_number",
    "is_verified", "is_active", "deleted_at"
]

ws.append(headers)

states_cities = [
    ("Tamil Nadu", "Chennai"),
    ("Karnataka", "Bangalore"),
    ("Maharashtra", "Mumbai"),
    ("Telangana", "Hyderabad"),
    ("Kerala", "Kochi"),
    ("Delhi", "New Delhi"),
    ("Gujarat", "Ahmedabad"),
    ("West Bengal", "Kolkata"),
    ("Rajasthan", "Jaipur"),
    ("Punjab", "Chandigarh"),
]

restaurant_names = [
    "Royal Spice Villa",
    "Urban Tandoor",
    "Ocean Pearl",
    "Grand Thali House",
    "Spicy Route",
    "Metro Grill",
    "Golden Curry",
    "Food Fiesta",
    "Flavors of India",
    "Taste Town",
]

for i in range(10):
    state, city = states_cities[i]
    now = datetime.now()

    row = [
        i + 1,                     # id
        now,                       # created_at
        now,                       # updated_at
        False,                     # is_deleted
        1,                         # created_by
        1,                         # updated_by
        None,                      # deleted_by
        restaurant_names[i],       # name
        f"logo_{i+1}.png",         # logo_image
        f"banner_{i+1}.png",       # banner_image
        f"{city} Central",         # location
        f"{random.randint(10,500)} Main Road, {city}",
        state,
        city,
        round(random.uniform(3.5, 5.0), 1),
        "Multi-Cuisine",
        1,                         # user (foreign key id)
        "09:00:00",
        "23:00:00",
        f"1234567890{i}",
        f"SBIN0000{i}",
        f"33ABCDE1234F{i}Z5",
        f"ABCDE1234{i}F",
        True,
        True,
        None
    ]

    ws.append(row)

# Save file
wb.save("Fully_Filled_New_Restaurants.xlsx")

print("Excel file created successfully!")