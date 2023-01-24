# this code is only a user interface for the extractor
# if the extraction is not working, change pdf_extractor.py instead


import pygame
import tkinter   # used for clipboard and file dialog features
import sys, os, math
from threading import Thread
from tkinter import filedialog
from pdf_extractor import create_csv


pygame.init()

# change gui colour scheme here (use RGB values)

MEDIUM_COLOUR = (255, 179, 71)
DARK_COLOUR = (253, 88, 0)
LIGHT_COLOUR = (255, 213, 128)
MISC_COLOUR = (255, 255, 255) # colour for fonts, sliders, etc

font = pygame.font.SysFont("arial", 25)

# handles user events (mouse click, keyboard input, etc)

class EventHandler:
    def __init__(self):
        self.update()

    def update(self):
        self.quit = False
        self.click = False
        self.key = None
        self.key_name = None
        self.resize = None
        self.scroll = 0
        self.drop_file = None
        
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
            elif event.type == pygame.MOUSEWHEEL:
                self.scroll = event.y
            elif event.type == pygame.DROPFILE:
                self.drop_file = event.file

        self.mouse = pygame.mouse.get_pos()
        self.mouse_down = pygame.mouse.get_pressed()[0]
        self.key_down = pygame.key.get_pressed()

# saves fields into a text file

def save_fields(path, fields):
    with open(path, "w") as file:
        for f in fields:
            if f == "":
                continue
            file.write(f + "\n")

# loads fields from a text file

def load_fields(path):
    with open(path, "r") as file:
        return [line.strip("\n") for line in file.readlines()]


class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.pos = self.rect.topleft
        self.text = text
        
        self.hover = False
        self.click = False

        self.border = 0

    def update(self, events):
        self.hover = self.click = False
        
        if self.rect.collidepoint(events.mouse):
            self.hover = True
            if events.click:
                self.click = True

        self.border += (8 * self.hover - self.border) / 5

    def draw(self, win):
        # 15 represents corner roundness at each of the 4 corners

        pygame.draw.rect(win, MEDIUM_COLOUR, self.rect, 0, 15, 15, 15, 15)
        if int(self.border) != 0:
            pygame.draw.rect(win, DARK_COLOUR, self.rect, int(self.border), 15, 15, 15, 15)

        text_surf = font.render(self.text, True, MISC_COLOUR)
        win.blit(text_surf, text_surf.get_rect(center=self.rect.center).topleft)


class Slider:
    def __init__(self, win):
        self.dragging = False
        self.win = win
        self.value = 0

        self.configure_points(False)

    # rescales the slider when screen is resized

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

        self.line = self.make_surf()

    def make_surf(self):
        surf = pygame.Surface((1, 10))
        surf.fill(MEDIUM_COLOUR)
        pygame.draw.line(surf, MISC_COLOUR, (0, 1), (0, 8))
        return pygame.transform.smoothscale(surf, (3, self.end - self.start))

    def update(self, events):
        if self.dragging:
            self.circle_pos = (self.x, min(max(events.mouse[1], self.start), self.end))
            self.value = (self.circle_pos[1] - self.start) / (self.end - self.start)
            
            if not events.mouse_down:
                self.dragging = False

        elif math.dist(self.circle_pos, events.mouse) <= 15 and events.click:
            self.dragging = True
            events.click = False
            
        elif events.scroll != 0:
            self.circle_pos = (self.x, min(max(self.circle_pos[1] + events.scroll * -10, self.start), self.end))
            self.value = (self.circle_pos[1] - self.start) / (self.end - self.start)

    def draw(self):
        self.win.blit(self.line, (self.x, self.start))
        
        pygame.draw.circle(self.win, MISC_COLOUR, self.circle_pos, 15)
        pygame.draw.circle(self.win, MEDIUM_COLOUR, self.circle_pos, 12)


# loading screen shown during extraction

