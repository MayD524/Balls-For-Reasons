import pygame
import random
import math
import time
import numpy as np
import subprocess
import cv2
import os

# Initialize Pygame
pygame.init()

frame_count = 0

# Constants
VIDEO_FPS = 30
FPS = 30
VIDEO_ENCODER = "mp4v"
TEMP_VIDEO_OUTPUT = "temp.mp4"
VIDEO_OUTPUT = "video.mp4"
VIDEO_TIME = 30 ## seconds
RUN_FOR_FRAMES = VIDEO_FPS * VIDEO_TIME
FUNNY_COOLDOWN = 10  # Number of bounces before the ball is considered funny
WIDTH, HEIGHT = 720, 1280
BALL_RADIUS = 20
BACKGROUND_COLOR = (0, 0, 0)
FLOOR_HEIGHT = HEIGHT-30
BOUNCE_FACTOR = 0.8  # Coefficient of restitution for the ball
GRAVITY = 0.5
TRAIL_LENGTH = 10  # Length of the trail in frames
MAX_VELOCITY = 15  # Maximum velocity for the balls
UPPER_LIMIT = 200 ## -1 is unlimited ballz anything higher will start deleting them

time_left = RUN_FOR_FRAMES


# Define keybindings for actions
keybindings = {
    "increase_velocity": pygame.K_v,
    "clone_ball": pygame.K_c,
    "change_size": pygame.K_s,
    "change_color": pygame.K_p,
    "show_status": pygame.K_k,
}

# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Physics-based Bouncing Ball with Trails")
capture_surface = pygame.Surface((WIDTH, HEIGHT))

# Ball properties
default_ball = {
    "x": WIDTH // 2,
    "y": HEIGHT // 2,
    "speed_x": random.uniform(-10, 10),
    "speed_y": random.uniform(-10, 10),
    "last_speed_x": 0,
    "last_speed_y": 0,
    "color": (200, 200, 200),
    "radius": BALL_RADIUS,
    "trail": [],
    "funny_cooldown": FUNNY_COOLDOWN,
}

balls = [default_ball]  # Start with the default ball

fun_mode = {
    "increase_velocity": True,
    "clone_ball": True,
    "change_size": True,
    "change_color": False,
    "show_status": True,
}

# fun_mode_chances = {
#     "increase_velocity": 0.75,
#     "clone_ball": 0.05,
#     "change_size": 0.05,
#     "change_color": 0.05,
#     "show_status": 1,
# }

fun_mode_chances = {
    "increase_velocity": 1,
    "clone_ball": 1,
    "change_size": 1,
    "change_color": 1,
    "show_status": 1,
}

# Create a single color object for all balls
default_color = (200, 200, 200)

# Function to create a new ball
def create_ball(x, y):
    ball_speed_y = random.uniform(-10, 10)
    ball_speed_x = random.uniform(-10, 10)
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    radius = BALL_RADIUS
    trail = []
    return {"x": x,
            "y": y, 
            "speed_x": ball_speed_x,
            "speed_y": ball_speed_y, 
            "last_speed_x": 0, 
            "last_speed_y": 0, 
            "color": color, 
            "radius": radius, 
            "trail": trail, 
            "funny_cooldown": FUNNY_COOLDOWN
        }

def fun_mode_actions(ball):
    if ball["funny_cooldown"] > 0:
        return
    
    if ball["speed_x"] == ball["last_speed_x"] and round(ball["speed_y"]) == round(ball["last_speed_y"]):
        return ## don't do anything if the ball has not moved
    
    if fun_mode["increase_velocity"] and random.random() < fun_mode_chances["increase_velocity"] / len(balls):
        ball["speed_x"] *= 1.02
        ball["speed_y"] *= 1.02
        
    chance_of_cloning = fun_mode_chances["clone_ball"]
    if len(balls) == UPPER_LIMIT:
        chance_of_cloning = chance_of_cloning / (len(balls) * 3)
        
    if fun_mode["clone_ball"] and random.random() < chance_of_cloning:
        
        new_ball = create_ball(ball["x"], ball["y"])
        balls.append(new_ball)
        if UPPER_LIMIT > 0 and len(balls) > UPPER_LIMIT:
            balls.pop(0)
        
    if fun_mode["change_size"] and random.random() < fun_mode_chances["change_size"]:
        ball["radius"] = random.randint(10, BALL_RADIUS * 2)
        
    if fun_mode["change_color"] and random.random() < fun_mode_chances["change_color"]:
        ball["color"] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    ball["funny_cooldown"] = FUNNY_COOLDOWN
    
