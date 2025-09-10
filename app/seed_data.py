"""
Seed script to populate the database with initial game data
"""

import logging
from app.game_service import GameService


def seed_database():
    """Populate database with initial game data"""
    service = GameService()

    # Create default player
    default_player = service.get_or_create_player("Mario")
    logging.info(f"Created default player: {default_player.name}")

    # Create default level with objects
    default_level = service.get_or_create_default_level()
    logging.info(f"Created default level: {default_level.name}")

    # Get level objects count
    if default_level.id is not None:
        objects = service.get_level_objects(default_level.id)
    else:
        objects = []
    platforms = [obj for obj in objects if obj.object_type.value == "platform"]
    coins = [obj for obj in objects if obj.object_type.value == "coin"]

    logging.info(f"Level has {len(platforms)} platforms and {len(coins)} coins")

    # Create game config
    config = service.get_or_create_game_config()
    logging.info(f"Game config: Speed={config.player_speed}, Jump={config.jump_strength}")

    logging.info("Database seeded successfully!")


if __name__ == "__main__":
    seed_database()
