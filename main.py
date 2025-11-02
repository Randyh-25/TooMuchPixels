import pygame
import sys
import pygame_menu
from settings import *
from utils import pause_menu, highest_score_menu, load_game_data, save_game_data
from ui import render_text_with_border
from settings import load_font
from sound_manager import SoundManager
import solo
import coop
import math
import random
import os
from player_animations import PlayerAnimations

pygame.init()

# Centralized display management to avoid crashes when toggling resolution/fullscreen
def _safe_set_mode(size, flags=0):
    """Safely call set_mode and return the new screen surface. Fallback to 1280x720 on failure."""
    try:
        scr = pygame.display.set_mode(size, flags)
        return scr
    except Exception as e:
        # Fallback to a safe windowed resolution
        try:
            scr = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
            return scr
        except Exception:
            raise e

def _get_desktop_resolution():
    info = pygame.display.Info()
    return (info.current_w, info.current_h)

# Load and set window icon (scaled) – responsive to platform expectations
def _set_window_icon():
    icon_candidates = [
        os.path.join('assets', 'UI', 'logo.png'),
        os.path.join('assets', 'UI', 'btn', 'play.png'),
    ]
    for path in icon_candidates:
        if os.path.exists(path):
            try:
                icon = pygame.image.load(path).convert_alpha()
                # Scale to a typical icon size
                icon_size = 48
                icon = pygame.transform.smoothscale(icon, (icon_size, icon_size))
                pygame.display.set_icon(icon)
                break
            except Exception:
                continue

# Initialize display (windowed-only)
screen = _safe_set_mode(CURRENT_RESOLUTION, pygame.RESIZABLE)
WIDTH, HEIGHT = screen.get_size()

pygame.display.set_caption("Too Much Pixels") # menetapkan judul
_set_window_icon()

clock = pygame.time.Clock() # membuat objek clock untuk mengatur frame rate
sound_manager = SoundManager() # inisialisasi manajer suara

# Inisialisasi animasi player sekali saja
player_anim = PlayerAnimations() # objek animasi untuk player pertama 
player_anim2 = PlayerAnimations()  # Untuk player kedua jika co-op

# efek partikel untuk latar belakang
class MenuParticle:
    def __init__(self, x, y): # konstruktor dengan posisi awal partikel
        self.x = x
        self.y = y
        self.size = random.randint(1, 3) # ukuran partikel secara acak antara 1 dan 3
        self.color = (random.randint(180, 255), random.randint(180, 255), random.randint(180, 255))
        self.speed = random.uniform(0.2, 1.0)
        self.angle = random.uniform(0, 2 * math.pi)
        self.lifetime = random.randint(100, 200)
        
    def update(self):
        self.x += math.cos(self.angle) * self.speed # menggerakkan partikel secara horizontal berdasarkan sudut dan kecepatan
        self.y += math.sin(self.angle) * self.speed # menggerakkan partikel secara vertikal berdasarkan sudut dan kecepatan
        self.lifetime -= 1 # mengurangi umur partikel setiap frame

        # efek menghilang
        if self.lifetime < 50:
            alpha = int((self.lifetime / 50) * 255) # menghitung tingkat transparansi berdasarkan sisa umur
            self.color = (*self.color[:3], alpha) # menambahkan nilai alpha ke warna
        
    def draw(self, surface): # menggambar partikel ke permukaan jika masi hidup
        if self.lifetime > 0: # hanya gambar jika masih ada sisa umur
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size) # gambar lingkaran partikel

