import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading
import random

class Message:
    def __init__(self, canvas, start_pos, end_pos, color, text, duration=1.0, is_lost=False):
        self.canvas = canvas
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.color = color
        self.text = text
        self.duration = duration
        self.is_lost = is_lost
        
        self.id = canvas.create_oval(start_pos[0]-10, start_pos[1]-10, start_pos[0]+10, start_pos[1]+10, fill=color)
        self.label_id = canvas.create_text(start_pos[0], start_pos[1]-20, text=text, fill="black", font=("Arial", 8))
        self.start_time = time.time()
        self.finished = False
        self.lost_triggered = False

    def update(self):
        elapsed = time.time() - self.start_time
        
        # Simulate packet loss halfway through the journey
        if self.is_lost and elapsed >= self.duration / 2:
            if not self.lost_triggered:
                self.canvas.itemconfig(self.id, fill="black")
                self.canvas.itemconfig(self.label_id, text="[LOST]")
                self.lost_triggered = True
                
                # Make it disappear after short delay
                self.canvas.after(500, self.destroy)
            return

        if self.lost_triggered:
            return

        if elapsed >= self.duration:
            self.canvas.coords(self.id, self.end_pos[0]-10, self.end_pos[1]-10, self.end_pos[0]+10, self.end_pos[1]+10)
            self.canvas.coords(self.label_id, self.end_pos[0], self.end_pos[1]-20)
            self.finished = True
            return

        ratio = elapsed / self.duration
        curr_x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * ratio
        curr_y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * ratio
        
        self.canvas.coords(self.id, curr_x-10, curr_y-10, curr_x+10, curr_y+10)
        self.canvas.coords(self.label_id, curr_x, curr_y-20)

    def destroy(self):
        if hasattr(self, "id"):
            self.canvas.delete(self.id)
        if hasattr(self, "label_id"):
            self.canvas.delete(self.label_id)
        self.finished = True