class DoneLocation:
    def __init__(self, main):
        self.win = main.win
        self.events = main.events

        # communicator with actual pdf extractor

        self.running = False
        self.comm = {"percent":0, "stop":False}

        '''
        change input/output paths here
        input - where the pdfs are located
        output - where the spreadsheet will be made (must be a csv file)
        '''
        
        self.input_path = "pdfs"
        self.output_path = "output.csv"

        self.fields = []

    # do not remove method
    
    def update(self):
        pass

    def draw(self):
        w, h = self.win.get_size()
        center = (round(w / 2), round(h / 2))
        
        self.win.fill(MEDIUM_COLOUR)
        
        pygame.draw.circle(self.win, LIGHT_COLOUR, center, 100)
        pygame.draw.circle(self.win, DARK_COLOUR, center, 60, 5)

        # draws loading screen

        for i in range(round(360 * self.comm["percent"])):
            angle = math.radians(i - 90)
            pygame.draw.circle(self.win, DARK_COLOUR, (w / 2 + math.cos(angle) * 80, h / 2 + math.sin(angle) * 80), 10)

        text = font.render(str(round(self.comm["percent"] * 100)) + "%", True, (0, 0, 0))
        self.win.blit(text, text.get_rect(center=center).topleft)

    # runs the pdf extractor in a thread

    def threaded_extract(self):
        self.running = True
        
        create_csv(self.input_path, self.output_path, self.fields, self.comm)

        self.running = False
        
        if self.comm["percent"] == 1.0:
           os.startfile(self.output_path)


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


