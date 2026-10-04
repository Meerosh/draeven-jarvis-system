"""Private user-entered setup. Never prints or exposes the API key."""
import tkinter as tk
from tkinter import ttk
import threading
from eleven_voice import voices,save_key,VoiceError
root=tk.Tk();root.title('Connect ElevenLabs to Draeven');root.geometry('560x270');root.resizable(False,False)
frame=ttk.Frame(root,padding=22);frame.pack(fill='both',expand=True)
ttk.Label(frame,text='Enter your ElevenLabs API key here, not in chat.',wraplength=510).pack(anchor='w')
ttk.Label(frame,text='Needs Voices read and Text to Speech permission. This check only lists voices; it does not generate paid audio.',wraplength=510).pack(anchor='w',pady=10)
key=tk.StringVar();entry=ttk.Entry(frame,textvariable=key,show='•',width=65);entry.pack(fill='x');entry.focus_set()
status=tk.StringVar(value='The key will be encrypted for your Windows account and kept outside the HUD folder.')
ttk.Label(frame,textvariable=status,wraplength=510).pack(anchor='w',pady=14)
def finish(message):
    status.set(message);button.configure(state='normal')
def save():
    value=key.get().strip()
    if not value:status.set('Please enter your API key.');return
    button.configure(state='disabled');status.set('Checking the key with ElevenLabs…')
    def worker():
        try:
            result=voices(value);save_key(value)
            root.after(0,lambda:key.set(''))
            root.after(0,lambda:finish('Connected. Refresh Draeven, choose ElevenLabs, then choose a voice. Audio plays only when you request it.'))
        except VoiceError as error:
            message=str(error);root.after(0,lambda:finish(message))
        except Exception:root.after(0,lambda:finish('Could not save the connection. Please try again.'))
    threading.Thread(target=worker,daemon=True).start()
button=ttk.Button(frame,text='Verify and save privately',command=save);button.pack(anchor='w')
root.mainloop()