class DistributedSystemSim:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulasi Model Komunikasi Sistem Terdistribusi (Advanced)")
        self.root.geometry("1100x750")
        
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("Header.TLabel", font=("Arial", 14, "bold"))

        self.latency = 1.0  # seconds
        self.packet_loss_rate = 0.0 # 0.0 to 1.0
        self.messages = []
        
        # Metrics
        self.req_resp_success = 0
        self.req_resp_failed = 0
        self.pub_sub_success = 0
        self.pub_sub_failed = 0
        self.total_msgs_sent = 0
        
        self.setup_ui()
        self.animate()

    def setup_ui(self):
        # Main Layout
        control_panel = ttk.Frame(self.root, padding="10", width=350)
        control_panel.pack(side=tk.LEFT, fill=tk.Y)
        control_panel.pack_propagate(False)
        
        display_panel = ttk.Frame(self.root, padding="10")
        display_panel.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        # Control Panel Elements
        ttk.Label(control_panel, text="Model Komunikasi", style="Header.TLabel").pack(pady=10)
        
        # Request-Response Controls
        rr_frame = ttk.LabelFrame(control_panel, text="Request-Response", padding="10")
        rr_frame.pack(fill=tk.X, pady=5)
        ttk.Button(rr_frame, text="Kirim Request (HTTP GET)", command=self.start_request_response).pack(fill=tk.X)
        ttk.Label(rr_frame, text="Skenario: Browser meminta data ke Web Server", font=("Arial", 8, "italic"), wraplength=300).pack()

        # Pub-Sub Controls
        ps_frame = ttk.LabelFrame(control_panel, text="Publish-Subscribe", padding="10")
        ps_frame.pack(fill=tk.X, pady=5)
        self.topic_var = tk.StringVar(value="SuhuRuangan")
        ttk.OptionMenu(ps_frame, self.topic_var, "SuhuRuangan", "SuhuRuangan", "StatusMesin").pack(fill=tk.X, pady=2)
        ttk.Button(ps_frame, text="Publish Pesan", command=self.start_publish_subscribe).pack(fill=tk.X)
        ttk.Label(ps_frame, text="Skenario: Sensor IoT mengirim data ke MQTT Broker", font=("Arial", 8, "italic"), wraplength=300).pack()

        # Settings
        settings_frame = ttk.LabelFrame(control_panel, text="Pengaturan Network (Tantangan Dunia Nyata)", padding="10")
        settings_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(settings_frame, text="Latency Jaringan (detik):").pack()
        self.latency_scale = ttk.Scale(settings_frame, from_=0.1, to=3.0, orient=tk.HORIZONTAL, value=1.0, command=self.update_latency)
        self.latency_scale.pack(fill=tk.X)
        self.latency_label = ttk.Label(settings_frame, text="1.0s")
        self.latency_label.pack()

        ttk.Label(settings_frame, text="Packet Loss Rate (%):").pack(pady=(5,0))
        self.loss_scale = ttk.Scale(settings_frame, from_=0, to=100, orient=tk.HORIZONTAL, value=0, command=self.update_loss)
        self.loss_scale.pack(fill=tk.X)
        self.loss_label = ttk.Label(settings_frame, text="0%")
        self.loss_label.pack()

        # Metrics Panel
        metrics_frame = ttk.LabelFrame(control_panel, text="Metrik Perbandingan & Analisis", padding="10")
        metrics_frame.pack(fill=tk.X, pady=10)
        self.metrics_label = ttk.Label(metrics_frame, text="Req-Resp (Sukses/Gagal): 0 / 0\nPub-Sub (Sukses/Gagal): 0 / 0\nTotal Pesan Fisik: 0", justify=tk.LEFT)
        self.metrics_label.pack()
        ttk.Button(metrics_frame, text="Reset Metrik", command=self.reset_metrics).pack(fill=tk.X, pady=5)

        # Log Area
        ttk.Label(control_panel, text="Log Aktivitas:").pack(anchor=tk.W)
        
        # Scrollable Text
        log_frame = ttk.Frame(control_panel)
        log_frame.pack(fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text = tk.Text(log_frame, height=10, width=30, font=("Consolas", 8), yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)

        # Canvas for Animation
        self.canvas = tk.Canvas(display_panel, bg="#f0f0f0", highlightthickness=1, highlightbackground="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.draw_nodes()

    def update_latency(self, val):
        self.latency = float(val)
        self.latency_label.config(text=f"{self.latency:.1f}s")

    def update_loss(self, val):
        self.packet_loss_rate = float(val) / 100.0
        self.loss_label.config(text=f"{int(float(val))}%")

    def draw_nodes(self):
        self.canvas.delete("node")
        
        # Section Titles
        self.canvas.create_text(350, 40, text="Model Request-Response (Synchronous)", font=("Arial", 14, "bold"), fill="#333", tags="node")
        self.canvas.create_text(350, 330, text="Model Publish-Subscribe (Asynchronous)", font=("Arial", 14, "bold"), fill="#333", tags="node")
        self.canvas.create_line(50, 290, 650, 290, dash=(4, 4), fill="#ccc", tags="node")

        # RR Nodes - Repositioned for better spacing
        self.client_pos = (150, 140)
        self.server_pos = (550, 140)
        self.create_node(self.client_pos, "Client\n(Browser)", "lightblue", icon="💻")
        self.create_node(self.server_pos, "Server\n(Web API)", "lightgreen", icon="🖥️")
        self.canvas.create_line(150, 140, 550, 140, dash=(4, 4), fill="gray", tags="node")

        # Pub-Sub Nodes - Adjusted Y-coordinates
        self.pub_pos = (150, 520)
        self.broker_pos = (350, 520)
        self.sub1_pos = (550, 420)
        self.sub2_pos = (550, 520)
        self.sub3_pos = (550, 620)
        
        self.create_node(self.pub_pos, "Publisher\n(Sensor Suhu)", "#ffcc99", icon="🌡️")
        self.create_node(self.broker_pos, "Message Broker\n(MQTT)", "#cc99ff", icon="🔄")
        self.create_node(self.sub1_pos, "Subscriber 1\n(App Mobile)", "#ffff99", icon="📱")
        self.create_node(self.sub2_pos, "Subscriber 2\n(Database)", "#ffff99", icon="💾")
        self.create_node(self.sub3_pos, "Subscriber 3\n(Alarm Panel)", "#ff99cc", icon="🚨")

        # Connection lines for Pub-Sub
        self.canvas.create_line(150, 520, 350, 520, dash=(4, 4), fill="gray", tags="node")
        self.canvas.create_line(350, 520, 550, 420, dash=(4, 4), fill="gray", tags="node")
        self.canvas.create_line(350, 520, 550, 520, dash=(4, 4), fill="gray", tags="node")
        self.canvas.create_line(350, 520, 550, 620, dash=(4, 4), fill="gray", tags="node")

        # Topics Text - Moved up to avoid overlapping with rectangles
        self.canvas.create_text(550, 370, text="Topics: SuhuRuangan", font=("Arial", 8, "italic"), fill="#555", tags="node")
        self.canvas.create_text(550, 470, text="Topics: SuhuRuangan", font=("Arial", 8, "italic"), fill="#555", tags="node")
        self.canvas.create_text(550, 570, text="Topics: StatusMesin", font=("Arial", 8, "italic"), fill="#555", tags="node")

    def create_node(self, pos, name, color, icon=""):
        x, y = pos
        # Larger rectangle for better spacing
        self.canvas.create_rectangle(x-50, y-40, x+50, y+40, fill=color, outline="#666", width=2, tags="node")
        # Adjusted text positions for vertical alignment
        self.canvas.create_text(x, y-15, text=icon, font=("Arial", 20), tags="node")
        self.canvas.create_text(x, y+18, text=name, font=("Arial", 9, "bold"), fill="#333", justify=tk.CENTER, tags="node")

    def log(self, message):
        t = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{t}] {message}\n")
        self.log_text.see(tk.END)

    def is_packet_lost(self):
        return random.random() < self.packet_loss_rate

    def start_request_response(self):
        self.log("Client: Mengirim HTTP GET Request...")
        
        lost = self.is_packet_lost()
        msg = Message(self.canvas, self.client_pos, self.server_pos, "blue", "GET /data", self.latency, is_lost=lost)
        self.messages.append(msg)
        self.total_msgs_sent += 1
        
        if lost:
            def handle_timeout():
                time.sleep(self.latency * 1.5)
                self.root.after(0, lambda: self.log("Client: ERROR - Request Timeout (Packet Loss)!"))
                self.req_resp_failed += 1
                self.root.after(0, self.update_metrics)
            threading.Thread(target=handle_timeout, daemon=True).start()
            return
            
        def handle_server():
            time.sleep(self.latency)
            self.root.after(0, lambda: self.log("Server: Request diterima, memproses DB..."))
            time.sleep(0.5) # Processing time
            self.root.after(0, self.send_response)
        
        threading.Thread(target=handle_server, daemon=True).start()

    def send_response(self):
        lost = self.is_packet_lost()
        self.log("Server: Mengirim HTTP 200 OK Response...")
        msg = Message(self.canvas, self.server_pos, self.client_pos, "green", "200 OK", self.latency, is_lost=lost)
        self.messages.append(msg)
        self.total_msgs_sent += 1
        
        if lost:
            def handle_timeout():
                time.sleep(self.latency * 1.5)
                self.root.after(0, lambda: self.log("Client: ERROR - Menunggu Response Timeout (Packet Loss)!"))
                self.req_resp_failed += 1
                self.root.after(0, self.update_metrics)
            threading.Thread(target=handle_timeout, daemon=True).start()
        else:
            def handle_success():
                time.sleep(self.latency)
                self.root.after(0, lambda: self.log("Client: Response diterima sukses."))
                self.req_resp_success += 1
                self.root.after(0, self.update_metrics)
            threading.Thread(target=handle_success, daemon=True).start()

    def start_publish_subscribe(self):
        topic = self.topic_var.get()
        self.log(f"Publisher: Publish data ke MQTT Broker (Topic: {topic})")
        
        lost = self.is_packet_lost()
        msg = Message(self.canvas, self.pub_pos, self.broker_pos, "red", f"Pub: {topic}", self.latency, is_lost=lost)
        self.messages.append(msg)
        self.total_msgs_sent += 1
        
        if lost:
            def handle_timeout():
                time.sleep(self.latency * 1.5)
                self.root.after(0, lambda: self.log("Publisher: WARNING - Pesan gagal mencapai Broker (Packet Loss)!"))
                self.pub_sub_failed += 1
                self.root.after(0, self.update_metrics)
            threading.Thread(target=handle_timeout, daemon=True).start()
            return

        def handle_broker():
            time.sleep(self.latency)
            self.root.after(0, lambda: self.log(f"Broker: Menerima pesan, mendistribusikan ke topic {topic}..."))
            
            # Logic for topic distribution
            subs = []
            if topic == "SuhuRuangan":
                subs = [(self.sub1_pos, "App Mobile"), (self.sub2_pos, "Database")]
            else:
                subs = [(self.sub3_pos, "Alarm Panel")]
            
            for sub_pos, sub_name in subs:
                self.root.after(0, lambda p=sub_pos, n=sub_name: self.deliver_to_subscriber(p, n))
            
            self.pub_sub_success += 1
            self.root.after(0, self.update_metrics)

        threading.Thread(target=handle_broker, daemon=True).start()

    def deliver_to_subscriber(self, pos, sub_name):
        lost = self.is_packet_lost()
        msg = Message(self.canvas, self.broker_pos, pos, "magenta", "Data", self.latency, is_lost=lost)
        self.messages.append(msg)
        self.total_msgs_sent += 1
        
        if lost:
            def handle_loss():
                time.sleep(self.latency / 2)
                self.root.after(0, lambda: self.log(f"Broker: Gagal mengirim ke {sub_name} (Packet Loss)."))
            threading.Thread(target=handle_loss, daemon=True).start()
        else:
            def handle_recv():
                time.sleep(self.latency)
                self.root.after(0, lambda: self.log(f"Subscriber ({sub_name}): Menerima data."))
            threading.Thread(target=handle_recv, daemon=True).start()


    def update_metrics(self):
        self.metrics_label.config(
            text=f"Req-Resp (Sukses/Gagal): {self.req_resp_success} / {self.req_resp_failed}\n"
                 f"Pub-Sub (Sukses/Gagal): {self.pub_sub_success} / {self.pub_sub_failed}\n"
                 f"Total Pesan Fisik: {self.total_msgs_sent}"
        )

    def reset_metrics(self):
        self.req_resp_success = 0
        self.req_resp_failed = 0
        self.pub_sub_success = 0
        self.pub_sub_failed = 0
        self.total_msgs_sent = 0
        self.update_metrics()
        self.log("Metrics reset.")

    def animate(self):
        to_remove = []
        # Gunakan list copy untuk iterasi yang aman
        for msg in list(self.messages):
            msg.update()
            if msg.finished:
                to_remove.append(msg)
        
        for msg in to_remove:
            # Panggil destroy untuk menghapus visual dot dari canvas
            msg.destroy()
            if msg in self.messages:
                self.messages.remove(msg)
            
        self.root.after(30, self.animate)

if __name__ == "__main__":
    root = tk.Tk()
    app = DistributedSystemSim(root)
    
    # Information Overlay / Welcome
    messagebox.showinfo("Simulasi Model Komunikasi", 
        "Selamat datang di Simulasi Sistem Terdistribusi (Advanced)!\n\n"
        "Fitur Utama:\n"
        "1. Dua Model Komunikasi: Request-Response & Publish-Subscribe.\n"
        "2. Skenario Dunia Nyata: IoT Sensor, Web API, Broker MQTT.\n"
        "3. Simulasi Tantangan Nyata: Atur 'Packet Loss Rate' untuk melihat "
        "dampak hilangnya paket di jaringan pada masing-masing model.\n"
        "4. Visualisasi & Metrik: Animasi real-time dan perhitungan success/failure rate.\n\n"
        "Silakan bereksperimen dengan panel di sebelah kiri.")
    
    root.mainloop()