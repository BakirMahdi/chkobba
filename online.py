import pygame
import random
import time
import sys
import math
import json
import os
import socket
import threading
import select
from itertools import combinations

pygame.init()
pygame.font.init()
pygame.mixer.init()

try:
    screen_info = pygame.display.Info()
    SCREEN_WIDTH = screen_info.current_w
    SCREEN_HEIGHT = screen_info.current_h
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
except Exception as e:
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

pygame.display.set_caption("Tunisian Chkobba")
clock = pygame.time.Clock()

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
PORT = 12345
BUFFER_SIZE = 1024

music_playing = True
current_song_index = 0
song_list = []
online = False
is_host = False
client_socket = None
server_socket = None
opponent_connected = False

try:
    song_folder = "songs"
    song_files = [f for f in os.listdir(song_folder) if f.endswith(".mp3")]
    song_list = [os.path.join(song_folder, f) for f in song_files]
    if song_list:
        pygame.mixer.music.load(song_list[0])
        pygame.mixer.music.set_volume(1.0)
except Exception as e:
    pass

def play_next_song():
    global current_song_index
    if song_list:
        current_song_index = (current_song_index + 1) % len(song_list)
        pygame.mixer.music.load(song_list[current_song_index])
        pygame.mixer.music.play()

pygame.mixer.music.set_endevent(pygame.USEREVENT)

def main_menu():
    menu_font = pygame.font.SysFont('Arial', 72)
    button_font = pygame.font.SysFont('Arial', 48)
    running = True

    while running:
        screen.fill(COLORS['green'])
        
        title_text = menu_font.render("Chkobba Tunisienne", True, COLORS['gold'])
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2+30, SCREEN_HEIGHT//4))
        screen.blit(title_text, title_rect)

        local_btn = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 60, 200, 80)
        pygame.draw.rect(screen, COLORS['blue'], local_btn)
        local_text = button_font.render("VS AI", True, COLORS['white'])
        screen.blit(local_text, (local_btn.x + 50, local_btn.y + 10))

        online_btn = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 60, 200, 80)
        pygame.draw.rect(screen, COLORS['yellow'], online_btn)
        online_text = button_font.render("Online", True, COLORS['black'])
        screen.blit(online_text, (online_btn.x + 40, online_btn.y + 10))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if local_btn.collidepoint(pos):
                    start_menu()
                elif online_btn.collidepoint(pos):
                    online_menu()

def online_menu():
    menu_font = pygame.font.SysFont('Arial', 72)
    button_font = pygame.font.SysFont('Arial', 48)
    running = True

    while running:
        screen.fill(COLORS['green'])
        
        title_text = menu_font.render("Online Chkobba", True, COLORS['gold'])
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
        screen.blit(title_text, title_rect)

        host_btn = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 60, 200, 80)
        pygame.draw.rect(screen, COLORS['blue'], host_btn)
        host_text = button_font.render("Host", True, COLORS['white'])
        screen.blit(host_text, (host_btn.x + 50, host_btn.y + 10))

        join_btn = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 60, 200, 80)
        pygame.draw.rect(screen, COLORS['yellow'], join_btn)
        join_text = button_font.render("Join", True, COLORS['black'])
        screen.blit(join_text, (join_btn.x + 50, join_btn.y + 10))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if host_btn.collidepoint(pos):
                    host_game()
                    running = False
                elif join_btn.collidepoint(pos):
                    join_game()
                    running = False

def safe_error_display(msg):
    print(f"Error: {msg}")
    try:
        if pygame.display.get_init():
            font = pygame.font.SysFont('Arial', 36)
            screen.fill(COLORS['red'])
            lines = msg.split('\n')
            y = SCREEN_HEIGHT//2 - 50
            for line in lines:
                text = font.render(line, True, COLORS['white'])
                screen.blit(text, (50, y))
                y += 40
            pygame.display.flip()
            pygame.time.wait(5000)
    except:
        pass

