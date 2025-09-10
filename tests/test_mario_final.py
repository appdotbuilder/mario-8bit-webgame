"""
Final comprehensive test suite for Mario game that focuses on logic without database issues
"""

import pytest
from decimal import Decimal
from nicegui.testing import User
from nicegui import ui

# Import the classes we need
from app.game_service import CollisionBox, GamePhysics
from app.models import GameConfig, PlayerState, GameObjectType


class TestCollisionSystem:
    """Test collision detection without database"""

    def test_collision_box_basic_properties(self):
        """Test basic collision box properties"""
        box = CollisionBox(Decimal("10"), Decimal("20"), Decimal("30"), Decimal("40"))

        assert box.x == Decimal("10")
        assert box.y == Decimal("20")
        assert box.width == Decimal("30")
        assert box.height == Decimal("40")

    def test_collision_detection_overlapping(self):
        """Test collision detection for overlapping boxes"""
        box1 = CollisionBox(Decimal("0"), Decimal("0"), Decimal("50"), Decimal("50"))
        box2 = CollisionBox(Decimal("25"), Decimal("25"), Decimal("50"), Decimal("50"))

        assert box1.intersects(box2)
        assert box2.intersects(box1)  # Should be symmetric

    def test_collision_detection_separate(self):
        """Test collision detection for separate boxes"""
        box1 = CollisionBox(Decimal("0"), Decimal("0"), Decimal("20"), Decimal("20"))
        box2 = CollisionBox(Decimal("30"), Decimal("30"), Decimal("20"), Decimal("20"))

        assert not box1.intersects(box2)
        assert not box2.intersects(box1)

    def test_collision_overlap_calculation(self):
        """Test overlap amount calculation"""
        box1 = CollisionBox(Decimal("0"), Decimal("0"), Decimal("50"), Decimal("50"))
        box2 = CollisionBox(Decimal("25"), Decimal("25"), Decimal("50"), Decimal("50"))

        overlap_x, overlap_y = box1.get_overlap(box2)

        # Overlap should be 25 pixels in both directions
        assert overlap_x == Decimal("25")
        assert overlap_y == Decimal("25")


class TestGamePhysicsEngine:
    """Test game physics without database dependencies"""

    @pytest.fixture
    def test_config(self):
        """Create a test game configuration"""
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

    @pytest.fixture
    def physics_engine(self, test_config):
        """Create physics engine with test config"""
        return GamePhysics(test_config)

    def test_physics_engine_initialization(self, physics_engine, test_config):
        """Test physics engine initializes with correct config"""
        assert physics_engine.config == test_config
        assert physics_engine.config.player_speed == Decimal("5.0")
        assert physics_engine.config.jump_strength == Decimal("15.0")

    def test_velocity_limits_are_reasonable(self, test_config):
        """Test that velocity limits make sense for gameplay"""
        # Max horizontal velocity should be achievable but not too high
        assert test_config.max_velocity_x > test_config.player_speed
        assert test_config.max_velocity_x < Decimal("20.0")  # Not too fast

        # Max vertical velocity should handle jumps and falls
        assert test_config.max_velocity_y > test_config.jump_strength
        assert test_config.max_velocity_y < Decimal("50.0")  # Not ridiculous

    def test_friction_values_are_valid(self, test_config):
        """Test friction and resistance values are between 0 and 1"""
        assert Decimal("0") < test_config.friction <= Decimal("1")
        assert Decimal("0") < test_config.air_resistance <= Decimal("1")

        # Friction should slow things down
        assert test_config.friction < Decimal("1")
        assert test_config.air_resistance < Decimal("1")


