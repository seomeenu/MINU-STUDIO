#pallette
#https://lospec.com/palette-list/sweetie-16

import pygame
import sys
import json
import copy
import time
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

filename = filedialog.askopenfilename(initialdir="")
if filename.strip() == "":
    sys.exit()

pygame.init()
pygame.mixer.init(size=32)

screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("MINU STUDIO")

clock = pygame.time.Clock()

bpm = 120
patterns = {"0":[]}
with open(filename) as file:
    content = file.read()
    if content.strip() != "":
        data = json.loads(content)
        bpm = data["bpm"]
        patterns = data["patterns"]

cur_pattern = 0
old_pattern = cur_pattern

font = pygame.font.Font("src/Galmuri7.ttf", 24)
fontb = pygame.font.Font("src/Galmuri11-Bold.ttf", 24)
def draw_text(text, x, y, color="#f4f4f4", font=font):
    render = font.render(text, False, color)
    screen.blit(render, (x, y))
    return render

#0: lead 1: bass, 2: drums
cur_inst = 0

# class Note:
#     def __init__(self, pos, pitch, inst):
#         self["pos"] = pos #0~32
#         self["pitch"] = pitch #0~24
#         self["inst"] = inst

global_volume = 0.5
class Sound:
    def __init__(self, src, volume=0.5):
        self.sound = pygame.mixer.Sound(src)
        self.volume = volume
        self.sound.set_volume(self.volume * global_volume)
        self.play_time = time.time()
        
    def play(self):
        self.sound.stop()
        self.sound.play()

cur_offset = 0

lead_sounds = []
for i in range(1, 48+1):
    lead_sounds.append(Sound(f"sounds/lead/{i}.ogg"))

bass_sounds = []
for i in range(1, 48+1):
    bass_sounds.append(Sound(f"sounds/bass/{i}.ogg"))

drum_sounds = []
for i in range(1, 4+1):
    drum_sounds.append(Sound(f"sounds/drums/{i}.ogg"))

metronome_sounds = []
for i in range(1, 2+1):
    metronome_sounds.append(Sound(f"sounds/metronome/{i}.ogg", 1))

bar_pos = 0
old_bar_pos = 0

playing = False
play_time = pygame.time.get_ticks()

top_mult = 5
top_height = 24*top_mult
#note width, note height
nw = screen_width/32
nh = (screen_height-top_height)/24

play_pos = 0

note_names = [
    "C",
    "C#",
    "D",
    "D#",
    "E",
    "F",
    "F#",
    "G",
    "G#",
    "A",
    "A#",
    "B"
]*4

clipboard = []

def can_place_check(mouse_x=0, mouse_y=0, note=None):
    # new_note = Note(int(mouse_x/nw), int((mouse_y)/nh)-top_mult, cur_inst)
    new_note = note
    if note == None:
        new_note = {
            "pos": int(mouse_x/nw),
            "pitch": 24-int((mouse_y)/nh-top_mult)+cur_offset,
            "inst": cur_inst
        }

    can_place = True
    remove_note = None
    for note in patterns[str(cur_pattern)]:
        if new_note["pos"] == note["pos"] and new_note["pitch"] == note["pitch"] and new_note["inst"] == note["inst"]:
            can_place = False
            remove_note = note
            break
    if can_place:
        return True, new_note
    else:
        return False, remove_note

div_layer = pygame.Surface((screen_width, screen_height*2))
div_layer.set_colorkey("#000000")
for i, name in enumerate(note_names):
    if not ("#" in name):
        pygame.draw.rect(div_layer, "#f4f4f4", (0, top_height+i*nh, screen_width, nh))
        
for i in range(0, 32, 8):
    div_rect = [i*nw, top_height, nw/4, screen_height*2-top_height]
    pygame.draw.rect(div_layer, "#1a1c2c", div_rect)

div_layer.set_alpha(10)

pat_text = draw_text(f"PAT: {cur_pattern}", 0, 0)
pat_rect = pygame.Rect(screen_width-150, 10, pat_text.get_width()+20, pat_text.get_height()+20)

met_text = draw_text(f"MET: -", 0, 0)
met_rect = pygame.Rect(screen_width-260, 10, met_text.get_width()+20, met_text.get_height()+20)

ctrl = False
sel_start_pos = [0, 0]
sel_end_pos = [0, 0]

move_x = 0
move_y = 0

sel_rect = [0, 0, 0, 0]
sel_notes = []
sel_move = False

hold_note = None

metronome = False

def play(note):
    if note["inst"] == 0:
        lead_sounds[note["pitch"]].play()
    elif note["inst"] == 1:
        bass_sounds[note["pitch"]].play()
    elif note["inst"] == 2:
        if note["pitch"] < len(drum_sounds):
            drum_sounds[note["pitch"]].play()