class MenuParticleSystem:
    def __init__(self, width, height): # menerima lebar dan tinggi area partikel
        self.width = width
        self.height = height
        self.particles = [] # menyimpan semua partikel aktif
        self.spawn_timer = 0 # mengatur kapan partikel baru dibuat
        
    def update(self): # memperbarui sistem partikel setiap frame
        # menambahkan partikel baru secara berkala
        self.spawn_timer += 1 # menambahkan timer
        if self.spawn_timer >= 5:  # setiap 5 frame
            self.spawn_timer = 0
            for _ in range(2):  # menambahkan 2 partikel sekaligus
                self.particles.append(MenuParticle(
                    random.randint(0, self.width),
                    random.randint(0, self.height)
                ))
        
        # memperbarui semua partikel yang ada
        for particle in self.particles[:]:
            particle.update() # update status dan posisi partikel
            if particle.lifetime <= 0:
                self.particles.remove(particle) # hapus partikel dari sistem
                
    def draw(self, surface): # menggambar semua partikel ke permukaan target
        for particle in self.particles:
            particle.draw(surface) # memanggil metode draw milik masing-masing partikel

# membuat latar belakang menu menggunakan partikel
particle_system = MenuParticleSystem(WIDTH, HEIGHT) # inisialisasi sistem partikel untuk ukuran layar
menu_background = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA) # surface transparan untuk latar menu

# Helper to apply windowed resolution changes consistently
def apply_display_changes(new_resolution=None):
    """
    Apply windowed display changes safely, update global screen, WIDTH/HEIGHT, and dependent surfaces.
    - new_resolution: (w,h) or None
    Returns: None
    """
    global screen, WIDTH, HEIGHT, CURRENT_RESOLUTION, particle_system, menu_background

    flags = pygame.RESIZABLE
    if new_resolution is not None:
        CURRENT_RESOLUTION = new_resolution
    target_size = CURRENT_RESOLUTION

    screen = _safe_set_mode(target_size, flags)
    WIDTH, HEIGHT = screen.get_size()

    # Update dependent surfaces and systems
    if hasattr(particle_system, 'width'):
        particle_system.width = WIDTH
    if hasattr(particle_system, 'height'):
        particle_system.height = HEIGHT
    menu_background = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

# mesin suara kustom untuk pygame_menu dengan feedback suara yang disesuaikan
class SoundEngine(pygame_menu.sound.Sound):
    def __init__(self, sound_manager): # menerima objek manajer suara dari game
        super().__init__()
        self.sound_manager = sound_manager # menyimpan referensi ke manajer suara
        
    def play_click_sound(self) -> None:
        self.sound_manager.play_ui_click()
        
    def play_key_add_sound(self) -> None:
        self.sound_manager.play_ui_hover()
        
    def play_open_menu_sound(self) -> None:
        self.sound_manager.play_ui_click()
        
    def play_close_menu_sound(self) -> None:
        self.sound_manager.play_ui_click()

# efek widget yang ditingkatkan - efek denyut untuk tombol menu
class PulseWidgetTransform(pygame_menu.widgets.core.Selection):
    def __init__(self):
        super().__init__()
        self.pulse_time = 0 # waktu untuk menghitung fase denyut
        self.pulse_amplitude = 0.03  # seberapa besarr efek skala
        self.pulse_frequency = 0.05  # seberapa cepat denyutan terjadi
        
    def draw(self, surface, widget):
        if widget.is_selected():
            # buat efek denyutan dengan fungsi sinus untuk menghasilkan skaka yang naik-turun
            self.pulse_time += self.pulse_frequency
            scale_factor = 1.0 + self.pulse_amplitude * math.sin(self.pulse_time)
            
            # salin surface asli widget untuk diberi efek visual
            if hasattr(widget, '_surface'):
                original_rect = widget.get_rect()
                
                # Calculate scaled dimensions
                scaled_width = int(original_rect.width * scale_factor)
                scaled_height = int(original_rect.height * scale_factor)
                
                # Center the scaled surface
                x_offset = (original_rect.width - scaled_width) // 2
                y_offset = (original_rect.height - scaled_height) // 2
                
                # Apply scaling
                surface_copy = pygame.transform.scale(widget._surface, (scaled_width, scaled_height))
                
                # Add glow effect
                glow_color = (255, 255, 0, 50)  # Subtle yellow glow
                glow = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
                glow.fill(glow_color)
                surface_copy.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
                
                # Draw the transformed surface
                surface.blit(surface_copy, (original_rect.x + x_offset, original_rect.y + y_offset))
                return True
                
        return False