# Function to toggle fun mode actions based on keybindings
def toggle_fun_mode_actions():
    for action, key in keybindings.items():
        if keys[key]:
            if action == "toggle_velocity":
                fun_mode["increase_velocity"] = not fun_mode["increase_velocity"]
            elif action == "toggle_clone":
                fun_mode["clone_ball"] = not fun_mode["clone_ball"]
            elif action == "toggle_size":
                fun_mode["change_size"] = not fun_mode["change_size"]
            elif action == "toggle_color":
                fun_mode["change_color"] = not fun_mode["change_color"]
            elif action == "toggle_status":
                fun_mode["show_status"] = not fun_mode["show_status"]
            elif action == "randomize_fun_mode":
                fun_mode["increase_velocity"] = random.choice([True, False])
                fun_mode["clone_ball"] = random.choice([True, False])
                fun_mode["change_size"] = random.choice([True, False])
                fun_mode["change_color"] = random.choice([True, False])

def is_ball_stopped(ball):
    # Check if the ball has stopped (both speed_x and speed_y are very close to 0)
    return abs(ball["speed_x"]) < 0.1 and abs(ball["speed_y"]) < 0.1

def check_ball_collisions(ball, other_ball):
    distance = math.sqrt((ball["x"] - other_ball["x"]) ** 2 + (ball['y'] - other_ball["y"]) ** 2)
        
    if distance < ball["radius"] + other_ball["radius"]:
        angle = math.atan2(other_ball["y"] - ball['y'], other_ball["x"] - ball["x"])
        overlap = (ball["radius"] + other_ball["radius"]) - distance
        ball['speed_x'] -= overlap * math.cos(angle) * 0.5
        ball['speed_y'] -= overlap * math.sin(angle) * 0.5
        other_ball["speed_x"] += overlap * math.cos(angle) * 0.5
        other_ball["speed_y"] += overlap * math.sin(angle) * 0.5
        
        # Apply a coefficient of friction to slow down the balls
        friction = 0.95
        ball['speed_x'] *= friction
        ball['speed_y'] *= friction
        other_ball["speed_x"] *= friction
        other_ball["speed_y"] *= friction
        fun_mode_actions(ball)

# Function to check for collisions and trigger fun mode actions
def check_collisions(ball):
    ball_speed_y = ball["speed_y"] + GRAVITY
    ball_speed_x = ball["speed_x"]
    trail = ball['trail']
    
    new_last_speeds = (ball["speed_x"], ball["speed_y"])
    
    # Ensure the maximum velocity is MAX_VELOCITY
    current_velocity = math.sqrt(ball_speed_x ** 2 + ball_speed_y ** 2)
    max_v = MAX_VELOCITY if not fun_mode["increase_velocity"] else MAX_VELOCITY * 5
    
    if current_velocity > max_v:
        scaling_factor = max_v / current_velocity
        ball_speed_x *= scaling_factor
        ball_speed_y *= scaling_factor

    ball_y = ball["y"] + ball_speed_y
    ball_x = ball["x"] + ball_speed_x

    left_corner_offset = ball["radius"]
    right_corner_offset = WIDTH - ball["radius"]

    # Check collision with the floor
    if ball_y + ball["radius"] > FLOOR_HEIGHT:
        ball_y = FLOOR_HEIGHT - ball["radius"]
        ball_speed_y *= -BOUNCE_FACTOR
        fun_mode_actions(ball)

    # Check collision with the walls
    if ball_x - ball["radius"] < 10 or ball_x + ball["radius"] > WIDTH+10:
        ball_speed_x *= -BOUNCE_FACTOR
        fun_mode_actions(ball)

    # Check collision with other balls
    if len(balls) > 1:
        [
            check_ball_collisions(ball, other_ball) 
            for other_ball in balls 
            if other_ball!= ball
        ]

    # Reset the ball if it's not moving or hits the left or right corners in the specified height range
    if (is_ball_stopped(ball) and ball_y >= FLOOR_HEIGHT-10) or (
        (ball_y >= FLOOR_HEIGHT-20) and
        (ball_x <= left_corner_offset or ball_x >= right_corner_offset)
    ):
        # Set a random starting point within the upper half of the screen
        ball_x = random.uniform(ball["radius"], WIDTH - ball["radius"])
        ball_y = random.uniform(ball["radius"], HEIGHT / 2 - ball["radius"])

        # Calculate a random direction
        direction_angle = random.uniform(0, 2 * math.pi)
        ball_speed_x = math.cos(direction_angle) * random.uniform(2, MAX_VELOCITY)
        ball_speed_y = math.sin(direction_angle) * random.uniform(2, MAX_VELOCITY)

    if (ball_x < 0 or ball_x > WIDTH) or (ball_y > HEIGHT or ball_y < 0):
        # Set a random starting point within the upper half of the screen
        ball_x = random.uniform(ball["radius"], WIDTH - ball["radius"])
        ball_y = random.uniform(ball["radius"], HEIGHT / 2 - ball["radius"])

        # Calculate a random direction
        direction_angle = random.uniform(0, 2 * math.pi)
        ball_speed_x = math.cos(direction_angle) * random.uniform(2, MAX_VELOCITY)
        ball_speed_y = math.sin(direction_angle) * random.uniform(2, MAX_VELOCITY)

    # Add the current position to the shared trail list
    trail.append((ball_x, ball_y))

    # Limit the trail length
    trail_count = TRAIL_LENGTH / (len(balls) / 2)
    trail_count = trail_count if trail_count > 1 else 1
    if len(trail) > trail_count:
        trail.pop(0)

    ball["speed_x"] = ball_speed_x
    ball["speed_y"] = ball_speed_y
    ball["x"] = ball_x
    ball["y"] = ball_y
    ball["last_speed_x"] = new_last_speeds[0]
    ball["last_speed_y"] = new_last_speeds[1]
    ball["funny_cooldown"] -= 1
    if ball["funny_cooldown"] <= 0:
        ball["funny_cooldown"] = 0

