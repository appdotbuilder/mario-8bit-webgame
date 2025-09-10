from app.database import create_tables
import app.mario_game


def startup() -> None:
    # this function is called before the first request
    create_tables()

    # Initialize the Mario game module
    app.mario_game.create()
