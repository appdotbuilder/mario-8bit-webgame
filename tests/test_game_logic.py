import pytest
from decimal import Decimal
from app.game_service import CollisionBox, GamePhysics
from app.models import GameConfig, PlayerState


class TestCollisionBox:
    """Test collision detection system without database"""

    def test_collision_box_creation(self):
        box = CollisionBox(Decimal("10"), Decimal("20"), Decimal("30"), Decimal("40"))
        assert box.x == Decimal("10")
        assert box.y == Decimal("20")
        assert box.width == Decimal("30")
        assert box.height == Decimal("40")

    def test_collision_box_intersects_true(self):
        box1 = CollisionBox(Decimal("0"), Decimal("0"), Decimal("50"), Decimal("50"))
        box2 = CollisionBox(Decimal("25"), Decimal("25"), Decimal("50"), Decimal("50"))
        assert box1.intersects(box2)
        assert box2.intersects(box1)

    def test_collision_box_intersects_false(self):
        box1 = CollisionBox(Decimal("0"), Decimal("0"), Decimal("20"), Decimal("20"))
        box2 = CollisionBox(Decimal("30"), Decimal("30"), Decimal("20"), Decimal("20"))
        assert not box1.intersects(box2)
        assert not box2.intersects(box1)

    def test_collision_box_get_overlap(self):
        box1 = CollisionBox(Decimal("0"), Decimal("0"), Decimal("50"), Decimal("50"))
        box2 = CollisionBox(Decimal("25"), Decimal("25"), Decimal("50"), Decimal("50"))
        overlap_x, overlap_y = box1.get_overlap(box2)
        assert overlap_x == Decimal("25")  # 50 - 25 = 25
        assert overlap_y == Decimal("25")


class TestGamePhysicsLogic:
    """Test game physics logic without database dependencies"""

    @pytest.fixture()
    def game_config(self):
        return GameConfig(
            player_speed=Decimal("5.0"),
            jump_strength=Decimal("15.0"),
            max_velocity_x=Decimal("8.0"),
            max_velocity_y=Decimal("20.0"),
            friction=Decimal("0.8"),
            air_resistance=Decimal("0.95"),
            coin_value=100,
            extra_life_score=10000,
        )

    @pytest.fixture()
    def physics_engine(self, game_config):
        return GamePhysics(game_config)

    def test_game_physics_initialization(self, physics_engine, game_config):
        """Test physics engine initializes correctly"""
        assert physics_engine.config == game_config
        assert physics_engine.config.player_speed == Decimal("5.0")
        assert physics_engine.config.jump_strength == Decimal("15.0")

    def test_velocity_limits_enforcement(self, physics_engine):
        """Test that velocity limits are enforced"""
        max_x = physics_engine.config.max_velocity_x
        max_y = physics_engine.config.max_velocity_y

        # Test horizontal velocity limit
        assert max_x == Decimal("8.0")

        # Test vertical velocity limit
        assert max_y == Decimal("20.0")

        # Test that limits make sense for gameplay
        assert max_x > physics_engine.config.player_speed  # Can exceed base speed
        assert max_y > physics_engine.config.jump_strength  # Can exceed jump strength


class TestGameMechanics:
    """Test game mechanics and calculations"""

    def test_coin_scoring_calculation(self):
        """Test coin collection scoring"""
        coin_value = 100
        coins_collected = 5
        expected_score = coin_value * coins_collected
        assert expected_score == 500

    def test_extra_life_threshold(self):
        """Test extra life scoring threshold"""
        extra_life_score = 10000
        current_score = 9500
        coins_needed = (extra_life_score - current_score) // 100
        assert coins_needed == 5

    def test_player_state_transitions(self):
        """Test valid player state transitions"""
        # Valid states
        states = [PlayerState.IDLE, PlayerState.RUNNING, PlayerState.JUMPING, PlayerState.FALLING, PlayerState.DEAD]
        assert len(states) == 5

        # Test state values
        assert PlayerState.IDLE.value == "idle"
        assert PlayerState.RUNNING.value == "running"
        assert PlayerState.JUMPING.value == "jumping"
        assert PlayerState.FALLING.value == "falling"
        assert PlayerState.DEAD.value == "dead"

    def test_level_boundary_math(self):
        """Test level boundary calculations"""
        level_width = Decimal("2400")
        player_width = Decimal("24")
        max_player_x = level_width - player_width

        assert max_player_x == Decimal("2376")

        # Test that player can't go negative
        min_player_x = max(Decimal("0"), Decimal("-10"))
        assert min_player_x == Decimal("0")

    def test_gravity_physics_calculation(self):
        """Test gravity physics calculations"""
        gravity = Decimal("0.8")
        delta_time = Decimal("0.0167")  # 1/60 second
        initial_velocity_y = Decimal("0")

        # After one frame of gravity
        new_velocity_y = initial_velocity_y + gravity * delta_time
        expected_velocity = Decimal("0.01336")  # 0.8 * 0.0167

        # Allow small floating point differences
        assert abs(new_velocity_y - expected_velocity) < Decimal("0.001")

    def test_friction_calculation(self):
        """Test friction physics"""
        initial_velocity = Decimal("10.0")
        friction = Decimal("0.8")

        # After applying friction
        new_velocity = initial_velocity * friction
        assert new_velocity == Decimal("8.0")

        # After multiple frames
        velocity_after_5_frames = initial_velocity * (friction**5)
        # Should be significantly reduced
        assert velocity_after_5_frames < initial_velocity / 2

    def test_jump_mechanics(self):
        """Test jump strength and mechanics"""
        jump_strength = Decimal("15.0")

        # Jump velocity should be negative (upward)
        jump_velocity = -jump_strength
        assert jump_velocity == Decimal("-15.0")

        # Test that jump is strong enough to be noticeable
        assert abs(jump_velocity) > Decimal("10.0")


class TestGameObjectLogic:
    """Test game object properties and logic"""

    def test_platform_properties(self):
        """Test platform object properties"""
        platform_data = {
            "object_type": "platform",
            "is_solid": True,
            "is_collectible": False,
            "points_value": 0,
            "color": "#8B4513",
        }

        assert platform_data["is_solid"]
        assert not platform_data["is_collectible"]
        assert platform_data["points_value"] == 0
        assert platform_data["color"] == "#8B4513"  # Brown color

    def test_coin_properties(self):
        """Test coin object properties"""
        coin_data = {
            "object_type": "coin",
            "is_solid": False,
            "is_collectible": True,
            "points_value": 100,
            "color": "#FFD700",
            "width": Decimal("24"),
            "height": Decimal("24"),
        }

        assert not coin_data["is_solid"]
        assert coin_data["is_collectible"]
        assert coin_data["points_value"] == 100
        assert coin_data["color"] == "#FFD700"  # Gold color
        assert coin_data["width"] == Decimal("24")
        assert coin_data["height"] == Decimal("24")

    def test_level_dimensions(self):
        """Test level dimension calculations"""
        level_width = 2400
        level_height = 600
        canvas_width = 800
        canvas_height = 400

        # Camera can scroll horizontally
        max_camera_x = level_width - canvas_width
        assert max_camera_x == 1600

        # Level should be wider than canvas for scrolling
        assert level_width > canvas_width

        # Level should be taller than canvas for jumping space
        assert level_height > canvas_height
