from nicegui import ui
from typing import Dict, Optional
import json
import logging
from datetime import datetime

from app.game_service import GameService, GamePhysics
from app.models import GameSession, GameConfig, GameObject


class MarioGame:
    """Main Mario game UI component"""

    def __init__(self):
        self.game_service = GameService()
        self.current_session: Optional[GameSession] = None
        self.current_config: Optional[GameConfig] = None
        self.level_objects: list[GameObject] = []
        self.keys_pressed: Dict[str, bool] = {}
        self.game_loop_running = False
        self.canvas_element = None
        self.last_update = datetime.now()
        self.camera_x = 0  # Camera offset for scrolling

    def create_game_ui(self):
        """Create the main game interface"""

        # Apply Mario-themed colors
        ui.colors(
            primary="#dc2626",  # Mario red
            secondary="#1d4ed8",  # Mario blue
            accent="#fbbf24",  # Coin gold
            positive="#10b981",  # Success green
            negative="#ef4444",  # Game over red
        )

        with ui.column().classes("w-full h-screen bg-gradient-to-b from-sky-300 to-sky-500"):
            # Game header
            with ui.row().classes("w-full justify-between items-center p-4 bg-gray-900 text-white"):
                ui.label("Super Mario Web").classes("text-2xl font-bold")

                with ui.row().classes("gap-6"):
                    self.score_label = ui.label("Score: 0").classes("text-lg font-mono")
                    self.coins_label = ui.label("Coins: 0").classes("text-lg font-mono")
                    self.lives_label = ui.label("Lives: 3").classes("text-lg font-mono")
                    self.time_label = ui.label("Time: 400").classes("text-lg font-mono")

            # Game canvas container
            with ui.card().classes("flex-1 w-full max-w-6xl mx-auto p-0 overflow-hidden"):
                # Game canvas
                self.canvas_element = ui.html("""
                    <canvas id="gameCanvas" width="800" height="400" 
                            style="border: 2px solid #333; display: block; cursor: crosshair;">
                        Your browser does not support HTML5 Canvas
                    </canvas>
                """).classes("w-full")

                # Add keyboard event handling
                ui.add_head_html("""
                    <script>
                        const gameKeys = {};
                        
                        document.addEventListener('keydown', (e) => {
                            gameKeys[e.key] = true;
                            if(['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', ' '].includes(e.key)) {
                                e.preventDefault();
                            }
                        });
                        
                        document.addEventListener('keyup', (e) => {
                            gameKeys[e.key] = false;
                        });
                        
                        window.getGameKeys = () => gameKeys;
                        
                        // Make canvas focusable
                        document.addEventListener('DOMContentLoaded', () => {
                            const canvas = document.getElementById('gameCanvas');
                            if (canvas) {
                                canvas.setAttribute('tabindex', '0');
                                canvas.focus();
                            }
                        });
                    </script>
                """)

            # Game controls
            with ui.row().classes("w-full justify-center gap-4 p-4"):
                ui.button("New Game", on_click=self.start_new_game).classes(
                    "bg-primary text-white px-6 py-3 text-lg font-bold"
                )
                ui.button("Pause/Resume", on_click=self.toggle_pause).classes("bg-secondary text-white px-6 py-3")

            # Controls instructions
            with ui.card().classes("w-full max-w-2xl mx-auto p-4"):
                ui.label("Controls").classes("text-lg font-bold mb-2")
                with ui.grid(columns=3).classes("gap-4 text-sm"):
                    ui.label("← → or A/D: Move left/right")
                    ui.label("↑ or W or Space: Jump")
                    ui.label("Collect all the golden coins!")

        # Initialize canvas rendering
        ui.timer(0.1, self.setup_canvas, once=True)  # Setup after DOM is ready

        # Start game loop
        ui.timer(1 / 60, self.game_loop)  # 60 FPS

    async def setup_canvas(self):
        """Initialize the game canvas and rendering context"""
        await ui.run_javascript("""
            const canvas = document.getElementById('gameCanvas');
            if (canvas) {
                const ctx = canvas.getContext('2d');
                
                // Store context globally for game rendering
                window.gameCanvas = canvas;
                window.gameCtx = ctx;
                
                // Set canvas size
                canvas.width = 800;
                canvas.height = 400;
                
                console.log('Game canvas initialized');
            }
        """)

    async def start_new_game(self):
        """Start a new game session"""
        try:
            # Get or create player and level
            player = self.game_service.get_or_create_player()
            level = self.game_service.get_or_create_default_level()
            self.current_config = self.game_service.get_or_create_game_config()

            # Start new session
            if player.id is not None and level.id is not None:
                self.current_session = self.game_service.start_new_session(player.id, level.id)
            else:
                raise ValueError("Failed to create player or level")
            if level.id is not None:
                self.level_objects = self.game_service.get_level_objects(level.id)
            else:
                raise ValueError("Level ID is None")

            # Reset camera
            self.camera_x = 0

            # Start game loop
            self.game_loop_running = True

            ui.notify("New game started! Use arrow keys or WASD to move and jump.", type="positive")

        except Exception as e:
            logging.error(f"Error starting game: {e}")
            ui.notify(f"Error starting game: {e}", type="negative")

    def toggle_pause(self):
        """Toggle game pause state"""
        self.game_loop_running = not self.game_loop_running
        status = "resumed" if self.game_loop_running else "paused"
        ui.notify(f"Game {status}", type="info")

    async def game_loop(self):
        """Main game loop - runs at 60 FPS"""
        if not self.game_loop_running or not self.current_session or not self.current_config:
            return

        try:
            # Get current keys state from browser
            keys_result = await ui.run_javascript("return window.getGameKeys ? window.getGameKeys() : {}")
            if keys_result:
                self.keys_pressed = keys_result

            # Calculate delta time
            now = datetime.now()
            delta_time = (now - self.last_update).total_seconds()
            self.last_update = now

            # Update physics
            physics = GamePhysics(self.current_config)
            self.current_session = physics.update_player_physics(
                self.current_session, self.level_objects, self.keys_pressed, delta_time
            )

            # Update camera to follow player
            self.update_camera()

            # Update UI labels
            self.update_ui_display()

            # Render game frame
            await self.render_game()

            # Check win condition
            total_coins = sum(1 for obj in self.level_objects if obj.object_type.value == "coin")
            if self.current_session.coins_collected >= total_coins:
                self.current_session.is_completed = True
                self.game_loop_running = False
                ui.notify("Congratulations! You collected all coins!", type="positive")

            # Check game over condition
            if self.current_session.is_game_over:
                self.game_loop_running = False
                ui.notify("Game Over! Click New Game to try again.", type="negative")

        except Exception as e:
            logging.error(f"Game loop error: {e}")

    def update_camera(self):
        """Update camera position to follow player"""
        if not self.current_session:
            return

        # Center camera on player with some offset
        target_camera_x = float(self.current_session.player_x) - 400  # Center of 800px canvas

        # Smooth camera movement
        camera_speed = 0.1
        self.camera_x += (target_camera_x - self.camera_x) * camera_speed

        # Keep camera within level bounds
        max_camera_x = float(self.current_session.level.width) - 800
        self.camera_x = max(0, min(self.camera_x, max_camera_x))

    def update_ui_display(self):
        """Update the UI display with current game state"""
        if not self.current_session:
            return

        self.score_label.set_text(f"Score: {self.current_session.current_score}")
        self.coins_label.set_text(f"Coins: {self.current_session.coins_collected}")
        self.lives_label.set_text(f"Lives: {self.current_session.lives_remaining}")
        self.time_label.set_text(f"Time: {self.current_session.time_remaining}")

    async def render_game(self):
        """Render the current game frame to canvas"""
        if not self.current_session:
            return

        try:
            # Prepare render data
            render_data = {
                "player": {
                    "x": float(self.current_session.player_x),
                    "y": float(self.current_session.player_y),
                    "facing_right": self.current_session.is_facing_right,
                    "state": self.current_session.player_state.value,
                },
                "camera_x": self.camera_x,
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.object_type.value,
                        "x": float(obj.x_position),
                        "y": float(obj.y_position),
                        "width": float(obj.width),
                        "height": float(obj.height),
                        "color": obj.color,
                        "collected": obj.id in self.current_session.collected_objects,
                    }
                    for obj in self.level_objects
                ],
                "level": {
                    "width": float(self.current_session.level.width),
                    "height": float(self.current_session.level.height),
                    "background_color": self.current_session.level.background_color,
                },
            }

            # Render using JavaScript
            await ui.run_javascript(f"""
                const canvas = window.gameCanvas;
                const ctx = window.gameCtx;
                
                if (!canvas || !ctx) return;
                
                const data = {json.dumps(render_data)};
                
                // Clear canvas with sky background
                ctx.fillStyle = data.level.background_color;
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                // Draw clouds (simple decoration)
                ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
                for (let i = 0; i < 3; i++) {{
                    const cloudX = (i * 300 + 100 - data.camera_x * 0.5) % (canvas.width + 100);
                    ctx.beginPath();
                    ctx.arc(cloudX, 80, 30, 0, Math.PI * 2);
                    ctx.arc(cloudX + 25, 80, 35, 0, Math.PI * 2);
                    ctx.arc(cloudX + 50, 80, 30, 0, Math.PI * 2);
                    ctx.fill();
                }}
                
                // Draw level objects
                data.objects.forEach(obj => {{
                    if (obj.collected && obj.type === 'coin') return; // Skip collected coins
                    
                    const screenX = obj.x - data.camera_x;
                    const screenY = obj.y;
                    
                    // Only draw if on screen
                    if (screenX + obj.width >= 0 && screenX <= canvas.width) {{
                        ctx.fillStyle = obj.color;
                        
                        if (obj.type === 'coin') {{
                            // Draw coin as circle with shine effect
                            ctx.beginPath();
                            ctx.arc(screenX + obj.width/2, screenY + obj.height/2, obj.width/2, 0, Math.PI * 2);
                            ctx.fill();
                            
                            // Add shine
                            ctx.fillStyle = '#FFFF99';
                            ctx.beginPath();
                            ctx.arc(screenX + obj.width/2 - 3, screenY + obj.height/2 - 3, 4, 0, Math.PI * 2);
                            ctx.fill();
                        }} else {{
                            // Draw platform as rectangle with border
                            ctx.fillRect(screenX, screenY, obj.width, obj.height);
                            
                            // Add border for platforms
                            ctx.strokeStyle = '#654321';
                            ctx.lineWidth = 2;
                            ctx.strokeRect(screenX, screenY, obj.width, obj.height);
                        }}
                    }}
                }});
                
                // Draw Mario
                const marioScreenX = data.player.x - data.camera_x;
                const marioScreenY = data.player.y;
                
                // Mario body (red)
                ctx.fillStyle = '#DC2626';
                ctx.fillRect(marioScreenX + 2, marioScreenY + 8, 20, 16);
                
                // Mario overalls (blue)
                ctx.fillStyle = '#1D4ED8';
                ctx.fillRect(marioScreenX + 4, marioScreenY + 12, 16, 12);
                
                // Mario face (peach)
                ctx.fillStyle = '#FBBF84';
                ctx.fillRect(marioScreenX + 6, marioScreenY + 4, 12, 8);
                
                // Mario hat (red with darker shade)
                ctx.fillStyle = '#B91C1C';
                ctx.fillRect(marioScreenX + 4, marioScreenY, 16, 8);
                
                // Mario mustache (brown)
                ctx.fillStyle = '#92400E';
                ctx.fillRect(marioScreenX + 8, marioScreenY + 8, 8, 2);
                
                // Mario eyes (black dots)
                ctx.fillStyle = '#000000';
                ctx.fillRect(marioScreenX + 8, marioScreenY + 6, 2, 2);
                ctx.fillRect(marioScreenX + 12, marioScreenY + 6, 2, 2);
                
                // Mario shoes (brown)
                ctx.fillStyle = '#92400E';
                ctx.fillRect(marioScreenX, marioScreenY + 24, 8, 8);
                ctx.fillRect(marioScreenX + 16, marioScreenY + 24, 8, 8);
                
                // Mario direction indicator (simple arrow)
                if (!data.player.facing_right) {{
                    // Flip appearance slightly for left-facing
                    ctx.fillStyle = '#666666';
                    ctx.fillRect(marioScreenX - 2, marioScreenY + 12, 2, 4);
                }} else {{
                    ctx.fillStyle = '#666666'; 
                    ctx.fillRect(marioScreenX + 24, marioScreenY + 12, 2, 4);
                }}
            """)

        except Exception as e:
            logging.error(f"Render error: {e}")


def create():
    """Create the Mario game module"""

    @ui.page("/mario")
    def mario_page():
        game = MarioGame()
        game.create_game_ui()

    # Also update the main page to redirect to Mario
    @ui.page("/")
    def index():
        with ui.column().classes(
            "w-full h-screen items-center justify-center bg-gradient-to-b from-blue-400 to-blue-600"
        ):
            with ui.card().classes("p-8 text-center shadow-xl"):
                ui.label("🍄 Super Mario Web Game 🍄").classes("text-4xl font-bold mb-6 text-red-600")
                ui.label("A classic 2D platformer adventure!").classes("text-xl mb-6 text-gray-600")
                ui.button("Start Playing", on_click=lambda: ui.navigate.to("/mario")).classes(
                    "bg-red-500 hover:bg-red-600 text-white text-xl px-8 py-4 font-bold"
                )

                with ui.row().classes("mt-6 gap-4 text-sm text-gray-500"):
                    ui.label("🎮 Use arrow keys or WASD to move")
                    ui.label("💰 Collect golden coins")
                    ui.label("🏆 Complete the level!")
