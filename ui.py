import pygame
import os
import math
from settings import WIDTH, HEIGHT, WHITE, BLACK, FONT_PATH
from utils import load_game_data 
from settings import load_font 

def get_ui_scale(base_width=1366, base_height=768):
    """Return a UI scale factor based on current window size vs. a base resolution."""
    try:
        surface = pygame.display.get_surface()
        if not surface:
            return 1.0
        w, h = surface.get_size()
        return min(w / base_width, h / base_height)
    except Exception:
        return 1.0

def render_text_with_border(font, text, text_color, border_color):
    text_surface = font.render(text, True, text_color)
    final_surface = pygame.Surface((text_surface.get_width() + 2, text_surface.get_height() + 2), pygame.SRCALPHA)
    
    for dx, dy in [(-1,-1), (0,-1), (1,-1), (-1,0), (1,0), (-1,1), (0,1), (1,1)]:
        border_text = font.render(text, True, border_color)
        final_surface.blit(border_text, (dx + 1, dy + 1))
    
    final_surface.blit(text_surface, (1, 1))
    return final_surface

class HealthBar:
    def __init__(self):
        self.box = pygame.image.load("assets/UI/profile/health-bar-box.png").convert_alpha()
        self.bar = pygame.image.load("assets/UI/profile/health-bar.png").convert_alpha()
        
        scale = get_ui_scale()
        
        self.box_width = int(192 * scale)
        self.box_height = int(30 * scale)
        self.box = pygame.transform.scale(self.box, (self.box_width, self.box_height))
        
        self.bar_width = int(156 * scale)
        self.bar_height = int(20 * scale)
        self.bar = pygame.transform.scale(self.bar, (self.bar_width, self.bar_height))
        
        self.x = int(10 * scale)
        self.y = int(10 * scale)
        
        self.bar_x_offset = (self.box_width - self.bar_width) // 2
        self.bar_y_offset = (self.box_height - self.bar_height) // 2

    def draw(self, screen, current_health, max_health):
        screen.blit(self.box, (self.x, self.y))
        
        health_ratio = max(0, min(current_health / max_health, 1))
        fill_width = int(self.bar_width * health_ratio)
        
        if fill_width > 0:
            health_bar = pygame.Surface((fill_width, self.bar_height), pygame.SRCALPHA)
            health_bar.blit(self.bar, (0, 0), (0, 0, fill_width, self.bar_height))
            screen.blit(health_bar, (
                self.x + self.bar_x_offset, 
                self.y + self.bar_y_offset
            ))

class MoneyDisplay:
    def __init__(self):
        self.icon = pygame.image.load("assets/UI/level/money.png").convert_alpha()
        
        scale = get_ui_scale()
        
        self.icon_width = int(32 * scale)
        self.icon_height = int(32 * scale)
        self.icon = pygame.transform.scale(self.icon, (self.icon_width, self.icon_height))
        
        self.x = int(10 * scale)
        self.y = int(45 * scale)
        
        self.font = load_font(max(16, int(32 * scale)))
        
    def draw(self, screen, player_session_money):
        screen.blit(self.icon, (self.x, self.y))
        
        saved_money, _, _ = load_game_data()
        total_money = saved_money + player_session_money
        
        money_text = render_text_with_border(self.font, f": {total_money}", WHITE, BLACK)
        text_y = self.y + (self.icon_height - money_text.get_height()) // 2
        screen.blit(money_text, (
            self.x + self.icon_width + 5,
            text_y
        ))

class XPBar:
    def __init__(self, screen_width, screen_height):
        self.bg = pygame.image.load("assets/UI/level/lvl.bg.png").convert_alpha()
        self.fill = pygame.image.load("assets/UI/level/lvl.fill.png").convert_alpha()
        
        self.bg_width = screen_width
        self.bg_height = 14
        self.fill_width = screen_width - 20
        self.fill_height = 14
        
        self.bg = pygame.transform.scale(self.bg, (self.bg_width, self.bg_height))
        self.fill = pygame.transform.scale(self.fill, (self.fill_width, self.fill_height))
        
        self.x = 0
        self.y = screen_height - self.bg_height
        
        self.fill_x_offset = (self.bg_width - self.fill_width) // 2
        self.fill_y_offset = (self.bg_height - self.fill_height) // 2
        
        self.font = load_font(20)
        
        self.text_margin_bottom = 30

    def draw(self, screen, current_xp, max_xp, level, max_width=None):
        if max_width is None:
            max_width = self.bg_width
            
        # Scale background and fill to viewport width
        scaled_bg = pygame.transform.scale(self.bg, (max_width, self.bg_height))
        scaled_fill = pygame.transform.scale(self.fill, (max_width - 20, self.fill_height))
        
        screen.blit(scaled_bg, (self.x, self.y))
        
        xp_ratio = max(0, min(current_xp / max_xp, 1))
        current_fill_width = int((max_width - 20) * xp_ratio)
        
        if current_fill_width > 0:
            fill_surface = pygame.Surface((current_fill_width, self.fill_height), pygame.SRCALPHA)
            fill_surface.blit(scaled_fill, (0, 0), (0, 0, current_fill_width, self.fill_height))
            screen.blit(fill_surface, (
                self.x + self.fill_x_offset,
                self.y + self.fill_y_offset
            ))
        
        # Draw text with proper positioning
        level_text = render_text_with_border(self.font, f"Level {level}", WHITE, BLACK)
        text_x = self.x + 10
        text_y = self.y - self.text_margin_bottom
        screen.blit(level_text, (text_x, text_y))
        
        xp_text = render_text_with_border(self.font, f"{current_xp}/{max_xp} XP", WHITE, BLACK)
        xp_x = self.x + max_width - xp_text.get_width() - 10
        xp_y = self.y - self.text_margin_bottom
        screen.blit(xp_text, (xp_x, xp_y))

