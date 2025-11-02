import pygame
import random
import math
import os
from settings import *
from player import Player, Camera
from enemy import Enemy
from projectile import Projectile
from experience import Experience, LevelUpEffect
from utils import pause_menu, splitscreen_game_over, show_victory_screen
from maps import Map
from ui import HealthBar, MoneyDisplay, XPBar, SplitScreenUI, InteractionButton, render_text_with_border, SkillBar, MiniMap, DevilShop
from settings import load_font
from particles import ParticleSystem
from partner import Partner
from player2 import Player2
from hit_effects import RockHitEffect
from devil import Devil
from gollux_boss import Gollux  # Import Gollux boss class
from bi_enemy import BiEnemy
from bi_projectile import BiProjectile
from skill import update_sound_manager, Skill, available_skills

def create_blur_surface(surface):
    scale = 0.25
    small_surface = pygame.transform.scale(surface, 
        (int(surface.get_width() * scale), int(surface.get_height() * scale)))
    return pygame.transform.scale(small_surface, 
        (surface.get_width(), surface.get_height()))

# Tambahkan fungsi helper untuk aktivasi skill yang konsisten
def activate_player_skill(player, skill, enemies, all_sprites, skill_effects):
    """Helper function to consistently activate skills for any player"""
    effect = None
    
    if skill:
        if skill.name == "Heal":
            effect = skill.activate(player, enemies=enemies)
        elif skill.name == "Nuke":
            effect = skill.activate(player, enemies=enemies)
            # Set variable pada effect untuk menandai blocking spawns
            if effect:
                effect.block_enemy_spawns = True
        elif skill.name == "Thunder Strike":
            effect = skill.activate(player.rect.center, enemies=enemies)
        else:
            effect = skill.activate(player.rect.center, enemies=enemies)
        
        if effect:
            all_sprites.add(effect)
            skill_effects.add(effect)
            return True
    return False

# Tambahkan konstanta untuk kontrol yang lebih jelas
PLAYER1_SKILL_KEY = pygame.K_1        # Tombol "1" untuk Player 1
PLAYER2_SKILL_KEY = pygame.K_RCTRL    # Tombol "Right Ctrl" untuk Player 2
MENU_KEY = pygame.K_ESCAPE
TOGGLE_CHEAT_KEY = pygame.K_BACKQUOTE  # Tombol ` (backtick) untuk toggle cheat console

# Remove or comment out devil-related classes and constants:
# SHOP_INTERACT_KEY = pygame.K_e
# PLAYER1_BUY_KEY = pygame.K_RETURN
# PLAYER2_BUY_KEY = pygame.K_SLASH
# ShopInteractionManager, update_interaction_button_class, enhance_devil_shop

# Keep CoopUIManager class as it's used for UI, but remove devil-related parts

class CoopUIManager:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.split_width = width // 2
        
        # Initialize UI components
        self.mini_map1 = MiniMap(0, 0, width, height, player_id=1, position="left")
        self.mini_map2 = MiniMap(0, 0, width, height, player_id=2, position="right")
        self.skill_bar1 = SkillBar(player_id=1, position="left", mode="coop")
        self.skill_bar2 = SkillBar(player_id=2, position="right", mode="coop")
        
        # Divider settings
        self.divider_width = 4
        self.divider_color = (255, 215, 0)  # Gold color
        self.shadow_width = 2
        self.shadow_color = (100, 100, 100, 128)
        
    def set_map_dimensions(self, map_width, map_height):
        """Update map dimensions for minimaps"""
        self.mini_map1.update_map_size(map_width, map_height)
        self.mini_map2.update_map_size(map_width, map_height)
    
    def set_players(self, player1, player2):
        """Set player references for skill bars"""
        self.skill_bar1.player = player1
        self.skill_bar2.player = player2
    
    def draw_divider(self, screen):
        """Draw the central divider in split screen mode"""
        divider_rect = pygame.Rect(
            self.width//2 - self.divider_width//2, 
            0, 
            self.divider_width, 
            self.height
        )
        pygame.draw.rect(screen, self.divider_color, divider_rect)
        
        # Add shadow effects
        pygame.draw.rect(
            screen, 
            self.shadow_color, 
            pygame.Rect(
                self.width//2 - self.divider_width//2 - self.shadow_width, 
                0, 
                self.shadow_width, 
                self.height
            )
        )
        pygame.draw.rect(
            screen, 
            self.shadow_color, 
            pygame.Rect(
                self.width//2 + self.divider_width//2, 
                0, 
                self.shadow_width, 
                self.height
            )
        )
    
    def get_viewports(self):
        """Return the viewport rectangles for split screen mode"""
        left_viewport = pygame.Rect(
            0, 
            0, 
            self.width//2 - self.divider_width//2, 
            self.height
        )
        right_viewport = pygame.Rect(
            self.width//2 + self.divider_width//2, 
            0, 
            self.width//2 - self.divider_width//2, 
            self.height
        )
        return left_viewport, right_viewport
    
    def draw(self, screen, player1, player2, enemies, devil, boss, camera):
        """Draw all UI elements based on current screen mode"""
        split_mode = camera.split_mode
        
        if split_mode:
            self.draw_divider(screen)
            left_viewport, right_viewport = self.get_viewports()
            
            # Draw UI for Player 1 (left) if alive
            if player1.health > 0:
                self.mini_map1.adjust_for_split_screen(True, self.split_width)
                self.mini_map1.draw(
                    screen.subsurface(left_viewport), 
                    player1, player2, enemies, devil, boss
                )
                self.skill_bar1.adjust_position(True, self.width)
                self.skill_bar1.draw(screen)
            
            # Draw UI for Player 2 (right) if alive
            if player2.health > 0:
                self.mini_map2.adjust_for_split_screen(True, self.split_width)
                self.mini_map2.draw(
                    screen.subsurface(right_viewport), 
                    player2, player1, enemies, devil, boss
                )
                self.skill_bar2.adjust_position(True, self.width)
                self.skill_bar2.draw(screen)
        else:
            # Single screen mode - draw UI elements that make sense
            if player1.health > 0:
                self.mini_map1.adjust_for_split_screen(False, self.width)
                self.mini_map1.draw(screen, player1, player2, enemies, devil, boss)
                self.skill_bar1.adjust_position(False, self.width)
                self.skill_bar1.draw(screen)
            
            if player2.health > 0:
                # In single screen, only draw player 2's UI if they're alive
                # and place it in a non-conflicting position
                self.mini_map2.adjust_for_split_screen(False, self.width)
                self.mini_map2.draw(screen, player2, player1, enemies, devil, boss)
                self.skill_bar2.adjust_position(False, self.width)
                self.skill_bar2.draw(screen)

