"""Desktop entry point for ClipForge."""
import multiprocessing

from studio.desktop import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
