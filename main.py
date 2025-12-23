import tkinter as tk
from tkinter import messagebox
import csv
import os
from datetime import datetime
import webbrowser
from PIL import Image, ImageTk
import imageio

class WorkoutApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Workout Partner")
        self.root.geometry("600x800")

        self.break_time = 120

        self.current_day = "" # Track which file to update
        self.current_exercises = []
        self.current_idx = 0
        self.current_set = 1
        self.time_left = 0
        self.is_paused = False
        self.is_break = False
        self.timer_running = None
        
        self.video_reader = None
        self.video_stream = None

        self.routine_file_name = ""

        self.setup_main_menu()

    def setup_main_menu(self):
        self.clear_screen()
        self.stop_video()
        tk.Label(self.root, text="Select Training Day", font=("Arial", 18, "bold")).pack(pady=20)
        
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in days:
            tk.Button(self.root, text=day, width=20, command=lambda d=day: self.load_day(d)).pack(pady=5)

    def load_day(self, day):
        self.current_day = day
        self.routine_file_name = f"days/{day}.csv"
        if not os.path.exists(self.routine_file_name):
            messagebox.showerror("Error", f"File {self.routine_file_name} not found!")
            return

        self.current_exercises = []
        with open(self.routine_file_name, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.current_exercises.append(dict(row))
        self.show_exercise_list(day)

    def show_exercise_list(self, day):
        self.clear_screen()
        tk.Label(self.root, text=f"{day} Routine", font=("Arial", 16, "bold")).pack(pady=10)
        
        for ex in self.current_exercises:
            tk.Label(self.root, text=f"{ex['exercise']} - {ex['weight']} | {ex['sets']} sets").pack()

        tk.Button(self.root, text="START WORKOUT", bg="green", fg="black", 
                  command=self.start_workout, font=("Arial", 12, "bold")).pack(pady=20)
        tk.Button(self.root, text="Back", command=self.setup_main_menu).pack()

    def start_workout(self):
        self.current_idx = 0
        self.current_set = 1
        self.is_break = False
        self.setup_timer_screen()

    def setup_timer_screen(self):
        self.clear_screen()
        self.stop_video()
        ex = self.current_exercises[self.current_idx]
        
        self.status_label = tk.Label(self.root, text="", font=("Arial", 14, "italic"))
        self.status_label.pack(pady=5)
        
        self.main_title = tk.Label(self.root, text=ex['exercise'], font=("Arial", 22, "bold"))
        self.main_title.pack()
        
        # Editable Weight
        self.weight_frame = tk.Frame(self.root)
        self.weight_frame.pack(pady=5)
        tk.Label(self.weight_frame, text="Weight:", font=("Arial", 12)).pack(side=tk.LEFT)
        self.weight_entry = tk.Entry(self.weight_frame, font=("Arial", 12, "bold"), width=8, justify='center')
        self.weight_entry.insert(0, ex['weight'])
        self.weight_entry.pack(side=tk.LEFT, padx=5)

        # Media Handling
        self.media_label = tk.Label(self.root, bg="black")
        self.media_label.pack(pady=10)
        self.handle_media(f"media/{ex['image']}")

        self.timer_label = tk.Label(self.root, text="00:00", font=("Arial", 60, "bold"))
        self.timer_label.pack(pady=10)

        self.set_label = tk.Label(self.root, text=f"Set {self.current_set} of {ex['sets']}", font=("Arial", 12))
        self.set_label.pack()

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        self.pause_btn = tk.Button(btn_frame, text="Pause", width=10, command=self.toggle_pause)
        self.pause_btn.grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Skip", width=10, bg="#ffcccb", command=self.skip_current).grid(row=0, column=1, padx=5)

        self.next_timer_phase()

    def handle_media(self, path):
        # Clear previous YouTube buttons if they exist
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Button) and widget.cget("text") == "Open YouTube Video":
                widget.destroy()

        if "youtube.com" in path or "youtu.be" in path:
            self.media_label.config(image='', text="YouTube Exercise", fg="white", width=30, height=5)
            tk.Button(self.root, text="Open YouTube Video", bg="red", fg="black",
                      command=lambda: webbrowser.open(path)).pack()
            return

        if not os.path.exists(path):
            self.media_label.config(image='', text="No Image/Video Found", fg="white", width=30, height=10)
            return

        ext = os.path.splitext(path)[1].lower()
        if ext in ['.mp4', '.avi', '.mov']:
            self.play_video(path)
        else:
            img = Image.open(path)
            img.thumbnail((400, 300))
            self.photo = ImageTk.PhotoImage(img)
            self.media_label.config(image=self.photo)

    def play_video(self, filename):
        try:
            self.video_reader = imageio.get_reader(filename)
            self.video_stream = self.video_reader.iter_data()
            self.animate_video()
        except Exception:
            self.media_label.config(text="Video Error")

    def animate_video(self):
        if self.video_stream and not self.is_paused:
            try:
                frame = next(self.video_stream)
                img = Image.fromarray(frame)
                img.thumbnail((400, 300))
                self.photo = ImageTk.PhotoImage(img)
                self.media_label.config(image=self.photo)
                self.video_loop = self.root.after(33, self.animate_video)
            except StopIteration:
                self.play_video(self.current_exercises[self.current_idx]['image'])
        elif self.is_paused:
            self.video_loop = self.root.after(100, self.animate_video)

    def stop_video(self):
        if hasattr(self, 'video_loop'): self.root.after_cancel(self.video_loop)
        if self.video_reader:
            self.video_reader.close()
            self.video_reader = None

    def save_current_weight(self):
        if hasattr(self, 'weight_entry'):
            new_weight = self.weight_entry.get()
            self.current_exercises[self.current_idx]['weight'] = new_weight

    def next_timer_phase(self):
        ex = self.current_exercises[self.current_idx]
        if self.is_break:
            self.status_label.config(text="REST", fg="blue")
            self.time_left = self.break_time
            # self.weight_entry.config(state='disabled')
        else:
            self.status_label.config(text="WORK", fg="green")
            self.time_left = int(ex['duration'])
            # self.weight_entry.config(state='normal')
        self.update_timer()

    def update_timer(self):
        if self.time_left >= 0 and not self.is_paused:
            mins, secs = divmod(self.time_left, 60)
            self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
            
            # --- NEW FEATURE: Show Next Exercise after 30 seconds of break ---
            if self.is_break and self.time_left == int(self.break_time * 0.75): # 120 - 30 = 90 seconds left
                self.show_preview()

            self.time_left -= 1
            self.timer_running = self.root.after(1000, self.update_timer)
        elif self.is_paused:
            self.timer_running = self.root.after(1000, self.update_timer)
        else:
            self.handle_transition()

    def show_preview(self):
        """Updates the UI during a break to show what is coming next."""
        # Check if next thing is another set of same exercise or a new exercise
        ex = self.current_exercises[self.current_idx]
        if self.current_set < int(ex['sets']):
            next_text = f"UP NEXT: {ex['exercise']} (Set {self.current_set + 1})"
            next_img = ex['image']
        elif self.current_idx + 1 < len(self.current_exercises):
            next_ex = self.current_exercises[self.current_idx + 1]
            next_text = f"UP NEXT: {next_ex['exercise']} (Set 1)"
            next_img = next_ex['image']
        else:
            next_text = "FINISHING WORKOUT!"
            next_img = ""

        self.status_label.config(text=next_text, fg="purple")
        if next_img:
            self.handle_media(next_img)

    def skip_current(self):
        if self.timer_running: self.root.after_cancel(self.timer_running)
        self.handle_transition()

    def handle_transition(self):
        # if not self.is_break:
        self.save_current_weight()
        
        ex = self.current_exercises[self.current_idx]
        if not self.is_break:
            # if self.current_set < int(ex['sets']):
            self.is_break = True
            self.next_timer_phase()
            # else:
            #     self.move_to_next_exercise()
        else:
            self.is_break = False
            self.current_set += 1
            if self.current_set > int(ex['sets']): # Transitioned via preview to next ex
                self.current_set = 1
                self.move_to_next_exercise()
            self.setup_timer_screen()

    def move_to_next_exercise(self):
        self.current_idx += 1
        if self.current_idx < len(self.current_exercises):
            self.current_set = 1
            self.is_break = False
            self.setup_timer_screen()
        else:
            self.finish_workout()

    def finish_workout(self):
        self.stop_video()
        if messagebox.askyesno("Done!", "Workout Complete! Save progress and update routine files?"):
            self.save_progress()
            self.update_routine_csv()
        self.setup_main_menu()

    def update_routine_csv(self):
        """Overwrites the original Day.csv with the new weights."""
        keys = self.current_exercises[0].keys()
        with open(self.routine_file_name, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictReader(f) # Not used, need DictWriter
            dw = csv.DictWriter(f, fieldnames=keys)
            dw.writeheader()
            dw.writerows(self.current_exercises)
        messagebox.showinfo("Updated", f"{self.current_day} has been updated with new weights.")

    def save_progress(self):
        date_str = datetime.now().strftime("%d.%m.%Y")
        details = [f"{ex['exercise']} ({ex['weight']})" for ex in self.current_exercises]
        summary = " | ".join(details)
        
        file_exists = os.path.isfile("progress.csv")
        with open("progress.csv", "a", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Date", "Workout Details"])
            writer.writerow([date_str, summary])

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.pause_btn.config(text="Resume" if self.is_paused else "Pause")

    def clear_screen(self):
        if self.timer_running: self.root.after_cancel(self.timer_running)
        for widget in self.root.winfo_children(): widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = WorkoutApp(root)
    root.mainloop()