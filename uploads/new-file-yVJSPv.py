
if __name__ == "__main__":    
    info = {
        "Ball Angle": 0,
        "Ball Distance": 0,
        "Heading": 0,
        "Initial Heading": 0,
        "TOF Distances": [0]
    }
    max_header = max([len(x) for x in info])
    for header in info:
        line = info[header]
        if type(line) == float: line = round(line, 2)
        print(f"{(header + ' ' * max_header)[:max_header]} | {line}")
    print()