def online_game_loop():
    global client_socket, opponent_connected
    try:
        total_scores = {'player': 0, 'opponent': 0}
        round_starter = random.choice(['player', 'opponent'])
        clock = pygame.time.Clock()
        
        while opponent_connected:
            deck = create_deck()
            board, remaining = deal_cards(deck)
            player_hand = []
            opponent_hand = []
            player_captured = []
            opponent_captured = []
            selected_card = None
            selected_board = []
            running = True
            player_turn = (round_starter == 'player')
            message = None
            last_capturer = None
            moving_cards = []
            dealing_phase = True
            dealing_queue = []

            if round_starter == 'player':
                for _ in range(3):
                    if remaining: dealing_queue.append(('player', remaining.pop(0)))
                for _ in range(3):
                    if remaining: dealing_queue.append(('opponent', remaining.pop(0)))
            else:
                for _ in range(3):
                    if remaining: dealing_queue.append(('opponent', remaining.pop(0)))
                for _ in range(3):
                    if remaining: dealing_queue.append(('player', remaining.pop(0)))

            while running and opponent_connected:
                clock.tick(FPS)
                current_time = time.time()
                
                try:
                    client_socket.settimeout(2)
                    if player_turn:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                            if event.type == pygame.MOUSEBUTTONDOWN and not dealing_phase:
                                pos = pygame.mouse.get_pos()
                                selected_card = None
                                for card in player_hand:
                                    if card.rect.collidepoint(pos):
                                        selected_card = card
                                        break

                        move_data = json.dumps({
                            'hand': [c.value for c in player_hand],
                            'board': [c.value for c in board],
                            'selected': selected_card.value if selected_card else None,
                            'turn': player_turn,
                            'score': total_scores,
                            'remaining': len(remaining),
                            'dealing_queue': [(t, c.value) for t, c in dealing_queue]
                        })
                        client_socket.send(move_data.encode())
                    else:
                        data = client_socket.recv(4096)
                        if data:
                            opponent_data = json.loads(data.decode())
                            board = [Card('virtual', v) for v in opponent_data['board']]
                            remaining = [Card('virtual', '?')] * opponent_data['remaining']
                            dealing_queue = [(t, Card('virtual', v)) for t, v in opponent_data['dealing_queue']]
                            player_turn = opponent_data['turn']
                            total_scores = opponent_data['score']

                except socket.timeout:
                    continue
                except Exception as e:
                    safe_error_display(f"Network error: {str(e)}")
                    break

                if dealing_phase:
                    if dealing_queue and not moving_cards:
                        target, card = dealing_queue.pop(0)
                        start_pos = (SCREEN_WIDTH - CARD_SIZE - 20, SCREEN_HEIGHT//2 + 100)
                        if target == 'player':
                            player_start_x = (SCREEN_WIDTH - (3 * CARD_SIZE + 2 * 10)) // 2
                            target_pos = (
                                player_start_x + len(player_hand) * (CARD_SIZE + 10),
                                SCREEN_HEIGHT - CARD_SIZE - 50
                            )
                            moving_cards.append(MovingCard(card, start_pos, target_pos, 'player_hand'))
                        else:
                            ai_start_x = (SCREEN_WIDTH - (3 * CARD_SIZE + 2 * 10)) // 2
                            target_pos = (
                                ai_start_x + len(opponent_hand) * (CARD_SIZE + 10),
                                50
                            )
                            moving_cards.append(MovingCard(card, start_pos, target_pos, 'opponent_hand'))
                    elif not dealing_queue and not moving_cards:
                        dealing_phase = False

                completed_cards = []
                for mc in moving_cards:
                    if mc.update():
                        completed_cards.append(mc)
                for mc in completed_cards:
                    if mc.destination == 'board':
                        board.append(mc.card)
                    elif mc.destination == 'player_pile':
                        player_captured.append(mc.card)
                    elif mc.destination == 'opponent_pile':
                        opponent_captured.append(mc.card)
                    elif mc.destination == 'player_hand':
                        player_hand.append(mc.card)
                    elif mc.destination == 'opponent_hand':
                        opponent_hand.append(mc.card)
                    moving_cards.remove(mc)

                draw_game(
                    player_hand, opponent_hand, board, total_scores, 
                    selected_card, selected_board, message, player_captured,
                    opponent_captured, moving_cards, (20, SCREEN_HEIGHT - CARD_SIZE - 50),
                    (SCREEN_WIDTH - CARD_SIZE - 20, 50), player_turn, remaining, dealing_phase
                )

                if not player_hand and not opponent_hand and not remaining:
                    running = False

            score_breakdown = calculate_scores(player_captured, opponent_captured, 0, 0)
            total_scores['player'] += sum(1 for v in score_breakdown.values() if v == 'player')
            total_scores['opponent'] += sum(1 for v in score_breakdown.values() if v == 'opponent')
            
            show_round_scores(score_breakdown, total_scores, 11)
            
            if (total_scores['player'] >= 11 or total_scores['opponent'] >= 11) and abs(total_scores['player'] - total_scores['opponent']) >= 2:
                show_final_winner(total_scores, 11)
                break

            round_starter = 'opponent' if round_starter == 'player' else 'player'

    except Exception as e:
        safe_error_display(str(e))
    finally:
        if client_socket:
            client_socket.close()
        opponent_connected = False

def host_game():
    global server_socket, client_socket, opponent_connected
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', PORT))
        server_socket.listen(1)
        server_socket.settimeout(30)
        
        connection_screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        connection_screen.fill(COLORS['green'])
        font = pygame.font.SysFont('Arial', 48)
        text = font.render("Waiting for player...", True, COLORS['white'])
        connection_screen.blit(text, (SCREEN_WIDTH//2-150, SCREEN_HEIGHT//2))
        screen.blit(connection_screen, (0, 0))
        pygame.display.flip()
        
        client_socket, addr = server_socket.accept()
        opponent_connected = True
        online_game_loop()

    except Exception as e:
        safe_error_display(f"Hosting failed: {str(e)}")
    finally:
        if server_socket:
            server_socket.close()

def join_game():
    global client_socket, opponent_connected
    try:
        ip = ip_input_menu()
        if not ip: return
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(10)
        
        connection_screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        connection_screen.fill(COLORS['green'])
        font = pygame.font.SysFont('Arial', 48)
        text = font.render("Connecting...", True, COLORS['white'])
        connection_screen.blit(text, (SCREEN_WIDTH//2-150, SCREEN_HEIGHT//2))
        screen.blit(connection_screen, (0, 0))
        pygame.display.flip()

        client_socket.connect((ip, PORT))
        opponent_connected = True
        online_game_loop()

    except Exception as e:
        safe_error_display(f"Connection failed: {str(e)}")
    finally:
        if client_socket:
            client_socket.close()

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
    return (deck[:4], deck[4:])

def draw_game(player_hand, opponent_hand, board, total_scores, selected_card, 
             selected_board, message, player_captured, opponent_captured, moving_cards, 
             player_pile_pos, opponent_pile_pos, player_turn, remaining, dealing_phase):
    try:
        screen.fill(COLORS['green'])
        
        if not hasattr(draw_game, 'back_image'):
            draw_game.back_image = load_back_image()

        def center_x(elements_count, element_width, spacing=10):
            total_width = elements_count * element_width + (elements_count - 1) * spacing
            return (SCREEN_WIDTH - total_width) // 2

        button_font = pygame.font.SysFont('Arial', 24)
        stop_btn = pygame.Rect(SCREEN_WIDTH - 150, SCREEN_HEIGHT - 100, 140, 40)
        next_btn = pygame.Rect(SCREEN_WIDTH - 150, SCREEN_HEIGHT - 50, 140, 40)
        
        pygame.draw.rect(screen, COLORS['red' if music_playing else 'blue'], stop_btn)
        pygame.draw.rect(screen, COLORS['yellow'], next_btn)
        
        stop_text = button_font.render("Stop Music" if music_playing else "Play Music", True, COLORS['white'])
        next_text = button_font.render("Next Song", True, COLORS['black'])
        screen.blit(stop_text, (stop_btn.x + 10, stop_btn.y + 10))
        screen.blit(next_text, (next_btn.x + 10, next_btn.y + 10))

        if len(remaining) > 0:
            remaining_pos = (SCREEN_WIDTH - CARD_SIZE - 20, SCREEN_HEIGHT//2 + 100)
            pile_scale = 0.7
            scaled_back = pygame.transform.scale(draw_game.back_image, 
                                               (int(CARD_SIZE*pile_scale), 
                                                int(CARD_SIZE*pile_scale)))
            screen.blit(scaled_back, remaining_pos)
            
            count_font = pygame.font.SysFont('Arial', 36)
            count_text = count_font.render(str(len(remaining)), True, COLORS['black'])
            text_rect = count_text.get_rect(center=(remaining_pos[0] + CARD_SIZE*pile_scale//2, 
                                                  remaining_pos[1] + CARD_SIZE*pile_scale//2))
            screen.blit(count_text, text_rect)

        def draw_pile(captured, position):
            if captured:
                pile_scale = 1 + 0.1 * math.log(len(captured) + 1)
                scaled_back = pygame.transform.scale(draw_game.back_image, 
                                                    (int(CARD_SIZE*pile_scale), 
                                                     int(CARD_SIZE*pile_scale)))
                screen.blit(scaled_back, position)

        draw_pile(player_captured, player_pile_pos)
        draw_pile(opponent_captured, opponent_pile_pos)

        for mc in moving_cards:
            if mc.destination in ['opponent_hand', 'opponent_pile']:
                screen.blit(draw_game.back_image, mc.pos)
            else:
                mc.card.draw(screen, mc.pos)

        if opponent_hand:
            ai_start_x = center_x(len(opponent_hand), CARD_SIZE)
            for i in range(len(opponent_hand)):
                x = ai_start_x + i*(CARD_SIZE + 10)
                y = 50
                screen.blit(draw_game.back_image, (x, y))

        if board:
            board_start_x = center_x(len(board), CARD_SIZE, 20)
            for i, card in enumerate(board):
                pos = (board_start_x + i*(CARD_SIZE + 20), SCREEN_HEIGHT//3)
                card.draw(screen, pos)
                if selected_card and card.value == selected_card.value:
                    pygame.draw.rect(screen, COLORS['yellow'], card.rect, 3)
                if card in selected_board:
                    pygame.draw.rect(screen, COLORS['blue'], card.rect, 3)

        if player_hand:
            player_start_x = center_x(len(player_hand), CARD_SIZE)
            for i, card in enumerate(player_hand):
                pos = (player_start_x + i*(CARD_SIZE + 10), SCREEN_HEIGHT - CARD_SIZE - 50)
                card.draw(screen, pos)
                if card == selected_card:
                    pygame.draw.rect(screen, COLORS['red'], card.rect, 3)

        font = pygame.font.SysFont('Arial', 36)
        score_text = font.render(f"Total Score: Player {total_scores['player']} - Opponent {total_scores['opponent']}", True, COLORS['black'])
        screen.blit(score_text, (10, 10))
        
        message_font = pygame.font.SysFont('Arial', 48, bold=True)
        if dealing_phase:
            msg_surface = message_font.render("Dealing cards...", True, COLORS['white'])
        elif message and time.time() - message["time"] < MESSAGE_DURATION:
            msg_surface = message_font.render(message["text"], True, message["color"])
        else:
            turn_text = "Your Turn" if player_turn else "Opponent's Turn"
            msg_surface = message_font.render(turn_text, True, COLORS['white'])
        msg_rect = msg_surface.get_rect(center=(SCREEN_WIDTH//2, 550))
        screen.blit(msg_surface, msg_rect)

        pygame.display.flip()
    except pygame.error:
        return

def calculate_scores(player_captured, opponent_captured, player_chkobba, opponent_chkobba):
    scores = {
        '7aya': None,
        'karta': None,
        'dineri': None,
        'bermila': None,
        'chkobba': {'player': player_chkobba, 'opponent': opponent_chkobba}
    }

    p_7d = any(c.suit == 'diamonds' and c.value == 7 for c in player_captured)
    a_7d = any(c.suit == 'diamonds' and c.value == 7 for c in opponent_captured)
    if p_7d: scores['7aya'] = 'player'
    elif a_7d: scores['7aya'] = 'opponent'

    p_total = len(player_captured)
    a_total = len(opponent_captured)
    if p_total > a_total: scores['karta'] = 'player'
    elif a_total > p_total: scores['karta'] = 'opponent'

    p_d = sum(1 for c in player_captured if c.suit == 'diamonds')
    a_d = sum(1 for c in opponent_captured if c.suit == 'diamonds')
    if p_d > a_d: scores['dineri'] = 'player'
    elif a_d > p_d: scores['dineri'] = 'opponent'

    p_7 = sum(1 for c in player_captured if c.value == 7)
    a_7 = sum(1 for c in opponent_captured if c.value == 7)
    if p_7 > a_7:
        scores['bermila'] = 'player'
    elif a_7 > p_7:
        scores['bermila'] = 'opponent'
    else:
        p_6 = sum(1 for c in player_captured if c.value == 6)
        a_6 = sum(1 for c in opponent_captured if c.value == 6)
        if p_6 > a_6: scores['bermila'] = 'player'
        elif a_6 > p_6: scores['bermila'] = 'opponent'

    return scores

def show_round_scores(score_breakdown, total_scores, winning_score):
    screen.fill(COLORS['green'])
    font = pygame.font.SysFont('Arial', 40)
    small_font = pygame.font.SysFont('Arial', 28)
    
    round_points = {
        'player': sum(1 for v in score_breakdown.values() if isinstance(v, str) and v == 'player') + score_breakdown['chkobba']['player'],
        'opponent': sum(1 for v in score_breakdown.values() if isinstance(v, str) and v == 'opponent') + score_breakdown['chkobba']['opponent']
    }
    
    lines = [
        "Round Scores:",
        f"7aya: {score_breakdown['7aya'] or 'None'}",
        f"Karta: {score_breakdown['karta'] or 'None'}", 
        f"Dineri: {score_breakdown['dineri'] or 'None'}",
        f"Bermila: {score_breakdown['bermila'] or 'None'}",
        f"Chkobba: Player {score_breakdown['chkobba']['player']} - Opponent {score_breakdown['chkobba']['opponent']}",
        "",
        f"Round Points: Player {round_points['player']} - Opponent {round_points['opponent']}",
        f"Total Score: Player {total_scores['player']} - Opponent {total_scores['opponent']}",
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
    
    winner = "Player" if total_scores['player'] >= winning_score and (total_scores['player'] - total_scores['opponent']) >= 2 else "Opponent" if total_scores['opponent'] >= winning_score and (total_scores['opponent'] - total_scores['player']) >= 2 else None
    if not winner:
        winner = "Player" if total_scores['player'] > total_scores['opponent'] else "Opponent"
    
    lines = [
        f"Game Winner: {winner}!",
        f"Final Score: Player {total_scores['player']} - Opponent {total_scores['opponent']}",
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

def load_back_image():
    try:
        back_image = pygame.image.load("cards/back.png").convert_alpha()
        return pygame.transform.scale(back_image, (CARD_SIZE, CARD_SIZE))
    except Exception as e:
        back = pygame.Surface((CARD_SIZE, CARD_SIZE))
        back.fill(COLORS['red'])
        return back
    
    
def start_menu():
    menu_font = pygame.font.SysFont('Arial', 72)
    button_font = pygame.font.SysFont('Arial', 48)
    selected_score = 11
    running = True

    while running:
        screen.fill(COLORS['green'])
        
        title_text = menu_font.render("Select Game Mode", True, COLORS['gold'])
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
        screen.blit(title_text, title_rect)

        btn_11 = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 - 50, 100, 80)
        pygame.draw.rect(screen, COLORS['yellow'], btn_11)
        text_11 = button_font.render("11", True, COLORS['black'])
        screen.blit(text_11, (btn_11.x + 30, btn_11.y + 20))

        btn_21 = pygame.Rect(SCREEN_WIDTH//2 + 50, SCREEN_HEIGHT//2 - 50, 100, 80)
        pygame.draw.rect(screen, COLORS['yellow'], btn_21)
        text_21 = button_font.render("21", True, COLORS['black'])
        screen.blit(text_21, (btn_21.x + 30, btn_21.y + 20))

        start_btn = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 200, 200, 80)
        pygame.draw.rect(screen, COLORS['blue'], start_btn)
        start_text = button_font.render("Start Game", True, COLORS['white'])
        screen.blit(start_text, (start_btn.x + 20, start_btn.y + 20))

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
                    main_game_loop(selected_score)
                    running = False

def ip_input_menu():
    font = pygame.font.SysFont('Arial', 48)
    input_font = pygame.font.SysFont('Arial', 36)
    ip_text = ""
    running = True
    clock = pygame.time.Clock()

    while running:
        clock.tick(30)
        screen.fill(COLORS['green'])
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    ip_text = ip_text[:-1]
                elif event.key == pygame.K_RETURN:
                    return ip_text.strip()
                else:
                    ip_text += event.unicode
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                confirm_btn = pygame.Rect(SCREEN_WIDTH//2 - 75, SCREEN_HEIGHT - 200, 150, 60)
                if confirm_btn.collidepoint(mouse_pos):
                    return ip_text.strip()

        title = font.render("Enter Server IP:", True, COLORS['black'])
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
        screen.blit(title, title_rect)

        input_box = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 - 25, 300, 50)
        pygame.draw.rect(screen, COLORS['white'], input_box)
        
        txt_surface = input_font.render(ip_text, True, COLORS['black'])
        screen.blit(txt_surface, (input_box.x + 10, input_box.y + 10))

        confirm_btn = pygame.Rect(SCREEN_WIDTH//2 - 75, SCREEN_HEIGHT - 200, 150, 60)
        pygame.draw.rect(screen, COLORS['blue'], confirm_btn)
        confirm_text = input_font.render("Connect", True, COLORS['white'])
        screen.blit(confirm_text, (confirm_btn.x + 10, confirm_btn.y + 10))

        pygame.display.flip()

    return None

class Card:
    def __init__(self, suit, value):
        self.suit = suit
        self.value = int(value)
        try:
            img = pygame.image.load(f"cards/{suit}_{value}.png").convert_alpha()
            self.image = pygame.transform.scale(img, (CARD_SIZE, CARD_SIZE))
        except Exception as e:
            self.image = pygame.Surface((CARD_SIZE, CARD_SIZE), pygame.SRCALPHA)
            self.image.fill((255, 255, 255, 0))
            font = pygame.font.SysFont('Arial', 24)
            text = font.render(f"{value} {suit[0]}", True, COLORS['black'])
            text_rect = text.get_rect(center=(CARD_SIZE//2, CARD_SIZE//2))
            self.image.blit(text, text_rect)
        self.rect = None
    def draw(self, surface, pos):
        x, y = pos
        self.rect = self.image.get_rect(topleft=(x, y))
        surface.blit(self.image, (x, y))

if __name__ == "__main__":
    main_menu()