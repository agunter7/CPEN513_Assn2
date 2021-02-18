import cProfile
import pstats
import sim_anneal


def main():
    #profiler = cProfile.Profile()
    #profiler.enable()
    sim_anneal.anneal()
    #profiler.disable()
    #stats = pstats.Stats(profiler).sort_stats('cumtime')
    #stats.print_stats()


if __name__ == "__main__":
    main()
