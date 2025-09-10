from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum


class GameObjectType(str, Enum):
    """Types of game objects that can be placed in levels"""

    PLATFORM = "platform"
    COIN = "coin"
    ENEMY = "enemy"
    POWER_UP = "power_up"
    FLAG = "flag"


class PlayerState(str, Enum):
    """Player character states"""

    IDLE = "idle"
    RUNNING = "running"
    JUMPING = "jumping"
    FALLING = "falling"
    DEAD = "dead"


# Persistent models (stored in database)
class Player(SQLModel, table=True):
    """Player character model - tracks Mario's persistent data"""

    __tablename__ = "players"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50, default="Mario")
    total_coins_collected: int = Field(default=0)
    total_score: int = Field(default=0)
    highest_level: int = Field(default=1)
    lives: int = Field(default=3)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    game_sessions: List["GameSession"] = Relationship(back_populates="player")


class GameLevel(SQLModel, table=True):
    """Game level definition with layout and metadata"""

    __tablename__ = "game_levels"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    level_number: int = Field(unique=True)
    width: int = Field(default=1920)  # Level width in pixels
    height: int = Field(default=600)  # Level height in pixels
    background_color: str = Field(default="#87CEEB", max_length=7)  # Sky blue
    gravity: Decimal = Field(default=Decimal("0.8"))  # Gravity strength
    player_spawn_x: Decimal = Field(default=Decimal("100"))  # Player start X position
    player_spawn_y: Decimal = Field(default=Decimal("400"))  # Player start Y position
    time_limit: int = Field(default=400)  # Time limit in seconds
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    game_objects: List["GameObject"] = Relationship(back_populates="level")
    game_sessions: List["GameSession"] = Relationship(back_populates="level")


class GameObject(SQLModel, table=True):
    """Generic game object that can be platforms, coins, enemies, etc."""

    __tablename__ = "game_objects"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    level_id: int = Field(foreign_key="game_levels.id")
    object_type: GameObjectType
    x_position: Decimal = Field(decimal_places=2)  # X coordinate in pixels
    y_position: Decimal = Field(decimal_places=2)  # Y coordinate in pixels
    width: Decimal = Field(decimal_places=2, default=Decimal("32"))  # Width in pixels
    height: Decimal = Field(decimal_places=2, default=Decimal("32"))  # Height in pixels
    color: str = Field(default="#8B4513", max_length=7)  # Brown for platforms
    is_solid: bool = Field(default=True)  # Whether player can pass through
    is_collectible: bool = Field(default=False)  # Whether object can be collected
    points_value: int = Field(default=0)  # Points awarded when collected
    properties: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Additional properties

    # Relationships
    level: GameLevel = Relationship(back_populates="game_objects")


class GameSession(SQLModel, table=True):
    """Individual game session tracking progress through a level"""

    __tablename__ = "game_sessions"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="players.id")
    level_id: int = Field(foreign_key="game_levels.id")
    current_score: int = Field(default=0)
    coins_collected: int = Field(default=0)
    lives_remaining: int = Field(default=3)
    time_remaining: int = Field(default=400)  # Time left in seconds
    player_x: Decimal = Field(decimal_places=2, default=Decimal("100"))  # Current X position
    player_y: Decimal = Field(decimal_places=2, default=Decimal("400"))  # Current Y position
    player_velocity_x: Decimal = Field(decimal_places=2, default=Decimal("0"))  # X velocity
    player_velocity_y: Decimal = Field(decimal_places=2, default=Decimal("0"))  # Y velocity
    player_state: PlayerState = Field(default=PlayerState.IDLE)
    is_facing_right: bool = Field(default=True)  # Direction player is facing
    is_on_ground: bool = Field(default=False)  # Whether player is on ground
    is_completed: bool = Field(default=False)
    is_game_over: bool = Field(default=False)
    collected_objects: List[int] = Field(default=[], sa_column=Column(JSON))  # IDs of collected objects
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    # Relationships
    player: Player = Relationship(back_populates="game_sessions")
    level: GameLevel = Relationship(back_populates="game_sessions")