# fungsi bantu untuk membuat menu bertema dengan visual yang ditingkatkan
def create_themed_menu(title, width, height):
    # membuat tema khusus berdasarkan tema gelap 
    theme = pygame_menu.themes.THEME_DARK.copy()
    theme.widget_font = FONT_PATH
    theme.title_font = FONT_PATH
    
    # gaya judul yang ditingkatkan
    theme.title_background_color = (20, 20, 30, 220)
    theme.title_font_shadow = True
    theme.title_font_shadow_color = (0, 0, 0)
    theme.title_font_shadow_offset = 3
    theme.title_bar_style = pygame_menu.widgets.MENUBAR_STYLE_SIMPLE
    theme.title_font_size = 45
    theme.title_font_antialias = True
    theme.title_font_color = (255, 230, 150)  # Warm gold color
    
    # Title positioning and decoration
    theme.title_offset = (5, 5)
    theme.title_padding = (15, 15)
    
    # Improved widget styling
    theme.widget_font_size = 36
    theme.widget_padding = (10, 15)
    theme.widget_margin = (0, 15)
    
    # Gunakan SimpleSelection sebagai fallback yang aman
    theme.widget_selection_effect = pygame_menu.widgets.SimpleSelection()
    
    # Button styling
    theme.widget_font_color = (220, 220, 220)
    theme.selection_color = (255, 215, 0)
    theme.widget_selection_color = (255, 255, 150)
    
    # Menu background
    theme.background_color = pygame_menu.baseimage.BaseImage(
        image_path='assets/UI/bg.png',
        drawing_mode=pygame_menu.baseimage.IMAGE_MODE_FILL,
        drawing_offset=(0, 0)
    )
    
    # Create decorated borders
    theme.border_width = 2
    theme.border_color = (255, 215, 0)  # Gold border
    
    # Title underline for style
    # theme.title_bar_style = pygame_menu.widgets.MENUBAR_STYLE_UNDERLINE_TITLE
    # theme.title_underline_width = 3
    # theme.title_underline_color = (255, 215, 0)  # Gold underline
    theme.title_bar_style = pygame_menu.widgets.MENUBAR_STYLE_NONE
    
    # Create menu with the enhanced theme
    menu = pygame_menu.Menu(
        title, 
        width,
        height,
        theme=theme,
        onclose=pygame_menu.events.CLOSE,
        center_content=True
    )
    
    # Add custom sound engine
    menu.set_sound(SoundEngine(sound_manager))
    
    return menu