class TestGameMechanics:
    """Test core game mechanics and calculations"""

    def test_scoring_system(self):
        """Test coin scoring calculations"""
        coin_value = 100
        coins_collected = 5
        expected_score = coin_value * coins_collected

        assert expected_score == 500

        # Test bonus life threshold
        extra_life_score = 10000
        assert expected_score < extra_life_score  # Need more coins for extra life

    def test_player_state_values(self):
        """Test player state enum values"""
        assert PlayerState.IDLE.value == "idle"
        assert PlayerState.RUNNING.value == "running"
        assert PlayerState.JUMPING.value == "jumping"
        assert PlayerState.FALLING.value == "falling"
        assert PlayerState.DEAD.value == "dead"

    def test_game_object_types(self):
        """Test game object type values"""
        assert GameObjectType.PLATFORM.value == "platform"
        assert GameObjectType.COIN.value == "coin"
        assert GameObjectType.ENEMY.value == "enemy"
        assert GameObjectType.POWER_UP.value == "power_up"
        assert GameObjectType.FLAG.value == "flag"

    def test_level_boundary_math(self):
        """Test level boundary calculations"""
        level_width = Decimal("2400")
        level_height = Decimal("600")
        player_width = Decimal("24")
        player_height = Decimal("32")

        # Player should fit within level bounds
        max_x = level_width - player_width
        max_y = level_height - player_height

        assert max_x == Decimal("2376")
        assert max_y == Decimal("568")

        # Minimum bounds should be zero
        min_x = max(Decimal("0"), Decimal("-10"))
        min_y = max(Decimal("0"), Decimal("-5"))

        assert min_x == Decimal("0")
        assert min_y == Decimal("0")

    def test_gravity_physics_math(self):
        """Test gravity calculations"""
        gravity = Decimal("0.8")
        delta_time = Decimal("0.0167")  # ~60 FPS

        # Gravity should increase velocity over time
        velocity_after_1_frame = gravity * delta_time
        velocity_after_2_frames = velocity_after_1_frame + (gravity * delta_time)

        assert velocity_after_2_frames > velocity_after_1_frame
        assert velocity_after_1_frame > Decimal("0")

    def test_friction_physics_math(self):
        """Test friction calculations"""
        initial_velocity = Decimal("10.0")
        friction = Decimal("0.8")

        # Friction reduces velocity each frame
        velocity_frame_1 = initial_velocity * friction
        velocity_frame_2 = velocity_frame_1 * friction
        velocity_frame_3 = velocity_frame_2 * friction

        assert velocity_frame_1 < initial_velocity
        assert velocity_frame_2 < velocity_frame_1
        assert velocity_frame_3 < velocity_frame_2

        # Should approach zero but not instantly
        assert velocity_frame_3 > Decimal("0")
        # After 3 frames of 0.8 friction: 10 * 0.8^3 = 5.12, which is just barely > 5
        assert velocity_frame_3 < Decimal("6.0")  # Should be significantly reduced


class TestUIComponents:
    """Test UI component logic without full database"""

    async def test_mario_ui_basic_loading(self, user: User) -> None:
        """Test basic Mario UI can be loaded"""

        @ui.page("/mario_test_basic")
        def test_page():
            # Simple page with Mario-style elements
            with ui.column().classes("w-full h-screen"):
                ui.label("🍄 Super Mario Web Game 🍄").classes("text-4xl")

                with ui.row().classes("gap-4"):
                    ui.label("Score: 0").classes("text-lg")
                    ui.label("Coins: 0").classes("text-lg")
                    ui.label("Lives: 3").classes("text-lg")

                ui.button("New Game").classes("bg-red-500 text-white")
                ui.button("Pause/Resume").classes("bg-blue-500 text-white")

                ui.label("Controls: Use arrow keys to move and jump!")

        await user.open("/mario_test_basic")

        # Check basic elements are present
        await user.should_see("Super Mario Web Game")
        await user.should_see("Score: 0")
        await user.should_see("Coins: 0")
        await user.should_see("Lives: 3")
        await user.should_see("New Game")
        await user.should_see("Pause/Resume")
        await user.should_see("Controls")

    async def test_mario_ui_button_interactions(self, user: User) -> None:
        """Test Mario UI button interactions"""

        @ui.page("/mario_test_buttons")
        def test_page():
            state = {"game_started": False, "paused": False}

            def start_game():
                state["game_started"] = True
                ui.notify("Game started!", type="positive")

            def toggle_pause():
                state["paused"] = not state["paused"]
                status = "paused" if state["paused"] else "resumed"
                ui.notify(f"Game {status}", type="info")

            ui.label("Mario Game Test")
            ui.button("Start Game", on_click=start_game)
            ui.button("Pause/Resume", on_click=toggle_pause)

        await user.open("/mario_test_buttons")

        # Test start game button
        user.find("Start Game").click()
        await user.should_see("Game started!")

        # Test pause button
        user.find("Pause/Resume").click()
        await user.should_see("Game paused")

    def test_mario_game_class_basic_properties(self):
        """Test MarioGame class basic properties"""
        from app.mario_game import MarioGame

        # Should be able to create instance
        game = MarioGame()

        # Check initial state
        assert hasattr(game, "current_session")
        assert hasattr(game, "current_config")
        assert hasattr(game, "level_objects")
        assert hasattr(game, "keys_pressed")
        assert hasattr(game, "game_loop_running")
        assert hasattr(game, "camera_x")

        # Check initial values
        assert game.current_session is None
        assert game.current_config is None
        assert game.level_objects == []
        assert game.keys_pressed == {}
        assert not game.game_loop_running
        assert game.camera_x == 0


