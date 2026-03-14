import customtkinter as ctk
import threading
import ipaddress
from urllib.request import urlopen

try:
    import scapy.all as scapy
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

# ── Tema ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Logica di scansione ───────────────────────────────────────────────────────

def validate_ip_range(ip_range):
    try:
        ipaddress.ip_network(ip_range, strict=False)
        return True
    except ValueError:
        return False

def get_mac_vendor(mac):
    try:
        with urlopen(f"https://api.macvendors.com/{mac}", timeout=2) as r:
            vendor = r.read(256).decode()
            return vendor.strip().encode("ascii", errors="ignore").decode()[:64]
    except Exception:
        return "Unknown"

def arp_scan(ip_range, callback_row, callback_done, callback_error):
    if not SCAPY_AVAILABLE:
        callback_error("Scapy is not installed. Run: pip install scapy")
        return
    if not validate_ip_range(ip_range):
        callback_error("Invalid IP range. Example: 192.168.1.0/24")
        return
    try:
        packet = scapy.Ether(dst="ff:ff:ff:ff:ff:ff") / scapy.ARP(pdst=ip_range)
        answered = scapy.srp(packet, timeout=2, verbose=False)[0]
        if not answered:
            callback_error("No hosts found.")
            return
        for _, pkt in answered:
            vendor = get_mac_vendor(pkt.hwsrc)
            callback_row(pkt.psrc, pkt.hwsrc, vendor)
        callback_done(len(answered))
    except Exception as e:
        callback_error(f"Errore: {e}")

# ── GUI ───────────────────────────────────────────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ARP Scanner")
        self.geometry("820x560")
        self.resizable(False, False)
        self._build_ui()

    def _build_ui(self):
        # Titolo
        ctk.CTkLabel(self, text="ARP Scanner", font=ctk.CTkFont("Courier New", 22, "bold")).pack(pady=(20, 4))
        ctk.CTkLabel(self, text="Scan active hosts on the local network", font=ctk.CTkFont(size=12),
                     text_color="gray").pack(pady=(0, 16))

        # Input row
        frame_input = ctk.CTkFrame(self, fg_color="transparent")
        frame_input.pack(padx=30, fill="x")

        self.entry = ctk.CTkEntry(frame_input, placeholder_text="e.g. 192.168.1.0/24",
                                  font=ctk.CTkFont("Courier New", 13), height=38)
        self.entry.pack(side="left", expand=True, fill="x", padx=(0, 10))

        self.btn_scan = ctk.CTkButton(frame_input, text="▶  Scan", width=120, height=38,
                                      font=ctk.CTkFont(size=13, weight="bold"),
                                      command=self._start_scan)
        self.btn_scan.pack(side="left")

        self.btn_clear = ctk.CTkButton(frame_input, text="✕  Clear", width=100, height=38,
                                       font=ctk.CTkFont(size=13), fg_color="#3a3a3a",
                                       hover_color="#555", command=self._clear)
        self.btn_clear.pack(side="left", padx=(8, 0))

        # Header tabella
        frame_header = ctk.CTkFrame(self, fg_color="#1e2a38", corner_radius=8)
        frame_header.pack(padx=30, pady=(14, 0), fill="x")
        for col, w in [("IP Address", 220), ("MAC Address", 200), ("Vendor", 340)]:
            ctk.CTkLabel(frame_header, text=col, font=ctk.CTkFont("Courier New", 12, "bold"),
                         width=w, anchor="w", text_color="#61afef").pack(side="left", padx=12, pady=6)

        # Area risultati scrollabile
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="#161b22", corner_radius=8)
        self.scroll.pack(padx=30, pady=(2, 10), fill="both", expand=True)

        # Status bar
        self.status = ctk.CTkLabel(self, text="Waiting for a scan...",
                                   font=ctk.CTkFont(size=11), text_color="gray")
        self.status.pack(pady=(0, 12))

    # ── Helpers UI ────────────────────────────────────────────────────────────

    def _add_row(self, ip, mac, vendor):
        row = ctk.CTkFrame(self.scroll, fg_color="#1c2128", corner_radius=6)
        row.pack(fill="x", pady=2)
        for text, w in [(ip, 220), (mac, 200), (vendor, 340)]:
            ctk.CTkLabel(row, text=text, font=ctk.CTkFont("Courier New", 12),
                         width=w, anchor="w", text_color="#e6edf3").pack(side="left", padx=12, pady=7)

    def _clear(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self.status.configure(text="Waiting for a scan...", text_color="gray")

    def _set_scanning(self, scanning: bool):
        state = "disabled" if scanning else "normal"
        self.btn_scan.configure(state=state, text="⏳ Scanning..." if scanning else "▶  Scan")

    # ── Scan ──────────────────────────────────────────────────────────────────

    def _start_scan(self):
        ip_range = self.entry.get().strip()
        if not ip_range:
            self.status.configure(text="⚠ Please enter a valid IP range.", text_color="#e5c07b")
            return
        self._clear()
        self._set_scanning(True)
        self.status.configure(text="Scanning...", text_color="#61afef")

        threading.Thread(target=arp_scan, daemon=True, args=(
            ip_range,
            lambda ip, mac, v: self.after(0, self._add_row, ip, mac, v),
            lambda n: self.after(0, self._on_done, n),
            lambda msg: self.after(0, self._on_error, msg),
        )).start()

    def _on_done(self, count):
        self._set_scanning(False)
        self.status.configure(text=f"✔ Scan complete — {count} host(s) found.", text_color="#98c379")

    def _on_error(self, msg):
        self._set_scanning(False)
        self.status.configure(text=f"✖ {msg}", text_color="#e06c75")


if __name__ == "__main__":
    App().mainloop()
