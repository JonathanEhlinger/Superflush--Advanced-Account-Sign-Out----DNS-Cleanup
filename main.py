# MIT License
# 
# Copyright (c) 2024 ejona
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
import platform
import ctypes
import math

# ----- Configuration: adjust paths/profiles as needed -----
BROWSER_PROFILES = {
    'chrome': os.path.expanduser(r'~\AppData\Local\Google\Chrome\User Data\Default'),
    'edge': os.path.expanduser(r'~\AppData\Local\Microsoft\Edge\User Data\Default'),
    'firefox': os.path.expanduser(r'~\AppData\Roaming\Mozilla\Firefox\Profiles')
}
GIT_DESKTOP_CREDENTIALS = os.path.expanduser(r'~\AppData\Roaming\GitHub Desktop')

# ----- Utility Functions -----
def is_admin():
    """Check if the script is running with admin privileges (Windows only)."""
    if os.name == 'nt':
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
    return os.geteuid() == 0 if hasattr(os, "geteuid") else False

def log_error(msg):
    with open("superflush.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# ----- Core Functions -----
def flush_dns():
    """Flush the DNS cache"""
    try:
        system = platform.system()
        if system == 'Windows':
            if not is_admin():
                raise PermissionError("Administrator privileges required to flush DNS on Windows.")
            subprocess.check_call(['ipconfig', '/flushdns'])
        elif system == 'Linux':
            subprocess.check_call(['systemd-resolve', '--flush-caches'])
        elif system == 'Darwin':  # macOS
            subprocess.check_call(['dscacheutil', '-flushcache'])
            subprocess.check_call(['killall', '-HUP', 'mDNSResponder'])
        else:
            raise RuntimeError(f"Unsupported OS: {system}")
        return True, "DNS cache flushed successfully."
    except Exception as e:
        log_error(f"DNS flush error: {e}")
        return False, str(e)

def clear_browser_data():
    """Delete history, cache, and cookies for supported browsers"""
    errors = []
    for name, path in BROWSER_PROFILES.items():
        if os.path.exists(path):
            try:
                # Chrome/Edge stores cookies and history in SQLite files
                for entry in ['History', 'Cookies', 'Login Data', 'Cache']:
                    target = os.path.join(path, entry)
                    if os.path.exists(target):
                        if os.path.isdir(target):
                            shutil.rmtree(target, ignore_errors=True)
                        else:
                            os.remove(target)
                # Firefox: delete entire profile folder contents
                if name == 'firefox':
                    for profile in os.listdir(path):
                        prof_path = os.path.join(path, profile)
                        shutil.rmtree(prof_path, ignore_errors=True)
            except Exception as e:
                err_msg = f"{name}: {e}"
                log_error(err_msg)
                errors.append(err_msg)
    return errors

def sign_out_services():
    """Attempt to sign out of various desktop services"""
    errors = []
    # Example: GitHub Desktop
    try:
        cred_file = os.path.join(GIT_DESKTOP_CREDENTIALS, 'git-credential-desktop.json')
        if os.path.exists(cred_file):
            os.remove(cred_file)
    except Exception as e:
        err_msg = f"GitHub Desktop: {e}"
        log_error(err_msg)
        errors.append(err_msg)
    # Windows Credential Manager sign out (removes generic credentials for GitHub, Chrome, etc.)
    if os.name == 'nt':
        try:
            # Remove all generic credentials related to GitHub and browsers
            for target in ["git:", "github", "chrome", "edge"]:
                subprocess.run(['cmdkey', '/delete', target], capture_output=True)
        except Exception as e:
            err_msg = f"Windows Credentials: {e}"
            log_error(err_msg)
            errors.append(err_msg)
    # TODO: Add more services (VPN clients, etc.)
    return errors

# ----- GUI -----
class TrippyFrame(tk.Canvas):
    """A Canvas with a green trippy wavy background."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.bind("<Configure>", self._draw_trippy_bg)

    def _draw_trippy_bg(self, event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        # Draw a green gradient
        for i in range(h):
            color = "#%02x%02x%02x" % (
                0,
                int(180 + 60 * math.sin(i / 15.0)),
                int(80 + 80 * math.cos(i / 30.0))
            )
            self.create_line(0, i, w, i, fill=color)
        # Overlay wavy lines
        for y in range(0, h, 18):
            points = []
            for x in range(0, w, 8):
                offset = 10 * math.sin((x + y) / 18.0)
                points.append(x)
                points.append(y + offset)
            self.create_line(points, fill="#00ff99", width=2, smooth=True, stipple="gray50")

class SuperflushApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Superflush \u2013 Privacy Cleanup')
        self.geometry('420x340')
        self.resizable(True, False)
        self.configure(bg="#1a3d1a")
        self.create_trippy_bg()
        self.create_widgets()
        self.create_menu()
        self.status_var = tk.StringVar()
        self.status_var.set("Ready.")
        self.create_statusbar()

    def create_trippy_bg(self):
        self.trippy = TrippyFrame(self, highlightthickness=0)
        self.trippy.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lower(self.trippy)

    def create_widgets(self):
        frm = ttk.Frame(self, padding=20, style="Trippy.TFrame")
        frm.place(relx=0.5, rely=0.5, anchor="center")
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Trippy.TFrame", background="#1a3d1a")
        style.configure("Trippy.TButton", font=("Arial Black", 12, "bold"), foreground="#00ff99", background="#1a3d1a")
        style.map("Trippy.TButton",
                  background=[('active', '#00ff99')],
                  foreground=[('active', '#1a3d1a')])

        btn_flush = ttk.Button(frm, text='Flush DNS', command=self.action_flush, style="Trippy.TButton")
        btn_flush.grid(row=0, column=0, sticky="ew", pady=8)
        self.create_tooltip(btn_flush, "Flushes your system DNS cache (requires admin on Windows)")

        btn_clear = ttk.Button(frm, text='Clear Browser Data', command=self.action_clear, style="Trippy.TButton")
        btn_clear.grid(row=1, column=0, sticky="ew", pady=8)
        self.create_tooltip(btn_clear, "Deletes browser history, cookies, and cache for Chrome, Edge, and Firefox")

        btn_signout = ttk.Button(frm, text='Sign Out Services', command=self.action_signout, style="Trippy.TButton")
        btn_signout.grid(row=2, column=0, sticky="ew", pady=8)
        self.create_tooltip(btn_signout, "Signs out of supported desktop services (e.g., GitHub Desktop)")

        btn_all = ttk.Button(frm, text='Run All', command=self.action_all, style="Trippy.TButton")
        btn_all.grid(row=3, column=0, sticky="ew", pady=16)
        self.create_tooltip(btn_all, "Performs all cleanup actions above")

        frm.columnconfigure(0, weight=1)

    def create_menu(self):
        menubar = tk.Menu(self)
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=helpmenu)
        self.config(menu=menubar)

    def create_statusbar(self):
        status = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        status.pack(side=tk.BOTTOM, fill=tk.X)

    def set_status(self, msg):
        self.status_var.set(msg)
        self.update_idletasks()

    def show_about(self):
        messagebox.showinfo("About Superflush", "Superflush – Advanced Account Sign-Out & DNS Cleanup\n\n"
                                                "Cleans browser data, flushes DNS, and signs out of desktop services.\n"
                                                "GitHub: https://github.com/your-repo")

    def create_tooltip(self, widget, text):
        # Simple tooltip implementation
        def on_enter(event):
            self.status_var.set(text)
        def on_leave(event):
            self.status_var.set("Ready.")
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def action_flush(self):
        self.set_status("Flushing DNS...")
        ok, msg = flush_dns()
        if ok:
            messagebox.showinfo('Flush DNS', msg)
        else:
            messagebox.showerror('Flush DNS Error', msg)
        self.set_status("Ready.")

    def action_clear(self):
        self.set_status("Clearing browser data...")
        errs = clear_browser_data()
        if errs:
            messagebox.showwarning('Clear Data', '\n'.join(errs))
        else:
            messagebox.showinfo('Clear Data', 'Browser data cleared successfully.')
        self.set_status("Ready.")

    def action_signout(self):
        self.set_status("Signing out of services...")
        errs = sign_out_services()
        if errs:
            messagebox.showwarning('Sign Out', '\n'.join(errs))
        else:
            messagebox.showinfo('Sign Out', 'Signed out of services successfully.')
        self.set_status("Ready.")

    def action_all(self):
        self.set_status("Running all cleanup actions...")
        reports = []
        ok, msg = flush_dns()
        reports.append(msg)
        errors = clear_browser_data() + sign_out_services()
        if errors:
            reports.extend(errors)
        messagebox.showinfo('Superflush Report', '\n'.join(reports))
        self.set_status("Ready.")

if __name__ == '__main__':
    app = SuperflushApp()
    app.mainloop()
