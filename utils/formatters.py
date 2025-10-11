def degrees_to_cardinal(degrees):
    """Convert wind direction in degrees to cardinal direction"""
    directions_list = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                      'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    index = int((degrees + 11.25) / 22.5) % 16
    return directions_list[index]