# Perbaiki DevilShop untuk mendukung multi-player
def enhance_devil_shop():
    # Add necessary methods to the DevilShop class if they don't exist
    if not hasattr(DevilShop, 'set_active_player'):
        def set_active_player(self, player_id):
            self.active_player_id = player_id
            # Visual feedback for active player
            self.active_indicator_timer = 1.0  # Timer untuk visual feedback
            
        DevilShop.set_active_player = set_active_player
    
    if not hasattr(DevilShop, 'on_active_player_changed'):
        def on_active_player_changed(self):
            # Reset selection atau lakukan aksi lain saat player aktif berubah
            pass
            
        DevilShop.on_active_player_changed = on_active_player_changed
    
    # Enhance purchase method untuk menunjukkan player mana yang membeli
    original_purchase = DevilShop.purchase_item
    
    def enhanced_purchase(self, player, partner, player_id=None):
        # Tambahkan visual feedback untuk player mana yang melakukan pembelian
        result = original_purchase(self, player, partner)
        if result:
            # Tampilkan pesan pembelian berhasil
            self.show_purchase_message = True
            self.purchase_message = f"Player {player_id or 1} purchased item!"
            self.purchase_message_timer = 2.0  # Tampilkan selama 2 detik
        return result
    
    DevilShop.purchase_item = enhanced_purchase

# Perbaiki UI Manager untuk mode single dan split screen
class CoopUIManager:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.split_width = width // 2
        
        # Initialize UI components
        self.mini_map1 = MiniMap(0, 0, width, height, player_id=1, position="left")
        self.mini_map2 = MiniMap(0, 0, width, height, player_id=2, position="right")
        self.skill_bar1 = SkillBar(player_id=1, position="left", mode="coop")
        self.skill_bar2 = SkillBar(player_id=2, position="right", mode="coop")
        
        # Divider settings
        self.divider_width = 4
        self.divider_color = (255, 215, 0)  # Gold color
        self.shadow_width = 2
        self.shadow_color = (100, 100, 100, 128)
        
    def set_map_dimensions(self, map_width, map_height):
        """Update map dimensions for minimaps"""
        self.mini_map1.update_map_size(map_width, map_height)
        self.mini_map2.update_map_size(map_width, map_height)
    
    def set_players(self, player1, player2):
        """Set player references for skill bars"""
        self.skill_bar1.player = player1
        self.skill_bar2.player = player2
    
    def draw_divider(self, screen):
        """Draw the central divider in split screen mode"""
        divider_rect = pygame.Rect(
            self.width//2 - self.divider_width//2, 
            0, 
            self.divider_width, 
            self.height
        )
        pygame.draw.rect(screen, self.divider_color, divider_rect)
        
        # Add shadow effects
        pygame.draw.rect(
            screen, 
            self.shadow_color, 
            pygame.Rect(
                self.width//2 - self.divider_width//2 - self.shadow_width, 
                0, 
                self.shadow_width, 
                self.height
            )
        )
        pygame.draw.rect(
            screen, 
            self.shadow_color, 
            pygame.Rect(
                self.width//2 + self.divider_width//2, 
                0, 
                self.shadow_width, 
                self.height
            )
        )
    
    def get_viewports(self):
        """Return the viewport rectangles for split screen mode"""
        left_viewport = pygame.Rect(
            0, 
            0, 
            self.width//2 - self.divider_width//2, 
            self.height
        )
        right_viewport = pygame.Rect(
            self.width//2 + self.divider_width//2, 
            0, 
            self.width//2 - self.divider_width//2, 
            self.height
        )
        return left_viewport, right_viewport
    
    def draw(self, screen, player1, player2, enemies, devil, boss, camera):
        """Draw all UI elements based on current screen mode"""
        split_mode = camera.split_mode
        
        if split_mode:
            self.draw_divider(screen)
            left_viewport, right_viewport = self.get_viewports()
            
            # Draw UI for Player 1 (left) if alive
            if player1.health > 0:
                self.mini_map1.adjust_for_split_screen(True, self.split_width)
                self.mini_map1.draw(
                    screen.subsurface(left_viewport), 
                    player1, player2, enemies, devil, boss
                )
                self.skill_bar1.adjust_position(True, self.width)
                self.skill_bar1.draw(screen)
            
            # Draw UI for Player 2 (right) if alive
            if player2.health > 0:
                self.mini_map2.adjust_for_split_screen(True, self.split_width)
                self.mini_map2.draw(
                    screen.subsurface(right_viewport), 
                    player2, player1, enemies, devil, boss
                )
                self.skill_bar2.adjust_position(True, self.width)
                self.skill_bar2.draw(screen)
        else:
            # Single screen mode - draw UI elements that make sense
            if player1.health > 0:
                self.mini_map1.adjust_for_split_screen(False, self.width)
                self.mini_map1.draw(screen, player1, player2, enemies, devil, boss)
                self.skill_bar1.adjust_position(False, self.width)
                self.skill_bar1.draw(screen)
            
            if player2.health > 0:
                # In single screen, only draw player 2's UI if they're alive
                # and place it in a non-conflicting position
                self.mini_map2.adjust_for_split_screen(False, self.width)
                self.mini_map2.draw(screen, player2, player1, enemies, devil, boss)
                self.skill_bar2.adjust_position(False, self.width)
                self.skill_bar2.draw(screen)

