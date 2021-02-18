import cProfile
import pstats
import sim_anneal

FILE_NAMES = ["alu2.txt", "apex1.txt", "apex4.txt", "C880.txt", "cm138a.txt", "cm150a.txt", "cm151a.txt",
              "cm162a.txt", "cps.txt", "e64.txt", "paira.txt", "pairb.txt"]
COOLING_FACTORS = [0.8, 0.85, 0.9, 0.95]
INITIAL_TEMP_FACTORS = [10, 20, 30]
MOVES_PER_TEMP_FACTORS = [25, 50, 75]

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
