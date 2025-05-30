import pygame
from settings import WIDTH, HEIGHT, BLUE
from utils import load_game_data
from player_animations import PlayerAnimations

class Player2(pygame.sprite.Sprite):  # Kelas Player2 mewarisi Sprite dari pygame
    def __init__(self):
        super().__init__()
        self.animations = PlayerAnimations()  # Objek untuk animasi player
        self.player_id = 2  # ID khusus untuk Player2

        self.image = self.animations.animations['idle_down'][0]  # Gambar awal (diam menghadap bawah)
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2 + 100, HEIGHT // 2)  # Posisi awal, sedikit ke kanan dari Player1

        self.speed = 5  # Kecepatan gerak
        self.max_health = 100  # HP maksimum
        self.health = self.max_health  # HP awal
        self.session_money = 0  # Uang sementara per sesi
        self.xp = 0  # XP awal
        self.max_xp = 100  # XP maksimum sebelum naik level
        self.level = 1  # Level awal

        self.facing = 'idle_down'  # Arah menghadap saat idle
        self.is_moving = False  # Status pergerakan
        self.last_direction = 'down'  # Arah terakhir bergerak

        self.is_dying = False  # Status kematian
        self.death_frame = 0  # Frame animasi kematian
        self.death_animation_speed = 0.1  # Kecepatan animasi mati
        self.death_timer = 0  # Timer untuk animasi mati
        self.was_moving = False  # Apakah sebelumnya bergerak
        self.step_timer = 0  # Timer langkah
        self.step_delay = 300  # Jeda antara langkah kaki (ms)
        self.last_step_time = 0  # Waktu terakhir suara langkah dimainkan

    def get_movement_direction(self, dx, dy):  # Menentukan arah gerak berdasarkan input
        if dx > 0:
            if dy > 0:
                self.last_direction = 'down_right'
                return 'walk_down_right'
            elif dy < 0:
                self.last_direction = 'up_right'
                return 'walk_up_right'
            else:
                self.last_direction = 'right'
                return 'walk_right'
        elif dx < 0:
            if dy > 0:
                self.last_direction = 'down_left'
                return 'walk_down_left'
            elif dy < 0:
                self.last_direction = 'up_left'
                return 'walk_up_left'
            else:
                self.last_direction = 'left'
                return 'walk_left'
        elif dy > 0:
            self.last_direction = 'down'
            return 'walk_down'
        elif dy < 0:
            self.last_direction = 'up'
            return 'walk_up'
        
        return self.get_idle_direction()  # Jika tidak bergerak, arah idle

    def get_idle_direction(self):
        return f'idle_{self.last_direction}'  # Mengembalikan animasi idle sesuai arah terakhir

    def start_death_animation(self):  # Memulai animasi mati
        self.is_dying = True
        self.death_frame = 0
        self.death_timer = 0
        self.death_animation_complete = False  # Reset flag
        
        # Play death sound
        if hasattr(self, 'sound_manager') and self.sound_manager:
            self.sound_manager.play_player_death()

    def update_death_animation(self, dt):  # Proses animasi mati per frame
        if not self.is_dying:
            return False

        # Only process if the animation isn't already complete
        if not self.death_animation_complete:  
            self.death_timer += dt
            if self.death_timer >= self.death_animation_speed:
                self.death_timer = 0
                self.death_frame += 1
                if self.death_frame < len(self.animations.animations['death']):
                    self.image = self.animations.animations['death'][self.death_frame]
                else:
                    # Set the flag when animation completes
                    self.death_animation_complete = True
                    # Keep the last frame visible
                    self.death_frame = len(self.animations.animations['death']) - 1
                    self.image = self.animations.animations['death'][self.death_frame]
                    return True
    
        # Return True if animation has completed, False otherwise
        return self.death_animation_complete

    def animate(self, dt):  # Mengatur animasi gerakan atau idle
        if self.is_dying:
            return self.update_death_animation(dt)

        self.animations.animation_timer += dt

        if not self.is_moving:
            current_anim = self.get_idle_direction()
        else:
            current_anim = self.facing

        if self.animations.animation_timer >= self.animations.animation_speed:
            self.animations.animation_timer = 0
            self.animations.frame_index = (self.animations.frame_index + 1) % len(self.animations.animations[current_anim])
            self.image = self.animations.animations[current_anim][self.animations.frame_index]

    def play_footstep(self):  # Mainkan suara langkah jika waktunya sesuai
        current_time = pygame.time.get_ticks()
        if current_time - self.last_step_time >= self.step_delay:
            self.sound_manager.play_random_footstep()
            self.last_step_time = current_time

    def update(self, dt):  # Fungsi utama update tiap frame
        if self.is_dying:
            return  # Jika mati, tidak bisa update gerakan

        old_x = self.rect.x
        old_y = self.rect.y

        dx = 0
        dy = 0
        keys = pygame.key.get_pressed()

        # Kontrol arah untuk Player 2 (tombol panah)
        if keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_RIGHT]:
            dx += 1
        if keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_DOWN]:
            dy += 1

        # Normalisasi diagonal agar tidak lebih cepat
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        self.is_moving = dx != 0 or dy != 0  # Update status gerak

        if self.is_moving:
            self.play_footstep()

        self.was_moving = self.is_moving

        if self.is_moving:
            self.facing = self.get_movement_direction(dx, dy)

        # Hitung kecepatan berdasarkan delta time (frame-independent movement)
        frame_speed = self.speed * dt * 60

        # Pergerakan horizontal + cek tabrakan dengan pagar atau pohon
        self.rect.x += dx * frame_speed
        if hasattr(self, 'game_map') and (
            any(self.rect.colliderect(fence) for fence in self.game_map.fence_rects) or
            any(self.rect.colliderect(tree) for tree in self.game_map.tree_collision_rects)):
            self.rect.x = old_x  # Kembalikan jika tabrakan

        # Pergerakan vertikal + cek tabrakan
        self.rect.y += dy * frame_speed
        if hasattr(self, 'game_map') and (
            any(self.rect.colliderect(fence) for fence in self.game_map.fence_rects) or
            any(self.rect.colliderect(tree) for tree in self.game_map.tree_collision_rects)):
            self.rect.y = old_y  # Kembalikan jika tabrakan

        self.animate(dt)  # Jalankan animasi sesuai arah/status