# Perbaiki DevilShop untuk mendukung multi-player
def enhance_devil_shop():
    # Add necessary methods to the DevilShop class if they don't exist
    if not hasattr(DevilShop, 'set_active_player'):
        def set_active_player(self, player_id):
            self.active_player_id = player_id
            # Visual feedback for active player
            self.active_indicator_timer = 1.0  # Timer untuk visual feedback
            
        DevilShop.set_active_player = set_active_player
    
    if not hasattr(DevilShop, 'on_active_player_changed'):
        def on_active_player_changed(self):
            # Reset selection atau lakukan aksi lain saat player aktif berubah
            pass
            
        DevilShop.on_active_player_changed = on_active_player_changed
    
    # Enhance purchase method untuk menunjukkan player mana yang membeli
    original_purchase = DevilShop.purchase_item
    
    def enhanced_purchase(self, player, partner, player_id=None):
        # Tambahkan visual feedback untuk player mana yang melakukan pembelian
        result = original_purchase(self, player, partner)
        if result:
            # Tampilkan pesan pembelian berhasil
            self.show_purchase_message = True
            self.purchase_message = f"Player {player_id or 1} purchased item!"
            self.purchase_message_timer = 2.0  # Tampilkan selama 2 detik
        return result
    
    DevilShop.purchase_item = enhanced_purchase

# Perbaiki UI Manager untuk mode single dan split screen
class CoopUIManager:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.split_width = width // 2
        
        # Initialize UI components
        self.mini_map1 = MiniMap(0, 0, width, height, player_id=1, position="left")
        self.mini_map2 = MiniMap(0, 0, width, height, player_id=2, position="right")
        self.skill_bar1 = SkillBar(player_id=1, position="left", mode="coop")
        self.skill_bar2 = SkillBar(player_id=2, position="right", mode="coop")
        
        # Divider settings
        self.divider_width = 4
        self.divider_color = (255, 215, 0)  # Gold color
        self.shadow_width = 2
        self.shadow_color = (100, 100, 100, 128)
        
    def set_map_dimensions(self, map_width, map_height):
        """Update map dimensions for minimaps"""
        self.mini_map1.update_map_size(map_width, map_height)
        self.mini_map2.update_map_size(map_width, map_height)
    
    def set_players(self, player1, player2):
        """Set player references for skill bars"""
        self.skill_bar1.player = player1
        self.skill_bar2.player = player2
    
    def draw_divider(self, screen):
        """Draw the central divider in split screen mode"""
        divider_rect = pygame.Rect(
            self.width//2 - self.divider_width//2, 
            0, 
            self.divider_width, 
            self.height
        )
        pygame.draw.rect(screen, self.divider_color, divider_rect)
        
        # Add shadow effects
        pygame.draw.rect(
            screen, 
            self.shadow_color, 
            pygame.Rect(
                self.width//2 - self.divider_width//2 - self.shadow_width, 
                0, 
                self.shadow_width, 
                self.height
            )
        )
        pygame.draw.rect(
            screen, 
            self.shadow_color, 
            pygame.Rect(
                self.width//2 + self.divider_width//2, 
                0, 
                self.shadow_width, 
                self.height
            )
        )
    
    def get_viewports(self):
        """Return the viewport rectangles for split screen mode"""
        left_viewport = pygame.Rect(
            0, 
            0, 
            self.width//2 - self.divider_width//2, 
            self.height
        )
        right_viewport = pygame.Rect(
            self.width//2 + self.divider_width//2, 
            0, 
            self.width//2 - self.divider_width//2, 
            self.height
        )
        return left_viewport, right_viewport
    
    def draw(self, screen, player1, player2, enemies, devil, boss, camera):
        """Draw all UI elements based on current screen mode"""
        split_mode = camera.split_mode
        
        if split_mode:
            self.draw_divider(screen)
            left_viewport, right_viewport = self.get_viewports()
            
            # Draw UI for Player 1 (left) if alive
            if player1.health > 0:
                self.mini_map1.adjust_for_split_screen(True, self.split_width)
                self.mini_map1.draw(
                    screen.subsurface(left_viewport), 
                    player1, player2, enemies, devil, boss
                )
                self.skill_bar1.adjust_position(True, self.width)
                self.skill_bar1.draw(screen)
            
            # Draw UI for Player 2 (right) if alive
            if player2.health > 0:
                self.mini_map2.adjust_for_split_screen(True, self.split_width)
                self.mini_map2.draw(
                    screen.subsurface(right_viewport), 
                    player2, player1, enemies, devil, boss
                )
                self.skill_bar2.adjust_position(True, self.width)
                self.skill_bar2.draw(screen)
        else:
            # Single screen mode - draw UI elements that make sense
            if player1.health > 0:
                self.mini_map1.adjust_for_split_screen(False, self.width)
                self.mini_map1.draw(screen, player1, player2, enemies, devil, boss)
                self.skill_bar1.adjust_position(False, self.width)
                self.skill_bar1.draw(screen)
            
            if player2.health > 0:
                # In single screen, only draw player 2's UI if they're alive
                # and place it in a non-conflicting position
                self.mini_map2.adjust_for_split_screen(False, self.width)
                self.mini_map2.draw(screen, player2, player1, enemies, devil, boss)
                self.skill_bar2.adjust_position(False, self.width)
                self.skill_bar2.draw(screen)

# Ubah InteractionButton untuk support highlighting active player
def update_interaction_button_class():
    # Extend the InteractionButton class functionality
    original_draw = InteractionButton.draw
    
    def enhanced_draw(self, surface, camera_offset, is_active=False):
        # First call the original draw method
        original_draw(self, surface, camera_offset)
        
        # Add highlight for active player
        if is_active:
            # Draw a glowing outline around the button
            button_rect = self.image.get_rect()
            button_rect.center = (
                self.target_entity.rect.centerx + camera_offset[0],
                self.target_entity.rect.top - 20 + camera_offset[1]
            )
            # Draw a slightly larger rectangle behind as highlight
            highlight_rect = button_rect.copy()
            highlight_rect.inflate_ip(6, 6)
            pygame.draw.rect(surface, (255, 215, 0), highlight_rect, 2, border_radius=5)
    
    # Replace the original draw method
    InteractionButton.draw = enhanced_draw

# Import section modifications - no changes needed as we'll still use all imports

