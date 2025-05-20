def convert_to_minutes(timeframe: str) -> int:
    # Mapping of timeframes to their corresponding minute values
    timeframe_map = {
        "5": 5,
        "15": 15,
        "30": 30,
        "45": 45,
        "60": 60, "H": 60,
        "120": 120, "2H": 120,
        "180": 180, "3H": 180,
        "240": 240, "4H": 240,
        "360": 360, "6H": 360,
        "480": 480, "8H": 480,
        "720": 720, "12H": 720,
        "1440": 1440, "D": 1440,
        "2880": 2880, "2D": 2880,
        "4320": 4320, "3D": 4320,
        "10080": 10080, "W": 10080,
        "43200": 43200, "M": 43200,
    }

    # Convert the input timeframe to uppercase for consistent lookup
    timeframe = timeframe.upper().replace(" ", "")

    # Return the corresponding minute value or raise an error if invalid
    if timeframe in timeframe_map:
        return timeframe_map[timeframe]
    else:
        raise ValueError(f"Invalid timeframe: {timeframe}")