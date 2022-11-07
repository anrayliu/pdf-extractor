'''
Anray Liu (high school co op student)
Nov 2 2022
User interface for pdf extractor
'''

import pygame
import tkinter
import sys
import math
from types import SimpleNamespace as Ns
from threading import Thread
from tkinter import filedialog
import pdf_extractor
import os

pygame.init()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
MEDIUM_COLOUR = (255, 179, 71)
DARK_COLOUR = (253, 88, 0)
LIGHT_COLOUR = (255, 213, 128)
FONT_COLOUR = WHITE
SLIDER_COLOUR = WHITE
arial = pygame.font.SysFont("arial", 25)


class EventHandler:
    def __init__(self):
        self.update()

    def update(self):
        self.quit = False
        self.click = False
        self.key = None
        self.key_name = None
        self.drop_file = None
        self.resize = None
        self.scroll = 0
        self.mouse_up = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit = True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.click = True
            elif event.type == pygame.KEYDOWN:
                self.key = event.unicode
                self.key_name = pygame.key.name(event.key)
            elif event.type == pygame.VIDEORESIZE:
                self.resize = (event.w, event.h)
            elif event.type == pygame.DROPFILE:
                self.drop_file = event.file
            elif event.type == pygame.MOUSEWHEEL:
                self.scroll = event.y
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.mouse_up = True

        self.mouse = pygame.mouse.get_pos()
        self.mouse_down = pygame.mouse.get_pressed()[0]
        self.key_down = pygame.key.get_pressed()

def save(path, fields):
    with open(path, "w") as file:
        for f in fields:
            if f == "":
                continue
            file.write(f + "\n")

def load(path):
    fields = []
    with open(path, "r") as file:
        for line in file.readlines():
            fields.append(line.strip("\n"))
    return fields

class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.pos = self.rect.topleft
        self.text = text
        
        self.hover = False
        self.click = False

    def update(self, events):
        self.hover = self.click = False
        
        if self.rect.collidepoint(events.mouse):
            self.hover = True
            if events.click:
                self.click = True

    def draw(self, win):
        draw_round_rect(win, MEDIUM_COLOUR, self.rect, 30)
        if self.hover:
            pygame.draw.rect(win, DARK_COLOUR, self.rect, 5)
        text_surf = arial.render(self.text, True, FONT_COLOUR)
        win.blit(text_surf, text_surf.get_rect(center=self.rect.center).topleft)
        
class BackButton:
    def __init__(self, pos, size):
        self.big_points = [(pos[0] + math.cos(math.radians(315 - i * 135)) * size, pos[1] + math.sin(math.radians(315 - i * 135)) * size) for i in range(3)]
        self.small_points = [(pos[0] + math.cos(math.radians(315 - i * 135)) * size * 0.7, pos[1] + math.sin(math.radians(315 - i * 135)) * size * 0.7) for i in range(3)]
        self.points = self.big_points
        self.size = size
        self.pos = pos

        self.click = False
         
    def update(self, events):
        self.click = False
        
        self.points = self.big_points
        if math.dist(events.mouse, self.pos) < self.size:
            if events.mouse_down:
                self.points = self.small_points
            elif events.mouse_up:
                self.click = True

    def draw(self, win):
        for i in range(3):
            pygame.draw.line(win, WHITE, self.points[i], self.points[0] if i == 2 else self.points[i + 1], 3)

