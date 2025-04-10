import pygame
import random
import time
import sys
import math
import os
from itertools import combinations

# Initialize Pygame modules
pygame.init()
pygame.font.init()
pygame.mixer.init()

# Configure display settings
try:
    screen_info = pygame.display.Info()
    SCREEN_WIDTH = screen_info.current_w
    SCREEN_HEIGHT = screen_info.current_h
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
except Exception as e:
    print(f"Display error: {e}, using windowed mode")
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

pygame.display.set_caption("Tunisian Chkobba")
clock = pygame.time.Clock()

# Game constants
CARD_SIZE = 150
FPS = 120
COLORS = {
    'green': (34, 139, 34),
    'red': (255, 0, 0),
    'blue': (0, 0, 255),
    'yellow': (255, 255, 0),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
    'gold': (255, 215, 0)
}
AI_DELAY = 2
MESSAGE_DURATION = 2
TRANSITION_DELAY = 1
CARD_MOVE_SPEED = 15

# Music configuration
music_playing = True
current_song_index = 0
song_list = []

# Load music files
try:
    song_folder = "songs"
    song_files = [f for f in os.listdir(song_folder) if f.endswith(".mp3")]
    song_list = [os.path.join(song_folder, f) for f in song_files]
    if song_list:
        pygame.mixer.music.load(song_list[0])
        pygame.mixer.music.set_volume(1.0)
except Exception as e:
    print(f"Error loading music: {e}")

def play_next_song():
    global current_song_index
    if song_list:
        current_song_index = (current_song_index + 1) % len(song_list)
        pygame.mixer.music.load(song_list[current_song_index])
        pygame.mixer.music.play()

# Set up music end event
pygame.mixer.music.set_endevent(pygame.USEREVENT)

