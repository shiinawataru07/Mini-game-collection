"""Mini-game collection entry point."""

import pygame
from games.menu import run as run_menu


def run() -> None:
    """Own the shared Pygame lifecycle for the whole collection."""

    pygame.init()
    try:
        run_menu()
    finally:
        pygame.quit()


if __name__ == "__main__":
    run()