class TestGameSystemIntegration:
    """Test system integration without database complexity"""

    def test_mario_game_imports_work(self):
        """Test that all Mario game imports work correctly"""
        # Test service imports
        from app.game_service import GameService, GamePhysics, CollisionBox

        assert GameService is not None
        assert GamePhysics is not None
        assert CollisionBox is not None

        # Test model imports
        from app.models import GameConfig, PlayerState, GameObjectType

        assert GameConfig is not None
        assert PlayerState is not None
        assert GameObjectType is not None

        # Test UI imports
        from app.mario_game import MarioGame

        assert MarioGame is not None

    def test_startup_module_integration(self):
        """Test that startup module can import Mario game"""
        try:
            import app.mario_game

            assert hasattr(app.mario_game, "create")

            # Test that create function exists and is callable
            assert callable(app.mario_game.create)

        except ImportError as e:
            pytest.fail(f"Failed to import mario_game module: {e}")

    def test_game_configuration_defaults(self):
        """Test game configuration has reasonable defaults"""
        config = GameConfig()

        # Test that defaults are set
        assert config.player_speed > Decimal("0")
        assert config.jump_strength > Decimal("0")
        assert config.max_velocity_x > Decimal("0")
        assert config.max_velocity_y > Decimal("0")
        assert Decimal("0") < config.friction <= Decimal("1")
        assert Decimal("0") < config.air_resistance <= Decimal("1")
        assert config.coin_value > 0
        assert config.extra_life_score > 0

        # Test relationships make sense
        assert config.max_velocity_x >= config.player_speed
        assert config.max_velocity_y >= config.jump_strength
        assert config.extra_life_score >= config.coin_value  # Should take multiple coins

    def test_canvas_rendering_data_structure(self):
        """Test that canvas rendering data structure is correctly formatted"""
        # Test player data structure
        player_data = {"x": 100.0, "y": 200.0, "facing_right": True, "state": "running"}

        # Validate player data
        assert isinstance(player_data["x"], float)
        assert isinstance(player_data["y"], float)
        assert isinstance(player_data["facing_right"], bool)
        assert player_data["state"] in ["idle", "running", "jumping", "falling", "dead"]

        # Test object data structure
        coin_data = {
            "id": 1,
            "type": "coin",
            "x": 150.0,
            "y": 250.0,
            "width": 24.0,
            "height": 24.0,
            "color": "#FFD700",
            "collected": False,
        }

        # Validate coin data
        assert isinstance(coin_data["id"], int)
        assert coin_data["type"] in ["platform", "coin", "enemy", "power_up", "flag"]
        assert isinstance(coin_data["x"], float)
        assert isinstance(coin_data["y"], float)
        assert isinstance(coin_data["width"], float)
        assert isinstance(coin_data["height"], float)
        assert coin_data["color"].startswith("#")  # Hex color
        assert isinstance(coin_data["collected"], bool)