def start_menu():
    menu_font = pygame.font.SysFont('Arial', 72)
    button_font = pygame.font.SysFont('Arial', 48)
    selected_score = 11
    running = True

    while running:
        screen.fill(COLORS['green'])
        
        # Title
        title_text = menu_font.render("Chkobba Tunisienne", True, COLORS['gold'])
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2+30, SCREEN_HEIGHT//4))
        screen.blit(title_text, title_rect)

        # Score selection
        score_text = button_font.render("Select Winning Score:", True, COLORS['black'])
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2+30, SCREEN_HEIGHT//2 - 50))
        screen.blit(score_text, score_rect)

        # 11 points button
        btn_11_color = COLORS['yellow'] if selected_score == 11 else COLORS['white']
        btn_11 = pygame.Rect(SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 + 20, 125, 80)
        pygame.draw.rect(screen, btn_11_color, btn_11)
        text_11 = button_font.render("11", True, COLORS['black'])
        screen.blit(text_11, (btn_11.x + 40, btn_11.y + 10))

        # 21 points button
        btn_21_color = COLORS['yellow'] if selected_score == 21 else COLORS['white']
        btn_21 = pygame.Rect(SCREEN_WIDTH//2 + 60, SCREEN_HEIGHT//2 + 20, 125, 80)
        pygame.draw.rect(screen, btn_21_color, btn_21)
        text_21 = button_font.render("21", True, COLORS['black'])
        screen.blit(text_21, (btn_21.x + 40, btn_21.y + 10))

        # Start button
        start_btn = pygame.Rect(SCREEN_WIDTH//2 - 85, SCREEN_HEIGHT - 200, 243, 80)
        pygame.draw.rect(screen, COLORS['blue'], start_btn)
        start_text = button_font.render("Start Game", True, COLORS['white'])
        screen.blit(start_text, (start_btn.x + 20, start_btn.y + 10))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if btn_11.collidepoint(pos):
                    selected_score = 11
                elif btn_21.collidepoint(pos):
                    selected_score = 21
                elif start_btn.collidepoint(pos):
                    return selected_score

def load_back_image():
    try:
        back_image = pygame.image.load("cards/back.png").convert_alpha()
        return pygame.transform.scale(back_image, (CARD_SIZE, CARD_SIZE))
    except Exception as e:
        print(f"Error loading back image: {e}")
        back = pygame.Surface((CARD_SIZE, CARD_SIZE))
        back.fill(COLORS['red'])
        return back

class Card:
    def __init__(self, suit, value):
        self.suit = suit
        self.value = int(value)
        self.image = pygame.Surface((CARD_SIZE, CARD_SIZE))
        self.rect = None
        
        try:
            img = pygame.image.load(f"cards/{suit}_{value}.png").convert_alpha()
            self.image = pygame.transform.scale(img, (CARD_SIZE, CARD_SIZE))
        except Exception as e:
            self.image.fill(COLORS['white'])
            font = pygame.font.SysFont('Arial', 24)
            text = font.render(f"{value} {suit[0]}", True, COLORS['black'])
            text_rect = text.get_rect(center=(CARD_SIZE//2, CARD_SIZE//2))
            self.image.blit(text, text_rect)

    def draw(self, surface, pos):
        x, y = pos
        self.rect = self.image.get_rect(topleft=(x, y))
        surface.blit(self.image, (x, y))

class MovingCard:
    def __init__(self, card, start_pos, target_pos, destination):
        self.card = card
        self.pos = list(start_pos)
        self.target_pos = target_pos
        self.destination = destination
        self.speed = CARD_MOVE_SPEED
        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        distance = math.hypot(dx, dy)
        self.dx = dx / distance if distance > 0 else 0
        self.dy = dy / distance if distance > 0 else 0

    def update(self):
        self.pos[0] += self.dx * self.speed
        self.pos[1] += self.dy * self.speed
        return self.reached_target()

    def reached_target(self):
        return (abs(self.pos[0] - self.target_pos[0]) < self.speed and 
                abs(self.pos[1] - self.target_pos[1]) < self.speed)

def create_deck():
    suits = ['clubs', 'diamonds', 'hearts', 'spades']
    return [Card(suit, str(value)) for suit in suits for value in range(1, 11)]

def deal_cards(deck):
    random.shuffle(deck)
    return (
        deck[:4],   # Board
        deck[4:]    # Remaining cards (including player/AI hands)
    )

def draw_game(player_hand, ai_hand, board, total_scores, selected_card, 
             selected_board, message, player_captured, ai_captured, moving_cards, 
             player_pile_pos, ai_pile_pos, player_turn, remaining_cards, dealing_phase):
    screen.fill(COLORS['green'])
    
    if not hasattr(draw_game, 'back_image'):
        draw_game.back_image = load_back_image()

    def center_x(elements_count, element_width, spacing=10):
        total_width = elements_count * element_width + (elements_count - 1) * spacing
        return (SCREEN_WIDTH - total_width) // 2

    # Draw music control buttons
    button_font = pygame.font.SysFont('Arial', 24)
    stop_btn = pygame.Rect(SCREEN_WIDTH - 150, SCREEN_HEIGHT - 100, 140, 40)
    next_btn = pygame.Rect(SCREEN_WIDTH - 150, SCREEN_HEIGHT - 50, 140, 40)
    
    pygame.draw.rect(screen, COLORS['red' if music_playing else 'blue'], stop_btn)
    pygame.draw.rect(screen, COLORS['yellow'], next_btn)
    
    stop_text = button_font.render("Stop Music" if music_playing else "Play Music", True, COLORS['white'])
    next_text = button_font.render("Next Song", True, COLORS['black'])
    screen.blit(stop_text, (stop_btn.x + 10, stop_btn.y + 10))
    screen.blit(next_text, (next_btn.x + 10, next_btn.y + 10))

    # Draw remaining cards pile (right side)
    if len(remaining_cards) > 0:
        remaining_pos = (SCREEN_WIDTH - CARD_SIZE - 20, SCREEN_HEIGHT//2 + 100)
        pile_scale = 0.7
        scaled_back = pygame.transform.scale(draw_game.back_image, 
                                           (int(CARD_SIZE*pile_scale), 
                                            int(CARD_SIZE*pile_scale)))
        screen.blit(scaled_back, remaining_pos)
        
        count_font = pygame.font.SysFont('Arial', 36)
        count_text = count_font.render(str(len(remaining_cards)), True, COLORS['black'])
        text_rect = count_text.get_rect(center=(remaining_pos[0] + CARD_SIZE*pile_scale//2, 
                                              remaining_pos[1] + CARD_SIZE*pile_scale//2))
        screen.blit(count_text, text_rect)

    # Draw captured piles
    def draw_pile(captured, position):
        if captured:
            pile_scale = 1 + 0.1 * math.log(len(captured) + 1)
            scaled_back = pygame.transform.scale(draw_game.back_image, 
                                                (int(CARD_SIZE*pile_scale), 
                                                 int(CARD_SIZE*pile_scale)))
            screen.blit(scaled_back, position)

    draw_pile(player_captured, player_pile_pos)
    draw_pile(ai_captured, ai_pile_pos)

    # Draw moving cards with AI cards flipped
    for mc in moving_cards:
        if mc.destination in ['ai_hand', 'ai_pile']:
            screen.blit(draw_game.back_image, mc.pos)
        else:
            mc.card.draw(screen, mc.pos)

    # Draw AI hand (always show backs)
    if ai_hand:
        ai_start_x = center_x(len(ai_hand), CARD_SIZE)
        for i in range(len(ai_hand)):
            x = ai_start_x + i*(CARD_SIZE + 10)
            y = 50
            screen.blit(draw_game.back_image, (x, y))

    # Draw board
    if board:
        board_start_x = center_x(len(board), CARD_SIZE, 20)
        for i, card in enumerate(board):
            pos = (board_start_x + i*(CARD_SIZE + 20), SCREEN_HEIGHT//3)
            card.draw(screen, pos)
            if selected_card and card.value == selected_card.value:
                pygame.draw.rect(screen, COLORS['yellow'], card.rect, 3)
            if card in selected_board:
                pygame.draw.rect(screen, COLORS['blue'], card.rect, 3)

    # Draw player hand
    if player_hand:
        player_start_x = center_x(len(player_hand), CARD_SIZE)
        for i, card in enumerate(player_hand):
            pos = (player_start_x + i*(CARD_SIZE + 10), SCREEN_HEIGHT - CARD_SIZE - 50)
            card.draw(screen, pos)
            if card == selected_card:
                pygame.draw.rect(screen, COLORS['red'], card.rect, 3)

    # Score display
    font = pygame.font.SysFont('Arial', 36)
    score_text = font.render(f"Total Score: Player {total_scores['player']} - AI {total_scores['ai']}", True, COLORS['black'])
    screen.blit(score_text, (10, 10))
    
    # Message display
    message_font = pygame.font.SysFont('Arial', 48, bold=True)
    if dealing_phase:
        msg_surface = message_font.render("Dealing cards...", True, COLORS['white'])
    elif message and time.time() - message["time"] < MESSAGE_DURATION:
        msg_surface = message_font.render(message["text"], True, message["color"])
    else:
        turn_text = "Your Turn" if player_turn else "AI's Turn"
        msg_surface = message_font.render(turn_text, True, COLORS['white'])
    msg_rect = msg_surface.get_rect(center=(SCREEN_WIDTH//2, 550))
    screen.blit(msg_surface, msg_rect)

    pygame.display.flip()

def calculate_scores(player_captured, ai_captured, player_chkobba, ai_chkobba):
    scores = {
        '7aya': None,
        'karta': None,
        'dineri': None,
        'bermila': None,
        'chkobba': {'player': player_chkobba, 'ai': ai_chkobba}
    }

    # 7aya scoring
    p_7d = any(c.suit == 'diamonds' and c.value == 7 for c in player_captured)
    a_7d = any(c.suit == 'diamonds' and c.value == 7 for c in ai_captured)
    if p_7d: scores['7aya'] = 'player'
    elif a_7d: scores['7aya'] = 'ai'

    # Karta scoring
    p_total = len(player_captured)
    a_total = len(ai_captured)
    if p_total > a_total: scores['karta'] = 'player'
    elif a_total > p_total: scores['karta'] = 'ai'

    # Dineri scoring
    p_d = sum(1 for c in player_captured if c.suit == 'diamonds')
    a_d = sum(1 for c in ai_captured if c.suit == 'diamonds')
    if p_d > a_d: scores['dineri'] = 'player'
    elif a_d > p_d: scores['dineri'] = 'ai'

    # Bermila scoring
    p_7 = sum(1 for c in player_captured if c.value == 7)
    a_7 = sum(1 for c in ai_captured if c.value == 7)
    if p_7 > a_7:
        scores['bermila'] = 'player'
    elif a_7 > p_7:
        scores['bermila'] = 'ai'
    else:
        p_6 = sum(1 for c in player_captured if c.value == 6)
        a_6 = sum(1 for c in ai_captured if c.value == 6)
        if p_6 > a_6: scores['bermila'] = 'player'
        elif a_6 > p_6: scores['bermila'] = 'ai'

    return scores

def show_round_scores(score_breakdown, total_scores, winning_score):
    screen.fill(COLORS['green'])
    font = pygame.font.SysFont('Arial', 40)
    small_font = pygame.font.SysFont('Arial', 28)
    
    round_points = {
        'player': sum(1 for v in score_breakdown.values() if isinstance(v, str) and v == 'player') + score_breakdown['chkobba']['player'],
        'ai': sum(1 for v in score_breakdown.values() if isinstance(v, str) and v == 'ai') + score_breakdown['chkobba']['ai']
    }
    
    lines = [
        "Round Scores:",
        f"7aya: {score_breakdown['7aya'] or 'None'}",
        f"Karta: {score_breakdown['karta'] or 'None'}", 
        f"Dineri: {score_breakdown['dineri'] or 'None'}",
        f"Bermila: {score_breakdown['bermila'] or 'None'}",
        f"Chkobba: Player {score_breakdown['chkobba']['player']} - AI {score_breakdown['chkobba']['ai']}",
        "",
        f"Round Points: Player {round_points['player']} - AI {round_points['ai']}",
        f"Total Score: Player {total_scores['player']} - AI {total_scores['ai']}",
        f"Target Score: {winning_score}",
        "",
        "Press any key to continue..."
    ]
    
    y_pos = SCREEN_HEIGHT // 4
    for line in lines:
        text = font.render(line, True, COLORS['black']) if line.startswith("Round") or "Total" in line else small_font.render(line, True, COLORS['black'])
        rect = text.get_rect(center=(SCREEN_WIDTH//2, y_pos))
        screen.blit(text, rect)
        y_pos += 40
    
    pygame.display.flip()
    
    while True:
        for event in pygame.event.get():
            if event.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return

def show_final_winner(total_scores, winning_score):
    screen.fill(COLORS['green'])
    font = pygame.font.SysFont('Arial', 72)
    small_font = pygame.font.SysFont('Arial', 36)
    
    winner = "Player" if total_scores['player'] >= winning_score and (total_scores['player'] - total_scores['ai']) >= 2 else "AI" if total_scores['ai'] >= winning_score and (total_scores['ai'] - total_scores['player']) >= 2 else None
    if not winner:  # This should theoretically never happen
        winner = "Player" if total_scores['player'] > total_scores['ai'] else "AI"
    
    lines = [
        f"Game Winner: {winner}!",
        f"Final Score: Player {total_scores['player']} - AI {total_scores['ai']}",
        f"Target Score: {winning_score}",
        "",
        "Press any key to exit..."
    ]
    
    y_pos = SCREEN_HEIGHT // 3
    for line in lines:
        text = font.render(line, True, COLORS['black']) if line.startswith("Game") else small_font.render(line, True, COLORS['black'])
        rect = text.get_rect(center=(SCREEN_WIDTH//2, y_pos))
        screen.blit(text, rect)
        y_pos += 80
    
    pygame.display.flip()
    
    while True:
        for event in pygame.event.get():
            if event.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return

def main():
    global music_playing, current_song_index
    try:
        winning_score = start_menu()
        total_scores = {'player': 0, 'ai': 0}
        round_starter = random.choice(['player', 'ai'])
        game_counter = 1
        
        if song_list:
            pygame.mixer.music.play()
        
        while True:  # Main loop to continue until end condition is met
            deck = create_deck()
            board, remaining = deal_cards(deck)
            player_hand = []
            ai_hand = []
            
            # Round state
            player_captured = []
            ai_captured = []
            selected_card = None
            selected_board = []
            running = True
            player_turn = (round_starter == 'player')
            message = None
            last_capturer = None
            ai_turn_start_time = 0
            round_transition = False
            transition_start_time = 0
            player_chkobba = 0
            ai_chkobba = 0
            moving_cards = []
            player_pile_pos = (20, SCREEN_HEIGHT - CARD_SIZE - 50)
            ai_pile_pos = (SCREEN_WIDTH - CARD_SIZE - 20, 50)
            dealing_phase = True
            dealing_queue = []

            # Initialize dealing queue
            if round_starter == 'player':
                for _ in range(3):
                    if remaining:
                        card = remaining.pop(0)
                        dealing_queue.append(('player', card))
                for _ in range(3):
                    if remaining:
                        card = remaining.pop(0)
                        dealing_queue.append(('ai', card))
            else:
                for _ in range(3):
                    if remaining:
                        card = remaining.pop(0)
                        dealing_queue.append(('ai', card))
                for _ in range(3):
                    if remaining:
                        card = remaining.pop(0)
                        dealing_queue.append(('player', card))

            while running:
                clock.tick(FPS)
                current_time = time.time()

                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()
                    if event.type == pygame.USEREVENT:
                        play_next_song()
                    if not dealing_phase and event.type == pygame.MOUSEBUTTONDOWN:
                        pos = pygame.mouse.get_pos()
                        # Music controls
                        stop_btn = pygame.Rect(SCREEN_WIDTH - 150, SCREEN_HEIGHT - 100, 140, 40)
                        next_btn = pygame.Rect(SCREEN_WIDTH - 150, SCREEN_HEIGHT - 50, 140, 40)
                        if stop_btn.collidepoint(pos):
                            music_playing = not music_playing
                            if music_playing:
                                pygame.mixer.music.unpause()
                            else:
                                pygame.mixer.music.pause()
                        elif next_btn.collidepoint(pos) and song_list:
                            play_next_song()
                        else:
                            # Game controls
                            if event.button == 1:  # Left click
                                if player_turn and not moving_cards:
                                    new_selection = None
                                    for card in player_hand:
                                        if card.rect and card.rect.collidepoint(pos):
                                            new_selection = card
                                            break
                                    
                                    if new_selection:
                                        selected_card = new_selection if selected_card != new_selection else None
                                        selected_board = []
                                    elif selected_card:
                                        for card in board:
                                            if card.rect and card.rect.collidepoint(pos):
                                                if card in selected_board:
                                                    selected_board.remove(card)
                                                else:
                                                    selected_board.append(card)
                                                break
                            
                            if event.button == 3:  # Right click
                                if player_turn and not moving_cards and selected_card:
                                    if selected_board:
                                        total = sum(c.value for c in selected_board)
                                        direct_matches = [c for c in board if c.value == selected_card.value]
                                                
                                        if any(c.value == selected_card.value for c in selected_board):
                                            if total == selected_card.value:
                                                board_length_before = len(board)
                                                
                                                # Create moving cards for player capture
                                                for card in [selected_card] + selected_board:
                                                    if card.rect:
                                                        start_pos = card.rect.topleft
                                                    else:
                                                        player_index = player_hand.index(selected_card)
                                                        player_start_x = (SCREEN_WIDTH - (len(player_hand)*CARD_SIZE + (len(player_hand)-1)*10)) // 2
                                                        start_pos = (player_start_x + player_index*(CARD_SIZE + 10), 
                                                                    SCREEN_HEIGHT - CARD_SIZE - 50)
                                                    moving_cards.append(MovingCard(card, start_pos, player_pile_pos, 'player_pile'))
                                                
                                                player_captured.extend([selected_card] + selected_board)
                                                for c in selected_board:
                                                    board.remove(c)
                                                
                                                # Modified Chkobba condition
                                                if (board_length_before > 0 
                                                    and len(board) == 0 
                                                    and (len(remaining) + len(player_hand) + len(ai_hand) > 1)):
                                                    player_chkobba += 1
                                                    message = {"text": "Chkobba! +1 point", "color": COLORS['yellow'], "time": current_time}
                                                
                                                player_hand.remove(selected_card)
                                                last_capturer = "player"
                                                selected_card = None
                                                selected_board = []
                                                player_turn = False
                                                ai_turn_start_time = current_time
                                            else:
                                                message = {"text": "Must capture exact matches!", "color": COLORS['red'], "time": current_time}
                                        else:
                                            if direct_matches:
                                                message = {"text": "Direct matches available!", "color": COLORS['red'], "time": current_time}
                                            elif total == selected_card.value:
                                                board_length_before = len(board)
                                                
                                                # Create moving cards
                                                for card in [selected_card] + selected_board:
                                                    if card.rect:
                                                        start_pos = card.rect.topleft
                                                    else:
                                                        player_index = player_hand.index(selected_card)
                                                        player_start_x = (SCREEN_WIDTH - (len(player_hand)*CARD_SIZE + (len(player_hand)-1)*10)) // 2
                                                        start_pos = (player_start_x + player_index*(CARD_SIZE + 10), 
                                                                    SCREEN_HEIGHT - CARD_SIZE - 50)
                                                    moving_cards.append(MovingCard(card, start_pos, player_pile_pos, 'player_pile'))
                                                
                                                player_captured.extend([selected_card] + selected_board)
                                                for c in selected_board:
                                                    board.remove(c)
                                                
                                                # Modified Chkobba condition
                                                if (board_length_before > 0 
                                                    and len(board) == 0 
                                                    and (len(remaining) + len(player_hand) + len(ai_hand) > 1)):
                                                    player_chkobba += 1
                                                    message = {"text": "Chkobba! +1 point", "color": COLORS['yellow'], "time": current_time}
                                                
                                                player_hand.remove(selected_card)
                                                last_capturer = "player"
                                                selected_card = None
                                                selected_board = []
                                                player_turn = False
                                                ai_turn_start_time = current_time
                                            else:
                                                message = {"text": "Sum doesn't match!", "color": COLORS['red'], "time": current_time}
                                    else:
                                        if any(c.value == selected_card.value for c in board):
                                            message = {"text": "Must capture direct matches!", "color": COLORS['red'], "time": current_time}
                                        else:
                                            # Throw animation
                                            player_index = player_hand.index(selected_card)
                                            player_start_x = (SCREEN_WIDTH - (len(player_hand)*CARD_SIZE + (len(player_hand)-1)*10)) // 2
                                            start_pos = (player_start_x + player_index*(CARD_SIZE + 10), 
                                                        SCREEN_HEIGHT - CARD_SIZE - 50)
                                            
                                            new_board_length = len(board) + 1
                                            board_start_x = (SCREEN_WIDTH - (new_board_length * CARD_SIZE + (new_board_length -1)*20)) // 2
                                            target_x = board_start_x + (new_board_length -1)*(CARD_SIZE + 20)
                                            target_y = SCREEN_HEIGHT // 3
                                            
                                            moving_cards.append(MovingCard(selected_card, start_pos, (target_x, target_y), 'board'))
                                            player_hand.remove(selected_card)
                                            selected_card = None
                                            player_turn = False
                                            ai_turn_start_time = current_time

                # Handle dealing phase
                if dealing_phase:
                    if dealing_queue and not moving_cards:
                        target, card = dealing_queue.pop(0)
                        start_pos = (SCREEN_WIDTH - CARD_SIZE - 20, SCREEN_HEIGHT//2 + 100)
                        if target == 'player':
                            player_start_x = (SCREEN_WIDTH - (3 * CARD_SIZE + 2 * 10)) // 2
                            target_pos = (player_start_x + (len(player_hand)*(CARD_SIZE + 10)),
                                          SCREEN_HEIGHT - CARD_SIZE - 50)
                            moving_cards.append(MovingCard(card, start_pos, target_pos, 'player_hand'))
                        else:
                            ai_start_x = (SCREEN_WIDTH - (3 * CARD_SIZE + 2 * 10)) // 2
                            target_pos = (ai_start_x + (len(ai_hand)*(CARD_SIZE + 10)), 50)
                            moving_cards.append(MovingCard(card, start_pos, target_pos, 'ai_hand'))
                    elif not dealing_queue and not moving_cards:
                        dealing_phase = False

                # Update moving cards
                completed_cards = []
                for mc in moving_cards:
                    if mc.update():
                        completed_cards.append(mc)
                for mc in completed_cards:
                    if mc.destination == 'board':
                        board.append(mc.card)
                    elif mc.destination == 'player_pile':
                        player_captured.append(mc.card)
                    elif mc.destination == 'ai_pile':
                        ai_captured.append(mc.card)
                    elif mc.destination == 'player_hand':
                        player_hand.append(mc.card)
                    elif mc.destination == 'ai_hand':
                        ai_hand.append(mc.card)
                    moving_cards.remove(mc)

                # AI turn logic
                if not dealing_phase and not player_turn and not round_transition:
                    if ai_turn_start_time == 0:
                        ai_turn_start_time = current_time
                    
                    if current_time - ai_turn_start_time >= AI_DELAY and not moving_cards:
                        ai_move = None
                        
                        # Check for direct matches
                        for ai_card in ai_hand:
                            direct_matches = [c for c in board if c.value == ai_card.value]
                            if direct_matches:
                                ai_move = (ai_card, direct_matches)
                                break
                        
                        # Check for combination captures
                        if not ai_move:
                            for ai_card in ai_hand:
                                for r in range(len(board), 0, -1):
                                    for combo in combinations(board, r):
                                        if sum(c.value for c in combo) == ai_card.value:
                                            ai_move = (ai_card, combo)
                                            break
                                    if ai_move: break
                                if ai_move: break
                        
                        if ai_move:
                            ai_card, target = ai_move
                            board_length_before = len(board)
                            
                            # Create moving cards for AI capture
                            for card in [ai_card] + list(target):
                                if card.rect:
                                    start_pos = card.rect.topleft
                                else:
                                    ai_index = ai_hand.index(ai_card)
                                    ai_start_x = (SCREEN_WIDTH - (len(ai_hand)*CARD_SIZE + (len(ai_hand)-1)*10)) // 2
                                    start_pos = (ai_start_x + ai_index*(CARD_SIZE + 10), 50)
                                moving_cards.append(MovingCard(card, start_pos, ai_pile_pos, 'ai_pile'))
                            
                            ai_captured.extend([ai_card] + list(target))
                            for card in target:
                                board.remove(card)
                            
                            # Modified Chkobba condition
                            if (board_length_before > 0 
                                and len(board) == 0 
                                and (len(remaining) + len(player_hand) + len(ai_hand) > 1)):
                                ai_chkobba += 1
                                message = {"text": "AI made Chkobba! +1 point", "color": COLORS['yellow'], "time": current_time}
                            
                            ai_hand.remove(ai_card)
                            last_capturer = "ai"
                        elif ai_hand:
                            # Throw the rightmost card
                            ai_card = ai_hand[-1]
                            ai_index = len(ai_hand) - 1
                            ai_start_x = (SCREEN_WIDTH - (len(ai_hand)*CARD_SIZE + (len(ai_hand)-1)*10)) // 2
                            start_pos = (ai_start_x + ai_index*(CARD_SIZE + 10), 50)
                            
                            new_board_length = len(board) + 1
                            board_start_x = (SCREEN_WIDTH - (new_board_length * CARD_SIZE + (new_board_length -1)*20)) // 2
                            target_x = board_start_x + (new_board_length -1)*(CARD_SIZE + 20)
                            target_y = SCREEN_HEIGHT // 3
                            
                            moving_cards.append(MovingCard(ai_card, start_pos, (target_x, target_y), 'board'))
                            ai_hand.pop(-1)
                        
                        # Check if both players are out of cards
                        if not player_hand and not ai_hand:
                            round_transition = True
                            transition_start_time = current_time
                        
                        ai_turn_start_time = 0
                        player_turn = True

                if round_transition:
                    if current_time - transition_start_time >= TRANSITION_DELAY and not moving_cards:
                        if len(remaining) >= 6:
                            # Deal new cards
                            for _ in range(3):
                                if remaining:
                                    card = remaining.pop(0)
                                    dealing_queue.append(('player', card))
                            for _ in range(3):
                                if remaining:
                                    card = remaining.pop(0)
                                    dealing_queue.append(('ai', card))
                            dealing_phase = True
                            round_transition = False
                        else:
                            if remaining:
                                board.extend(remaining)
                                remaining = []
                            if board:
                                if last_capturer == "player":
                                    player_captured.extend(board)
                                elif last_capturer == "ai":
                                    ai_captured.extend(board)
                                else:
                                    if player_turn:
                                        ai_captured.extend(board)
                                    else:
                                        player_captured.extend(board)
                                board.clear()
                            running = False

                draw_game(
                    player_hand, 
                    ai_hand, 
                    board, 
                    total_scores, 
                    selected_card, 
                    selected_board, 
                    message,
                    player_captured,
                    ai_captured,
                    moving_cards,
                    player_pile_pos,
                    ai_pile_pos,
                    player_turn,
                    remaining,
                    dealing_phase
                )

            # Calculate and show round scores
            score_breakdown = calculate_scores(player_captured, ai_captured, player_chkobba, ai_chkobba)
            round_player = sum(1 for v in score_breakdown.values() if isinstance(v, str) and v == 'player') + score_breakdown['chkobba']['player']
            round_ai = sum(1 for v in score_breakdown.values() if isinstance(v, str) and v == 'ai') + score_breakdown['chkobba']['ai']
            total_scores['player'] += round_player
            total_scores['ai'] += round_ai
            
            show_round_scores(score_breakdown, total_scores, winning_score)
            
            # Check if the game should end
            if (total_scores['player'] >= winning_score or total_scores['ai'] >= winning_score) and abs(total_scores['player'] - total_scores['ai']) >= 2:
                show_final_winner(total_scores, winning_score)
                return

            # Alternate round starter
            round_starter = 'ai' if round_starter == 'player' else 'player'

    except Exception as e:
        print(f"Game error: {e}")
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()