# Ukuran default window (windowed-only)
WIDTH, HEIGHT = 1280, 720

# Jumlah frame per detik (frame rate)
FPS = 60

# Definisi warna dalam format RGB
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE  = (0, 0, 255)
YELLOW = (255, 255, 0)

# Status fullscreen dimatikan (game windowed-only)
FULLSCREEN = False

# Resolusi saat ini (mengacu ke ukuran WIDTH dan HEIGHT)
CURRENT_RESOLUTION = (WIDTH, HEIGHT)

# Nilai volume awal (dalam persen)
VOLUME = 50

# Daftar resolusi yang tersedia untuk dipilih di pengaturan
# Hanya dua resolusi windowed yang diizinkan
RESOLUTIONS = [
    ('1280x720', (1280, 720)),
    ('1920x1080', (1920, 1080)),
]

# Import modul pygame dan pygame_menu
import pygame
import pygame_menu
import os

# Path ke font khusus yang digunakan
FONT_PATH = "assets/font/PixelifySans-VariableFont_wght.ttf"

def load_font(size):
    """Fungsi untuk memuat font khusus dengan ukuran tertentu"""
    try:
        return pygame.font.Font(FONT_PATH, size)  # Load dari file
    except:
        # Jika gagal, gunakan font default dari sistem
        print(f"Warning: Could not load font {FONT_PATH}, using system default")
        return pygame.font.SysFont(None, size)

# Variabel global untuk status fullscreen dan resolusi saat ini
fullscreen = [FULLSCREEN]
current_resolution = CURRENT_RESOLUTION

def settings_menu(screen, main_menu_callback):
    """Fungsi untuk menampilkan menu pengaturan"""
    resolutions = RESOLUTIONS

    # Hilangkan dukungan fullscreen; game windowed-only
    def toggle_fullscreen(value):
        pass

    def change_resolution(_, res):
        """Fungsi untuk mengubah resolusi saat tidak fullscreen"""
        global current_resolution
        current_resolution = res
        pygame.display.set_mode(res, pygame.RESIZABLE)

    # Buat menu pengaturan menggunakan pygame_menu
    menu = pygame_menu.Menu('Settings', WIDTH, HEIGHT, theme=pygame_menu.themes.THEME_DARK)
    
    # Tambahkan selector untuk memilih resolusi
    resolution_selector = menu.add.selector('Resolution: ', resolutions, onchange=change_resolution)
    # Selalu tampilkan pilihan resolusi (windowed-only)

    # Hilangkan toggle fullscreen

    # Tambahkan slider untuk pengaturan volume
    menu.add.range_slider('Master Volume: ', default=VOLUME, range_values=(0, 100), increment=1,
                          onchange=lambda value: print(f"Volume set to {value}"))

    # Tombol untuk kembali ke menu utama
    menu.add.button('Back', main_menu_callback)

    # Jalankan menu
    menu.mainloop(screen)