# Modified splash screen with particle effects and smoother transitions
def splash_screen():
    particles = []
    
    # Create initial particles
    for _ in range(50):
        particles.append(MenuParticle(
            random.randint(0, WIDTH),
            random.randint(0, HEIGHT)
        ))
    
    fade_surface = pygame.Surface((WIDTH, HEIGHT))
    fade_surface.fill(BLACK)
    
    # Prepare text with better styling
    title_font = load_font(100)
    studio_font = load_font(48)
    subtext_font = load_font(24)
    
    title_text = title_font.render("Too Much Pixels", True, (255, 230, 150))
    studio_text = studio_font.render("D'King Studio", True, (200, 200, 200))
    subtext = subtext_font.render("Long Live D'King", True, (150, 150, 150))
    
    # Position text
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80))
    studio_rect = studio_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
    subtext_rect = subtext.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
    
    # Play splash sound
    sound_manager.play_splash_sound()
    
    # Fade in
    for alpha in range(255, 0, -3):
        screen.fill((10, 10, 15))  # Dark blue-black background
        
        # Update and draw particles
        for particle in particles[:]:
            particle.update()
            particle.draw(screen)
            if particle.lifetime <= 0:
                particles.remove(particle)
                if len(particles) < 50:
                    particles.append(MenuParticle(
                        random.randint(0, WIDTH),
                        random.randint(0, HEIGHT)
                    ))
        
        # Draw text with shadow
        shadow_offset = 3
        shadow_color = (0, 0, 0, 100)
        
        # Draw shadows
        shadow_title = title_font.render("Too Much Pixels", True, shadow_color)
        shadow_studio = studio_font.render("D'King Studio", True, shadow_color)
        shadow_subtext = subtext_font.render("Long Live D'King", True, shadow_color)
        
        screen.blit(shadow_title, (title_rect.x + shadow_offset, title_rect.y + shadow_offset))
        screen.blit(shadow_studio, (studio_rect.x + shadow_offset, studio_rect.y + shadow_offset))
        screen.blit(shadow_subtext, (subtext_rect.x + shadow_offset, subtext_rect.y + shadow_offset))
        
        # Draw actual text
        screen.blit(title_text, title_rect)
        screen.blit(studio_text, studio_rect)
        screen.blit(subtext, subtext_rect)
        
        # Apply fade
        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))
        
        pygame.display.flip()
        clock.tick(60)
    
    # Hold for a moment
    pygame.time.delay(2000)
    
    # Fade out
    for alpha in range(0, 255, 3):
        screen.fill((10, 10, 15))
        
        for particle in particles[:]:
            particle.update()
            particle.draw(screen)
            if particle.lifetime <= 0:
                particles.remove(particle)
        
        screen.blit(title_text, title_rect)
        screen.blit(studio_text, studio_rect)
        screen.blit(subtext, subtext_rect)
        
        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))
        
        pygame.display.flip()
        clock.tick(60)

def start_game(mode):
    # transisi awal 
    fade_surface = pygame.Surface((WIDTH, HEIGHT))
    fade_surface.fill(BLACK)
    
    # mainkan suara klik UI sebelum memulai transisi
    sound_manager.play_ui_click()
    pygame.time.delay(200)

    # efek transisi fade-in ke hitam
    for alpha in range(0, 255, 5):
        screen.fill((10, 10, 15))
        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))
        pygame.display.flip()
        pygame.time.delay(5)
    
    # menghentikan musik menu dengan transisi
    sound_manager.stop_menu_music()

    # memindahkan ke mode permainan yang dipilih
    if mode == "solo":
        solo.main(screen, clock, sound_manager, main_menu) # mulai mode solo
    elif mode == "split_screen":
        coop.split_screen_main(screen, clock, sound_manager, main_menu) # mulai mode split-screen co-op

