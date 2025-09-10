from decimal import Decimal
from typing import Optional, List, Tuple, Dict
from sqlmodel import select

from app.database import get_session
from app.models import (
    Player,
    GameLevel,
    GameObject,
    GameSession,
    GameConfig,
    GameObjectType,
    PlayerState,
    PlayerCreate,
    GameLevelCreate,
    GameSessionCreate,
    GameSessionUpdate,
)


class CollisionBox:
    """Simple rectangle collision box"""

    def __init__(self, x: Decimal, y: Decimal, width: Decimal, height: Decimal):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def intersects(self, other: "CollisionBox") -> bool:
        """Check if this box intersects with another box"""
        return (
            self.x < other.x + other.width
            and self.x + self.width > other.x
            and self.y < other.y + other.height
            and self.y + self.height > other.y
        )

    def get_overlap(self, other: "CollisionBox") -> Tuple[Decimal, Decimal]:
        """Get overlap amounts (x, y) with another box"""
        overlap_x = min(self.x + self.width, other.x + other.width) - max(self.x, other.x)
        overlap_y = min(self.y + self.height, other.y + other.height) - max(self.y, other.y)
        return overlap_x, overlap_y


class GameService:
    """Service layer for game logic and database operations"""

    def __init__(self):
        self.session = get_session()

    def get_or_create_player(self, name: str = "Mario") -> Player:
        """Get existing player or create a new one"""
        player = self.session.exec(select(Player).where(Player.name == name)).first()
        if player is None:
            player_create = PlayerCreate(name=name)
            player = Player(**player_create.model_dump())
            self.session.add(player)
            self.session.commit()
            self.session.refresh(player)
        return player

    def get_or_create_default_level(self) -> GameLevel:
        """Get or create the default level"""
        level = self.session.exec(select(GameLevel).where(GameLevel.level_number == 1)).first()
        if level is None:
            level = self.create_default_level()
        return level

    def create_default_level(self) -> GameLevel:
        """Create a default Mario-style level with platforms and coins"""
        level_create = GameLevelCreate(
            name="World 1-1",
            level_number=1,
            width=2400,  # Wider level for exploration
            height=600,
            background_color="#87CEEB",  # Sky blue
            gravity=Decimal("0.8"),
            player_spawn_x=Decimal("100"),
            player_spawn_y=Decimal("400"),
            time_limit=400,
        )

        level = GameLevel(**level_create.model_dump())
        self.session.add(level)
        self.session.commit()
        self.session.refresh(level)

        # We need the level ID to exist first, so let's create objects after level is committed
        if level.id is None:
            raise ValueError("Level ID is None after commit")

        level_id = level.id

        # Create ground platforms
        ground_objects_data = [
            # Main ground
            {
                "level_id": level_id,
                "object_type": GameObjectType.PLATFORM,
                "x_position": Decimal("0"),
                "y_position": Decimal("550"),
                "width": Decimal("800"),
                "height": Decimal("50"),
                "color": "#8B4513",  # Brown
                "is_solid": True,
                "is_collectible": False,
                "points_value": 0,
            },
            # Gap for jumping
            {
                "level_id": level_id,
                "object_type": GameObjectType.PLATFORM,
                "x_position": Decimal("900"),
                "y_position": Decimal("550"),
                "width": Decimal("500"),
                "height": Decimal("50"),
                "color": "#8B4513",
                "is_solid": True,
                "is_collectible": False,
                "points_value": 0,
            },
            # Higher platform
            {
                "level_id": level_id,
                "object_type": GameObjectType.PLATFORM,
                "x_position": Decimal("600"),
                "y_position": Decimal("450"),
                "width": Decimal("200"),
                "height": Decimal("32"),
                "color": "#8B4513",
                "is_solid": True,
                "is_collectible": False,
                "points_value": 0,
            },
            # More platforms
            {
                "level_id": level_id,
                "object_type": GameObjectType.PLATFORM,
                "x_position": Decimal("1000"),
                "y_position": Decimal("400"),
                "width": Decimal("150"),
                "height": Decimal("32"),
                "color": "#8B4513",
                "is_solid": True,
                "is_collectible": False,
                "points_value": 0,
            },
            {
                "level_id": level_id,
                "object_type": GameObjectType.PLATFORM,
                "x_position": Decimal("1300"),
                "y_position": Decimal("350"),
                "width": Decimal("200"),
                "height": Decimal("32"),
                "color": "#8B4513",
                "is_solid": True,
                "is_collectible": False,
                "points_value": 0,
            },
            # Final ground section
            {
                "level_id": level_id,
                "object_type": GameObjectType.PLATFORM,
                "x_position": Decimal("1500"),
                "y_position": Decimal("550"),
                "width": Decimal("900"),
                "height": Decimal("50"),
                "color": "#8B4513",
                "is_solid": True,
                "is_collectible": False,
                "points_value": 0,
            },
        ]

        # Create coins
        coin_objects_data = [
            # Coins above first platform
            {
                "level_id": level_id,
                "object_type": GameObjectType.COIN,
                "x_position": Decimal("200"),
                "y_position": Decimal("300"),
                "width": Decimal("24"),
                "height": Decimal("24"),
                "color": "#FFD700",  # Gold
                "is_solid": False,
                "is_collectible": True,
                "points_value": 100,
            },
            {
                "level_id": level_id,
                "object_type": GameObjectType.COIN,
                "x_position": Decimal("300"),
                "y_position": Decimal("250"),
                "width": Decimal("24"),
                "height": Decimal("24"),
                "color": "#FFD700",
                "is_solid": False,
                "is_collectible": True,
                "points_value": 100,
            },
            # Coins on elevated platform
            {
                "level_id": level_id,
                "object_type": GameObjectType.COIN,
                "x_position": Decimal("650"),
                "y_position": Decimal("400"),
                "width": Decimal("24"),
                "height": Decimal("24"),
                "color": "#FFD700",
                "is_solid": False,
                "is_collectible": True,
                "points_value": 100,
            },
            {
                "level_id": level_id,
                "object_type": GameObjectType.COIN,
                "x_position": Decimal("700"),
                "y_position": Decimal("400"),
                "width": Decimal("24"),
                "height": Decimal("24"),
                "color": "#FFD700",
                "is_solid": False,
                "is_collectible": True,
                "points_value": 100,
            },
            # More coins scattered around
            {
                "level_id": level_id,
                "object_type": GameObjectType.COIN,
                "x_position": Decimal("1050"),
                "y_position": Decimal("350"),
                "width": Decimal("24"),
                "height": Decimal("24"),
                "color": "#FFD700",
                "is_solid": False,
                "is_collectible": True,
                "points_value": 100,
            },
            {
                "level_id": level_id,
                "object_type": GameObjectType.COIN,
                "x_position": Decimal("1400"),
                "y_position": Decimal("300"),
                "width": Decimal("24"),
                "height": Decimal("24"),
                "color": "#FFD700",
                "is_solid": False,
                "is_collectible": True,
                "points_value": 100,
            },
            {
                "level_id": level_id,
                "object_type": GameObjectType.COIN,
                "x_position": Decimal("1800"),
                "y_position": Decimal("400"),
                "width": Decimal("24"),
                "height": Decimal("24"),
                "color": "#FFD700",
                "is_solid": False,
                "is_collectible": True,
                "points_value": 100,
            },
            {
                "level_id": level_id,
                "object_type": GameObjectType.COIN,
                "x_position": Decimal("2000"),
                "y_position": Decimal("350"),
                "width": Decimal("24"),
                "height": Decimal("24"),
                "color": "#FFD700",
                "is_solid": False,
                "is_collectible": True,
                "points_value": 100,
            },
        ]

        # Add all objects to database
        all_objects_data = ground_objects_data + coin_objects_data
        for obj_data in all_objects_data:
            obj = GameObject(**obj_data)
            self.session.add(obj)

        self.session.commit()
        return level

    def get_or_create_game_config(self) -> GameConfig:
        """Get or create default game configuration"""
        config = self.session.exec(select(GameConfig)).first()
        if config is None:
            config = GameConfig()
            self.session.add(config)
            self.session.commit()
            self.session.refresh(config)
        return config

    def start_new_session(self, player_id: int, level_id: int) -> GameSession:
        """Start a new game session"""
        level = self.session.get(GameLevel, level_id)
        if level is None:
            raise ValueError(f"Level {level_id} not found")

        session_create = GameSessionCreate(player_id=player_id, level_id=level_id)
        game_session = GameSession(
            **session_create.model_dump(),
            player_x=level.player_spawn_x,
            player_y=level.player_spawn_y,
            time_remaining=level.time_limit,
        )

        self.session.add(game_session)
        self.session.commit()
        self.session.refresh(game_session)
        return game_session

    def update_session(self, session_id: int, update_data: GameSessionUpdate) -> Optional[GameSession]:
        """Update game session with new state"""
        game_session = self.session.get(GameSession, session_id)
        if game_session is None:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(game_session, key, value)

        self.session.commit()
        self.session.refresh(game_session)
        return game_session

    def get_session(self, session_id: int) -> Optional[GameSession]:
        """Get game session by ID"""
        return self.session.get(GameSession, session_id)

    def get_level_objects(self, level_id: int) -> List[GameObject]:
        """Get all objects for a level"""
        return list(self.session.exec(select(GameObject).where(GameObject.level_id == level_id)))