class Slider:
    def __init__(self, win):
        self.dragging = False
        self.win = win
        self.value = 0

        self.configure_points(False)

    def configure_points(self, configured_before=True):
        win_size = self.win.get_size()

        if configured_before:
            percent = (self.circle_pos[1] - self.start) / (self.end - self.start)
        else:
            percent = 0

        self.x = win_size[0] - 50
        self.start = 50
        self.end = win_size[1] - 50

        self.circle_pos = (self.x, self.start + percent * (self.end - self.start))

        surf = pygame.Surface((1, 10))
        surf.fill(SLIDER_COLOUR)
        pygame.draw.rect(surf, MEDIUM_COLOUR, (0, 0, 1, 1))
        pygame.draw.rect(surf, MEDIUM_COLOUR, (0, 9, 1, 1))
        self.line = pygame.transform.smoothscale(surf, (3, self.end - self.start))

    def update(self, events):
        if self.dragging:
            self.circle_pos = (self.x, min(max(events.mouse[1], self.start), self.end))
            self.value = (self.circle_pos[1] - self.start) / (self.end - self.start)
            
            if not events.mouse_down:
                self.dragging = False

        elif math.dist(self.circle_pos, events.mouse) <= 15 and events.click:
            self.dragging = True
            
        elif events.scroll != 0:
            self.circle_pos = (self.x, min(max(self.circle_pos[1] + events.scroll * -10, self.start), self.end))
            self.value = (self.circle_pos[1] - self.start) / (self.end - self.start)

    def draw(self):
        self.win.blit(self.line, (self.x, self.start))
        
        pygame.draw.circle(self.win, SLIDER_COLOUR, self.circle_pos, 15)
        pygame.draw.circle(self.win, MEDIUM_COLOUR, self.circle_pos, 12)            
        
def draw_round_rect(surface, colour, rect, r):
    x, y, w, h = rect

    pygame.draw.ellipse(surface, colour,(x,y,r,r))
    pygame.draw.ellipse(surface, colour,(x+w-r,y,r,r))
    pygame.draw.ellipse(surface, colour,(x,y+h-r,r,r))
    pygame.draw.ellipse(surface, colour,(x+w-r,y+h-r,r,r))

    pygame.draw.rect(surface, colour,(x+r/2,y,w-r,r))
    pygame.draw.rect(surface, colour,(x+r/2,y+h-r/2-r/2,w-r,r))
    pygame.draw.rect(surface, colour,(x,y+r/2,r,h-r))
    pygame.draw.rect(surface, colour,(x+w-r,y+r/2,r,h-r))

    pygame.draw.rect(surface, colour,(x+r,y+r,w-r*2,h-r*2))

class PathsLocation:
    def __init__(self, main):
        self.win = main.win
        self.events = main.events
        self.main = main

        self.back_button = BackButton((50, 50), 25)

        self.in_txt_surf = arial.render("In:  ", True, BLACK)
        self.out_txt_surf = arial.render("Out: ", True, BLACK)

        self.in_surf = arial.render("Select Path", True, FONT_COLOUR)
        self.out_surf = self.in_surf.copy()

        self.in_rect = pygame.Rect(120 + self.in_txt_surf.get_width(), 100 - self.in_txt_surf.get_height() / 2, self.in_surf.get_width() + 50, 60)
        self.out_rect = self.in_rect.move(0, 80)

        self.ok_button = Button((self.win.get_width() - 100, self.win.get_height() - 100, 80, 80), "OK")

        self.in_path = ""
        self.out_path = ""
        self.have_both_paths = False
        
    def update(self):
        self.back_button.update(self.events)
        if self.back_button.click:
            self.main.location = "fields"

        if self.events.click:
            if self.in_rect.collidepoint(self.events.mouse):
                self.in_path = filedialog.askdirectory()
                self.in_surf = arial.render(self.in_path, True, FONT_COLOUR)
                self.main.locations["done"].input_path = self.in_path
                self.in_rect.w = self.in_surf.get_width() + 50
                self.have_both_paths = os.path.exists(self.in_path) and os.path.exists(os.path.dirname(self.out_path))

            elif self.out_rect.collidepoint(self.events.mouse):
                self.out_path = filedialog.asksaveasfilename()
                if self.out_path != "" and not self.out_path.endswith(".csv"):
                    self.out_path += ".csv"
                self.out_surf = arial.render(self.out_path, True, FONT_COLOUR)
                self.main.locations["done"].output_path = self.out_path
                self.out_rect.w = self.out_surf.get_width() + 50
                self.have_both_paths = os.path.exists(self.in_path) and os.path.exists(os.path.dirname(self.out_path))

        if self.have_both_paths:
            self.ok_button.update(self.events)
            if self.ok_button.click:
                self.main.locations["done"].output_path = self.out_path
                self.main.locations["done"].input_path = self.in_path
                self.main.location = "done"

    def draw(self):
        self.win.fill(MEDIUM_COLOUR)

        self.back_button.draw(self.win)

        self.win.blit(self.in_txt_surf, (100, 100))
        draw_round_rect(self.win, DARK_COLOUR, self.in_rect, 30)
        self.win.blit(self.in_surf, self.in_surf.get_rect(center=self.in_rect.center).topleft)

        self.win.blit(self.out_txt_surf, (100, 180))
        draw_round_rect(self.win, DARK_COLOUR, self.out_rect, 30)
        self.win.blit(self.out_surf, self.out_surf.get_rect(center=self.out_rect.center).topleft)

        if self.have_both_paths:
            self.ok_button.draw(self.win)

