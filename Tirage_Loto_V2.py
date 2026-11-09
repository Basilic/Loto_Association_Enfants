

import tkinter as tk
from tkinter import Label, Button
import random
from PIL import Image, ImageTk
import pygame

import os
import sys

def get_app_path():
    """
    Retourne le dossier du script en mode Python
    ou le dossier de l'exécutable en mode PyInstaller.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)

    return os.path.dirname(os.path.abspath(__file__))


APP_PATH = get_app_path()


def image_file(number):
    return os.path.join(
        APP_PATH,
        "images",
        f"{number}.jpg"
    )


def sound_file():
    return os.path.join(
        APP_PATH,
        "tirage.mp3"
    )

class ImageApp:
    def __init__(self, range_start=0, range_end=20, history_size=7):   
        pygame.mixer.init()    
        self.range_start = range_start + 1
        self.range_end = range_end
        self.history_size = history_size + 1
        self.reset()

        self.root = tk.Tk()
        self.root.title("Video Projecteur")
        self.root.geometry("1280x720")

        self.main_image_frame = tk.Frame(self.root, width=700, height=720)
        self.main_image_frame.grid(row=0, column=4, padx=5, pady=5)

        self.main_image_label = Label(self.main_image_frame)
        self.main_image_label.grid(row=0, column=2)

        # ----- HISTORIQUE GAUCHE (fenêtre 1) -----
        self.history_frame = tk.Frame(self.main_image_frame, width=200, height=720)
        self.history_frame.grid(row=0, column=0, sticky="nsw")

        self.history_labels = [Label(self.history_frame) for _ in range(self.history_size)]
        for i, label in enumerate(self.history_labels):
            label.grid(row=i, column=0, padx=5, pady=5)


        self.full_history_window = tk.Toplevel(self.root)
        self.full_history_window.title("Ecran de contrôle")
        self.full_history_window.geometry("1920x1080")

        self.full_history_frame = tk.Frame(self.full_history_window)
        self.full_history_frame.pack(fill="both", expand=True)

        # ----- FRAME BOUTONS (ligne fixe) -----
        self.button_frame = tk.Frame(self.full_history_frame)
        self.button_frame.grid(row=0, column=0, sticky="w", pady=10)

        self.new_image_button = Button(
            self.button_frame,
            text="Nouveau Numéro",
            command=self.display_new_image
        )
        self.new_image_button.grid(row=0, column=0, padx=10)

        self.new_game_button = Button(
             self.button_frame,
             text="Nouvelle party",
             command=self.reset_all
        )
        self.new_game_button.grid(row=0, column=1, padx=10)

# Définition fonction tirage automatique
        tk.Label(self.button_frame, text="Intervalle (sec) :").grid(row=0, column=3, padx=10)
        self.interval_entry = tk.Entry(self.button_frame, width=5)
        self.interval_entry.insert(0, "8")  # valeur par défaut
        self.interval_entry.grid(row=0, column=4, padx=10)
        self.toggle_button = tk.Button(
            self.button_frame,
            text="Start",
            command=self.toggle_timer
        )
        self.toggle_button.grid(row=0, column=5, padx=10)

        self.running = False


        # ----- FRAME IMAGES (zone stable) -----
        self.images_frame = tk.Frame(self.full_history_frame)
        self.images_frame.grid(row=1, column=0, sticky="nw")

        self.display_Init()
        #self.display_new_image()

    def play_sound(self):
        try:
            pygame.mixer.music.load(sound_file())
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Erreur son : {e}")


    def toggle_timer(self):
        if not self.running:
            try:
                seconds = float(self.interval_entry.get())
                if seconds <= 0:
                    raise ValueError
            except ValueError:
                print("Intervalle invalide")
                return

            self.interval_ms = int(seconds * 1000)
            self.running = True
            self.toggle_button.config(text="Stop")
            self.run_periodic_action()

        else:
            self.running = False
            self.toggle_button.config(text="Start")

    def run_periodic_action(self):
        if not self.running:
            return

        # ===== ACTION À EXÉCUTER =====
        self.display_new_image()

        # Reprogrammation
        self.root.after(self.interval_ms, self.run_periodic_action)

    def generate_unique_number(self):
        available_numbers = set(range(self.range_start, self.range_end + 1)) - self.generated_numbers
        if not available_numbers:
            raise ValueError("Tous les numéros ont été générés.")
        return random.choice(list(available_numbers))

    def reset(self):
        self.generated_numbers = set()
        self.history = []

    def reset_all(self):
        self.reset()

        # Image principale
        self.main_image_label.config(image="")
        self.main_image_label.image = None

        # Numéro principal
        for widget in self.main_image_frame.grid_slaves(row=0, column=3):
            widget.destroy()

        # Historique gauche (vider seulement le contenu)
        for widget in self.history_frame.winfo_children():
            widget.destroy()

        # Fenêtre 2 : images uniquement
        for widget in self.images_frame.winfo_children():
            widget.destroy()

        self.display_Init()


    def display_Init(self):
        try:
            new_number = 0
            #image_path = f"images/{new_number}.jpg"
            image_path = image_file(new_number)
            try:
                image = Image.open(image_path)
            except FileNotFoundError:
                # Si le fichier n'existe pas, chargez l'image 0.jpg
                #image = Image.open("images/0.jpg")
                image = Image.open(image_file(0))
                
            image_main = image.resize((400, 400), Image.LANCZOS)
            photo_main = ImageTk.PhotoImage(image_main)
            self.main_image_label.config(image=photo_main)
            self.main_image_label.image = photo_main

            # Affichage du numéro associé à l'image principale
            for widget in self.main_image_frame.grid_slaves(row=0, column=3):
                widget.destroy()

            label2 = Label(self.main_image_frame, text=" ", font=("Arial", 80))
            label2.grid(row=0, column=3, padx=5, pady=5)

            for i, num in enumerate(reversed(self.history[:-1])):
                thumb_path = image_file(num)
                try:
                    thumb = Image.open(thumb_path)
                except FileNotFoundError:
                    # Si le fichier n'existe pas, chargez l'image 0.jpg
                    #thumb = Image.open("images/0.jpg")
                    thumb = Image.open(image_file(0))
                    
                thumb = thumb.resize((75, 75), Image.LANCZOS)
                thumb_photo = ImageTk.PhotoImage(thumb)
                label = Label(self.history_frame, image=thumb_photo)
                label.photo = thumb_photo
                label.grid(row=i, column=0, padx=5, pady=5)

                # Affichage du numéro du tirage en dessous de chaque image
                number_label = Label(self.history_frame, text=f"  ", font=("Arial", 90))
                number_label.grid(row=i, column=1, padx=5, pady=5)
                
        except FileNotFoundError:
            print(f"Image {new_number}.jpg not found.")

    def display_new_image(self):
        try:
            # ===== Génération =====
            new_number = self.generate_unique_number()
            self.generated_numbers.add(new_number)

            # ===== Image principale =====
            #image_path = f"images/{new_number}.jpg"
            image_path = image_file(new_number)
            try:
                image = Image.open(image_path)
            except FileNotFoundError:
                #image = Image.open("images/0.jpg")
                image = Image.open(image_file(0))

            image_main = image.resize((600, 600), Image.LANCZOS)
            photo_main = ImageTk.PhotoImage(image_main)

            self.main_image_label.config(image=photo_main)
            self.main_image_label.image = photo_main

            # ===== Numéro principal =====
            # Nettoyage ancien numéro
            for widget in self.main_image_frame.grid_slaves(row=0, column=3):
                widget.destroy()

            number_label = Label(
                self.main_image_frame,
                text=str(new_number),
                font=("Arial", 70)
            )
            number_label.grid(row=0, column=3, padx=5)

            # ===== Historique gauche =====
            if len(self.history) >= self.history_size:
                self.history.pop(0)
            self.history.append(new_number)

            for widget in self.history_frame.winfo_children():
                widget.destroy()

            for i, num in enumerate(reversed(self.history)):
                thumb_path = image_file(num)
                try:
                    thumb = Image.open(thumb_path)
                except FileNotFoundError:
                    #thumb = Image.open("images/0.jpg")
                    thumb = Image.open(image_file(0))
                    
                    thumb = thumb.resize((75, 75), Image.LANCZOS)
                thumb_photo = ImageTk.PhotoImage(thumb)

                img_label = Label(self.history_frame, image=thumb_photo)
                img_label.image = thumb_photo
                img_label.grid(row=i, column=0, padx=5, pady=5)

                num_label = Label(
                    self.history_frame,
                    text=str(num),
                    font=("Arial", 20)
                )
                num_label.grid(row=i, column=1, padx=5)

            # ===== Fenêtre 2 : images =====
            for widget in self.images_frame.winfo_children():
                widget.destroy()

            row = 0
            col = 0
            MAX_COL = 15

            for num in sorted(self.generated_numbers):
                thumb_path = image_file(num)
                try:
                    thumb = Image.open(thumb_path)
                except FileNotFoundError:
                    #thumb = Image.open("images/0.jpg")
                    thumb = Image.open(image_file(0))
                    
                thumb = thumb.resize((75, 75), Image.LANCZOS)
                thumb_photo = ImageTk.PhotoImage(thumb)

                img = Label(self.images_frame, image=thumb_photo)
                img.image = thumb_photo
                img.grid(row=row, column=col, padx=5, pady=5)

                lbl = Label(self.images_frame, text=str(num), font=("Arial", 18))
                lbl.grid(row=row + 1, column=col)

                col += 1
                if col >= MAX_COL:
                    col = 0
                    row += 2

        except Exception as e:
            print("Erreur dans display_new_image :", e)
        
        self.play_sound()
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ImageApp(range_start=0, range_end=90, history_size=8)
    app.run()