class SplitScreenUI:
    def __init__(self, screen_width, screen_height):
        self.health_bar1 = HealthBar()
        self.health_bar2 = HealthBar()
        self.health_bar2.x = screen_width - 200  # Tetap di pojok kanan atas
        self.health_bar2.y = 10                  # Pastikan di atas
        
        self.xp_bar1 = XPBar(screen_width // 2, screen_height)  # Half width for player 1
        self.xp_bar2 = XPBar(screen_width // 2, screen_height)  # Half width for player 2
        self.xp_bar2.x = screen_width // 2  # Position for player 2
        
        self.money_display = MoneyDisplay()  # Shared money display
        
        # Simpan variabel screen_width untuk digunakan dalam draw_split
        self.screen_width = screen_width
        self.screen_height = screen_height
    
    def draw(self, screen, player1, player2):
        self.health_bar1.draw(screen, player1.health, player1.max_health)
        self.health_bar2.draw(screen, player2.health, player2.max_health)
        self.xp_bar1.draw(screen, player1.xp, player1.max_xp, player1.level)
        self.xp_bar2.draw(screen, player2.xp, player2.max_xp, player2.level)
        total_session_money = player1.session_money + player2.session_money
        self.money_display.draw(screen, total_session_money)

    def draw_split(self, screen, player1, player2, split_mode):
        if split_mode:
            # Left side UI (Player 1)
            self.health_bar1.x = 10
            self.health_bar1.y = 10
            self.health_bar1.draw(screen, player1.health, player1.max_health)
            self.xp_bar1.draw(screen, player1.xp, player1.max_xp, player1.level, self.screen_width//2)
            
            # Right side UI (Player 2)
            self.health_bar2.draw(screen, player2.health, player2.max_health)
            self.xp_bar2.x = self.screen_width // 2
            # PERBAIKI DI SINI: gunakan self.screen_width//2
            self.xp_bar2.draw(screen, player2.xp, player2.max_xp, player2.level, self.screen_width//2)
            
            # Shared money display in center
            total_session_money = player1.session_money + player2.session_money
            self.money_display.draw(screen, total_session_money)
        else:
            self.draw(screen, player1, player2)

class InteractionButton:
    def __init__(self):
        self.frames = []
        self.load_frames()
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 0.15  # seconds between frames
        self.is_visible = False
        self.target_entity = None
        
    def load_frames(self):
        button_path = os.path.join("assets", "UI", "btn")
        try:
            self.frames.append(pygame.image.load(os.path.join(button_path, "E0.png")).convert_alpha())
            self.frames.append(pygame.image.load(os.path.join(button_path, "E1.png")).convert_alpha())
        except pygame.error as e:
            print(f"Error loading button frames: {e}")
            
    def update(self, dt):
        if not self.is_visible:
            return
            
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
    
    def show(self, target_entity):
        self.is_visible = True
        self.target_entity = target_entity
        
    def hide(self):
        self.is_visible = False
        self.target_entity = None
        
    def draw(self, surface, camera_offset):
        if not self.is_visible or not self.target_entity or not self.frames:
            return
        
        current_image = self.frames[self.current_frame]
        
        # Position the button above the target entity
        button_x = self.target_entity.rect.centerx - current_image.get_width() // 2
        button_y = self.target_entity.rect.top - current_image.get_height() - 10
        
        surface.blit(current_image, (button_x + camera_offset[0], button_y + camera_offset[1]))

class DevilShop:
    def __init__(self, sound_manager=None):
        self.sound_manager = sound_manager
        self.is_open = False
        self.selected_item = 0
        self.current_tab = 0  # 0: Potions, 1: Skills, 2: Partner
        self.tab_names = ["Potions", "Skills", "Partner"]
        
        # Define items for each tab
        self.potion_items = [
            {"name": "Health Potion", "price": 50, "desc": "Restore 20 health"},
            {"name": "XP Potion", "price": 100, "desc": "Gain 50 XP instantly"},
            {"name": "Speed Potion", "price": 150, "desc": "Temporary speed boost"},
            {"name": "Regen Potion", "price": 200, "desc": "Slowly restore health over time"}
        ]
        
        self.skill_items = [
            {"name": "Thunder Strike", "price": 200, "desc": "Call lightning from the sky to damage enemies"},
            {"name": "Heal", "price": 500, "desc": "Restore health to full"},
            {"name": "Nuke", "price": 700, "desc": "Eliminate all enemies but costs 50% of your health"}
        ]
        
        self.partner_items = [
            {"name": "Skull Partner", "price": 1000, "desc": "Replace your eagle with a skull companion"}
        ]
        
        # The active tab's items
        self.items = self.potion_items
        
        # Shop UI elements
        self.border_color = (255, 215, 0)  # Gold color for border
        self.bg_color = (40, 40, 40, 220)  # Dark semi-transparent background
        self.title_color = (255, 255, 255)
        self.text_color = (200, 200, 200)
        self.highlight_color = (255, 215, 0)
        self.error_color = (255, 80, 80)
        self.active_tab_color = (80, 80, 80)
        self.inactive_tab_color = (40, 40, 40)
        
        # Position and size
        self.width = 500
        self.height = 400
        self.padding = 20
        self.item_height = 50
        self.tab_height = 40
        self.message = ""
        self.message_timer = 0
        
        # Load fonts
        self.title_font = pygame.font.Font(FONT_PATH, 36)
        self.item_font = pygame.font.Font(FONT_PATH, 24)
        self.desc_font = pygame.font.Font(FONT_PATH, 18)
        self.tab_font = pygame.font.Font(FONT_PATH, 22)

    def open(self):
        self.is_open = True
        self.selected_item = 0
        self.message = ""
        # Set items based on current tab
        self.update_items_for_tab()
        if self.sound_manager:
            self.sound_manager.play_ui_click()
        
    def close(self):
        self.is_open = False
        if self.sound_manager:
            self.sound_manager.play_ui_click()
    
    def update_items_for_tab(self):
        if self.current_tab == 0:
            self.items = self.potion_items
        elif self.current_tab == 1:
            self.items = self.skill_items
        else:
            self.items = self.partner_items
        self.selected_item = min(self.selected_item, len(self.items) - 1)

    def update(self, events):
        if not self.is_open:
            return
        
        # Handle message timer
        if self.message:
            self.message_timer += 1
            if self.message_timer > 120:  # 2 seconds at 60 FPS
                self.message = ""
                self.message_timer = 0
        
        # Process input for menu navigation
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.close()
                elif event.key == pygame.K_UP:
                    self.selected_item = (self.selected_item - 1) % len(self.items)
                    if self.sound_manager:
                        self.sound_manager.play_ui_hover()
                elif event.key == pygame.K_DOWN:
                    self.selected_item = (self.selected_item + 1) % len(self.items)
                    if self.sound_manager:
                        self.sound_manager.play_ui_hover()
                elif event.key == pygame.K_LEFT:
                    self.current_tab = (self.current_tab - 1) % len(self.tab_names)
                    self.update_items_for_tab()
                    if self.sound_manager:
                        self.sound_manager.play_ui_hover()
                elif event.key == pygame.K_RIGHT:
                    self.current_tab = (self.current_tab + 1) % len(self.tab_names)
                    self.update_items_for_tab()
                    if self.sound_manager:
                        self.sound_manager.play_ui_hover()
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self.purchase_item()
                    if self.sound_manager:
                        self.sound_manager.play_ui_click()

    def purchase_item(self, player=None, partner=None):
        if len(self.items) == 0 or player is None:
            return False
            
        item = self.items[self.selected_item]
        
        # Check if player has enough money
        if player.session_money < item["price"]:
            self.message = f"Not enough money! Need ${item['price']}"
            self.message_timer = 0
            if self.sound_manager:
                self.sound_manager.play_ui_hover()  # Use hover sound for error
            return False
            
        # Process purchase based on item type
        purchased = False
        
        if self.current_tab == 0:  # Potions tab
            if item["name"] == "Health Potion":
                player.health = min(player.health + 20, player.max_health)
                purchased = True
            elif item["name"] == "XP Potion":
                player.gain_xp(50)
                purchased = True
            elif item["name"] == "Speed Potion":
                player.speed_boost_timer = 10  # 10 seconds boost
                player.speed_multiplier = 1.5
                purchased = True
            elif item["name"] == "Regen Potion":
                player.regen_timer = 15  # 15 seconds of regeneration
                player.regen_amount = 1  # 1 health per second
                purchased = True
                
        elif self.current_tab == 1:  # Skills tab
            if item["name"] == "Thunder Strike":
                # Initialize skills list if it doesn't exist
                if not hasattr(player, 'skills'):
                    player.skills = []
                
                # Check if player already has this skill
                already_has_skill = False
                for skill in player.skills:
                    if skill.name == "Thunder Strike":
                        already_has_skill = True
                        break
                        
                if already_has_skill:
                    self.message = f"You already have {item['name']}!"
                    self.message_timer = 0
                    if self.sound_manager:
                        self.sound_manager.play_ui_hover()  # Use hover sound for error
                    return False
                
                # If player doesn't have the skill yet, check if all skill slots are filled (solo mode)
                # Solo mode has 3 skill slots max
                if hasattr(player, 'player_id') and player.player_id == 1 and len(player.skills) >= 3:
                    self.message = "All skill slots are full!"
                    self.message_timer = 0
                    if self.sound_manager:
                        self.sound_manager.play_ui_hover()
                    return False
                
                # Import the skill module and create the skill
                from skill import create_skill
                thunder_skill = create_skill("thunder_strike", self.sound_manager)
                
                # Add to player's skills
                player.skills.append(thunder_skill)
                purchased = True
            elif item["name"] == "Heal":
                # Initialize skills list if it doesn't exist
                if not hasattr(player, 'skills'):
                    player.skills = []
                
                # Check if player already has this skill
                already_has_skill = False
                for skill in player.skills:
                    if skill.name == "Heal":
                        already_has_skill = True
                        break
                
                if already_has_skill:
                    self.message = f"You already have {item['name']}!"
                    self.message_timer = 0
                    if self.sound_manager:
                        self.sound_manager.play_ui_hover()  # Use hover sound for error
                    return False
                
                # If player doesn't have the skill yet, check if all skill slots are filled (solo mode)
                # Solo mode has 3 skill slots max
                if hasattr(player, 'player_id') and player.player_id == 1 and len(player.skills) >= 3:
                    self.message = "All skill slots are full!"
                    self.message_timer = 0
                    if self.sound_manager:
                        self.sound_manager.play_ui_hover()
                    return False
                
                # Import the skill module and create the skill
                from skill import create_skill
                heal_skill = create_skill("heal", self.sound_manager)
                
                # Add to player's skills
                player.skills.append(heal_skill)
                purchased = True
            elif item["name"] == "Nuke":
                # Initialize skills list if it doesn't exist
                if not hasattr(player, 'skills'):
                    player.skills = []
                
                # Check if player already has this skill
                already_has_skill = False
                for skill in player.skills:
                    if skill.name == "Nuke":
                        already_has_skill = True
                        break
                
                if already_has_skill:
                    self.message = f"You already have {item['name']}!"
                    self.message_timer = 0
                    if self.sound_manager:
                        self.sound_manager.play_ui_hover()  # Use hover sound for error
                    return False
                
                # If player doesn't have the skill yet, check if all skill slots are filled (solo mode)
                # Solo mode has 3 skill slots max
                if hasattr(player, 'player_id') and player.player_id == 1 and len(player.skills) >= 3:
                    self.message = "All skill slots are full!"
                    self.message_timer = 0
                    if self.sound_manager:
                        self.sound_manager.play_ui_hover()
                    return False
                
                # Import the skill module and create the skill
                from skill import create_skill
                nuke_skill = create_skill("nuke", self.sound_manager)
                
                # Add to player's skills
                player.skills.append(nuke_skill)
                purchased = True
        
        elif self.current_tab == 2:  # Partner tab
            if item["name"] == "Skull Partner" and partner:
                # Change partner type from eagle to skull
                partner.change_type("skull")
                purchased = True
            elif item["name"] == "Eagle Partner" and partner:
                # Change partner type from skull to eagle
                partner.change_type("eagle")
                purchased = True
            # Add more partner items as needed
    
        # If item was purchased successfully
        if purchased:
            # Deduct money
            player.session_money -= item["price"]
            
            # Display success message
            self.message = f"Purchased {item['name']}!"
            self.message_timer = 0
            
            # Play purchase sound
            if self.sound_manager:
                self.sound_manager.play_gold_sound()
                
        return purchased

    def draw(self, surface):
        if not self.is_open:
            return
        
        # Calculate position (centered on screen)
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        x = (screen_width - self.width) // 2
        y = (screen_height - self.height) // 2
        
        # Create a semi-transparent overlay just for the menu area
        shop_bg = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        shop_bg.fill(self.bg_color)
        surface.blit(shop_bg, (x, y))
        
        # Draw gold border
        pygame.draw.rect(surface, self.border_color, 
                         (x, y, self.width, self.height), 3, border_radius=10)
        
        # Draw devil shop title
        title = self.title_font.render("Devil's Shop", True, self.title_color)
        title_rect = title.get_rect(midtop=(x + self.width//2, y + self.padding))
        surface.blit(title, title_rect)
        
        # Draw tabs
        tab_width = self.width // len(self.tab_names)
        for i, tab_name in enumerate(self.tab_names):
            tab_color = self.active_tab_color if i == self.current_tab else self.inactive_tab_color
            tab_text_color = self.highlight_color if i == self.current_tab else self.text_color
            
            tab_rect = pygame.Rect(
                x + i * tab_width,
                y + title_rect.height + self.padding * 2,
                tab_width,
                self.tab_height
            )
            
            pygame.draw.rect(surface, tab_color, tab_rect, border_radius=5)
            if i == self.current_tab:
                pygame.draw.rect(surface, self.border_color, tab_rect, 2, border_radius=5)
            
            tab_surf = self.tab_font.render(tab_name, True, tab_text_color)
            tab_text_rect = tab_surf.get_rect(center=tab_rect.center)
            surface.blit(tab_surf, tab_text_rect)
        
        # Draw items
        item_start_y = y + title_rect.height + self.padding * 2 + self.tab_height + self.padding
        for i, item in enumerate(self.items):
            # Determine if this item is selected
            is_selected = i == self.selected_item
            item_color = self.highlight_color if is_selected else self.text_color
            
            # Draw selection indicator
            if is_selected:
                selection_rect = pygame.Rect(
                    x + self.padding // 2,
                    item_start_y + i * (self.item_height + 5),
                    self.width - self.padding,
                    self.item_height
                )
                pygame.draw.rect(surface, (60, 60, 60), selection_rect, border_radius=5)
                pygame.draw.rect(surface, self.border_color, selection_rect, 2, border_radius=5)
            
            # Item name and price
            item_text = f"{item['name']} - ${item['price']}"
            item_surface = self.item_font.render(item_text, True, item_color)
            surface.blit(item_surface, (
                x + self.padding * 2,
                item_start_y + i * (self.item_height + 5) + 5
            ))
            
            # Draw description text for selected item
            if is_selected:
                desc_surface = self.desc_font.render(item['desc'], True, self.text_color)
                surface.blit(desc_surface, (
                    x + self.padding * 2,
                    item_start_y + i * (self.item_height + 5) + 30
                ))
        
        # Draw message at the bottom if there is one
        if self.message:
            message_surface = self.item_font.render(self.message, True, self.highlight_color)
            message_rect = message_surface.get_rect(midbottom=(x + self.width//2, y + self.height - 20))
            surface.blit(message_surface, message_rect)
        
        # Draw navigation hints
        hint_text = "← → Switch Tabs | ↑↓ Select Item | Space/Enter Purchase | ESC Close"
        hint_surface = self.desc_font.render(hint_text, True, self.text_color)
        hint_rect = hint_surface.get_rect(midbottom=(x + self.width//2, y + self.height - 5))
        surface.blit(hint_surface, hint_rect)
        
        # Draw which player last purchased something
        if hasattr(self, 'show_purchase_message') and self.show_purchase_message:
            if hasattr(self, 'purchase_message') and hasattr(self, 'purchase_message_timer'):
                purchase_font = load_font(24)
                purchase_text = purchase_font.render(self.purchase_message, True, (255, 215, 0))
                purchase_rect = purchase_text.get_rect(center=(self.shop_rect.centerx, self.shop_rect.bottom + 30))
                surface.blit(purchase_text, purchase_rect)
                # Update timer
                self.purchase_message_timer -= 1/60  # Assuming 60 FPS
                if self.purchase_message_timer <= 0:
                    self.show_purchase_message = False
        
        # Show active player indicator if available
        if hasattr(self, 'active_player_id') and hasattr(self, 'active_indicator_timer'):
            if self.active_indicator_timer > 0:
                indicator_font = load_font(28)
                indicator_text = indicator_font.render(f"Player {self.active_player_id} is shopping", True, (200, 255, 200))
                indicator_rect = indicator_text.get_rect(center=(self.shop_rect.centerx, self.shop_rect.top - 30))
                surface.blit(indicator_text, indicator_rect)
                
                # Update timer
                self.active_indicator_timer -= 1/60  # Assuming 60 FPS

class MiniMap:
    def __init__(self, map_width, map_height, screen_width, screen_height, player_id=1, position="right"):
        self.map_width = map_width
        self.map_height = map_height
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.player_id = player_id  # 1 or 2 to identify which player this minimap belongs to
        self.position = position    # "left" or "right" to determine position
        
        # Mini map dimensions and position
        self.width = 150
        self.height = 150
        self.padding = 10
        
        # Set position based on the parameter
        if position == "left":
            self.x = self.padding
            self.y = screen_height - self.height - 50  # Above level text
        else:
            self.x = screen_width - self.width - self.padding
            self.y = screen_height - self.height - 50  # Above XP text
        
        # Mini map scale factors
        self.scale_x = self.width / map_width
        self.scale_y = self.height / map_height
        
        # Create the mini map surface with semi-transparency
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Entity colors
        self.player1_color = (0, 255, 0)        # Green for player 1
        self.player2_color = (255, 255, 0)      # Yellow for player 2
        self.enemy_color = (255, 0, 0)          # Red for enemies
        self.devil_color = (150, 0, 0)          # Dark red for devil outline
        self.devil_color_inner = (0, 0, 0)      # Black for devil inner circle
        self.boss_color = (255, 0, 255)         # Purple for boss
        self.boss_color_inner = (180, 0, 180)   # Inner color for boss
        
        # Entity sizes
        self.player_size = 5
        self.other_player_size = 4
        self.enemy_size = 3
        self.devil_size = 7
        self.boss_size = 9                      # Boss is larger than devil

    def update_map_size(self, map_width, map_height):
        """Update map size if needed"""
        self.map_width = map_width
        self.map_height = map_height
        self.scale_x = self.width / map_width
        self.scale_y = self.height / map_height
    
    def draw(self, screen, player, other_player=None, enemies=None, devil=None, boss=None):
        # Clear the surface with translucent dark background
        self.surface.fill((20, 20, 20, 180))
        
        # Draw border
        pygame.draw.rect(self.surface, (200, 200, 200), 
                         (0, 0, self.width, self.height), 2)
        
        # Draw enemies
        if enemies:
            for enemy in enemies:
                if not enemy.is_dying:  # Only show active enemies
                    mini_x = int(enemy.rect.centerx * self.scale_x)
                    mini_y = int(enemy.rect.centery * self.scale_y)
                    pygame.draw.circle(self.surface, self.enemy_color, (mini_x, mini_y), self.enemy_size)
        
        # Draw devil if exists
        if devil and not getattr(devil, "fading_out", False):
            mini_x = int(devil.rect.centerx * self.scale_x)
            mini_y = int(devil.rect.centery * self.scale_y)
            # Draw devil as a larger circle with two colors
            pygame.draw.circle(self.surface, self.devil_color, (mini_x, mini_y), self.devil_size)
            pygame.draw.circle(self.surface, self.devil_color_inner, (mini_x, mini_y), self.devil_size - 2)

        # Draw boss if exists
        if boss and not getattr(boss, "is_defeated", False):
            mini_x = int(boss.rect.centerx * self.scale_x)
            mini_y = int(boss.rect.centery * self.scale_y)
            # Draw boss as an even larger circle with two colors and pulsing effect
            size_mod = int(math.sin(pygame.time.get_ticks() * 0.01) * 2)
            pygame.draw.circle(self.surface, self.boss_color, (mini_x, mini_y), 
                              self.boss_size + size_mod)
            pygame.draw.circle(self.surface, self.boss_color_inner, (mini_x, mini_y), 
                              self.boss_size - 2 + size_mod)
        
        # Draw other player if exists and alive
        if other_player and other_player.health > 0:
            mini_x = int(other_player.rect.centerx * self.scale_x)
            mini_y = int(other_player.rect.centery * self.scale_y)
            # Use appropriate color for the other player
            other_color = self.player1_color if self.player_id == 2 else self.player2_color
            pygame.draw.circle(self.surface, other_color, (mini_x, mini_y), self.other_player_size)
        
        # Draw main player (draw last so it's on top)
        mini_x = int(player.rect.centerx * self.scale_x)
        mini_y = int(player.rect.centery * self.scale_y)
        # Use appropriate color for the player this minimap belongs to
        player_color = self.player1_color if self.player_id == 1 else self.player2_color
        pygame.draw.circle(self.surface, player_color, (mini_x, mini_y), self.player_size)
        
        # Draw the mini map on the screen
        screen.blit(self.surface, (self.x, self.y))

    def set_position(self, x, y):
        """Set custom position for the minimap"""
        self.x = x
        self.y = y

    def adjust_for_split_screen(self, is_split, viewport_width):
        """Adjust minimap position for split screen mode"""
        if is_split:
            if self.player_id == 1:
                # Player 1 minimap always in bottom left
                self.x = self.padding
                self.y = self.screen_height - self.height - 50
            else:
                # Player 2 minimap in bottom right of right viewport
                self.x = viewport_width + self.padding
                self.y = self.screen_height - self.height - 50
        else:
            # In normal mode, position based on left/right parameter
            if self.position == "left":
                self.x = self.padding
                self.y = self.screen_height - self.height - 50
            else:
                self.x = self.screen_width - self.width - self.padding
                self.y = self.screen_height - self.height - 50

class SkillBar:
    def __init__(self, player_id=1, position="left", mode="solo", key_label=None):
        # Load skill UI resources
        self.skill_border = pygame.image.load("assets/UI/skill/skillborder.png").convert_alpha()
        self.skill_empty = pygame.image.load("assets/UI/skill/skillempty.png").convert_alpha()
        
        # Set dimensions for skill slot (responsive)
        ui_scale = get_ui_scale()
        self.slot_size = max(40, int(64 * ui_scale))
        self.skill_border = pygame.transform.scale(self.skill_border, (self.slot_size, self.slot_size))
        self.skill_empty = pygame.transform.scale(self.skill_empty, (self.slot_size, self.slot_size))
        
        # Player identification and positioning
        self.player_id = player_id  # 1 for player 1, 2 for player 2
        self.position = position    # "left" or "right"
        self.mode = mode            # "solo" or "coop"
        
        # Position calculation - will be set based on adjustments (use live screen size)
        self.x = 0
        surf = pygame.display.get_surface()
        live_h = surf.get_height() if surf else HEIGHT
        self.y = live_h - int(120 * ui_scale)  # Default vertical position above XP bar
        
        # Add font initialization here
        self.font = load_font(max(12, int(20 * ui_scale)))  # Initialize the font responsively
        
        # Add missing attribute
        self.effect_duration = 0.5  # Duration in seconds for activation effect
        
        # In solo mode, use 3 skill slots
        if self.mode == "solo":
            self.skills = [None, None, None]
            self.cooldowns = [0, 0, 0]
            self.last_activation_time = [0, 0, 0]
            self.activation_effect = [0, 0, 0]
            self.key_labels = ["1", "2", "3"]
        # In coop mode, use 1 skill slot
        else:
            self.skill = None
            self.cooldown = 0
            self.last_activation_time = 0
            self.activation_effect = 0
            # Use provided key_label or default based on player
            self.key_label = key_label or ("1" if player_id == 1 else "RCTRL")
        
        # Max cooldown time
        self.max_cooldown = 5.0  # 5 seconds cooldown by default
        
        # Set the initial position using live screen size
        self.adjust_position()
        
    def adjust_position(self, is_split_screen=False, screen_width=None):
        """Position the skill slots appropriately"""
        padding = 10
        # Use live screen size if not provided
        surf = pygame.display.get_surface()
        live_w = surf.get_width() if surf else WIDTH
        live_h = surf.get_height() if surf else HEIGHT
        if screen_width is None:
            screen_width = live_w
        
        if self.mode == "solo":
            # Center the 3 skills in solo mode above the XP bar
            total_width = (self.slot_size * 3) + (padding * 2)
            self.start_x = (screen_width - total_width) // 2
            # Position above XP bar using live height
            self.y = live_h - max(80, int(120 * get_ui_scale()))
        else:
            # In coop mode, position next to minimap
            minimap_size = 150  # Same as MiniMap width
            
            if is_split_screen:
                # In split-screen, position next to minimap in respective viewport
                if self.player_id == 1:
                    # Player 1 (left side): Position to the right of the minimap
                    self.x = minimap_size + padding * 2
                    self.y = live_h - minimap_size // 2 - self.slot_size // 2 - 50
                else:
                    # Player 2 (right side): Position to the right of the minimap
                    self.x = screen_width // 2 + minimap_size + padding * 2
                    self.y = live_h - minimap_size // 2 - self.slot_size // 2 - 50
            else:
                # In regular mode, position both skills next to their respective minimaps
                if self.player_id == 1:
                    # Player 1: To the right of left minimap
                    self.x = minimap_size + padding * 2
                    self.y = live_h - minimap_size // 2 - self.slot_size // 2 - 50
                else:
                    # Player 2: To the left of right minimap
                    self.x = screen_width - minimap_size - padding * 2 - self.slot_size
                    self.y = live_h - minimap_size // 2 - self.slot_size // 2 - 50
        
    def draw(self, screen):
        current_time = pygame.time.get_ticks() / 1000  # Convert to seconds
        
        # Different drawing logic for solo vs coop
        if self.mode == "solo":
            # Draw three skill slots for solo mode, centered dynamically to current width
            surf = pygame.display.get_surface()
            sw = surf.get_width() if surf else WIDTH
            padding = 10
            total_width = (self.slot_size * 3) + (padding * 2)
            start_x = (sw - total_width) // 2
            for i in range(3):
                x = start_x + (i * (self.slot_size + 10))
                
                # Draw empty skill background
                screen.blit(self.skill_empty, (x, self.y))
                
                # If there's a skill in this slot, draw it over the empty slot
                if hasattr(self.player, 'skills') and i < len(self.player.skills):
                    skill_icon = self.player.skills[i].get_icon()
                    if skill_icon:
                        # Scale icon to fit the slot
                        scaled_icon = pygame.transform.scale(skill_icon, (self.slot_size, self.slot_size))
                        screen.blit(scaled_icon, (x, self.y))
                
                # Draw cooldown overlay if skill is on cooldown
                if self.cooldowns[i] > 0:
                    # Calculate remaining cooldown percentage
                    elapsed = current_time - self.last_activation_time[i]
                    remaining_pct = max(0, min(1, 1 - (elapsed / self.max_cooldown)))
                    
                    if remaining_pct > 0:
                        # Create a semi-transparent overlay
                        overlay = pygame.Surface((self.slot_size, self.slot_size * remaining_pct), pygame.SRCALPHA)
                        overlay.fill((0, 0, 0, 150))  # Semi-transparent black
                        screen.blit(overlay, (x, self.y + self.slot_size * (1 - remaining_pct)))
                
                # Draw key label
                key_text = self.font.render(self.key_labels[i], True, (255, 255, 255))
                key_rect = key_text.get_rect(bottomright=(x + self.slot_size - 5, self.y + self.slot_size - 5))
                screen.blit(key_text, key_rect)
        else:
            # Draw single skill slot for coop mode
            # Draw empty skill background
            screen.blit(self.skill_empty, (self.x, self.y))
            
            # If there's a skill in this slot, draw it here (implement later)
            # if self.skill:
            #     screen.blit(self.skill["icon"], (self.x, self.y))
            
            # Draw cooldown overlay if skill is on cooldown
            if self.cooldown > 0:
                # Calculate remaining cooldown percentage
                elapsed = current_time - self.last_activation_time
                remaining_pct = max(0, min(1, 1 - (elapsed / self.max_cooldown)))
                
                if remaining_pct > 0:
                    # Create a semi-transparent overlay
                    overlay = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
                    overlay_height = int(self.slot_size * remaining_pct)
                    overlay.fill((0, 0, 0, 180), (0, self.slot_size - overlay_height, self.slot_size, overlay_height))
                    screen.blit(overlay, (self.x, self.y))
                    
                    # Show cooldown number
                    cooldown_text = str(math.ceil(self.max_cooldown - elapsed))
                    text_surf = self.font.render(cooldown_text, True, (255, 255, 255))
                    text_rect = text_surf.get_rect(center=(self.x + self.slot_size//2, self.y + self.slot_size//2))
                    screen.blit(text_surf, text_rect)
                else:
                    self.cooldown = 0
            
            # Draw activation effect if recently activated
            if self.activation_effect > 0:
                # Calculate effect progress (0-1)
                elapsed = current_time - self.last_activation_time - self.cooldown
                effect_progress = max(0, min(1, elapsed / self.effect_duration))
                self.activation_effect = 1 - effect_progress
                
                if self.activation_effect > 0:
                    # Draw pulsing glow effect
                    glow_size = int(self.slot_size * (1 + 0.2 * self.activation_effect))
                    glow_offset = (glow_size - self.slot_size) // 2
                    
                    glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                    alpha = int(120 * self.activation_effect)
                    color = (0, 255, 0, alpha) if self.player_id == 1 else (255, 255, 0, alpha)
                    pygame.draw.rect(glow_surf, color, 
                                    (0, 0, glow_size, glow_size), 
                                    border_radius=8)
                    
                    screen.blit(glow_surf, (self.x - glow_offset, self.y - glow_offset))
                else:
                    self.activation_effect = 0
            
            # Always draw the border
            screen.blit(self.skill_border, (self.x, self.y))
            
            # Draw keybind indicator
            key_text = render_text_with_border(self.font, self.key_label, WHITE, BLACK)
            text_x = self.x + 5
            text_y = self.y + self.slot_size - 20
            screen.blit(key_text, (text_x, text_y))
            
    def activate_skill(self, index=0):
        """Activate a skill - for solo mode index matters, for coop it's ignored"""
        if self.mode == "solo":
            # Check if the index is valid, skill exists, and not on cooldown
            if (0 <= index < 3 and not self.cooldowns[index] and 
                hasattr(self.player, 'skills') and index < len(self.player.skills)):
                
                skill = self.player.skills[index]
                # Start cooldown
                current_time = pygame.time.get_ticks() / 1000
                self.last_activation_time[index] = current_time
                self.cooldowns[index] = skill.cooldown  # Use skill's actual cooldown
                self.activation_effect[index] = 1.0
                
                # Return the skill for activation
                return skill
            return None
        else:
            # In coop mode, use the first skill if available and not on cooldown
            if not self.cooldown and hasattr(self.player, 'skills') and len(self.player.skills) > 0:
                skill = self.player.skills[0]
                current_time = pygame.time.get_ticks() / 1000
                self.last_activation_time = current_time
                self.cooldown = skill.cooldown
                self.activation_effect = 1.0
                
                # Return the skill for activation
                return skill
            return None
        
    def update(self, dt):
        # Update cooldowns
        current_time = pygame.time.get_ticks() / 1000
        
        if self.mode == "solo":
            for i in range(3):
                if self.cooldowns[i] > 0:
                    elapsed = current_time - self.last_activation_time[i]
                    if elapsed >= self.max_cooldown:
                        self.cooldowns[i] = 0
        else:
            if self.cooldown > 0:
                elapsed = current_time - self.last_activation_time
                if elapsed >= self.max_cooldown:
                    self.cooldown = 0