class DoneLocation:
    def __init__(self, main):
        self.win = main.win
        self.events = main.events

        self.ran = False
        self.ns = Ns(percent=0, request_stop=False, stopped=False)

        self.input_path = None
        self.output_path = None

    def update(self):
        if not self.ran:
            self.ran = True
            thread = Thread(target=self.threaded_extract)
            thread.start()

    def draw(self):
        self.win.fill(MEDIUM_COLOUR)
        
        w, h = self.win.get_size()
        center = (round(w / 2), round(h / 2))
        
        pygame.draw.circle(self.win, LIGHT_COLOUR, center, 100)
        
        for i in range(round(360 * self.ns.percent)):
            angle = math.radians(i - 90)
            pygame.draw.circle(self.win, DARK_COLOUR, (w / 2 + math.cos(angle) * 80, h / 2 + math.sin(angle) * 80), 10)
            
        text = arial.render(str(round(self.ns.percent * 100)) + "%", True, BLACK)
        self.win.blit(text, text.get_rect(center=center).topleft)

    def threaded_extract(self):
        pdf_extractor.create_csv(self.input_path, self.output_path, self.fields, self.ns)
        
        if not self.ns.stopped:
            os.startfile(self.output_path)
        
        self.ns.stopped = True

class Toolbar:
    def __init__(self, loc):
        self.events = loc.events
        self.win = loc.win

        self.size = 0
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.open = True
        self.action = None

        self.buttons = [Button((20, 20, 80, 80), "+"),
                        Button((20, 120, 80, 80), "done"),
                        Button((20, 220, 80, 80), "clear"),
                        Button((20, 320, 80, 35), "save"),
                        Button((20, 365, 80, 35), "load")]

    def update(self):
        w, h = self.win.get_size()
        
        self.size += (120 * self.open - self.size) / 10
        self.rect.size = (self.size, h)
        if self.events.click and self.events.mouse[0] > self.size and math.dist(self.events.mouse, (self.size, 40)) < 40:
            self.open = 1 - self.open
            self.events.click = False

        for button in self.buttons:
            button.rect.x = -120 + self.size + button.pos[0]
            button.update(self.events)
            if button.click:
                self.action = button.text

    def draw(self):
        pygame.draw.rect(self.win, LIGHT_COLOUR, self.rect)
        pygame.draw.circle(self.win, LIGHT_COLOUR, (self.size, 40), 40)

        for button in self.buttons:
            button.draw(self.win)