def settings_menu():
    # buat menu bertema dengan judul "settings"
    sw, sh = pygame.display.get_surface().get_size()
    menu = create_themed_menu('Settings', sw, sh)

    def change_resolution(_, res):
        global CURRENT_RESOLUTION
        sound_manager.play_ui_click()
        apply_display_changes(new_resolution=res)
        # menyesuaikan ukuran menu agar sesuai dengan resolusi layar baru
        try:
            menu.resize(WIDTH, HEIGHT)
        except Exception:
            pass

    def change_volume(value): # mengubah volume suara dari slider
        global VOLUME
        VOLUME = value
        sound_manager.set_volume(value)

    # Bungkus konten dalam panel semi-transparan agar tidak "nabrak" background
    panel_w = min(900, sw - 120)
    panel_h = 420  # relax, konten bisa melebihi
    content = menu.add.frame_v(panel_w, panel_h, background_color=(10, 10, 15, 200),
                               border_width=2, border_color=(255, 215, 0))
    content._relax = True
    content._pack_margin_warning = False

    # DISPLAY section
    lbl_display = menu.add.label('• DISPLAY SETTINGS •', font_size=28, font_color=(255, 215, 0))
    lbl_display.set_margin(0, 0)
    content.pack(lbl_display, align=pygame_menu.locals.ALIGN_CENTER)

    vm1 = menu.add.vertical_margin(10)
    vm1.set_margin(0, 0)
    content.pack(vm1)

    resolution_selector = menu.add.selector('Windowed Resolution: ', RESOLUTIONS, onchange=change_resolution,
                                         font_size=28, selection_color=(255, 255, 150))
    resolution_selector.set_margin(0, 0)
    content.pack(resolution_selector, align=pygame_menu.locals.ALIGN_CENTER)

    vm2 = menu.add.vertical_margin(20)
    vm2.set_margin(0, 0)
    content.pack(vm2)

    # AUDIO section
    lbl_audio = menu.add.label('• AUDIO SETTINGS •', font_size=28, font_color=(255, 215, 0))
    lbl_audio.set_margin(0, 0)
    content.pack(lbl_audio, align=pygame_menu.locals.ALIGN_CENTER)

    vm3 = menu.add.vertical_margin(10)
    vm3.set_margin(0, 0)
    content.pack(vm3)

    vol = menu.add.range_slider('Master Volume: ', default=VOLUME, range_values=(0, 100), 
                       increment=5, onchange=change_volume,
                       font_size=28, slider_color=(255, 215, 0))
    vol.set_margin(0, 0)
    content.pack(vol, align=pygame_menu.locals.ALIGN_CENTER)

    vm4 = menu.add.vertical_margin(20)
    vm4.set_margin(0, 0)
    content.pack(vm4)

    btn_back = menu.add.button('Back to Main Menu', main_menu, font_size=32, 
                  background_color=(40, 40, 60))
    btn_back.set_margin(0, 0)
    content.pack(btn_back, align=pygame_menu.locals.ALIGN_CENTER)
    
    # Create dynamic background with particles during menu loop
    while menu.is_enabled():
        # Update particle system
        particle_system.update()
        
        # Draw background and particles first
        menu_background.fill((10, 10, 15, 200))  # Semi-transparent background
        particle_system.draw(menu_background)
        
        # Update menu with the background
        events = pygame.event.get()
        menu.update(events)
        screen.blit(menu_background, (0, 0))
        menu.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)

def quit_confirmation():
    menu = create_themed_menu('Quit Game', WIDTH, HEIGHT)
    
    menu.add.vertical_margin(20)
    menu.add.label('Are you sure you want to exit the game?', font_size=40, 
                 font_color=(255, 255, 255), margin=(0, 30))
    menu.add.vertical_margin(20)
    
    # Create a more appealing button layout (relaxed to avoid size exceptions)
    button_layout = menu.add.frame_h(500, 120)
    button_layout._relax = True  # allow content to exceed frame constraints
    button_layout.pack(menu.add.button('Yes', pygame.quit, 
                                    font_size=36, 
                                    background_color=(170, 50, 50),
                                    border_width=2,
                                    border_color=(255, 150, 150),
                                    margin=(0, 0)), 
                    align=pygame_menu.locals.ALIGN_CENTER)
                    
    button_layout.pack(menu.add.button('No', main_menu, 
                                    font_size=36,
                                    background_color=(50, 170, 50),
                                    border_width=2,
                                    border_color=(150, 255, 150),
                                    margin=(0, 0)), 
                    align=pygame_menu.locals.ALIGN_CENTER)
    
    # Create dynamic background with particles during menu loop
    while menu.is_enabled():
        particle_system.update()
        
        menu_background.fill((10, 10, 15, 220))
        particle_system.draw(menu_background)
        
        events = pygame.event.get()
        menu.update(events)
        screen.blit(menu_background, (0, 0))
        menu.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)