class GamePhysics:
    """Game physics engine for Mario-style platformer"""

    def __init__(self, config: GameConfig):
        self.config = config

    def update_player_physics(
        self,
        session: GameSession,
        level_objects: List[GameObject],
        keys_pressed: Dict[str, bool],
        delta_time: float = 1.0 / 60.0,  # 60 FPS default
    ) -> GameSession:
        """Update player physics for one frame"""

        # Input handling
        move_left = keys_pressed.get("ArrowLeft", False) or keys_pressed.get("a", False)
        move_right = keys_pressed.get("ArrowRight", False) or keys_pressed.get("d", False)
        jump = keys_pressed.get(" ", False) or keys_pressed.get("ArrowUp", False) or keys_pressed.get("w", False)

        # Apply horizontal movement
        if move_left:
            session.player_velocity_x = max(
                session.player_velocity_x - self.config.player_speed * Decimal(str(delta_time)),
                -self.config.max_velocity_x,
            )
            session.is_facing_right = False
        elif move_right:
            session.player_velocity_x = min(
                session.player_velocity_x + self.config.player_speed * Decimal(str(delta_time)),
                self.config.max_velocity_x,
            )
            session.is_facing_right = True
        else:
            # Apply friction when not moving
            if session.is_on_ground:
                session.player_velocity_x *= self.config.friction
            else:
                session.player_velocity_x *= self.config.air_resistance

            # Stop very slow movement
            if abs(session.player_velocity_x) < Decimal("0.1"):
                session.player_velocity_x = Decimal("0")

        # Apply jumping
        if jump and session.is_on_ground:
            session.player_velocity_y = -self.config.jump_strength
            session.is_on_ground = False

        # Apply gravity
        if not session.is_on_ground:
            session.player_velocity_y = min(
                session.player_velocity_y + session.level.gravity * Decimal(str(delta_time)), self.config.max_velocity_y
            )

        # Update position based on velocity
        new_x = session.player_x + session.player_velocity_x * Decimal(
            str(delta_time * 10)
        )  # Scale for visible movement
        new_y = session.player_y + session.player_velocity_y * Decimal(str(delta_time * 10))

        # Create player collision box
        player_box = CollisionBox(new_x, new_y, Decimal("24"), Decimal("32"))  # Mario size

        # Check collisions with solid objects
        session.is_on_ground = False
        collectible_objects = []

        for obj in level_objects:
            obj_box = CollisionBox(obj.x_position, obj.y_position, obj.width, obj.height)

            if player_box.intersects(obj_box):
                if obj.is_collectible and obj.id not in session.collected_objects:
                    collectible_objects.append(obj)
                elif obj.is_solid:
                    # Handle solid collision
                    overlap_x, overlap_y = player_box.get_overlap(obj_box)

                    if overlap_x < overlap_y:
                        # Horizontal collision
                        if session.player_velocity_x > 0:
                            new_x = obj.x_position - Decimal("24")  # Player width
                        else:
                            new_x = obj.x_position + obj.width
                        session.player_velocity_x = Decimal("0")
                    else:
                        # Vertical collision
                        if session.player_velocity_y > 0:
                            # Landing on top of platform
                            new_y = obj.y_position - Decimal("32")  # Player height
                            session.player_velocity_y = Decimal("0")
                            session.is_on_ground = True
                        else:
                            # Hitting platform from below
                            new_y = obj.y_position + obj.height
                            session.player_velocity_y = Decimal("0")

        # Handle collectibles
        for obj in collectible_objects:
            if obj.id not in session.collected_objects:
                session.collected_objects.append(obj.id)
                session.coins_collected += 1
                session.current_score += obj.points_value

        # Update player state
        if session.is_on_ground:
            if abs(session.player_velocity_x) > Decimal("0.1"):
                session.player_state = PlayerState.RUNNING
            else:
                session.player_state = PlayerState.IDLE
        else:
            if session.player_velocity_y < 0:
                session.player_state = PlayerState.JUMPING
            else:
                session.player_state = PlayerState.FALLING

        # Prevent falling through the bottom of the level
        if new_y > session.level.height:
            # Player fell off the level - lose a life
            session.lives_remaining -= 1
            if session.lives_remaining <= 0:
                session.is_game_over = True
            else:
                # Respawn at start
                new_x = session.level.player_spawn_x
                new_y = session.level.player_spawn_y
                session.player_velocity_x = Decimal("0")
                session.player_velocity_y = Decimal("0")

        # Keep player within level bounds horizontally
        new_x = max(Decimal("0"), min(new_x, session.level.width - Decimal("24")))

        # Update final position
        session.player_x = new_x
        session.player_y = new_y

        return session
