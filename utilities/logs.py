from datetime import datetime

def dump_error(data):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"logs/{timestamp}.data"
    with open(filename, "a") as file:
        file.write(data)
