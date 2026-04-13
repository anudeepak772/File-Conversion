with open("big.txt", "w") as f:
    for i in range(10000):
        f.write("This is a large file test\n")