def note_to_rect(note):
    return pygame.Rect([note["pos"] * nw, (24-note["pitch"]+top_mult+cur_offset) * nh, nw, nh])

# def sign(num):
#     if num > 0:
#         return 1
#     elif num < 0:
#         return -1
#     return 0

def paste():
    global sel_notes
    sel_notes = []
    for note in clipboard:
        new_note = copy.deepcopy(note)
        new_note["inst"] = cur_inst
        # can_place, new_note = can_place_check(note=note)
        # new_note["pos"] += int(mouse_x/nw)
        # if can_place:
        sel_notes.append(new_note)
        # sel_notes.append(new_note)
    # print(temp_notes)
    patterns[str(cur_pattern)] += sel_notes

def move(some_notes=[], one_note=None, movement=None):
    global move_x, move_y
    if some_notes == []:
        some_notes = [one_note]
    if movement == None:
        if int(move_x/nw) != int(mouse_x/nw):
            # dir = sign(mouse_x-move_x)
            dir = int(mouse_x/nw)-int(move_x/nw)
            moveable = True
            for some_note in some_notes:
                # print(sel_note["pos"])
                if not(32 > some_note["pos"] + dir >= 0):
                    moveable = False
                    break
            if moveable:
                for some_note in some_notes:
                    some_note["pos"] += dir
            move_x = mouse_x

        if int(move_y/nw) != int(mouse_y/nw):
            dir = int(mouse_y/nw)-int(move_y/nw)
            moveable = True
            for some_note in some_notes:
                if not(48 > some_note["pitch"] - dir >= 0):
                    moveable = False
                    break
            if moveable:
                for some_note in some_notes:
                    some_note["pitch"] -= dir
            move_y = mouse_y
    else:
        dir = movement[0]
        moveable = True
        for some_note in some_notes:
            # print(sel_note["pos"])
            if not(32 > some_note["pos"] + dir >= 0):
                moveable = False
                break
        if moveable:
            for some_note in some_notes:
                some_note["pos"] += dir
        move_x = mouse_x

        dir = movement[1]
        moveable = True
        for some_note in some_notes:
            if not(48 > some_note["pitch"] - dir >= 0):
                moveable = False
                break
        if moveable:
            for some_note in some_notes:
                some_note["pitch"] -= dir
        move_y = mouse_y