# menu where fields are edited

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
            if self.events.key_down[pygame.K_UP]:
                self.events.scroll = 0.1
            elif self.events.key_down[pygame.K_DOWN]:
                self.events.scroll = -0.1
            
            self.slider.update(self.events)
        else:
            self.slider.value = 0

        self.toolbar.update()
        
        if self.selected_field == None:
            if self.events.key_name == "return":
                self.toolbar.action = "+"
            elif self.events.key_name == "tab":
                self.toolbar.open = not self.toolbar.open

        h = self.win.get_height()
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
                    
            field.update(self.slider.value * (60 * len(self.field_bubbles) + 90 - h))
            if field.delete:
                if field == self.selected_field:
                    self.selected_field = None
                    
                del self.field_bubbles[i]
                for o, field2 in enumerate(self.field_bubbles):
                    field2.y = 50 + o * 60
                    self.slider.configure_points()
                    
        if click_none and self.events.click:
            self.selected_field = None

        # handles dragging of fields

        if self.events.mouse_down:
            if self.mouse_save != None and self.mouse_save != self.events.mouse:
                self.dragging_field = self.hovered_field
                self.selected_field = None

                if self.shadow_size != self.dragging_field.rect.size:
                    self.shadow_size = self.dragging_field.rect.size
                    self.shadow.fill((0, 0, 0, 0))
                    self.shadow = pygame.transform.scale(self.shadow, self.shadow_size)
                    pygame.draw.rect(self.shadow, (0, 0, 0), (0, 0, *self.shadow_size), 0, 15, 15, 15, 15)
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

        ctrl = pygame.key.get_mods() & pygame.KMOD_CTRL

        # adds a new field
        
        if self.toolbar.action == "+":
            self.field_bubbles.append(FieldBubble(self, (150, 50 + len(self.field_bubbles) * 60, 0, 50), ""))
            self.slider.circle_pos = (self.slider.x, self.slider.end)
            self.slider.value = 1
            self.slider.configure_points()
            self.selected_field = self.field_bubbles[-1]

        # starts extraction
        
        elif self.toolbar.action == "done":
            self.main.location = "done"
            self.main.locations["done"].fields = [f.text for f in self.field_bubbles if f.text.strip("\n") != ""]
            Thread(target=self.main.locations["done"].threaded_extract).start()

        # removes all fields
        
        elif self.toolbar.action == "clear":
            self.field_bubbles = []
            self.slider.configure_points(False)

        # saves fields in a text file
        
        elif self.toolbar.action == "save" or (ctrl and self.events.key_name == "s"):
            file = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=(("Text files", ".txt"), ("All files", "*.*")))
            if file != "":
                save_fields(file, [f.text for f in self.field_bubbles])

        # loads fields from a text file
        
        elif self.toolbar.action == "load" or (ctrl and self.events.key_name == "o"):
            file = filedialog.askopenfilename(filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
            if file != "":
                self.field_bubbles = [FieldBubble(self, (0, 50 + i * 60, 0, 50), field) for i, field in enumerate(load_fields(file))]
                self.slider.value = 0
                self.slider.configure_points(False)
                
        self.toolbar.action = None

        # text files containing fields can be drag and dropped into gui

        if self.events.drop_file != None:
            self.field_bubbles = [FieldBubble(self, (0, 50 + i * 60, 0, 50), field) for i, field in enumerate(load_fields(self.events.drop_file))]
            self.slider.value = 0
            self.slider.configure_points(False)
            
        
    def draw(self):
        self.win.fill(MEDIUM_COLOUR)

        h = self.win.get_height()
        for i, field in enumerate(self.field_bubbles):
            if field.rect.top < h and field.rect.bottom > 0:
                if field != self.dragging_field:
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
        pygame.draw.line(self.x_surf, MISC_COLOUR, (0, 0), (50, 50), 8)
        pygame.draw.line(self.x_surf, MISC_COLOUR, (0, 50), (50, 0), 8)

        self.boostx = 0

        self.highlightw = 0

    def update(self, scrolly):
        # uncomment for "fun" mode
        #self.boostx = abs(self.events.mouse[1] - self.rect.centery)

        # uncomment for an extra visual detail when selecting fields
        #self.highlightw += (self.rect.centerx * (self == self.loc.selected_field) - self.highlightw) / 10
        
        self.text_surf = font.render(self.text, True, MISC_COLOUR)
        self.rect.w = self.text_surf.get_width() + 30

        self.x += (150 + (self.loc.selected_field == self) * 100 + self.boostx - self.x) / 10
        self.rect.x = self.x
        self.rect.y = self.y - scrolly

        if self == self.loc.selected_field:
            if self.events.key != None:
                if self.events.key_name == "backspace":
                    if self.text == "":
                        self.delete = True
                    else:
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
        self.delete_r = (self.rect.x - 150) / 5
        if self.delete_r != 0 and math.dist(self.delete_pos, self.events.mouse) < self.delete_r and self.events.click:
            self.delete = True

    def draw(self):
        pygame.draw.rect(self.win, LIGHT_COLOUR, (0, self.rect.y, self.highlightw, self.rect.h))
        
        rect = pygame.Rect(self.events.mouse, self.rect.size).move(self.rect.w / -2, self.rect.h / -2) if self.loc.dragging_field == self else self.rect
        pygame.draw.rect(self.win, DARK_COLOUR, rect, 0, 15, 15, 15, 15)
        text_rect = self.text_surf.get_rect(center=rect.center)
        self.win.blit(self.text_surf, text_rect.topleft)

        if self == self.loc.selected_field:
            
            self.flash_timer += 0.04
            if int(self.flash_timer) % 2 == 0:
                pygame.draw.rect(self.win, MISC_COLOUR, (self.rect.right - 15, text_rect.y, 2, text_rect.h))

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

        self.locations = {"done":DoneLocation(self),
                          "fields":FieldsLocation(self)}
        self.location = "fields"

        self.quit_queued = False

    def run(self):
        while True:
            self.events.update()
            if self.events.quit:
                self.quit_queued = True
            if self.events.resize != None:
                self.events.resize = (max(self.events.resize[0], 200), max(self.events.resize[1], 200))
                pygame.display.set_mode(self.events.resize, pygame.RESIZABLE)
                self.locations["fields"].slider.configure_points()

            if self.quit_queued:
                if self.locations["done"].running:
                    self.locations["done"].comm["stop"] = True
                else:
                    pygame.quit()
                    sys.exit()
                
            self.clock.tick(60) # do not change fps cap

            loc = self.locations[self.location]
            loc.update()
            loc.draw()

            # uncomment for an fps counter
            #self.win.blit(font.render(str(round(self.clock.get_fps())), False, (0, 0, 0)), (0, 0))
            
            pygame.display.update()


if __name__ == "__main__": 
    Main().run()
