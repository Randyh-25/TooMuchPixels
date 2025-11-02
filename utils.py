import os
import pickle
import pygame
import pygame_menu
import json
import random
import math
from settings import WIDTH, HEIGHT, load_font, FONT_PATH, BLACK, WHITE

SAVE_FILE = "game.dat"

def save_game_data(money=0, highest_score=0, player_name=""):
    game_data = {
        'money': money,
        'highest_score': highest_score,
        'player_name': player_name
    }
    with open(SAVE_FILE, 'wb') as file:
        pickle.dump(game_data, file)

def load_game_data():
    try:
        with open(SAVE_FILE, 'rb') as file:
            game_data = pickle.load(file)
            return (game_data['money'], 
                   game_data['highest_score'],
                   game_data.get('player_name', "")) 
    except (FileNotFoundError, EOFError, KeyError):
        return 0, 0, "" 

def create_themed_pause_menu(screen, title):
    """Buat themed menu untuk pause dengan gaya yang konsisten, mengikuti ukuran layar saat ini"""
    theme = pygame_menu.themes.THEME_DARK.copy()
    theme.widget_font = FONT_PATH
    theme.title_font = FONT_PATH
    
    # Enhanced title styling
    theme.title_background_color = (20, 20, 30, 220)
    theme.title_font_shadow = True
    theme.title_font_shadow_color = (0, 0, 0)
    theme.title_font_shadow_offset = 3
    theme.title_bar_style = pygame_menu.widgets.MENUBAR_STYLE_SIMPLE
    theme.title_font_size = 45
    theme.title_font_antialias = True
    theme.title_font_color = (255, 230, 150)  # Warm gold color
    
    # Improved widget styling
    theme.widget_font_size = 36
    theme.widget_padding = (10, 15)
    theme.widget_margin = (0, 15)
    
    # Button styling
    theme.widget_font_color = (220, 220, 220)
    theme.selection_color = (255, 215, 0)
    theme.widget_selection_color = (255, 255, 150)
    theme.widget_selection_effect = pygame_menu.widgets.SimpleSelection()
    
    # Menu background styling
    theme.background_color = (20, 20, 30, 200)
    
    # Create decorated borders
    theme.border_width = 2
    theme.border_color = (255, 215, 0)  # Gold border
    
    # Create menu with the enhanced theme using current surface size
    surf = pygame.display.get_surface()
    if surf:
        sw, sh = surf.get_size()
    else:
        sw, sh = WIDTH, HEIGHT
    width = max(300, sw - 100)
    height = max(200, sh - 100)
    
    menu = pygame_menu.Menu(
        title, 
        width,
        height,
        theme=theme,
        onclose=pygame_menu.events.CLOSE,
        center_content=True
    )
    
    return menu

def pause_menu(screen, main_menu_callback=None):
    """Menu pause dengan tema yang diperbarui"""
    from main import sound_manager
    
    # Use responsive pause menu sized to current screen
    menu = create_themed_pause_menu(screen, 'GAME PAUSED')
    
    # Button styling
    button_style = {
        'font_size': 36,
        'background_color': (40, 40, 60),
        'border_width': 2,
        'border_color': (255, 215, 0, 80)
    }
    
    # Inisialisasi hasil
    result = [False]  # False = kembali ke game, True = kembali ke main menu
    
    # Penambahan instruksi
    menu.add.vertical_margin(20)
    menu.add.label('GAME PAUSED', font_size=45, font_color=(255, 215, 0))
    menu.add.vertical_margin(30)
    
    # Tambahkan tombol dengan callback yang tidak segera ditutup
    def resume_game():
        result[0] = False  # Kembali ke game
        menu.disable()
        return
        
    def quit_to_menu():
        result[0] = True  # Kembali ke menu utama
        menu.disable()
        return
    
    menu.add.button('RESUME GAME', resume_game, **button_style)
    menu.add.vertical_margin(15)
    menu.add.button('QUIT TO MAIN MENU', quit_to_menu, **button_style)
    
    # Set sound engine jika sound_manager tersedia
    if sound_manager:
        class PauseMenuSound(pygame_menu.sound.Sound):
            def __init__(self):
                super().__init__()
                
            def play_click_sound(self):
                sound_manager.play_ui_click()
                
            def play_key_add_sound(self):
                sound_manager.play_ui_hover()
                
        menu.set_sound(PauseMenuSound())
    
    # Semi-transparan blur effect untuk background
    # Match overlay to current screen size
    sw, sh = screen.get_size()
    bg_surface = pygame.Surface((sw, sh), pygame.SRCALPHA)
    bg_surface.fill((0, 0, 0, 160))  # Semi-transparent black
    
    # Main loop untuk menu pause
    while menu.is_enabled():
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                return True  # Quit to main menu
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    menu.disable()
                    result[0] = False  # Tombol escape = resume game
        # Draw background overlay
        screen.blit(bg_surface, (0, 0))
        
        # Update dan gambar menu selama masih enabled
        menu.update(events)
        if menu.is_enabled():
            menu.draw(screen)
            
        pygame.display.flip()
    
    # Kembalikan hasil: True untuk keluar ke menu utama, False untuk melanjutkan game
    return result[0]

