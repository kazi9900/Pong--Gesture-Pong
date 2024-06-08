import cv2
import numpy as np
import threading
#import speech_recognition as sr
from HandDetectionModule import MediapipeLandmark

# Parameters
WIDTH = 1280
HEIGHT = 720
PADDLE_WIDTH = 20
PADDLE_HEIGHT = 150
PADDLE_COLOR = (75, 153, 242)
LIVES_INIT = 3
DELTAX_INIT = -10
DELTAY_INIT = 10
BALL_RADIUS = 8
BACKGROUND_COLOR = (30, 79, 24)
SCORE_COLOR = (149, 129, 252)
GAME_OVER_BACKGROUND_COLOR = (2, 1, 0)  # Black background for game over
GAME_OVER_TEXT_COLOR = (250, 1, 2)  # Red color for game over text

# Game state variables
xpos, ypos = WIDTH // 2, HEIGHT // 2
deltax, deltay = DELTAX_INIT, DELTAY_INIT
level = 1
ball = True
highscore = 0
lives = LIVES_INIT
myscore = 0

# Load background image
background_img = cv2.imread("C:\\Users\\Kazi\\Downloads\\Pong-Game-master\\Pong-Game-master\\background.png")
background_img = cv2.resize(background_img, (WIDTH, HEIGHT))