def split_screen_main(screen, clock, sound_manager, main_menu_callback):
    map_path = os.path.join("assets", "maps", "desert", "plain.png")
    map_type = "desert"  # Default to desert map
    
    cheat_mode = False
    cheat_input = ""
    cheat_message = ""
    original_max_health = None
    original_health = None

    try:
        game_map = Map(map_path)
    except Exception as e:
        print(f"Error loading map: {e}")
        return

    sound_manager.play_gameplay_music(map_type)
    
    camera = Camera(game_map.width, game_map.height)

    # Define the draw_game function - remove devil-related code from it
    def draw_game(viewport, offset_x=0, player_filter=None):
        # Clamp viewport to current screen rect to avoid subsurface errors
        screen_rect = screen.get_rect()
        safe_view = viewport.clip(screen_rect)
        viewport_surface = screen.subsurface(safe_view)
        
        # Tentukan kamera yang tepat berdasarkan viewport
        cam_x = camera.x
        cam_y = camera.y
        
        # Jika kita menggambar viewport kanan, gunakan x2/y2
        if camera.split_mode and offset_x > 0:
            cam_x = camera.x2
            cam_y = camera.y2
        
        # Gambar map dan particles
        game_map.draw(viewport_surface, (cam_x, cam_y))
        particle_system.draw(viewport_surface, (cam_x, cam_y))
        
        # Viewport rect untuk deteksi batas layar
        world_view_rect = pygame.Rect(-cam_x, -cam_y, viewport.width, viewport.height)
        
        # Remove devil damage circle drawing
        
        # Gambar semua sprite dengan kondisi filter
        for sprite in all_sprites:
            # Jika dalam mode split screen, filter berdasarkan viewport
            if camera.split_mode:
                # Kasus khusus untuk player dan partner
                if hasattr(sprite, 'player_id'):
                    # Di viewport kiri hanya gambar player1 dan partner1
                    if offset_x == 0 and sprite.player_id == 2:
                        continue
                    # Di viewport kanan hanya gambar player2 dan partner2
                    if offset_x > 0 and sprite.player_id == 1:
                        continue
    
            # Hanya gambar sprite jika ada dalam viewport
            if world_view_rect.colliderect(sprite.rect):
                if isinstance(sprite, Enemy):
                    sprite.draw(viewport_surface, (cam_x, cam_y))
                # Remove devil-specific rendering
                # Add Gollux-specific rendering
                elif isinstance(sprite, Gollux):
                    sprite.draw(viewport_surface, (cam_x, cam_y))
                else:
                    # Untuk viewport kanan, kita perlu menyesuaikan posisi x kamera
                    if camera.split_mode and offset_x > 0:
                        # Berikan offset tambahan untuk kompensasi viewport kanan
                        pos_x = sprite.rect.x + cam_x
                        pos_y = sprite.rect.y + cam_y
                        viewport_surface.blit(sprite.image, (pos_x, pos_y))
                    else:
                        viewport_surface.blit(sprite.image, (sprite.rect.x + cam_x, sprite.rect.y + cam_y))

        # Setelah menggambar semua sprite, tambahkan label di atas kepala player
        font_label = load_font(28)
        for p, label, color in [
            (player1, "Player 1", (0, 255, 0)),
            (player2, "Player 2", (255, 180, 0))
        ]:
            # Filter agar hanya tampil di viewport yang sesuai
            if camera.split_mode:
                if offset_x == 0 and getattr(p, "player_id", 1) != 1:
                    continue
                if offset_x > 0 and getattr(p, "player_id", 1) != 2:
                    continue
            # Jangan tampilkan jika player sedang mati
            if getattr(p, "is_dying", False):
                continue
            # Hitung posisi di layar
            px = p.rect.centerx + (camera.x2 if (camera.split_mode and offset_x > 0) else camera.x)
            py = p.rect.top + (camera.y2 if (camera.split_mode and offset_x > 0) else camera.y)
            label_surface = font_label.render(label, True, color)
            label_rect = label_surface.get_rect(center=(px, py - 18))
            viewport_surface.blit(label_surface, label_rect)

        # Handle fullscreen effects
        # First draw regular sprites with camera offset
        for sprite in all_sprites:
            if not hasattr(sprite, 'is_fullscreen_effect'):
                # (Your existing sprite drawing code)
                pass

        # Draw fullscreen effects on the entire viewport
        for sprite in all_sprites:
            if hasattr(sprite, 'is_fullscreen_effect') and sprite.is_fullscreen_effect:
                if hasattr(sprite, 'draw'):
                    sprite.draw(viewport_surface)

    # Define victory transition function - keep as is
    def victory_transition(surface):
        sw, sh = screen.get_size()
        fade_surface = pygame.Surface((sw, sh))
        fade_surface.fill((255, 255, 255))  # White flash for victory
        
        for alpha in range(0, 255, 5):
            fade_surface.set_alpha(alpha)
            screen.blit(fade_surface, (0, 0))
            pygame.display.flip()
            pygame.time.delay(10)
        
        pygame.time.delay(500)  # Hold the white screen briefly
        
        for alpha in range(255, 0, -5):
            fade_surface.set_alpha(alpha)
            screen.blit(fade_surface, (0, 0))
            pygame.display.flip()
            pygame.time.delay(10)

    # Initialize sprite groups
    all_sprites = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    projectiles1 = pygame.sprite.Group()
    projectiles2 = pygame.sprite.Group()
    experiences = pygame.sprite.Group()
    effects = pygame.sprite.Group()
    bi_enemies = pygame.sprite.Group()
    bi_projectiles = pygame.sprite.Group()

    # Initialize both players and their partners
    player1 = Player()
    player2 = Player2()
    
    for player in [player1, player2]:
        player.game_map = game_map
        player.sound_manager = sound_manager
        player.world_bounds = pygame.Rect(0, 0, game_map.width, game_map.height)
    
    # Position players apart from each other
    player1.rect.center = (game_map.width // 2 - 100, game_map.height // 2)
    player2.rect.center = (game_map.width // 2 + 100, game_map.height // 2)
    
    partner1 = Partner(player1, sound_manager=sound_manager)
    partner2 = Partner(player2, sound_manager=sound_manager)
    
    all_sprites.add(player1, player2, partner1, partner2)

    # Set player_id for partners
    partner1.player_id = 1
    partner2.player_id = 2

    # Create projectile pools for both players
    MAX_PROJECTILES = 20
    projectile_pool1 = []
    projectile_pool2 = []
    
    # Initialize boss variables
    boss = None
    boss_spawn_time = 5*60*1000  # 5 minutes
    boss_spawned = False
    boss_defeated = False
    show_boss_warning = False
    boss_warning_timer = 0
    
    for _ in range(MAX_PROJECTILES):
        for pool, group in [(projectile_pool1, projectiles1), (projectile_pool2, projectiles2)]:
            projectile = Projectile((0,0), (0,0))
            pool.append(projectile)
            all_sprites.add(projectile)
            group.add(projectile)
            projectile.kill()

    running = True
    paused = False
    enemy_spawn_timer = 0
    projectile_timer = 0
    game_time_seconds = 0
    bi_spawn_timer = 0
    last_second = 0
    
    # Initialize split screen UI
    sw, sh = screen.get_size()
    ui = SplitScreenUI(sw, sh)
    
    death_transition = False
    death_alpha = 0
    blur_surface = None
    FADE_SPEED = 15
    TRANSITION_DELAY = 5
    transition_timer = 0
    
    particle_system = ParticleSystem(sw, sh)
    
    # Remove devil-related variables

    session_start_ticks = pygame.time.get_ticks()  # Simpan waktu mulai session
    
    pause_ticks = 0
    pause_start = None

    cheat_pause_ticks = 0
    cheat_pause_start = None

    # Remove interaction button and shop initialization
    
    # Initialize mini maps for both players
    mini_map1 = MiniMap(game_map.width, game_map.height, sw, sh, player_id=1, position="left")
    mini_map2 = MiniMap(game_map.width, game_map.height, sw, sh, player_id=2, position="right")
    
    # Initialize skill bars for both players - each with one skill in coop mode
    skill_bar1 = SkillBar(player_id=1, position="left", mode="coop")
    skill_bar1.player = player1  # Add player1 reference
    skill_bar2 = SkillBar(player_id=2, position="right", mode="coop")
    skill_bar2.player = player2  # Add player2 reference
    
    # Create a new sprite group for skill effects
    skill_effects = pygame.sprite.Group()

    # Update sound manager at the beginning
    update_sound_manager(sound_manager)

    # Import skill-related modules
    from skill import create_skill, Skill
    
    # First initialize the skills list for both players
    player1.skills = []
    player2.skills = []
    
    # For player 1 - add thunder_strike skill with proper icon
    thunder_skill = create_skill("thunder_strike", sound_manager)
    if thunder_skill:
        # Ensure the icon is loaded
        if not hasattr(thunder_skill, 'icon') or thunder_skill.icon is None:
            icon_path = os.path.join("assets", "UI", "skill", "thunder_strike.png")
            if os.path.exists(icon_path):
                thunder_skill.icon = pygame.image.load(icon_path).convert_alpha()
        player1.skills.append(thunder_skill)
        print(f"Player 1 got skill: {thunder_skill.name}")
    
    # For player 2 - add heal skill with proper icon
    heal_skill = create_skill("heal", sound_manager)
    if heal_skill:
        # Ensure the icon is loaded
        if not hasattr(heal_skill, 'icon') or heal_skill.icon is None:
            icon_path = os.path.join("assets", "UI", "skill", "heal.png") 
            if os.path.exists(icon_path):
                heal_skill.icon = pygame.image.load(icon_path).convert_alpha()
        player2.skills.append(heal_skill)
        print(f"Player 2 got skill: {heal_skill.name}")

    # Set the skills on the skill bars
    skill_bar1.player = player1
    skill_bar2.player = player2

    while running:
        dt = clock.tick(FPS) / 1000.0
        
        # Update skill cooldowns
        skill_bar1.update(dt)
        skill_bar2.update(dt)
        
        # Update skill effects and remove them when they're done
        for effect in list(skill_effects):  # Use a copy of the list to safely modify during iteration
            if hasattr(effect, 'update'):
                effect.update(dt, enemies=enemies)
            
            # Check if effect should be removed
            if hasattr(effect, 'finished') and effect.finished:
                if hasattr(effect, 'fading_out') and not effect.fading_out:
                    effect.fading_out = True
                elif hasattr(effect, 'alpha') and effect.alpha <= 0:
                    effect.kill()
            
            # Safety check - remove effects after 5 seconds to prevent them getting stuck
            if not hasattr(effect, 'lifetime_timer'):
                effect.lifetime_timer = 0
            effect.lifetime_timer = getattr(effect, 'lifetime_timer', 0) + dt
            if effect.lifetime_timer > 5.0:  # 5 seconds max lifetime
                effect.kill()
        
        # Collect events before processing
        current_events = []
        for event in pygame.event.get():
            current_events.append(event)
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Player 1 skill activation (key 1)
                if event.key == PLAYER1_SKILL_KEY and player1.health > 0:
                    skill = skill_bar1.activate_skill()
                    activate_player_skill(player1, skill, enemies, all_sprites, skill_effects)
        
                # Player 2 skill activation (key right ctrl)
                elif event.key == PLAYER2_SKILL_KEY and player2.health > 0:
                    skill = skill_bar2.activate_skill()
                    activate_player_skill(player2, skill, enemies, all_sprites, skill_effects)
        
                # Menu handling
                elif event.key == MENU_KEY:
                    paused = True
                    pause_start = pygame.time.get_ticks()
                    quit_to_menu = pause_menu(screen, main_menu_callback)
                    if quit_to_menu:
                        return  # Keluar ke menu utama
                    paused = False
                    if pause_start is not None:
                        pause_ticks += pygame.time.get_ticks() - pause_start
                        pause_start = None
                
                # Toggle cheat mode
                elif event.key == TOGGLE_CHEAT_KEY:
                    cheat_mode = not cheat_mode
                    if cheat_mode:
                        cheat_pause_start = pygame.time.get_ticks()
                    else:
                        if cheat_pause_start is not None:
                            cheat_pause_ticks += pygame.time.get_ticks() - cheat_pause_start
                            cheat_pause_start = None
                    cheat_input = ""
                    cheat_message = ""
        
        # Remove devil shop handling
            
        if paused:
            continue
            
        # Cheat input handling
        if cheat_mode:
            # Draw semi-transparent overlay (benar-benar transparan, game tetap terlihat)
            sw, sh = screen.get_size()
            overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 80))  # alpha 80, makin kecil makin transparan
            screen.blit(overlay, (0, 0))

            # Draw input box
            font_cheat = load_font(36)
            box_rect = pygame.Rect(sw//2 - 200, sh//2 - 40, 400, 80)
            pygame.draw.rect(screen, (40, 40, 40), box_rect, border_radius=8)
            pygame.draw.rect(screen, (200, 200, 200), box_rect, 2, border_radius=8)

            input_surface = font_cheat.render(cheat_input, True, (255, 255, 0))
            screen.blit(input_surface, (box_rect.x + 20, box_rect.y + 20))

            # Draw message if any, geser ke bawah kotak
            if cheat_message:
                msg_surface = font_cheat.render(cheat_message, True, (0, 255, 0))
                msg_rect = msg_surface.get_rect(center=(sw//2, box_rect.y + box_rect.height + 30))
                screen.blit(msg_surface, msg_rect)

            pygame.display.flip()

            # Handle text input for cheat console
            keys = pygame.key.get_pressed()
            for event in current_events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        # Process cheat command
                        if cheat_input == "orkaybanh":
                            player1.session_money += 10000
                            player2.session_money += 10000
                            cheat_message = "Money +10000 for both players!"
                        elif cheat_input == "armordaribapak":
                            if original_max_health is None:
                                original_max_health = player1.max_health
                                original_health = player1.health
                            player1.max_health = 1000
                            player1.health = 1000
                            player2.max_health = 1000
                            player2.health = 1000
                            cheat_message = "Armor dari bapak aktif!"
                        elif cheat_input == "rakyatbiasa":
                            if original_max_health is not None:
                                player1.max_health = original_max_health
                                player1.health = original_health
                                player2.max_health = original_max_health
                                player2.health = original_health
                                original_max_health = None
                                original_health = None
                            cheat_message = "Cheat dinonaktifkan!"
                        elif cheat_input == "timeheist":
                            session_start_ticks -= 230 * 1000
                            cheat_message = "Waktu dipercepat +3:50!"
                        elif cheat_input == "spawnboss":
                            if boss is None:
                                # Spawn near active players
                                if player1.health > 0 and player2.health > 0:
                                    midpoint = ((player1.rect.centerx + player2.rect.centerx) // 2, 
                                               (player1.rect.centery + player2.rect.centery) // 2)
                                    boss = Gollux(game_map.width, game_map.height, midpoint)
                                elif player1.health > 0:
                                    boss = Gollux(game_map.width, game_map.height, player1.rect.center)
                                else:
                                    boss = Gollux(game_map.width, game_map.height, player2.rect.center)
                                    
                                boss.sound_manager = sound_manager  # Set sound manager reference
                                all_sprites.add(boss)
                                boss_spawned = True
                                cheat_message = "Gollux boss spawned!"
                            else:
                                cheat_message = "Boss sudah ada!"
                        elif cheat_input == "newskills":
                            # Give new random skills to both players
                            player1_skill = random.choice(available_skills)
                            player1.skills = [Skill(player1_skill)]
                            
                            remaining_skills = [s for s in available_skills if s != player1_skill]
                            player2_skill = random.choice(remaining_skills)
                            player2.skills = [Skill(player2_skill)]
                            
                            cheat_message = f"New skills! P1:{player1.skills[0].name}, P2:{player2.skills[0].name}"
                        else:
                            cheat_message = "Command tidak dikenal."
                        cheat_input = ""
                    elif event.key == pygame.K_BACKSPACE:
                        cheat_input = cheat_input[:-1]
                    elif event.key >= 32 and event.key <= 126:  # Printable ASCII characters
                        cheat_input += event.unicode
            
            # Continue to next frame, skipping regular game updates
            continue

        # Spawn enemies
        enemy_spawn_timer += 1
        MAX_ENEMIES = 15
        # Only spawn enemies if boss isn't spawned yet
        if enemy_spawn_timer >= 60 and len(enemies) < MAX_ENEMIES and not boss_spawned:
            # Add check for nuke blocking
            spawn_blocked = False
            for effect in skill_effects:
                if hasattr(effect, 'block_enemy_spawns') and effect.block_enemy_spawns:
                    spawn_blocked = True
                    break
    
            if not spawn_blocked:
                enemy = Enemy((
                    (player1.rect.centerx + player2.rect.centerx) // 2,
                    (player1.rect.centery + player2.rect.centery) // 2
                ))
                all_sprites.add(enemy)
                enemies.add(enemy)
                enemy_spawn_timer = 0
            
        # Also fix partner shooting in split screen mode
        projectile_timer += 1
        # Ubah kondisi menjadi memeriksa boss atau enemies
        if projectile_timer >= 30 and (len(enemies) > 0 or (boss is not None and not boss.is_defeated)):
            # Handle partner1 shooting
            if player1.health > 0:
                closest_enemy = None
                min_dist = float('inf')
                shoot_radius = 500
                
                # First check if boss exists and target it with priority
                if boss and not boss.is_defeated:
                    dist = math.hypot(boss.rect.centerx - player1.rect.centerx,
                                     boss.rect.centery - player1.rect.centery)
                    if dist < shoot_radius:
                        closest_enemy = boss
                        min_dist = dist
                # Jika tidak ada boss atau boss terlalu jauh, coba target musuh biasa
                if closest_enemy is None:
                    for enemy in enemies:
                        if enemy.is_dying:
                            continue
                            
                        dist = math.hypot(enemy.rect.centerx - player1.rect.centerx,
                                        enemy.rect.centery - player1.rect.centery)
                        if dist < min_dist and dist < shoot_radius:
                            min_dist = dist
                            closest_enemy = enemy
                
                if closest_enemy:
                    for projectile in projectile_pool1:
                        if not projectile.alive():
                            start_pos = partner1.get_shooting_position()
                            target_pos = (closest_enemy.rect.centerx, closest_enemy.rect.centery)
                            
                            partner1.shoot_at(target_pos)  # This will now play the sound
                            
                            # Get projectile type based on partner type
                            projectile_type = partner1.get_projectile_type()
                            
                            projectile.reset(start_pos, target_pos, projectile_type)
                            projectile.add(all_sprites, projectiles1)
                            break
                else:
                    partner1.stop_shooting()
            
            # Handle partner2 shooting (lakukan perubahan serupa)
            if player2.health > 0:
                closest_enemy = None
                min_dist = float('inf')
                shoot_radius = 500
                
                # First check if boss exists and target it with priority
                if boss and not boss.is_defeated:
                    dist = math.hypot(boss.rect.centerx - player2.rect.centerx,
                                     boss.rect.centery - player2.rect.centery)
                    if dist < shoot_radius:
                        closest_enemy = boss
                        min_dist = dist
                # Jika tidak ada boss atau boss terlalu jauh, coba target musuh biasa
                if closest_enemy is None:
                    for enemy in enemies:
                        if enemy.is_dying:
                            continue
                            
                        dist = math.hypot(enemy.rect.centerx - player2.rect.centerx,
                                        enemy.rect.centery - player2.rect.centery)
                        if dist < min_dist and dist < shoot_radius:
                            min_dist = dist
                            closest_enemy = enemy
                
                if closest_enemy:
                    for projectile in projectile_pool2:
                        if not projectile.alive():
                            start_pos = partner2.get_shooting_position()
                            target_pos = (closest_enemy.rect.centerx, closest_enemy.rect.centery)
                            
                            partner2.shoot_at(target_pos)
                            
                            # Get projectile type based on partner type
                            projectile_type = partner2.get_projectile_type()
                            
                            projectile.reset(start_pos, target_pos, projectile_type)
                            projectile.add(all_sprites, projectiles2)
                            break
                else:
                    partner2.stop_shooting()
                    
            projectile_timer = 0

        player1.update(dt)
        player2.update(dt)
        partner1.update(dt)
        partner2.update(dt)
        
        for enemy in enemies:
            # Enemies target the nearest LIVING player
            p1_dist = float('inf') if player1.is_dying else math.hypot(
                         player1.rect.centerx - enemy.rect.centerx,
                         player1.rect.centery - enemy.rect.centery)
            p2_dist = float('inf') if player2.is_dying else math.hypot(
                         player2.rect.centerx - enemy.rect.centerx,
                         player2.rect.centery - enemy.rect.centery)
                 
            # Pilih pemain yang masih hidup
            if p1_dist == float('inf') and p2_dist == float('inf'):
                # Jika keduanya mati, target acak (ini jarang terjadi)
                target = random.choice([player1, player2])
            else:
                target = player1 if p1_dist < p2_dist else player2
                
            hit_target, damage = enemy.update(target, enemies)
            
            # Jika enemy memberikan damage
            if hit_target and damage > 0:
                hit_target.health -= damage
                if hit_target.health <= 0:
                    hit_target.start_death_animation()
                    if not death_transition:  # Ambil screenshot blur hanya sekali
                        death_transition = True
                        blur_surface = create_blur_surface(screen.copy())
                    break

        projectiles1.update()
        projectiles2.update()
        experiences.update()
        effects.update(dt)

        # Handle projectile hits
        for projs in [projectiles1, projectiles2]:
            # Deteksi tumbukan dengan musuh biasa
            hits = pygame.sprite.groupcollide(projs, enemies, True, False)
            for projectile, hit_enemies in hits.items():
                for enemy in hit_enemies:
                    # Skip enemy yang sudah dalam animasi mati
                    if enemy.is_dying:
                        continue
                        
                    # Tambahkan efek hit dari rock
                    hit_effect = RockHitEffect((enemy.rect.centerx, enemy.rect.centery))
                    all_sprites.add(hit_effect)
                    effects.add(hit_effect)
                    
                    enemy.take_hit(projectile.damage)
                    if enemy.health <= 0:
                        # Remove devil-related check
                        exp = Experience(enemy.rect.centerx, enemy.rect.centery)
                        all_sprites.add(exp)
                        experiences.add(exp)
                        # Tambah uang ke player (coop - dibagi rata)
                        player1.session_money += 3
                        player2.session_money += 2

            # Deteksi tumbukan dengan boss
            if boss and not boss.is_defeated:
                hits = pygame.sprite.spritecollide(boss, projs, True)
                for projectile in hits:
                    # Add hit effect
                    hit_effect = RockHitEffect((boss.rect.centerx, boss.rect.centery))
                    all_sprites.add(hit_effect)
                    effects.add(hit_effect)
                    
                    # Deal damage to boss
                    boss_defeated = boss.take_hit(projectile.damage)
                    
                    # If boss is defeated, trigger victory
                    if boss_defeated:
                        # Hitung skor dan waktu bermain
                        elapsed_ms = pygame.time.get_ticks() - session_start_ticks - cheat_pause_ticks - pause_ticks
                        elapsed_seconds = elapsed_ms // 1000
                        
                        # Tambahkan reward uang untuk kedua pemain
                        player1.session_money += 1000
                        player2.session_money += 1000
                        
                        total_score = player1.session_money + player2.session_money
                        
                        # Transisi kemenangan
                        victory_transition(screen)
                        
                        # Tampilkan layar kemenangan dengan pesan kustom
                        show_victory_screen(screen, total_score, elapsed_seconds, sound_manager,
                                           "You've defeated Gollux together! The world is saved!")
                        return

        # Handle death transition
        if death_transition:
            both_players_dead = player1.health <= 0 and player2.health <= 0
    
            if player1.health <= 0:
                player1.update_death_animation(dt)
            if player2.health <= 0:
                player2.update_death_animation(dt)
            
            # Check if both players are dead and both animations are complete or if enough time has passed
            animation_complete = (player1.health <= 0 and player2.health <= 0 and 
                                 (getattr(player1, 'death_animation_complete', False) or 
                                  getattr(player2, 'death_animation_complete', False)))
            
            if animation_complete:
                # Proceed with game over
                death_alpha += FADE_SPEED
                if death_alpha >= 255:
                    transition_timer += 1
                    if transition_timer >= TRANSITION_DELAY:
                        # Show game over
                        splitscreen_game_over(screen, player1, player2, main_menu_callback, split_screen_main)
                        return

        # Handle experience collection
        for player in [player1, player2]:
            hits = pygame.sprite.spritecollide(player, experiences, True)
            for exp in hits:
                player.xp += 5
                player.session_money += 5
                
                if player.xp >= player.max_xp:
                    player.level += 1
                    player.xp -= player.max_xp
                    player.max_xp = int(player.max_xp * 1.2)
                    
                    # Tambahkan max health saat level up
                    player.max_health += 20
                    player.health = player.max_health  # Isi penuh health
                    
                    # Play level up sound
                    sound_manager.play_player_levelup()
                    
                    level_effect = LevelUpEffect(player)
                    effects.add(level_effect)
                    all_sprites.add(level_effect)

        # Update camera to follow midpoint between players
        if player1.health <= 0:
            # Player 1 mati, kamera ikuti player 2
            if player2 is not None and hasattr(player2, 'rect'):
                camera.update(player2)
            else:
                # Fallback to player1 if available, or do nothing
                if player1 is not None and hasattr(player1, 'rect'):
                    camera.update(player1)
        elif player2.health <= 0:
            # Player 2 mati, kamera ikuti player 1
            camera.update(player1)
        else:
            # Kedua player hidup, gunakan kamera split screen
            camera.update(player1, player2)

        # Draw everything
        if camera.split_mode:
            sw, sh = screen.get_size()
            # Draw more visible divider between viewports
            divider_width = 4  # Lebar garis pemisah (4 pixel)
            divider_rect = pygame.Rect(sw//2 - divider_width//2, 0, divider_width, sh)
            pygame.draw.rect(screen, (255, 215, 0), divider_rect)  # Warna kuning emas untuk visibilitas
            
            # Optional: Tambahkan shadow effect untuk kedalaman
            shadow_width = 2
            pygame.draw.rect(screen, (100, 100, 100, 128), 
                            pygame.Rect(sw//2 - divider_width//2 - shadow_width, 0, shadow_width, sh))
            pygame.draw.rect(screen, (100, 100, 100, 128), 
                            pygame.Rect(sw//2 + divider_width//2, 0, shadow_width, sh))
            
            # Draw left viewport (Player 1)
            left_viewport = pygame.Rect(0, 0, sw//2 - divider_width//2, sh)
            draw_game(left_viewport, 0, 1)  # Draw with player 1 filter
            
            # Right viewport (Player 2)
            right_viewport = pygame.Rect(sw//2 + divider_width//2, 0, sw//2 - divider_width//2, sh)
            draw_game(right_viewport, sw//2, 2)  # Draw with player 2 filter
            
            # Draw UI for both players
            ui.draw_split(screen, player1, player2, True)
        else:
            # Normal single screen drawing
            sw, sh = screen.get_size()
            full_viewport = pygame.Rect(0, 0, sw, sh)
            draw_game(full_viewport)
            ui.draw(screen, player1, player2)

        # --- SESSION TIMER ---
        elapsed_ms = pygame.time.get_ticks() - session_start_ticks - pause_ticks
        elapsed_seconds = elapsed_ms // 1000
        minutes = elapsed_seconds // 60
        seconds = elapsed_seconds % 60
        timer_text = f"{minutes:02d}:{seconds:02d}"

        timer_font = load_font(48)
        timer_surface = render_text_with_border(timer_font, timer_text, WHITE, BLACK)
        sw, sh = screen.get_size()
        timer_rect = timer_surface.get_rect(center=(sw // 2, 40))
        screen.blit(timer_surface, timer_rect)

        # Remove devil-related code
                
        # Update minimaps and skill positions based on split screen mode
        mini_map1.adjust_for_split_screen(camera.split_mode, sw//2)
        mini_map2.adjust_for_split_screen(camera.split_mode, sw//2)
        skill_bar1.adjust_position(camera.split_mode, sw)
        skill_bar2.adjust_position(camera.split_mode, sw)
        
        # Draw UI elements
        if camera.split_mode:
            # For split screen mode
            # Left half (player 1)
            left_viewport = pygame.Rect(0, 0, sw//2 - divider_width//2, sh)
            mini_map1.draw(screen, player1, player2, enemies, None, boss)  # Pass None for devil
            skill_bar1.draw(screen)
            
            # Right half (player 2)
            right_viewport = pygame.Rect(sw//2 + divider_width//2, 0, sw//2 - divider_width//2, sh)
            mini_map2.draw(screen, player2, player1, enemies, None, boss)  # Pass None for devil
            skill_bar2.draw(screen)
        else:
            # Single screen mode
            mini_map1.draw(screen, player1, player2, enemies, None, boss)  # Pass None for devil
            mini_map2.draw(screen, player2, player1, enemies, None, boss)  # Pass None for devil
            skill_bar1.draw(screen)
            if player2.health > 0:
                skill_bar2.draw(screen)
        
        # Check if boss should spawn based on elapsed time
        elapsed_time = pygame.time.get_ticks() - session_start_ticks - pause_ticks - cheat_pause_ticks
        if not boss_spawned and not boss_defeated and elapsed_time >= boss_spawn_time:
            # Create midpoint between active players
            if player1.health > 0 and player2.health > 0:
                midpoint = ((player1.rect.centerx + player2.rect.centerx) // 2, 
                           (player1.rect.centery + player2.rect.centery) // 2)
            elif player1.health > 0:
                midpoint = player1.rect.center
            else:
                midpoint = player2.rect.center
                
            # Create and setup boss
            boss = Gollux(game_map.width, game_map.height, midpoint)
            boss.sound_manager = sound_manager
            all_sprites.add(boss)
            boss_spawned = True
            
            # Show boss warning
            boss_warning_timer = pygame.time.get_ticks()
            show_boss_warning = True
            
        # Display boss warning if active
        if show_boss_warning:
            current_time = pygame.time.get_ticks()
            elapsed_time = current_time - boss_warning_timer
            
            if elapsed_time < 3000:  # Show for 3 seconds
                warning_font = load_font(48)
                warning_text = warning_font.render("BOSS APPROACHING!", True, (255, 0, 0))
                warning_rect = warning_text.get_rect(center=(sw // 2, sh // 3))
                
                # Add pulsing effect
                pulse = math.sin(current_time * 0.01) * 10 + 255
                pulse = max(0, min(255, pulse))
                warning_text.set_alpha(pulse)
                
                screen.blit(warning_text, warning_rect)
            else:
                show_boss_warning = False
        
        # Display current skills information at the bottom of the screen
       
            
        pygame.display.flip()

    return