def highest_score_menu(screen, player, main_menu_callback, replay_callback, sound_manager=None):
    from main import sound_manager as main_sound_manager
    
    # Load current saved data
    saved_money, current_highest_score, player_name = load_game_data()
    
    # Calculate total money and final score
    total_money = saved_money + player.session_money
    final_score = player.level * 100 + player.xp
    
    # Save new highest score if achieved
    if final_score > current_highest_score:
        current_highest_score = final_score
        save_game_data(total_money, current_highest_score, player_name)
    else:
        save_game_data(total_money, current_highest_score, player_name)
    
    # Use themed pause-style menu that adapts to current size
    menu = create_themed_pause_menu(screen, 'GAME OVER')
    
    # Add logo if exists
    import os
    logo_img = pygame.image.load('assets/UI/logo.png').convert_alpha() if os.path.exists('assets/UI/logo.png') else None
    if logo_img:
        logo_img = pygame.transform.scale(logo_img, (300, 100))
        menu.add.image(logo_img, scale=(1, 1), scale_smooth=True)
        menu.add.vertical_margin(20)
    
    # Game Over information dengan container yang sama seperti main menu
    # Perbesar ukuran frame dan tambahkan _relax=True untuk mengatasi overflow
    info_frame = menu.add.frame_v(450, 250, background_color=(0, 0, 0, 120), border_color=(255, 215, 0), border_width=2)
    info_frame._relax = True  # Izinkan konten melebihi ukuran frame
    
    # Game Over title
    info_frame.pack(menu.add.label("GAME OVER", font_size=32, font_color=(255, 100, 100)), align=pygame_menu.locals.ALIGN_CENTER)
    info_frame.pack(menu.add.vertical_margin(8))
    
    # Player stats dengan styling yang konsisten
    if player_name:
        info_frame.pack(menu.add.label(f"PLAYER: {player_name.upper()}", font_size=22, font_color=(255, 215, 0)), align=pygame_menu.locals.ALIGN_CENTER)
    
    info_frame.pack(menu.add.label(f"LEVEL REACHED: {player.level}", font_size=20, font_color=(255, 255, 255)), align=pygame_menu.locals.ALIGN_CENTER)
    info_frame.pack(menu.add.label(f"FINAL SCORE: {final_score}", font_size=20, font_color=(255, 255, 255)), align=pygame_menu.locals.ALIGN_CENTER)
    
    # Highlight new high score
    if final_score > (current_highest_score if final_score != current_highest_score else 0):
        info_frame.pack(menu.add.label("NEW HIGH SCORE!", font_size=18, font_color=(255, 215, 0)), align=pygame_menu.locals.ALIGN_CENTER)
    else:
        info_frame.pack(menu.add.label(f"BEST SCORE: {current_highest_score}", font_size=18, font_color=(200, 200, 200)), align=pygame_menu.locals.ALIGN_CENTER)
    
    info_frame.pack(menu.add.label(f"TOTAL GOLD: {total_money}", font_size=18, font_color=(255, 255, 255)), align=pygame_menu.locals.ALIGN_CENTER)
    
    menu.add.vertical_margin(30)
    
    # Button styling yang konsisten dengan main menu
    button_style = {
        'font_size': 36,
        'background_color': (40, 40, 60),
        'border_width': 2,
        'border_color': (255, 215, 0, 80)
    }
    
    menu.add.button('PLAY AGAIN', replay_callback, **button_style)
    menu.add.vertical_margin(10)
    menu.add.button('MAIN MENU', main_menu_callback, **button_style)
    
    # Set sound engine jika sound_manager tersedia
    if sound_manager:
        class GameOverSoundEngine(pygame_menu.sound.Sound):
            def __init__(self, sound_manager):
                super().__init__()
                self.sound_manager = sound_manager
                
            def play_click_sound(self) -> None:
                self.sound_manager.play_ui_click()
                
            def play_key_add_sound(self) -> None:
                self.sound_manager.play_ui_hover()
        
        menu.set_sound(GameOverSoundEngine(sound_manager))
    
    menu.mainloop(screen)

def save_splitscreen_data(money=0):
    game_data = {
        'money': money,
        'mode': 'splitscreen'
    }
    with open(SAVE_FILE, 'wb') as file:
        pickle.dump(game_data, file)

