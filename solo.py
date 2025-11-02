import pygame
import random
import math
import os
from settings import *
from player import Player, Camera
from enemy import Enemy
from projectile import Projectile
from experience import Experience, LevelUpEffect
from utils import pause_menu, highest_score_menu, load_game_data, save_game_data, show_victory_screen
from maps import Map
from ui import HealthBar, MoneyDisplay, XPBar, InteractionButton, render_text_with_border, SkillBar
from settings import load_font
from particles import ParticleSystem
from partner import Partner
from hit_effects import RockHitEffect
from devil import Devil
from ui import MiniMap
from gollux_boss import Gollux
from bi_enemy import BiEnemy
from bi_projectile import BiProjectile
from skill import update_sound_manager

def create_blur_surface(surface):
    scale = 0.25
    small_surface = pygame.transform.scale(surface, 
        (int(surface.get_width() * scale), int(surface.get_height() * scale)))
    return pygame.transform.scale(small_surface, 
        (surface.get_width(), surface.get_height()))

def main(screen, clock, sound_manager, main_menu_callback):
    map_path = os.path.join("assets", "maps", "desert", "plain.png")
    map_type = "desert"  # Default to desert map
    
    try:
        game_map = Map(map_path)
    except Exception as e:
        print(f"Error loading map: {e}")
        return

    # Play desert music
    sound_manager.play_gameplay_music(map_type)
    
    camera = Camera(game_map.width, game_map.height)

    all_sprites = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    projectiles = pygame.sprite.Group()
    experiences = pygame.sprite.Group()
    effects = pygame.sprite.Group()  
    bi_enemies = pygame.sprite.Group()
    bi_projectiles = pygame.sprite.Group()

    player = Player()
    player.game_map = game_map
    player.sound_manager = sound_manager
    
    partner = Partner(player, sound_manager)  # Pastikan sound_manager diteruskan
    all_sprites.add(player)
    all_sprites.add(partner)
    
    player.world_bounds = pygame.Rect(
        0,
        0,
        game_map.width,
        game_map.height
    )
    
    player.rect.center = (game_map.width // 2, game_map.height // 2)
    all_sprites.add(player)

    MAX_PROJECTILES = 20
    projectile_pool = []
    for _ in range(MAX_PROJECTILES):
        projectile = Projectile((0,0), (0,0))
        projectile_pool.append(projectile)
        all_sprites.add(projectile)
        projectiles.add(projectile)
        projectile.kill()

    running = True
    paused = False
    enemy_spawn_timer = 0
    projectile_timer = 0
    font = load_font(36)
    
    # Initialize UI elements - specify "solo" mode for skill bar
    sw, sh = screen.get_size()
    health_bar = HealthBar()
    money_display = MoneyDisplay()
    xp_bar = XPBar(sw, sh)
    skill_bar = SkillBar(player_id=1, mode="solo")  # Using solo mode with 3 skills
    skill_bar.player = player  # Add player reference
    interaction_button = InteractionButton()
    mini_map = MiniMap(game_map.width, game_map.height, sw, sh)
    
    # Create a new sprite group for skill effects
    skill_effects = pygame.sprite.Group()

    death_transition = False
    death_alpha = 0
    blur_surface = None
    FADE_SPEED = 15  
    TRANSITION_DELAY = 5  
    transition_timer = 0
    
    particle_system = ParticleSystem(WIDTH, HEIGHT)
    
    for _ in range(25):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        particle_system.create_particle(x, y)
    
    particle_spawn_timer = 0
    PARTICLE_SPAWN_RATE = 3
    PARTICLES_PER_SPAWN = 2
    
    session_start_ticks = pygame.time.get_ticks()  # Simpan waktu mulai session
    pause_ticks = 0
    pause_start = None

    cheat_pause_ticks = 0      
    cheat_pause_start = None   

    cheat_mode = False
    cheat_input = ""
    cheat_message = ""
    original_max_health = None
    original_health = None

    devil = None
    devil_spawn_times = [2*60*1000]  # ms, menit ke-2
    next_devil_time = devil_spawn_times[0]
    devil_notif_timer = 0
    devil_notif_show = False

    # Add interaction button and shop
    from ui import DevilShop
    devil_shop = DevilShop(sound_manager)
    
    # Add boss initialization
    boss = None
    boss_spawn_time = 5*60*1000  # 5 minutes
    boss_spawned = False
    boss_defeated = False
    
    show_boss_warning = False
    boss_warning_timer = 0
    
    game_time_seconds = 0
    bi_spawn_timer = 0
    last_second = 0
    
    # Update sound manager for skills
    update_sound_manager(sound_manager)
    
    # Add a variable to track if enemy spawns should be blocked
    nuke_blocking_spawns = False

    while running:
        dt = clock.tick(FPS) / 1000.0
        
        # Update skill cooldowns
        skill_bar.update(dt)
        
        # Collect events before processing to pass to shop
        current_events = []
        for event in pygame.event.get():
            current_events.append(event)
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Handle skill activation with three separate keys
                if event.key == pygame.K_1:
                    skill = skill_bar.activate_skill(0)
                    if skill:
                        if skill.name == "Heal":
                            effect = skill.activate(player, enemies=enemies)
                        elif skill.name == "Nuke":
                            effect = skill.activate(player, enemies=enemies)
                        else:
                            effect = skill.activate(player.rect.center, enemies=enemies)
                        if effect:
                            all_sprites.add(effect)
                            skill_effects.add(effect)
                elif event.key == pygame.K_2:
                    skill = skill_bar.activate_skill(1)
                    if skill:
                        if skill.name == "Heal":
                            effect = skill.activate(player, enemies=enemies)
                        else:
                            effect = skill.activate(player.rect.center, enemies=enemies)
                        if effect:
                            all_sprites.add(effect)
                            skill_effects.add(effect)
                elif event.key == pygame.K_3:
                    skill = skill_bar.activate_skill(2)
                    if skill:
                        if skill.name == "Heal":
                            effect = skill.activate(player, enemies=enemies)
                        else:
                            effect = skill.activate(player.rect.center, enemies=enemies)
                        if effect:
                            all_sprites.add(effect)
                            skill_effects.add(effect)
                if event.key == pygame.K_ESCAPE:
                    if devil_shop.is_open:
                        devil_shop.close()
                    else:
                        paused = True
                        pause_start = pygame.time.get_ticks()  # MULAI PAUSE
                        quit_to_menu = pause_menu(screen, main_menu_callback)
                        if quit_to_menu:
                            return  # Keluar dari fungsi main dan kembali ke main_menu
                        paused = False
                        if pause_start is not None:
                            pause_ticks += pygame.time.get_ticks() - pause_start  # TAMBAHKAN DURASI PAUSE
                            pause_start = None
                # Add cheat console toggle
                elif event.key == pygame.K_BACKQUOTE:
                    cheat_mode = not cheat_mode
                    if cheat_mode:
                        cheat_pause_start = pygame.time.get_ticks()
                    else:
                        if cheat_pause_start is not None:
                            cheat_pause_ticks += pygame.time.get_ticks() - cheat_pause_start
                            cheat_pause_start = None
                    cheat_input = ""
                    cheat_message = ""
                # Add E key to open shop when interaction is possible
                elif event.key == pygame.K_e:
                    if devil and devil.can_interact():
                        devil_shop.open()

        if devil_shop.is_open:
            devil_shop.update(current_events)
            # When shop is open, pass player and partner to purchase function
            if devil_shop.is_open and interaction_button.is_visible and interaction_button.target_entity == player:
                # If player presses enter or space, try to purchase the selected item
                keys = pygame.key.get_pressed()
                if keys[pygame.K_RETURN] or keys[pygame.K_SPACE]:
                    devil_shop.purchase_item(player, partner)
            # Skip regular game updates while shop is open
            devil_shop.draw(screen)
            pygame.display.flip()
            continue

        if paused:
            continue

        # Cheat input handling
        if cheat_mode:
            # Draw semi-transparent overlay (benar-benar transparan, game tetap terlihat)
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
                            player.session_money += 10000
                            cheat_message = "Money +10000!"
                        elif cheat_input == "armordaribapak":
                            if original_max_health is None:
                                original_max_health = player.max_health
                                original_health = player.health
                            player.max_health = 1000
                            player.health = 1000
                            cheat_message = "Armor dari bapak aktif!"
                        elif cheat_input == "rakyatbiasa":
                            if original_max_health is not None:
                                player.max_health = original_max_health
                                player.health = original_health
                                original_max_health = None
                                original_health = None
                            cheat_message = "Cheat dinonaktifkan!"
                        elif cheat_input == "timeheist":
                            session_start_ticks -= 230 * 1000
                            cheat_message = "Waktu dipercepat +3:50!"
                        elif cheat_input == "dealwiththedevil":
                            if devil is None:
                                devil = Devil(game_map.width, game_map.height)
                                all_sprites.add(devil)
                                cheat_message = "Devil muncul!"
                            else:
                                cheat_message = "Devil sudah ada!"
                        elif cheat_input == "highdamage":
                            for projectile in projectile_pool:
                                if projectile.alive():
                                    projectile.damage = 1000
                            cheat_message = "Damage tinggi!"
                        elif cheat_input == "spawnboss":
                            if not boss_spawned:
                                boss = Gollux(game_map.width, game_map.height, player.rect.center)
                                boss.sound_manager = sound_manager  # Set sound manager reference
                                all_sprites.add(boss)
                                boss_spawned = True
                                cheat_message = "Boss Gollux muncul!"
                            else:
                                cheat_message = "Boss sudah ada!"
                        else:
                            cheat_message = "Command tidak dikenal."
                        cheat_input = ""
                    elif event.key == pygame.K_BACKSPACE:
                        cheat_input = cheat_input[:-1]
                    elif event.key >= 32 and event.key <= 126:  # Printable ASCII characters
                        cheat_input += event.unicode
            
            # Continue to next frame, skipping regular game updates
            continue

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
                enemy = Enemy((player.rect.centerx, player.rect.centery))
                all_sprites.add(enemy)
                enemies.add(enemy)
                enemy_spawn_timer = 0

        projectile_timer += 1
        # Ubah kondisi menjadi memeriksa boss atau enemies
        if projectile_timer >= 30 and (len(enemies) > 0 or (boss is not None and not boss.is_defeated)):
            closest_enemy = None
            min_dist = float('inf')
            
            shoot_radius = 500
            # First check if boss exists and target it with priority
            if boss and not boss.is_defeated:
                dist = math.hypot(boss.rect.centerx - player.rect.centerx,
                                 boss.rect.centery - player.rect.centery)
                if dist < shoot_radius:
                    closest_enemy = boss
                    min_dist = dist
            # Jika tidak ada boss atau boss terlalu jauh, coba target musuh biasa
            if closest_enemy is None:
                for enemy in enemies:
                    if enemy.is_dying:
                        continue
                        
                    dist = math.hypot(enemy.rect.centerx - player.rect.centerx,
                                    enemy.rect.centery - player.rect.centery)
                    if dist < min_dist and dist < shoot_radius:
                        min_dist = dist
                        closest_enemy = enemy

            if closest_enemy:
                for projectile in projectile_pool:
                    if not projectile.alive():
                        start_pos = partner.get_shooting_position()
                        target_pos = (closest_enemy.rect.centerx, closest_enemy.rect.centery)
                        
                        partner.shoot_at(target_pos)  # This will now play the sound
                        
                        # Get projectile type based on partner type
                        projectile_type = partner.get_projectile_type()
                        
                        projectile.reset(start_pos, target_pos, projectile_type)
                        projectile.add(all_sprites, projectiles)
                        projectile_timer = 0
                        break
            else:
                partner.stop_shooting()

        player.update(dt)
        partner.update(dt)

        for enemy in enemies:
            target, damage = enemy.update(player, enemies)
            
            # Jika enemy memberikan damage
            if target and damage > 0:
                player.health -= damage
                if player.health <= 0:
                    player.start_death_animation()
                    # Track that the death animation has started
                    player.is_dying = True

        # Check if player is dying and death animation is complete
        if player.is_dying:
            animation_finished = player.update_death_animation(dt)
            
            if animation_finished or player.death_animation_complete:
                # Transition to game over
                if not death_transition:  # Only trigger once
                    death_transition = True
                    blur_surface = create_blur_surface(screen.copy())

        # Di loop utama game
        projectiles.update()
        experiences.update()
        effects.update(dt)

        # Check for projectiles hitting enemies
        hits = pygame.sprite.groupcollide(projectiles, enemies, True, False)
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
                    # Cek apakah enemy dibunuh devil
                    if not getattr(enemy, "killed_by_devil", False):
                        exp = Experience(enemy.rect.centerx, enemy.rect.centery)
                        all_sprites.add(exp)
                        experiences.add(exp)
                        # Tambah uang ke player (solo)
                        player.session_money += 5

        # Check for projectiles hitting boss - pastikan ini dijalankan SETELAH projectiles.update()
        if boss and not boss.is_defeated:
            hits = pygame.sprite.spritecollide(boss, projectiles, True)
            for projectile in hits:
                # Add hit effect
                hit_effect = RockHitEffect((boss.rect.centerx, boss.rect.centery))
                all_sprites.add(hit_effect)
                effects.add(hit_effect)
                
                # Deal damage to boss
                boss_defeated = boss.take_hit(projectile.damage)
                
                # If boss is defeated, trigger victory
                if boss_defeated:
                    show_victory_screen(screen, player.session_money, elapsed_seconds, sound_manager,
                                        "You've defeated Gollux! The world is saved!")
                    return

        # Update Bi enemies and handle their projectiles
        for bi in bi_enemies:
            target, damage = bi.update(player, enemies)
            
            # If Bi needs to create a projectile
            if target and damage > 0:
                # Create a new sting projectile
                start_pos = bi.rect.center
                target_pos = target.rect.center
                
                sting = BiProjectile(start_pos, target_pos, bi.sting_image)
                all_sprites.add(sting)
                bi_projectiles.add(sting)

        # Update Bi projectiles
        bi_projectiles.update()

        # Check for Bi projectiles hitting player
        if player.health > 0:
            hits = pygame.sprite.spritecollide(player, bi_projectiles, True)
            for projectile in hits:
                player.health -= projectile.damage
                # Optional: Add hit effect here
                
                if player.health <= 0:
                    player.start_death_animation()
                    # Track that the death animation has started
                    player.is_dying = True

        if death_transition:
            animation_finished = player.update_death_animation(dt)
            
            screen.blit(blur_surface, (0, 0))
            screen.blit(player.image, camera.apply(player))
            
            fade_surface = pygame.Surface((sw, sh))
            fade_surface.fill((0, 0, 0))
            
            if animation_finished:
                death_alpha = min(death_alpha + FADE_SPEED, 255)
                
                if death_alpha >= 255:
                    transition_timer += 1
                    if transition_timer >= TRANSITION_DELAY:
                        # Stop the gameplay music before going to score menu
                        sound_manager.stop_gameplay_music()
                        highest_score_menu(screen, player, main_menu_callback, lambda: main(screen, clock, sound_manager, main_menu_callback))
                        return
            
            fade_surface.set_alpha(death_alpha)
            screen.blit(fade_surface, (0, 0))
            
        else:
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

            if not player.is_dying and player.health > 0:
                camera.update(player)

            game_map.draw(screen, camera)

            particle_spawn_timer += 1
            if particle_spawn_timer >= PARTICLE_SPAWN_RATE:
                for _ in range(PARTICLES_PER_SPAWN):
                    x = random.randint(0, WIDTH)
                    y = random.randint(0, HEIGHT)
                    particle_system.create_particle(x, y)
                particle_spawn_timer = 0
                
            particle_system.update(camera.x, camera.y)
            
            game_map.draw(screen, camera)
            
            particle_system.draw(screen, camera)
            
            # First draw the regular sprites with camera offset
            for sprite in all_sprites:
                if not hasattr(sprite, 'is_fullscreen_effect'):
                    if hasattr(sprite, 'draw'):
                        sprite.draw(screen, (camera.x, camera.y))
                    else:
                        screen.blit(sprite.image, (sprite.rect.x + camera.x, sprite.rect.y + camera.y))

            # Then draw fullscreen effects directly on screen
            for sprite in all_sprites:
                if hasattr(sprite, 'is_fullscreen_effect') and sprite.is_fullscreen_effect:
                    if hasattr(sprite, 'draw'):
                        sprite.draw(screen)

            health_bar.draw(screen, player.health, player.max_health)
            
            money_display.draw(screen, player.session_money)
            
            xp_bar.draw(screen, player.xp, player.max_xp, player.level)
            skill_bar.draw(screen)  # Draw the 3-slot skill bar
        
        # --- SESSION TIMER ---
        elapsed_ms = pygame.time.get_ticks() - session_start_ticks - cheat_pause_ticks - pause_ticks
        elapsed_seconds = elapsed_ms // 1000
        minutes = elapsed_seconds // 60
        seconds = elapsed_seconds % 60
        timer_text = f"{minutes:02d}:{seconds:02d}"

        timer_font = load_font(48)
        timer_surface = render_text_with_border(timer_font, timer_text, WHITE, BLACK)
        timer_rect = timer_surface.get_rect(center=(sw // 2, 40))
        screen.blit(timer_surface, timer_rect)
        # --- END SESSION TIMER ---

        # Track game time
        current_second = pygame.time.get_ticks() // 1000
        if current_second > last_second:
            game_time_seconds = current_second
            last_second = current_second

        # Spawn Bi enemies after 1 minute with a slower spawn rate
        if game_time_seconds >=60:  # Only spawn Bi after 1 minute
            bi_spawn_timer += 1
            if bi_spawn_timer >= 200 and len(bi_enemies) < 3:  # Slower spawn rate, max 3 Bi enemies
                bi_enemy = BiEnemy((player.rect.centerx, player.rect.centery))
                all_sprites.add(bi_enemy)
                enemies.add(bi_enemy)  # Add to regular enemies group for collisions
                bi_enemies.add(bi_enemy)  # Also add to bi_enemies group for specialized updates
                bi_spawn_timer = 0

        now = pygame.time.get_ticks()
        if devil is None and now >= next_devil_time:
            devil = Devil(game_map.width, game_map.height)
            all_sprites.add(devil)
            devil_notif_timer = now
            devil_notif_show = True
            # Jadwalkan spawn berikutnya
            if len(devil_spawn_times) == 1:
                devil_spawn_times.append(next_devil_time + 2*60*1000)
            else:
                devil_spawn_times.append(devil_spawn_times[-1] + 2*60*1000)
            next_devil_time = devil_spawn_times[-1]

        if devil:
            devil.update(dt, player.rect, enemies)
            
            # Only show interaction button if devil is active (not fading out or despawning)
            if not getattr(devil, "fading_out", False) and not getattr(devil, "despawning", False):
                # Check if player is in range for interaction
                dx = devil.rect.centerx - player.rect.centerx
                dy = devil.rect.centery - player.rect.centery
                distance = math.hypot(dx, dy)
                
                # Show interaction button when player is in range
                if distance <= devil.damage_circle_radius and devil.is_shop_enabled:
                    interaction_button.show(player)
                else:
                    interaction_button.hide()
                
                # Draw devil indicator when far away
                if distance > 300:
                    angle = math.atan2(dy, dx)
                    arrow_x = sw//2 + math.cos(angle)*180
                    arrow_y = sh//2 + math.sin(angle)*180
                    pygame.draw.polygon(screen, (255,0,0), [
                        (arrow_x, arrow_y),
                        (arrow_x - 10*math.sin(angle), arrow_y + 10*math.cos(angle)),
                        (arrow_x + 10*math.sin(angle), arrow_y - 10*math.cos(angle)),
                    ])
            else:
                # Hide button if devil is fading out or despawning
                interaction_button.hide()
            
            # Draw the devil in layers to ensure proper ordering
            devil.draw_damage_circle(screen, (camera.x, camera.y))
            devil.draw_shadow(screen, (camera.x, camera.y))
            devil.draw_character(screen, (camera.x, camera.y))
        
        # Notif
        if devil_notif_show and pygame.time.get_ticks() - devil_notif_timer < 2500:
            notif_font = load_font(36)
            notif = notif_font.render("The Devil want to speak with you!", True, (255,50,50))
            notif_rect = notif.get_rect(center=(sw//2, sh//2-120))
            screen.blit(notif, notif_rect)
        else:
            devil_notif_show = False

        # Draw UI elements
        health_bar.draw(screen, player.health, player.max_health)
        money_display.draw(screen, player.session_money)
        xp_bar.draw(screen, player.xp, player.max_xp, player.level)
        mini_map.draw(screen, player, None, enemies, devil, boss)
        skill_bar.draw(screen)  # Draw the 3-slot skill bar
        
        # Draw timer
        screen.blit(timer_surface, timer_rect)

        # Draw interaction button after drawing player (should be on top)
        interaction_button.draw(screen, (camera.x, camera.y))
        
        # Check for boss spawn
        elapsed_ms = pygame.time.get_ticks() - session_start_ticks - cheat_pause_ticks - pause_ticks
        if not boss_spawned and elapsed_ms >= boss_spawn_time:
            boss = Gollux(game_map.width, game_map.height, player.rect.center)
            boss.sound_manager = sound_manager  # Set sound manager reference
            all_sprites.add(boss)  # Tambahkan ke all_sprites
            boss_spawned = True

            # Show boss warning
            boss_warning_timer = pygame.time.get_ticks()
            show_boss_warning = True
        
        # Update boss if spawned
        if boss and not boss_defeated:
            target, damage = boss.update(dt, player)
            if target and damage > 0:
                player.health -= damage
                if player.health <= 0:
                    player.start_death_animation()
                    death_transition = True
                    blur_surface = create_blur_surface(screen.copy())
        
        # Add near where you handle other warnings/notifications
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

        # Update skill effects
        skill_effects.update(dt, enemies)  # Update skill effects and pass enemies for damage

        pygame.display.flip()

    return

# Contoh di solo.py atau coop.py
def handle_pause(screen):
    """Helper to invoke pause menu; returns True if should quit to main menu."""
    quit_to_menu = pause_menu(screen)
    if quit_to_menu:
        return True
    return False
