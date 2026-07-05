try:
    from api.weather import handler
except ModuleNotFoundError:
    from weather import handler
