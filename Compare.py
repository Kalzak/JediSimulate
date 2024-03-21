from alive_progress import alive_bar
import json
import sys

from Uniswap import UniswapPool
from Jediswap import JSF

def main():
    jedi_fuzz = JSF()
    res = jedi_fuzz.add_i8(1,-10)
    print(res)
    res = jedi_fuzz.add_i256(-1,-100)
    print(res)



if __name__ == "__main__":
    main()