# Initialize camera
camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
camera.set(cv2.CAP_PROP_FPS, 30)
camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cv2.namedWindow('Classic Pong Game', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('Classic Pong Game', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

prev_val = HEIGHT // 2
hand_data = MediapipeLandmark(1)

# Initialize paddle positions
paddle_top_left = HEIGHT // 2 - PADDLE_HEIGHT // 2
paddle_bottom_left = HEIGHT // 2 + PADDLE_HEIGHT // 2

# Function to recognize speech
def recognize_speech():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        print("Listening for command...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        command = recognizer.recognize_google(audio).lower()
        print(f"Command received: {command}")
        return command
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
    return None

# Function to handle voice commands
def handle_voice_commands(command):
    global deltax, deltay, xpos, ypos, ball, lives, myscore, highscore, level

    if command == "start":
        ball = True
    elif command == "pause":
        ball = False
    elif command == "restart":
        xpos, ypos = WIDTH // 2, HEIGHT // 2
        deltax, deltay = DELTAX_INIT, DELTAY_INIT
        level, myscore, lives = 1, 0, LIVES_INIT
    elif command == "quit":
        return True
    return False

# Function to listen for voice commands in a separate thread
def voice_command_listener():
    while True:
        command = recognize_speech()
        if command and handle_voice_commands(command):
            break

# Start the voice command listener thread
voice_thread = threading.Thread(target=voice_command_listener)
voice_thread.start()

# Function to smooth hand movement
def smooth_hand_movement(current_val, prev_val, alpha=0.2):
    return int(alpha * current_val + (1 - alpha) * prev_val)

# Main game loop
while True:
    _, frame = camera.read()
    hand_val = hand_data.Coordinates(frame)
    background = background_img.copy()

    # Draw the right paddle (controlled by hand gestures)
    if hand_val == 0:
        hand_val = prev_val
    else:
        hand_val = smooth_hand_movement(hand_val, prev_val)
        prev_val = hand_val

    paddle_top_right = hand_val - PADDLE_HEIGHT // 2
    paddle_bottom_right = hand_val + PADDLE_HEIGHT // 2
    paddle_top_right = max(0, min(paddle_top_right, HEIGHT - PADDLE_HEIGHT))
    paddle_bottom_right = paddle_top_right + PADDLE_HEIGHT

    cv2.rectangle(background, (WIDTH - PADDLE_WIDTH, paddle_top_right), (WIDTH, paddle_bottom_right), PADDLE_COLOR, -1)

    # Draw the left paddle (controlled by AI)
    if ypos < paddle_top_left + PADDLE_HEIGHT // 2:
        paddle_top_left -= 10
        paddle_bottom_left -= 10
    elif ypos > paddle_bottom_left - PADDLE_HEIGHT // 2:
        paddle_top_left += 10
        paddle_bottom_left += 10

    # Ensure the AI paddle stays within bounds
    paddle_top_left = max(0, min(paddle_top_left, HEIGHT - PADDLE_HEIGHT))
    paddle_bottom_left = paddle_top_left + PADDLE_HEIGHT

    cv2.rectangle(background, (0, paddle_top_left), (PADDLE_WIDTH, paddle_bottom_left), PADDLE_COLOR, -1)

    # Draw the ball
    if ball:
        cv2.circle(background, (xpos, ypos), BALL_RADIUS, (255, 255, 255), -1)
        xpos += deltax
        ypos += deltay

    # Check for collisions with top and bottom walls
    if ypos >= HEIGHT - BALL_RADIUS or ypos <= BALL_RADIUS:
        deltay = -deltay

    # Check for collisions with paddles
    if (paddle_top_right <= ypos <= paddle_bottom_right and xpos >= WIDTH - PADDLE_WIDTH - BALL_RADIUS) or \
       (paddle_top_left <= ypos <= paddle_bottom_left and xpos <= PADDLE_WIDTH + BALL_RADIUS):
        deltax = -deltax
        myscore += 1
        if myscore % 5 == 0 and myscore >= 5:
            level += 1
            deltax += 2 if deltax > 0 else -2
            deltay += 1 if deltay > 0 else -1

    # Draw the score, lives, and level
    cv2.putText(background, 'Lives: ' + str(lives), (WIDTH - 250, 35), cv2.FONT_HERSHEY_PLAIN, 2, SCORE_COLOR, 2)
    cv2.putText(background, 'Level: ' + str(level), (WIDTH - 250, 68), cv2.FONT_HERSHEY_PLAIN, 2, SCORE_COLOR, 2)
    cv2.putText(background, 'Score: ' + str(myscore), (WIDTH - 250, 101), cv2.FONT_HERSHEY_PLAIN, 2, SCORE_COLOR, 2)

    # Check if the ball is out of the screen
    if xpos <= 0 or xpos >= WIDTH:
        lives -= 1
        temp = cv2.blur(background, (15, 15))
        cv2.putText(temp, 'You Lost a Life!', (300, 360), cv2.FONT_HERSHEY_DUPLEX, 3, (185, 89, 200), 3, 1)
        cv2.imshow('Classic Pong Game', temp)
        cv2.waitKey(2000)
        xpos, ypos = WIDTH // 2, HEIGHT // 2
        if deltay > 0:
            deltay = -deltay

    # Check for game over
    if lives == 0:
        ball = False
        deltax, deltay = DELTAX_INIT, DELTAY_INIT
        level = 0
        background = np.full((HEIGHT, WIDTH, 3), GAME_OVER_BACKGROUND_COLOR, dtype=np.uint8)
        cv2.waitKey(1000)
        for i in range(0, HEIGHT, 10):
            background[i:i + 10, :] = (24, 34, 255)
            cv2.imshow('Classic Pong Game', background)
            cv2.waitKey(10)
        cv2.putText(background, 'GAME OVER', (400, 360), cv2.FONT_HERSHEY_DUPLEX, 3, GAME_OVER_TEXT_COLOR, 2)
        cv2.putText(background, 'Your Score: ' + str(myscore), (420, 420), cv2.FONT_HERSHEY_PLAIN, 2, GAME_OVER_TEXT_COLOR, 2)
        if myscore > highscore:
            highscore = myscore
        cv2.putText(background, 'HIGH SCORE: ' + str(highscore), (420, 480), cv2.FONT_HERSHEY_PLAIN, 2, GAME_OVER_TEXT_COLOR, 2)
        cv2.putText(background, 'Press q twice to exit or game restarts in 5 seconds', (300, 550), cv2.FONT_HERSHEY_DUPLEX, 1, GAME_OVER_TEXT_COLOR, 2)
        cv2.imshow('Classic Pong Game', background)
        cv2.waitKey(5000)
        ball = True
        myscore = 0
        lives = LIVES_INIT

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    cv2.imshow('Classic Pong Game', background)

camera.release()
cv2.destroyAllWindows()