def draw_player_menu_animation(surface, solo_hover, coop_hover, frame_idx):
    # Perlambat animasi: ganti frame setiap 7 tick
    anim_speed = 7
    walk_anim = player_anim.animations['walk_down']
    walk_anim2 = player_anim2.animations['walk_down']
    frame = walk_anim[(frame_idx // anim_speed) % len(walk_anim)]
    frame2 = walk_anim2[(frame_idx // anim_speed) % len(walk_anim2)]

    # Perbesar sprite (misal 1.5x)
    scale_factor = 1.5
    frame = pygame.transform.scale(frame, (int(frame.get_width() * scale_factor), int(frame.get_height() * scale_factor)))
    frame2 = pygame.transform.scale(frame2, (int(frame2.get_width() * scale_factor), int(frame2.get_height() * scale_factor)))

    center_x = WIDTH // 2
    center_y = HEIGHT // 2 + 40

    if solo_hover:
        surface.blit(frame, (center_x - frame.get_width() // 2, center_y - frame.get_height() // 2))
    elif coop_hover:
        offset = 50  # Sedikit lebih lebar agar tidak bertumpuk
        surface.blit(frame, (center_x - frame.get_width() - offset//2, center_y - frame.get_height() // 2))
        surface.blit(frame2, (center_x + offset//2, center_y - frame2.get_height() // 2))

def main_menu():
    sound_manager.play_menu_music()
    
    sw, sh = pygame.display.get_surface().get_size()
    menu = create_themed_menu(' ', sw, sh)
    
    saved_money, highest_score, player_name = load_game_data()
    
    # Add animated logo
    logo_img = pygame.image.load('assets/UI/logo.png').convert_alpha() if os.path.exists('assets/UI/logo.png') else None
    if logo_img:
        logo_img = pygame.transform.scale(logo_img, (400, 150))
        menu.add.image(logo_img, scale=(1, 1), scale_smooth=True)
        menu.add.vertical_margin(20)
    
    # Player information: tampilkan langsung tanpa frame/container
    if player_name:
        menu.add.vertical_margin(150)
        menu.add.label(
            f"WELCOME, {player_name.upper()}",
            font_size=28,
            font_color=(255, 215, 0),
            font_shadow=True,
            font_shadow_color=(0, 0, 0),
            font_shadow_offset=2
        )
        
    
    # Button styling with improved visuals
    button_style = {
        'font_size': 42,
        'background_color': (40, 40, 60),
        'border_width': 2,
        'border_color': (255, 215, 0, 80),
        'cursor': pygame_menu.locals.CURSOR_HAND
    }
    
    menu.add.button('PLAY', game_mode_menu, **button_style)
    menu.add.vertical_margin(10)
    menu.add.button('SETTINGS', settings_menu, **button_style)
    menu.add.vertical_margin(10)
    menu.add.button('QUIT', quit_confirmation, **button_style)
    
    # Decorative footer
    menu.add.vertical_margin(50)
    menu.add.label("© 2025 D'King Studio", font_size=16, font_color=(150, 150, 150))
    
    # Create dynamic background with particles
    while menu.is_enabled():
        particle_system.update()
        
        menu_background.fill((10, 10, 15, 200))
        particle_system.draw(menu_background)
        
        events = pygame.event.get()
        menu.update(events)
        screen.blit(menu_background, (0, 0))
        menu.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)

def game_mode_menu():
    sw, sh = pygame.display.get_surface().get_size()
    menu = create_themed_menu('SELECT GAME MODE', sw, sh)
    
    # Add descriptive info for each mode
    menu.add.vertical_margin(30)
    
    # Buat layout horizontal untuk menempatkan mode game bersebelahan
    # Gunakan ukuran yang lebih besar untuk menghindari masalah overflow
    mode_layout = menu.add.frame_h(WIDTH - 100, 350)
    
    # KOLOM KIRI: Mode Solo
    solo_frame = menu.add.frame_v(430, 300, background_color=(20, 20, 30, 150), border_width=2, border_color=(255, 215, 0))
    solo_frame.set_margin(20, 20)  # Tambahkan margin
    
    # Tambahkan ikon solo jika tersedia
    if os.path.exists('assets/UI/solo_icon.png'):
        solo_icon = pygame.image.load('assets/UI/solo_icon.png').convert_alpha()
        solo_icon = pygame.transform.scale(solo_icon, (100, 100))
        solo_frame.pack(menu.add.image(solo_icon), align=pygame_menu.locals.ALIGN_CENTER)
    
    solo_frame.pack(menu.add.label('SOLO ADVENTURE', font_size=36, font_color=(255, 215, 0)), align=pygame_menu.locals.ALIGN_CENTER)
    solo_frame.pack(menu.add.vertical_margin(10))
    
    # Split description into multiple lines for better fit
    solo_frame.pack(menu.add.label('Face the dangers alone', font_size=20), align=pygame_menu.locals.ALIGN_CENTER)
    solo_frame.pack(menu.add.label('in a quest for survival', font_size=20), align=pygame_menu.locals.ALIGN_CENTER)
    solo_frame.pack(menu.add.vertical_margin(20))
    
    solo_button = menu.add.button('START SOLO', lambda: start_game("solo"), 
                  font_size=28, 
                  background_color=(40, 40, 60),
                  border_width=2,
                  border_color=(255, 215, 0, 80))
    solo_frame.pack(solo_button, align=pygame_menu.locals.ALIGN_CENTER)
    
    # KOLOM KANAN: Mode Co-op
    coop_frame = menu.add.frame_v(430, 300, background_color=(20, 20, 30, 150), border_width=2, border_color=(255, 215, 0))
    coop_frame.set_margin(20, 20)  # Tambahkan margin
    
    # Tambahkan ikon co-op jika tersedia
    if os.path.exists('assets/UI/coop_icon.png'):
        coop_icon = pygame.image.load('assets/UI/coop_icon.png').convert_alpha()
        coop_icon = pygame.transform.scale(coop_icon, (100, 100))
        coop_frame.pack(menu.add.image(coop_icon), align=pygame_menu.locals.ALIGN_CENTER)
    
    coop_frame.pack(menu.add.label('CO-OP MULTIPLAYER', font_size=36, font_color=(255, 215, 0)), align=pygame_menu.locals.ALIGN_CENTER)
    coop_frame.pack(menu.add.vertical_margin(10))
    
    # Split description into multiple lines for better fit
    coop_frame.pack(menu.add.label('Team up with a friend', font_size=20), align=pygame_menu.locals.ALIGN_CENTER)
    coop_frame.pack(menu.add.label('in split-screen action', font_size=20), align=pygame_menu.locals.ALIGN_CENTER)
    coop_frame.pack(menu.add.vertical_margin(20))
    
    coop_button = menu.add.button('START CO-OP', lambda: start_game("split_screen"),
                  font_size=28,
                  background_color=(40, 40, 60),
                  border_width=2,
                  border_color=(255, 215, 0, 80))
    coop_frame.pack(coop_button, align=pygame_menu.locals.ALIGN_CENTER)
    
    # Pack keduanya ke dalam layout horizontal
    mode_layout.pack(solo_frame, align=pygame_menu.locals.ALIGN_LEFT)
    mode_layout.pack(coop_frame, align=pygame_menu.locals.ALIGN_RIGHT)
    
    # Tambahkan tombol kembali di bawah layout
    menu.add.vertical_margin(30)
    menu.add.button('Back to Main Menu', main_menu, 
                  font_size=28,
                  background_color=(60, 60, 80))
    
    # Variabel status hover
    mode_hover = {"solo": False, "coop": False}

    # --- Tambahkan event handler hover ---
    def on_solo_hover(selected, value):
        mode_hover["solo"] = selected
        mode_hover["coop"] = False

    def on_coop_hover(selected, value):
        mode_hover["solo"] = False
        mode_hover["coop"] = selected

    solo_button.set_onselect(lambda: on_solo_hover(True, None))
    coop_button.set_onselect(lambda: on_coop_hover(True, None))

    def reset_hover():
        mode_hover["solo"] = False
        mode_hover["coop"] = False

    frame_idx = 0
    while menu.is_enabled():
        particle_system.update()
        menu_background.fill((10, 10, 15, 200))
        particle_system.draw(menu_background)

        events = pygame.event.get()
        menu.update(events)
        screen.blit(menu_background, (0, 0))
        menu.draw(screen)

        # Gambar animasi player di tengah
        draw_player_menu_animation(
            screen,
            mode_hover["solo"] or solo_button.is_selected(),
            mode_hover["coop"] or coop_button.is_selected(),
            frame_idx
        )
        frame_idx += 1
        if not (solo_button.is_selected() or coop_button.is_selected()):
            reset_hover()

        pygame.display.flip()
        clock.tick(60)

def player_name_screen():
    sw, sh = pygame.display.get_surface().get_size()
    menu = create_themed_menu('', sw, sh)
    
    player_name = [""]
    
    def save_name():
        sound_manager.play_ui_click()
        if player_name[0].strip():
            save_game_data(0, 0, player_name[0])
            
            # Show welcome message with animation
            welcome_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            welcome_font = load_font(50)
            welcome_text = welcome_font.render(f"Welcome, {player_name[0]}!", True, (255, 255, 255))
            welcome_rect = welcome_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            
            for alpha in range(0, 255, 5):
                welcome_surface.fill((0, 0, 0, 0))
                welcome_text.set_alpha(alpha)
                welcome_surface.blit(welcome_text, welcome_rect)
                screen.fill((10, 10, 15))
                screen.blit(welcome_surface, (0, 0))
                pygame.display.flip()
                pygame.time.delay(10)
            
            pygame.time.delay(1000)
            
            for alpha in range(255, 0, -5):
                welcome_surface.fill((0, 0, 0, 0))
                welcome_text.set_alpha(alpha)
                welcome_surface.blit(welcome_text, welcome_rect)
                screen.fill((10, 10, 15))
                screen.blit(welcome_surface, (0, 0))
                pygame.display.flip()
                pygame.time.delay(10)
                
            main_menu()
    
    def name_changed(value):
        player_name[0] = value
    
    # Add decorative elements
    menu.add.vertical_margin(150)
    menu.add.label("Begin Your Pixel Adventure", font_size=50, 
                   font_color=(255, 215, 0),
                   font_shadow=True,
                   font_shadow_color=(0, 0, 0),
                   font_shadow_offset=3)
    menu.add.vertical_margin(20)
    menu.add.label("Enter your hero's name:", font_size=30, font_color=(255, 215, 0),
                   font_shadow=True,
                   font_shadow_color=(0, 0, 0),
                   font_shadow_offset=3)
    menu.add.vertical_margin(20)
    
    # Perbaiki masalah dengan cursor_selection_color
    text_input = menu.add.text_input(
        ' ', 
        default='', 
        onchange=name_changed,
        font_size=36,
        selection_color=(255, 255, 150),
        border_width=2,
        border_color=(255, 215, 0),
        # Hapus cursor_selection_color dan gunakan parameter yang didukung
        maxchar=12
    )
    
    menu.add.vertical_margin(30)
    menu.add.button('Begin Journey', save_name, 
                  font_size=40,
                  background_color=(40, 40, 60),
                  border_width=2,
                  border_color=(255, 215, 0))
    
    # Create dynamic background with particles
    while menu.is_enabled():
        particle_system.update()
        
        menu_background.fill((10, 10, 15, 220))
        particle_system.draw(menu_background)
        
        events = pygame.event.get()
        menu.update(events)
        screen.blit(menu_background, (0, 0))
        menu.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
if __name__ == "__main__":
    splash_screen()
    _, _, player_name = load_game_data()
    if not player_name:
        player_name_screen()
    else:
        main_menu()