def splitscreen_game_over(screen, player1, player2, main_menu_callback, replay_callback):
    from main import sound_manager
    
    # Calculate total session money from both players
    total_session_money = player1.session_money + player2.session_money
    
    # Load and update saved money
    saved_money, _, _ = load_game_data()
    total_money = saved_money + total_session_money
    
    # Save updated money
    save_splitscreen_data(total_money)
    
    menu = create_themed_pause_menu(screen, 'Game Over')
    menu.add.label(f'Player 1 Level: {player1.level}')
    menu.add.label(f'Player 2 Level: {player2.level}')
    menu.add.label(f'Session Money: {total_session_money}')
    menu.add.label(f'Total Money: {total_money}')
    menu.add.button('Replay', replay_callback)
    menu.add.button('Main Menu', main_menu_callback)
    menu.mainloop(screen)

def show_victory_screen(screen, score, time_played, sound_manager=None, victory_message="VICTORY!"):
    """Layar kemenangan dengan tema yang diperbarui"""
    # Buat menu dengan tema yang konsisten
    menu = create_themed_pause_menu(screen, 'VICTORY')
    
    # Format waktu bermain
    minutes = int(time_played // 60)
    seconds = int(time_played % 60)
    time_str = f"{minutes:02}:{seconds:02}"
    
    # Konten menu
    menu.add.vertical_margin(20)
    menu.add.label(victory_message, font_size=40, font_color=(255, 215, 0))
    menu.add.vertical_margin(20)
    menu.add.label(f'FINAL SCORE: {score}', font_size=32)
    menu.add.label(f'TIME: {time_str}', font_size=32)
    menu.add.vertical_margin(40)
    
    # Button styling
    button_style = {
        'font_size': 36,
        'background_color': (40, 40, 60),
        'border_width': 2,
        'border_color': (255, 215, 0, 80)
    }
    
    # Ganti fungsi return_to_menu_callback untuk tidak memanggil menu apapun
    # Sebaliknya, cukup disable menu saat ini dan kembalikan nilai True
    # untuk memberi sinyal kembali ke main_menu
    return_signal = [False]  # Gunakan list untuk menyimpan status return
    
    def return_to_menu_callback():
        return_signal[0] = True
        menu.disable()
    
    menu.add.button('RETURN TO MAIN MENU', return_to_menu_callback, **button_style)
    
    # Set sound engine jika sound_manager tersedia
    if sound_manager:
        class SoundEngine(pygame_menu.sound.Sound):
            def __init__(self, sound_manager):
                super().__init__()
                self.sound_manager = sound_manager
                
            def play_click_sound(self) -> None:
                self.sound_manager.play_ui_click()
                
            def play_key_add_sound(self) -> None:
                self.sound_manager.play_ui_hover()
        
        menu.set_sound(SoundEngine(sound_manager))
        
        # Play victory sound
        sound_manager.play_victory_sound()
    
    # Tampilan victory dengan efek partikel dan transisi fade-in
    sw, sh = screen.get_size()
    particles = []
    for _ in range(100):
        particles.append({
            'x': random.randint(0, sw),
            'y': random.randint(0, sh),
            'size': random.randint(2, 6),
            'speed': random.uniform(1, 3),
            'color': (
                random.randint(200, 255),
                random.randint(200, 255),
                random.randint(100, 200)
            ),
            'angle': random.uniform(0, 2 * math.pi)
        })
    
    # Transisi fade-in untuk layar kemenangan
    fade_surface = pygame.Surface((sw, sh))
    fade_surface.fill((0, 0, 0))
    
    # Fade in dari hitam
    for alpha in range(255, 0, -5):
        # Semi-transparan background
        bg_surface = pygame.Surface((sw, sh), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 20, 160))
        screen.blit(bg_surface, (0, 0))
        
        # Update dan gambar partikel
        for p in particles:
            p['y'] -= p['speed']
            if p['y'] < -10:
                p['y'] = sh + 10
                p['x'] = random.randint(0, sw)
            
            pygame.draw.circle(
                screen,
                p['color'],
                (int(p['x']), int(p['y'])),
                p['size']
            )
        
        # Fade effect
        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))
        
        pygame.display.flip()
        pygame.time.delay(10)
    
    # Main menu loop
    menu_running = True
    while menu_running and menu.is_enabled():
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                menu.disable()
                menu_running = False
                return
            
        # Check if return signal was set
        if return_signal[0]:
            break
        
        # Semi-transparan background
        bg_surface = pygame.Surface((sw, sh), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 20, 160))
        screen.blit(bg_surface, (0, 0))
        
        # Update dan gambar partikel
        for p in particles:
            p['y'] -= p['speed']
            if p['y'] < -10:
                p['y'] = sh + 10
                p['x'] = random.randint(0, sw)
            
            pygame.draw.circle(
                screen,
                p['color'],
                (int(p['x']), int(p['y'])),
                p['size']
            )
        
        # Update dan gambar menu
        menu.update(events)
        if menu.is_enabled():
            menu.draw(screen)
        pygame.display.flip()
    
    # Return to main menu
    from main import main_menu
    main_menu()
