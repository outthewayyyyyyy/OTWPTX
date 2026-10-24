"""OTW PTX: drop a Pro Tools session, get a zip ready to send to a mix engineer."""
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import ptx

APP = 'OTW PTX'

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    root = TkinterDnD.Tk()
except Exception:  # drag & drop unavailable: the button still works
    DND_FILES, root = None, tk.Tk()

root.title(APP)
root.geometry('520x300')
root.minsize(420, 260)

drop = tk.Label(root, text='Drop your Pro Tools session (.ptx) here',
                relief='groove', borderwidth=2, font=('', 15))
drop.pack(fill='both', expand=True, padx=16, pady=(16, 8))
row = tk.Frame(root)
row.pack(fill='x', padx=16)
choose = ttk.Button(row, text='Choose Session…')
choose.pack(side='left')
show = ttk.Button(row, text='Show in Finder' if sys.platform == 'darwin' else 'Show in Explorer')
bar = ttk.Progressbar(root, maximum=1.0)
bar.pack(fill='x', padx=16, pady=8)
status = tk.Label(root, text='', anchor='w')
status.pack(fill='x', padx=16, pady=(0, 12))

state = {'busy': False, 'done': 0, 'total': 1, 'error': None, 'out': None}


def say(text):
    status.config(text=text)
    root.update_idletasks()


def reveal(path):
    if sys.platform == 'darwin':
        subprocess.run(['open', '-R', path])
    elif os.name == 'nt':
        subprocess.run(['explorer', '/select,', os.path.normpath(path)])
    else:
        subprocess.run(['xdg-open', os.path.dirname(path)])


def export(path):
    if state['busy']:
        return
    if not path.lower().endswith('.ptx') or not os.path.isfile(path):
        messagebox.showerror(APP, 'Please choose a Pro Tools session file (it ends in .ptx).')
        return
    name = os.path.splitext(os.path.basename(path))[0]
    say(f'Reading “{name}”…')
    try:
        found, missing, ok = ptx.scan(path)
    except OSError as e:
        messagebox.showerror(APP, f'Could not open the session:\n{e}')
        return say('')

    if not ok:
        if not messagebox.askokcancel(APP, 'This session’s file list couldn’t be read (maybe a newer Pro Tools '
                                      'version).\n\nThe whole Audio Files folder will be included instead. '
                                      'Ask your engineer to check nothing is missing.'):
            return say('')

    extra = []
    while missing:
        listing = '\n'.join(missing[:12]) + (f'\n…and {len(missing) - 12} more' if len(missing) > 12 else '')
        answer = messagebox.askyesnocancel(
            APP, f'{len(missing)} audio file(s) used by this session couldn’t be found:\n\n{listing}\n\n'
                 'Yes = choose a folder (or drive) to search\nNo = leave them out\nCancel = stop')
        if answer is None:
            return say('')
        if answer is False:
            break
        folder = filedialog.askdirectory(title='Choose a folder to search for the missing files')
        if folder:
            extra.append(folder)
            say('Searching…')
            found, missing, ok = ptx.scan(path, extra)

    out = filedialog.asksaveasfilename(
        title='Save zip for your engineer', initialdir=os.path.expanduser('~/Desktop'),
        initialfile=f'{name} - Mix.zip', defaultextension='.zip', filetypes=[('Zip file', '*.zip')])
    if not out:
        return say('')

    show.pack_forget()
    state.update(busy=True, done=0, total=1, error=None, out=out)
    choose.state(['disabled'])

    def work():
        try:
            ptx.build_zip(path, found, out, lambda d, t: state.update(done=d, total=t))
        except Exception as e:
            state['error'] = e
        state['busy'] = False

    threading.Thread(target=work, daemon=True).start()
    poll()


def poll():
    bar['value'] = state['done'] / state['total']
    if state['busy']:
        say(f'Zipping… {state["done"] / 2**20:,.0f} of {state["total"] / 2**20:,.0f} MB')
        root.after(100, poll)
        return
    choose.state(['!disabled'])
    if state['error']:
        bar['value'] = 0
        say('')
        messagebox.showerror(APP, f'Export failed:\n{state["error"]}')
    else:
        say(f'Done! Saved {os.path.basename(state["out"])}')
        show.pack(side='right')


def pick():
    p = filedialog.askopenfilename(title='Choose a Pro Tools session',
                                   filetypes=[('Pro Tools session', '*.ptx'), ('All files', '*.*')])
    if p:
        export(p)


choose.config(command=pick)
show.config(command=lambda: reveal(state['out']))
if DND_FILES:
    drop.drop_target_register(DND_FILES)
    drop.dnd_bind('<<Drop>>', lambda e: export(root.tk.splitlist(e.data)[0]))
# macOS: file dropped on the Dock icon / opened with the app
root.createcommand('::tk::mac::OpenDocument', lambda *paths: root.after(10, export, paths[0]))
# Windows: file dropped on the .exe icon
if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
    root.after(200, export, sys.argv[1])

root.mainloop()
