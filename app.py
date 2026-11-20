import random
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
from tkinter import ttk

import database
import word_fetcher
import word_source


SESSION_SIZE = 10
MAX_WORKERS = 4


class LingoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Lingo - Spanish Learning")
        self.root.geometry("720x580")
        self.root.minsize(600, 500)
        self.root.configure(bg="#f4f5f7")

        self.results = queue.Queue()

        self.session_words = []
        self.deferred_words = []
        self.current_word = None

        self.loading = False
        self.practice_mode = False
        self.current_is_deferred = False
        self.session_number = 0
        self.session_finished = False

        self.create_layout()
        self.start_new_session()

        self.root.after(150, self.check_results)

    # ---------- layout ----------
    def create_layout(self):
        header = ttk.Frame(self.root, padding=(25, 20))
        header.pack(fill="x")

        ttk.Label(
            header,
            text="LINGO",
            font=("Segoe UI", 23, "bold")
        ).pack(side="left")

        ttk.Button(
            header,
            text="Learned words",
            command=self.show_learned_words
        ).pack(side="right")

        self.content = ttk.Frame(self.root, padding=(25, 5))
        self.content.pack(fill="both", expand=True)

        self.card = tk.Frame(
            self.content,
            bg="white",
            padx=30,
            pady=25,
            highlightbackground="#e0e2e7",
            highlightthickness=1
        )
        self.card.pack(fill="both", expand=True)

        self.word_label = tk.Label(
            self.card,
            text="",
            font=("Segoe UI", 30, "bold"),
            bg="white",
            fg="#20242c"
        )
        self.word_label.pack(anchor="w")

        self.meaning_label = tk.Label(
            self.card,
            text="",
            font=("Segoe UI", 14),
            bg="white",
            fg="#424957"
        )
        self.meaning_label.pack(anchor="w", pady=(5, 20))

        self.info_label = tk.Label(
            self.card,
            text="",
            font=("Segoe UI", 10),
            bg="white",
            fg="#777f8d"
        )
        self.info_label.pack(anchor="w", pady=(0, 20))

        tk.Label(
            self.card,
            text="EXAMPLE",
            font=("Segoe UI", 9, "bold"),
            bg="white",
            fg="#777f8d"
        ).pack(anchor="w")

        self.example_label = tk.Label(
            self.card,
            text="",
            font=("Segoe UI", 12),
            bg="white",
            fg="#20242c",
            wraplength=580,
            justify="left"
        )
        self.example_label.pack(anchor="w", pady=(5, 15))

        self.translation_label = tk.Label(
            self.card,
            text="",
            font=("Segoe UI", 11, "italic"),
            bg="white",
            fg="#687181",
            wraplength=580,
            justify="left"
        )
        self.translation_label.pack(anchor="w")

        self.status_label = ttk.Label(
            self.content,
            text="",
            anchor="center"
        )
        self.status_label.pack(fill="x", pady=10)

        self.action_buttons = ttk.Frame(self.content)
        self.action_buttons.pack(fill="x", pady=(0, 15))

        self.learn_button = ttk.Button(
            self.action_buttons,
            text="Learned",
            command=self.mark_learned
        )
        self.learn_button.pack(
            side="left", expand=True, fill="x", padx=(0, 5)
        )

        self.later_button = ttk.Button(
            self.action_buttons,
            text="Study later",
            command=self.study_later
        )
        self.later_button.pack(
            side="left", expand=True, fill="x", padx=5
        )

        self.next_button = ttk.Button(
            self.action_buttons,
            text="Another word",
            command=self.show_next_word
        )
        self.next_button.pack(
            side="left", expand=True, fill="x", padx=(5, 0)
        )

        self.end_buttons = ttk.Frame(self.content)

        ttk.Button(
            self.end_buttons,
            text="Close app",
            command=self.root.destroy
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        ttk.Button(
            self.end_buttons,
            text="Practice learned words",
            command=self.start_practice
        ).pack(side="left", expand=True, fill="x", padx=5)

        ttk.Button(
            self.end_buttons,
            text="Try 10 new words",
            command=self.start_new_session
        ).pack(side="left", expand=True, fill="x", padx=(5, 0))

        self.end_buttons.pack_forget()

    # ---------- session lifecycle ----------
    def start_new_session(self):
        self.session_finished = False
        self.session_number += 1

        self.session_words = []
        self.deferred_words = []
        self.current_word = None

        self.loading = True
        self.practice_mode = False
        self.current_is_deferred = False

        self.end_buttons.pack_forget()
        self.action_buttons.pack(fill="x", pady=(0, 15))
        self.set_buttons(False)

        self.word_label.config(text="Loading 10 words...")
        self.meaning_label.config(
            text="Preparing your next Spanish session."
        )
        self.info_label.config(text="")
        self.example_label.config(text="")
        self.translation_label.config(text="")
        self.status_label.config(text="Fetching words...")

        threading.Thread(
            target=self.load_session_words,
            daemon=True
        ).start()

    def load_session_words(self):
        try:
            saved_words = database.get_saved_word_set()
            candidates = word_source.get_word_candidates(saved_words)

            random.shuffle(candidates)

            fetched = 0

            for start in range(0, len(candidates), MAX_WORKERS):
                if fetched >= SESSION_SIZE:
                    break

                batch = candidates[start:start + MAX_WORKERS]

                with ThreadPoolExecutor(
                    max_workers=MAX_WORKERS
                ) as executor:

                    futures = [
                        executor.submit(word_fetcher.fetch_word, word)
                        for word in batch
                    ]

                    for future in as_completed(futures):
                        if fetched >= SESSION_SIZE:
                            break

                        try:
                            data = future.result()
                            if not data.get("meaning"):
                                continue
                            self.results.put(("word", data))
                            fetched += 1
                        except Exception:
                            continue

            self.results.put(("finished", fetched))

        except Exception as error:
            self.results.put(("error", str(error)))

    # ---------- display ----------
    def display_word(self, word, is_deferred=False):
        self.current_word = word
        self.current_is_deferred = is_deferred

        self.word_label.config(text=word.get("word", ""))
        self.meaning_label.config(
            text=word.get("meaning") or "Meaning unavailable"
        )

        details = [
            word.get("part_of_speech") or "Part of speech unavailable",
            word.get("gender") or "Gender unavailable",
            word.get("pronunciation") or "Pronunciation unavailable"
        ]
        self.info_label.config(text="   |   ".join(details))

        self.example_label.config(
            text=word.get("example") or "No example available"
        )
        self.translation_label.config(
            text=word.get("translation") or "No translation available"
        )

        if self.practice_mode:
            self.status_label.config(text="Practicing learned words")
            self.learn_button.config(text="Next")
            self.later_button.config(state="disabled")
        else:
            self.status_label.config(
                text="Study later review" if is_deferred
                else f"New word | {len(self.session_words)} remaining"
            )
            self.learn_button.config(text="Learned")
            self.later_button.config(state="normal")

        self.set_buttons(True)

    # ---------- polling ----------
    def check_results(self):
        try:
            while True:
                kind, value = self.results.get_nowait()

                if kind == "word":
                    self.session_words.append(value)

                elif kind == "finished":
                    self.loading = False
                    self.status_label.config(
                        text=f"{value} words ready for this session."
                    )
                    # If we were waiting on data (no current word),
                    # pull the next one now that loading is done.
                    if self.current_word is None and not self.session_finished:
                        self.show_next_word()

                elif kind == "error":
                    self.loading = False
                    self.word_label.config(text="Could not load words")
                    self.meaning_label.config(text=value)
                    self.status_label.config(
                        text="Check your internet connection."
                    )

        except queue.Empty:
            pass
        except Exception as error:
            # Never let a bad word kill the poll loop.
            print("check_results error:", error)

        finally:
            if self.root.winfo_exists():
                self.root.after(150, self.check_results)

    def show_next_word(self):
        self.current_word = None

        if self.session_words:
            word = self.session_words.pop(0)
            self.display_word(word)
            return

        if self.deferred_words and not self.practice_mode:
            word = self.deferred_words.pop(0)
            self.display_word(word, is_deferred=True)
            return

        if self.loading:
            self.word_label.config(text="Finding words...")
            self.meaning_label.config(
                text="Waiting for the next word."
            )
            self.status_label.config(text="Please wait...")
            self.set_buttons(False)
            return

        self.show_session_end()

    def show_session_end(self):
        self.session_finished = True
        self.current_word = None

        self.word_label.config(text="Session complete")
        self.meaning_label.config(
            text="You've finished this session."
        )
        self.info_label.config(text="")
        self.example_label.config(text="")
        self.translation_label.config(text="")

        self.status_label.config(
            text="What would you like to do next?"
        )

        self.action_buttons.pack_forget()
        self.end_buttons.pack(fill="x", pady=(0, 15))

    def set_buttons(self, enabled):
        state = "normal" if enabled else "disabled"

        self.learn_button.config(state=state)
        self.next_button.config(state=state)

        if not self.practice_mode:
            self.later_button.config(state=state)

    # ---------- actions ----------
    def mark_learned(self):
        if not self.current_word:
            return

        if not self.practice_mode:
            database.save_learned_word(self.current_word)

        self.current_word = None
        self.show_next_word()

    def study_later(self):
        if not self.current_word or self.practice_mode:
            return

        if not self.current_is_deferred:
            self.deferred_words.append(self.current_word)

        self.current_word = None
        self.show_next_word()

    def start_practice(self):
        self.session_finished = False
        words = database.get_learned_words()

        if not words:
            self.word_label.config(text="No learned words yet")
            self.meaning_label.config(
                text="Mark some words as learned first."
            )
            self.status_label.config(text="")
            self.end_buttons.pack_forget()
            self.action_buttons.pack(fill="x", pady=(0, 15))
            self.set_buttons(False)
            return

        random.shuffle(words)

        self.session_words = words
        self.deferred_words = []
        self.current_word = None

        self.practice_mode = True
        self.loading = False

        self.end_buttons.pack_forget()
        self.action_buttons.pack(fill="x", pady=(0, 15))

        self.show_next_word()

    def show_learned_words(self):
        words = database.get_learned_words()

        window = tk.Toplevel(self.root)
        window.title("Learned words")
        window.geometry("650x450")

        if not words:
            ttk.Label(
                window,
                text="You haven't learned any words yet."
            ).pack(pady=30)
            return

        body = ttk.Frame(window, padding=15)
        body.pack(fill="both", expand=True)

        word_list = tk.Listbox(
            body,
            font=("Segoe UI", 11),
            width=22
        )
        word_list.pack(side="left", fill="y")

        details = tk.Text(
            body,
            font=("Segoe UI", 11),
            wrap="word",
            padx=15,
            pady=15
        )
        details.pack(
            side="left", fill="both", expand=True, padx=(12, 0)
        )
        details.config(state="disabled")

        for word in words:
            word_list.insert("end", word.get("word", "?"))

        def select_word(event):
            selection = word_list.curselection()
            if not selection:
                return

            word = words[selection[0]]

            content = (
                f'{word.get("word", "")}\n\n'
                f'Meaning: {word.get("meaning") or "Unavailable"}\n'
                f'Part of speech: {word.get("part_of_speech") or "Unavailable"}\n'
                f'Gender: {word.get("gender") or "Unavailable"}\n'
                f'Pronunciation: {word.get("pronunciation") or "Unavailable"}\n\n'
                f'Example:\n{word.get("example") or "Unavailable"}\n\n'
                f'Translation:\n{word.get("translation") or "Unavailable"}'
            )

            details.config(state="normal")
            details.delete("1.0", "end")
            details.insert("1.0", content)
            details.config(state="disabled")

        word_list.bind("<<ListboxSelect>>", select_word)

        word_list.selection_set(0)
        select_word(None)


if __name__ == "__main__":
    root = tk.Tk()
    app = LingoApp(root)
    root.mainloop()