while True:
    screen.fill("#333c57")
    mouse_x, mouse_y = pygame.mouse.get_pos()
    keys = pygame.key.get_pressed()
    ctrl = keys[pygame.K_LCTRL]
    shift = keys[pygame.K_LSHIFT]
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                playing = not playing
                play_time = pygame.time.get_ticks() - play_pos * 32 * 4 * (60/bpm)*2
            elif event.key == pygame.K_1:
                cur_inst = 0
            elif event.key == pygame.K_2:
                cur_inst = 1
            elif event.key == pygame.K_3:
                cur_inst = 2
            elif event.key == pygame.K_HOME:
                play_pos = 0
                play_time = pygame.time.get_ticks()

            if ctrl:
                if event.key == pygame.K_s:
                    with open(filename, "w") as file:
                        data = {
                            "bpm": bpm,
                            "patterns": patterns
                        }
                        json.dump(data, file, indent=4)

                elif event.key == pygame.K_c:
                    clipboard = copy.deepcopy(sel_notes)
                    
                elif event.key == pygame.K_v:
                    paste()
                    
                elif event.key == pygame.K_x:
                    clipboard = copy.deepcopy(sel_notes)
                    for sel_note in sel_notes:
                        if sel_note in patterns[str(cur_pattern)]:
                            patterns[str(cur_pattern)].remove(sel_note)

            if event.key == pygame.K_DELETE:
                for sel_note in sel_notes:
                    if sel_note in patterns[str(cur_pattern)]:
                        patterns[str(cur_pattern)].remove(sel_note)

            if shift:
                if len(sel_notes) > 0:
                    if event.key == pygame.K_UP:
                        move(sel_notes, movement=[0, -1])
                    elif event.key == pygame.K_DOWN:
                        move(sel_notes, movement=[0, 1])
                    elif event.key == pygame.K_RIGHT:
                        move(sel_notes, movement=[1, 0])
                    elif event.key == pygame.K_LEFT:
                        move(sel_notes, movement=[-1, 0])

        if event.type == pygame.MOUSEBUTTONDOWN:
            if pygame.mouse.get_pressed()[0]:
                if len(sel_notes) > 0 and not ctrl and shift:
                    clipboard = copy.deepcopy(sel_notes)
                    paste()
                can_place, move_note = can_place_check(mouse_x, mouse_y)
                if not can_place:
                    hold_note = move_note
                    move_x = mouse_x
                    move_y = mouse_y

                sel_move = False
                for sel_note in sel_notes:
                    if note_to_rect(sel_note).collidepoint(mouse_x, mouse_y):
                        sel_move = True
                        break

                if len(sel_notes) > 0:
                    can_place, _ = can_place_check(mouse_x, mouse_y)
                    if can_place:
                        sel_notes = []
                    move_x = mouse_x
                    move_y = mouse_y
                if ctrl or mouse_y < top_height:
                    sel_notes = []
                if ctrl:
                    sel_start_pos = [int(mouse_x/nw), 24-int((mouse_y)/nh-top_mult)+cur_offset]
                if mouse_y > top_height and not ctrl and len(sel_notes) == 0:
                    if not (str(cur_pattern) in patterns):
                        patterns[str(cur_pattern)] = []
                    can_place, new_note = can_place_check(mouse_x, mouse_y)
                    if can_place:
                        if not playing:
                            play(new_note)
                        patterns[str(cur_pattern)].append(new_note)

            if pat_rect.collidepoint((mouse_x, mouse_y)):
                if pygame.mouse.get_pressed()[0]:
                    cur_pattern += 1
                    patterns[str(cur_pattern)] = []
                elif pygame.mouse.get_pressed()[2]:
                    if len(patterns) > 1:
                        patterns.popitem()
                        if cur_pattern == len(patterns):
                            cur_pattern -= 1

            if met_rect.collidepoint((mouse_x, mouse_y)):
                if pygame.mouse.get_pressed()[0]:
                    metronome = not metronome
        
        elif event.type == pygame.MOUSEBUTTONUP:
            hold_note = None
            # print(hold_note)

        if event.type == pygame.MOUSEWHEEL:
            wheel = event.y
            if pat_rect.collidepoint((mouse_x, mouse_y)):
                if len(patterns) > cur_pattern + wheel >= 0:
                    cur_pattern += wheel
                    pat_text = draw_text(f"PAT: {cur_pattern}", screen_width-140, 20)
                    pat_rect = pygame.Rect(screen_width-150, 10, pat_text.get_width()+20, pat_text.get_height()+20)
            elif 24 > cur_offset+wheel >= 0:
                cur_offset += wheel

        if event.type == pygame.WINDOWMOVED:
            playing = False

    screen.blit(div_layer, (0, (cur_offset-24)*nh))
    
    if pygame.mouse.get_pressed()[0]:
        if ctrl:
            hold_note = None
            sel_end_pos = [int(mouse_x/nw), 24-int((mouse_y)/nh-top_mult)+cur_offset]
            sel_rect = [sel_start_pos[0] * nw, (24-sel_start_pos[1]+top_mult+cur_offset) * nh, (sel_end_pos[0]-sel_start_pos[0]) * nw, (sel_start_pos[1]-sel_end_pos[1]) * nh]
            
            if sel_end_pos[0] < sel_start_pos[0]:
                sel_rect[0] = sel_end_pos[0] * nw
                sel_rect[2] = (sel_start_pos[0]-sel_end_pos[0]) * nw
            if sel_end_pos[1] > sel_start_pos[1]:
                sel_rect[1] = (24-sel_end_pos[1]+top_mult+cur_offset) * nh
                sel_rect[3] = (sel_end_pos[1]-sel_start_pos[1]) * nh
            sel_rect[2] += nw
            sel_rect[3] += nh

            pygame.draw.rect(screen, "#ef7d57", sel_rect, int(nw/4))
        elif top_height-nh < mouse_y < top_height:
            play_pos = int(mouse_x/nw)
            bar_rect = [play_pos*nw, top_height, nw, screen_height-top_height]
            pygame.draw.rect(screen, "#ffcd75", bar_rect)

        if len(sel_notes) > 0 and not ctrl and sel_move:
            # moveable = False
            # for sel_note in sel_notes:
            #     if note_to_rect(sel_note).collidepoint(mouse_x, mouse_y):
            #         moveable = True
            # # print(sel_notes)
            # print(moveable)
            move(sel_notes)
            hold_note = None
            # if int(move_x/nw) != int(mouse_x/nw):
            #     dir = sign(mouse_x-move_x)
            #     moveable = True
            #     for sel_note in sel_notes:
            #         # print(sel_note["pos"])
            #         if not(32 > sel_note["pos"] + dir >= 0):
            #             moveable = False
            #             break
            #     if moveable:
            #         for sel_note in sel_notes:
            #             sel_note["pos"] += dir
            #     move_x = mouse_x
            # if int(move_y/nw) != int(mouse_y/nw):
            #     dir = sign(mouse_y-move_y)
            #     moveable = True
            #     for sel_note in sel_notes:
            #         if not(48 > sel_note["pitch"] - dir >= 0):
            #             moveable = False
            #             break
            #     if moveable:
            #         for sel_note in sel_notes:
            #             sel_note["pitch"] -= dir
            #     move_y = mouse_y
            
        elif hold_note != None:
            # pygame.draw.circle(screen, "#000000", [mouse_x, mouse_y], 10)
            # pygame.draw.circle(screen, "#000000", [move_x, move_y], 10)
            move(one_note=hold_note)
            sel_notes = []
                
    else:
        sel_rect = [0, 0, 0, 0]
    
    if ctrl and keys[pygame.K_a]:
        sel_rect = [0, -24*nh+top_height, 32*nw, 48*nh]
        pygame.draw.rect(screen, "#ef7d57", sel_rect, int(nw/4))

    if pygame.mouse.get_pressed()[2]:
        if mouse_y > top_height:
            can_place, remove_note = can_place_check(mouse_x, mouse_y)
            if not can_place:
                if remove_note != None:
                    patterns[str(cur_pattern)].remove(remove_note)

    if cur_pattern < len(patterns):
        render_notes = []
        for note in patterns[str(cur_pattern)]:
            note_rect = note_to_rect(note)
            if note["inst"] == cur_inst:
                render_notes.append(note)
            else:
                pygame.draw.rect(screen, "#566c86", note_rect)

        for note in render_notes:
            note_rect = note_to_rect(note)
            if note_rect.colliderect(sel_rect):
                if note not in sel_notes:
                    sel_notes.append(note)

            if note in sel_notes:
                pygame.draw.rect(screen, "#ef7d57", note_rect)
            else:
                pygame.draw.rect(screen, "#a7f070", note_rect)
        # print(sel_notes)

    pygame.draw.rect(screen, "#566c86", (0, 0, screen_width, top_height))

    mouse_x, mouse_y = pygame.mouse.get_pos()
    if mouse_y > top_height:
        hover_y = int(mouse_y/nh)*nh+40
        if hover_y+40 > screen_height:
            hover_y = int(mouse_y/nh)*nh-40
        draw_text(f"{note_names[24-int((mouse_y-top_height)/nh)+cur_offset-1]}", int(mouse_x/nw)*nw+40, hover_y)
        # draw_text(f"{int(mouse_x/nw)}:{note_names[24-int((mouse_y-top_height)/nh)+cur_offset-1]}", int(mouse_x/nw)*nw+40, hover_y)
        mouse_rect = [int(mouse_x/nw) * nw, int(mouse_y/nh) * nh, nw, nh]
        pygame.draw.rect(screen, "#94b0c2", mouse_rect)

    #4초 = 32칸
    if playing:
        bar_pos = int((pygame.time.get_ticks() - play_time)/(4+1)*32/screen_width * (bpm/60)/2)
        bar_rect = [bar_pos*screen_width/32, top_height, nw, screen_height-top_height]
        pygame.draw.rect(screen, "#ffcd75", bar_rect)
        if old_bar_pos != bar_pos:
            for i, note in enumerate(patterns[str(cur_pattern)]):
                if note["pos"] == int(bar_pos):
                    play(note)
            old_bar_pos = bar_pos
            if metronome:
                if bar_pos != 32:
                    if bar_pos % 16 == 0:
                        metronome_sounds[0].play()
                    elif bar_pos % 4 == 0:
                        metronome_sounds[1].play()

        if bar_pos >= 32:
            next_pattern = False
            for i in range(len(patterns)):
                if i > cur_pattern:
                    if patterns[str(i)] != []:
                        next_pattern = True
            if next_pattern:
                cur_pattern += 1
            else:
                cur_pattern = 0
            play_time = pygame.time.get_ticks()

    pygame.draw.rect(screen, "#ef7d57", [play_pos*nw, top_height-nh, nw, nh])

    draw_text(f"MINU STUDIO", 20, 20, color="#a7f070", font=fontb)
    draw_text(f"INST: {cur_inst+1}", 20, 50)
    draw_text(f"BPM: {bpm}", 120, 50)

    if metronome:
        draw_text("MET: O", screen_width-250, 20)
    else:
        draw_text("MET: -", screen_width-250, 20)
    if met_rect.collidepoint((mouse_x, mouse_y)):
        pygame.draw.rect(screen, "#333c57", met_rect, 5)

    draw_text(f"PAT: {cur_pattern}", screen_width-140, 20)
    if pat_rect.collidepoint((mouse_x, mouse_y)):
        pygame.draw.rect(screen, "#333c57", pat_rect, 5)
    # draw_text(f"OCT: {cur_octave}", screen_width-250, 20)

    # draw_text(f"{int(mouse_x)} {int(mouse_y)}", 200, 200)

    # print(ctrl, sel_notes)

    if old_pattern != cur_pattern:
        old_pattern = cur_pattern
        sel_notes = []

    pygame.display.update()
    clock.tick(60)