class FieldsLocation:
    def __init__(self, main):
        self.win = main.win
        self.events = main.events

        self.field_bubbles = []

        self.selected_field = None
        self.dragging_field = None
        self.mouse_save = None
        self.hovered_field = None

        self.slider = Slider(self.win)

        self.shadow_size = (0, 0)
        self.shadow = pygame.Surface((0, 0), pygame.SRCALPHA)
        self.shadow.set_alpha(50)

        self.need_slider = True
        self.toolbar = Toolbar(self)

        self.main = main

    def update(self):
        self.need_slider = 50 + len(self.field_bubbles) * 60 > self.win.get_height()
        if self.need_slider:
            self.slider.update(self.events)
        else:
            self.slider.value = 0

        self.toolbar.update()
        
        if self.selected_field == None:
            if self.events.key_name == "return":
                self.toolbar.action = "+"
            elif self.events.key_name == "tab":
                self.toolbar.open = not self.toolbar.open

        click_none = True
        for i, field in enumerate(self.field_bubbles):
            if field.rect.collidepoint(self.events.mouse) and self.events.click:
                click_none = False
                
                self.hovered_field = field
                
                if self.selected_field == field:
                    self.selected_field = None
                else:
                    self.selected_field = field

                self.mouse_save = self.events.mouse
                    
            field.update(self.slider.value * (60 * len(self.field_bubbles) + 90 - self.win.get_height()))
            if field.delete:
                del self.field_bubbles[i]
                for o, field2 in enumerate(self.field_bubbles):
                    field2.y = 50 + o * 60
                    self.slider.configure_points()
        if click_none and self.events.click:
            self.selected_field = None

        if self.events.mouse_down:
            if self.mouse_save != None and self.mouse_save != self.events.mouse:
                self.dragging_field = self.hovered_field
                self.selected_field = None

                if self.shadow_size != self.dragging_field.rect.size:
                    self.shadow_size = self.dragging_field.rect.size
                    self.shadow.fill((0, 0, 0, 0))
                    self.shadow = pygame.transform.scale(self.shadow, self.shadow_size)
                    draw_round_rect(self.shadow, BLACK, (0, 0, *self.shadow_size), 30)
        else:
            self.mouse_save = None
            if self.dragging_field != None:
                for i, field in enumerate(self.field_bubbles):
                    if field != self.dragging_field and field.rect.collidepoint(self.events.mouse):
                        self.field_bubbles.insert(i, self.field_bubbles.pop(self.field_bubbles.index(self.dragging_field)))
                        break
                for i, field in enumerate(self.field_bubbles):
                    field.y = 50 + i * 60
                    
                self.selected_field = self.dragging_field
                self.dragging_field = None
                self.selected_field.rect.x = 150
        
        if self.toolbar.action == "+":
            self.field_bubbles.append(FieldBubble(self, (150, 50 + len(self.field_bubbles) * 60, 0, 50), ""))
            self.slider.circle_pos = (self.slider.x, self.slider.end)
            self.slider.value = 1
            self.slider.configure_points()
            self.selected_field = self.field_bubbles[-1]
        elif self.toolbar.action == "done":
            self.main.location = "done"
            self.main.locations["done"].fields = [f.text for f in self.field_bubbles]
            self.main.locations["done"].input_path = "pdfs"
            self.main.locations["done"].output_path = "output.csv"
        elif self.toolbar.action == "clear":
            self.field_bubbles = []
            self.slider.configure_points(False)
        elif self.toolbar.action == "save":
            file = filedialog.asksaveasfilename()
            if file != "":
                if not file.endswith(".txt"):
                    file += ".txt"
                save(file, [f.text for f in self.field_bubbles])
        elif self.toolbar.action == "load":
            file = filedialog.askopenfilename()
            if file != "" and file.endswith(".txt"):
                fields = load(file)
                self.field_bubbles = [FieldBubble(self, (0, 50 + i * 60, 0, 50), field) for i, field in enumerate(fields)]
                self.slider.configure_points(False)
        self.toolbar.action = None
            
        
    def draw(self):
        self.win.fill(MEDIUM_COLOUR)
        
        h = self.win.get_height()
        for field in self.field_bubbles:
            if field != self.dragging_field and field.rect.top < h and field.rect.bottom > 0:
                field.draw()

        if self.need_slider:
            self.slider.draw()
        
        if self.dragging_field != None:
            self.win.blit(self.shadow, (self.events.mouse[0] - self.dragging_field.rect.w / 2 + 30, self.events.mouse[1]))
            self.dragging_field.draw()

        self.toolbar.draw()