class GameConfig(SQLModel, table=True):
    """Global game configuration settings"""

    __tablename__ = "game_config"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    player_speed: Decimal = Field(default=Decimal("5.0"), decimal_places=2)  # Horizontal movement speed
    jump_strength: Decimal = Field(default=Decimal("15.0"), decimal_places=2)  # Jump velocity
    max_velocity_x: Decimal = Field(default=Decimal("8.0"), decimal_places=2)  # Max horizontal velocity
    max_velocity_y: Decimal = Field(default=Decimal("20.0"), decimal_places=2)  # Max vertical velocity
    friction: Decimal = Field(default=Decimal("0.8"), decimal_places=2)  # Ground friction
    air_resistance: Decimal = Field(default=Decimal("0.95"), decimal_places=2)  # Air resistance
    coin_value: int = Field(default=100)  # Points per coin
    extra_life_score: int = Field(default=10000)  # Score needed for extra life
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Non-persistent schemas (for validation, forms, API requests/responses)
class PlayerCreate(SQLModel, table=False):
    """Schema for creating a new player"""

    name: str = Field(max_length=50, default="Mario")


class PlayerUpdate(SQLModel, table=False):
    """Schema for updating player data"""

    name: Optional[str] = Field(default=None, max_length=50)
    total_coins_collected: Optional[int] = Field(default=None)
    total_score: Optional[int] = Field(default=None)
    highest_level: Optional[int] = Field(default=None)
    lives: Optional[int] = Field(default=None)


class GameLevelCreate(SQLModel, table=False):
    """Schema for creating a new game level"""

    name: str = Field(max_length=100)
    level_number: int
    width: int = Field(default=1920)
    height: int = Field(default=600)
    background_color: str = Field(default="#87CEEB", max_length=7)
    gravity: Decimal = Field(default=Decimal("0.8"))
    player_spawn_x: Decimal = Field(default=Decimal("100"))
    player_spawn_y: Decimal = Field(default=Decimal("400"))
    time_limit: int = Field(default=400)


class GameObjectCreate(SQLModel, table=False):
    """Schema for creating game objects"""

    level_id: int
    object_type: GameObjectType
    x_position: Decimal = Field(decimal_places=2)
    y_position: Decimal = Field(decimal_places=2)
    width: Decimal = Field(decimal_places=2, default=Decimal("32"))
    height: Decimal = Field(decimal_places=2, default=Decimal("32"))
    color: str = Field(default="#8B4513", max_length=7)
    is_solid: bool = Field(default=True)
    is_collectible: bool = Field(default=False)
    points_value: int = Field(default=0)
    properties: Dict[str, Any] = Field(default={})


class GameSessionCreate(SQLModel, table=False):
    """Schema for starting a new game session"""

    player_id: int
    level_id: int


class GameSessionUpdate(SQLModel, table=False):
    """Schema for updating game session state"""

    current_score: Optional[int] = Field(default=None)
    coins_collected: Optional[int] = Field(default=None)
    lives_remaining: Optional[int] = Field(default=None)
    time_remaining: Optional[int] = Field(default=None)
    player_x: Optional[Decimal] = Field(default=None, decimal_places=2)
    player_y: Optional[Decimal] = Field(default=None, decimal_places=2)
    player_velocity_x: Optional[Decimal] = Field(default=None, decimal_places=2)
    player_velocity_y: Optional[Decimal] = Field(default=None, decimal_places=2)
    player_state: Optional[PlayerState] = Field(default=None)
    is_facing_right: Optional[bool] = Field(default=None)
    is_on_ground: Optional[bool] = Field(default=None)
    is_completed: Optional[bool] = Field(default=None)
    is_game_over: Optional[bool] = Field(default=None)
    collected_objects: Optional[List[int]] = Field(default=None)


class GameStateSnapshot(SQLModel, table=False):
    """Non-persistent model for real-time game state"""

    session_id: int
    player_x: Decimal = Field(decimal_places=2)
    player_y: Decimal = Field(decimal_places=2)
    player_velocity_x: Decimal = Field(decimal_places=2)
    player_velocity_y: Decimal = Field(decimal_places=2)
    player_state: PlayerState
    is_facing_right: bool
    is_on_ground: bool
    current_score: int
    coins_collected: int
    lives_remaining: int
    time_remaining: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