# ... (rest of the code)
running = True
clock = pygame.time.Clock()

def display_fun_mode_status():
    font = pygame.font.Font(None, 36)
    status_text = [
        "Velocity: ON" if fun_mode["increase_velocity"] else "Velocity: OFF",
        "Clone Ball: ON" if fun_mode["clone_ball"] else "Clone Ball: OFF",
        "Change Size: ON" if fun_mode["change_size"] else "Change Size: OFF",
        "Change Color: ON" if fun_mode["change_color"] else "Change Color: OFF",
        f"Balls: {len(balls)}",
        f"Clone ball chance: {(fun_mode_chances['clone_ball'] / len(balls)) * 100:.16f}%",
        f"Ball 0 velocity: ({balls[0]['speed_x']}, {balls[0]['speed_y']})",
        f"FPS: {clock.get_fps():.2f}",
        f"Ball 0 can funny: {not (balls[0]['speed_x'] == balls[0]['last_speed_x'] and round(balls[0]['speed_y']) == round(balls[0]['last_speed_y']))}",
        f"Ball 0 funny cooldown: {balls[0]['funny_cooldown']}",
        f"Total frames: {frame_count}",
        f"Frames left: {time_left}",
    ]

    font_height = font.get_linesize()
    y_position = 10

    for line in status_text:
        text_surface = font.render(line, True, (255, 255, 255))
        screen.blit(text_surface, (10, y_position))
        y_position += font_height

def check_keypress(pressed_key):
    for action, key in keybindings.items():
        if pressed_key == key:
            fun_mode[action] = not fun_mode[action]

frames = []

fourcc = cv2.VideoWriter_fourcc(*VIDEO_ENCODER)  # Codec for MP4 format
video = cv2.VideoWriter(TEMP_VIDEO_OUTPUT, fourcc, VIDEO_FPS, (WIDTH, HEIGHT))

start_time = time.time()

def handle_events(event):
    global running
    if event.type == pygame.QUIT:
        running = False
    elif event.type == pygame.KEYDOWN:
        check_keypress(event.key)

while time_left > 0 and running:
    frame_start = time.time()
    keys = pygame.key.get_pressed()
    
    [handle_events(event) for event in pygame.event.get()]

    # Update ball positions and velocities
    [check_collisions(ball) for ball in balls]

    # Clear the screen
    screen.fill(BACKGROUND_COLOR)

    # Draw the floor
    pygame.draw.rect(screen, (0, 255, 0), (0, FLOOR_HEIGHT, WIDTH, HEIGHT - FLOOR_HEIGHT))

    # Draw the trails and balls
    for ball in balls:
        if len(ball["trail"]) > 1: 
            for i, (x, y) in enumerate(ball['trail']):
                trail_color = tuple(int(c * (1 - i / TRAIL_LENGTH)) for c in default_color)
                pygame.draw.circle(screen, ball['color'], (int(x), int(y)), ball["radius"] + i)
        pygame.draw.circle(screen, ball["color"], (int(ball["x"]), int(ball["y"])), ball["radius"])

    # Display fun mode status in the top-left corner
    if fun_mode["show_status"]:
        display_fun_mode_status()

    ## save the frame for later
    pygame.image.save(screen, f"frames/frame_{frame_count}.png")
    
    ## read the frame data
    
    frame_count += 1
    time_left -= 1
    
    if fun_mode["increase_velocity"] and clock.get_fps() > FPS/2:
        fun_mode["increase_velocity"] = False
    
    # Update the display
    pygame.display.flip()
    # Limit the frame rate
    clock.tick(FPS)


pygame.quit()

print(f"Total time: {time.time() - start_time:.10f} seconds")
print("Simulation complete.")

def order_videos_by_frame_number():
    frames = os.listdir("frames")
    frames.sort(key=lambda x: int(x.split(".")[0].split("_")[-1]))
    return frames

print("Ordering video frames...")
frames = order_videos_by_frame_number()

print("Converting video frames to MP4...")
start_time = time.time()
for frame in frames:
    fm = cv2.imread(f"frames/{frame}")
    video.write(fm)
print(f"Conversion complete in {time.time() - start_time:.2f} seconds")

cv2.destroyAllWindows()
video.release()

print("Converting video to MP4...")
subprocess.call(args=["ffmpeg", "-y", "-i", TEMP_VIDEO_OUTPUT, "-c:v", "libx264", VIDEO_OUTPUT])

frames = os.listdir("frames")
for frame in frames:
    # delete the file
    os.remove(f"frames/{frame}")