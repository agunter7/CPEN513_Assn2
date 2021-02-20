import cProfile
import pstats
import sim_anneal

# "apex1.txt",
#FILE_NAMES = ["apex4.txt", "C880.txt", "cm138a.txt", "cm150a.txt", "cm151a.txt",
 #             "cm162a.txt", "cps.txt", "e64.txt", "paira.txt", "pairb.txt"]
FILE_NAMES = ["cps.txt"]
COOLING_FACTORS = [0.8]
INITIAL_TEMP_FACTORS = [10, 20]
MOVES_PER_TEMP_FACTORS = [75]

def main():
    #profiler = cProfile.Profile()
    #profiler.enable()
    for file_name in FILE_NAMES:
        for cooling_factor in COOLING_FACTORS:
            for initial_temp_factor in INITIAL_TEMP_FACTORS:
                for moves_per_temp_factor in MOVES_PER_TEMP_FACTORS:
                    sim_anneal.quick_anneal(file_name, cooling_factor, initial_temp_factor, moves_per_temp_factor)
    #profiler.disable()
    #stats = pstats.Stats(profiler).sort_stats('cumtime')
    #stats.print_stats()
    print("end")


if __name__ == "__main__":
    main()