class FieldBubble:
    def __init__(self, loc, rect, text):
        self.win = loc.win
        self.events = loc.events
        self.loc = loc

        self.rect = pygame.Rect(rect)
        self.y = self.rect.y
        self.x = self.rect.x
        
        self.text = text
        self.text_surf = pygame.Surface((0, 0))
        self.backspace_timer = 0

        self.flash_timer = 0
        self.delete_r = 0
        self.delete_pos = (0, 0)
        self.delete = False

        self.x_surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        pygame.draw.line(self.x_surf, WHITE, (0, 0), (50, 50), 8)
        pygame.draw.line(self.x_surf, WHITE, (0, 50), (50, 0), 8)

    def update(self, scrolly):
        self.text_surf = arial.render(self.text, True, FONT_COLOUR)
        self.rect.w = self.text_surf.get_width() + 30

        self.x += (150 + (self.loc.selected_field == self) * 100 - self.x) / 10
        self.rect.x = self.x
        self.rect.y = self.y - scrolly

        if self == self.loc.selected_field:
            if self.events.key != None:
                if self.events.key_name == "backspace":
                    self.text = self.text[:-1]
                elif self.events.key_name == "return":
                    self.loc.selected_field = None
                elif pygame.key.get_mods() & pygame.KMOD_CTRL:
                    if self.events.key_name == "v":
                        r = tkinter.Tk()
                        try:
                            self.text += r.clipboard_get()
                        except tkinter.TclError:
                            pass
                        r.withdraw()
                        r.update()
                        r.destroy()
                else:
                    self.text += self.events.key

            if self.events.key_down[pygame.K_BACKSPACE]:
                self.backspace_timer += 1
                if self.backspace_timer > 45 and self.backspace_timer % 2 == 0:
                    self.text = self.text[:-1]
            else:
                self.backspace_timer = 0

        self.delete_pos = (self.rect.right + 50, self.rect.centery)
        self.delete_r = (100 - (250 - self.rect.x)) / 100 * 25
        if self.delete_r != 0 and math.dist(self.delete_pos, self.events.mouse) < self.delete_r and self.events.click:
            self.delete = True

    def draw(self):
        rect = pygame.Rect(self.events.mouse, self.rect.size).move(self.rect.w / -2, self.rect.h / -2) if self.loc.dragging_field == self else self.rect
        draw_round_rect(self.win, DARK_COLOUR, rect, 30)
        text_rect = self.text_surf.get_rect(center=rect.center)
        self.win.blit(self.text_surf, text_rect.topleft)

        if self == self.loc.selected_field:
            self.flash_timer += 0.04
            if int(self.flash_timer) % 2 == 0:
                pygame.draw.rect(self.win, WHITE, (self.rect.right - 15, text_rect.y, 2, text_rect.h))

        pygame.draw.circle(self.win, DARK_COLOUR, self.delete_pos, self.delete_r)
        if self.delete_r > 3:
            surf = pygame.transform.smoothscale(self.x_surf, (self.delete_r * 0.8, self.delete_r * 0.8))
            self.win.blit(surf, surf.get_rect(center=self.delete_pos).topleft)

class Main:
    def __init__(self):
        self.win = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
        self.events = EventHandler()
        self.clock = pygame.time.Clock()
        pygame.display.set_caption("PDF extractor")

        self.locations = {"paths":PathsLocation(self),
                          "done":DoneLocation(self),
                          "fields":FieldsLocation(self)}
        self.location = "fields"

        self.quit_queued = False

    def run(self):
        while True:
            self.events.update()
            if self.events.quit:
                if not self.quit_queued:
                    self.quit_queued = True
            if self.events.resize != None:
                self.events.resize = (max(self.events.resize[0], 200), max(self.events.resize[1], 200))
                pygame.display.set_mode(self.events.resize, pygame.RESIZABLE)
                self.locations["fields"].slider.configure_points()
                self.locations["paths"].ok_button.rect.topleft = (self.win.get_width() - 100, self.win.get_height() - 100)

            if self.quit_queued:
                if self.locations["done"].ran:
                    if self.locations["done"].ns.stopped:
                        pygame.quit()
                        sys.exit()
                    else:
                        self.locations["done"].ns.request_stop = True
                else:
                    pygame.quit()
                    sys.exit()
                    
                
            self.clock.tick(60)

            loc = self.locations[self.location]
            loc.update()
            loc.draw()

            #self.win.blit(arial.render(str(round(self.clock.get_fps())), False, BLACK), (0, 0))
            pygame.display.update()


if __name__ == "__main__": 
    Main().run()
