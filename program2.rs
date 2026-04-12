use std::fs::File;
use std::io::{BufRead, BufReader};
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

fn main() {
    let (tx, rx) = mpsc::channel();
    let total_lines = 100;
    let num_threads = 4;
    let lines_per_thread = total_lines / num_threads;

    let mut reader_threads = vec![];

    // --- MULTI-THREAD PEMBACA (Banyak Produsen) ---
    for i in 0..num_threads {
        // Clone transmitter untuk thread ini
        let tx_clone = tx.clone(); 
        
        let start = i * lines_per_thread;
        let end = if i == num_threads - 1 { total_lines } else { (i + 1) * lines_per_thread };
        
        let handle = thread::spawn(move || {
            println!("[READER-{}] Mulai membaca baris {} hingga {}...", i+1, start, end - 1);
            let file = File::open("data.txt").unwrap();
            let reader = BufReader::new(file);

            // Melewati (skip) baris yang tidak perlu, lalu mengambil (take) sesuai porsi
            for line in reader.lines().skip(start).take(end - start) {
                let data = line.unwrap();
                thread::sleep(Duration::from_millis(50));
                
                tx_clone.send(format!("(Dibaca oleh T-{}) {}", i+1, data)).unwrap();
            }
            println!("[READER-{}] Selesai.", i+1);
        });
        reader_threads.push(handle);
    }

    // PENTING: Kita harus men-drop 'tx' asli di main thread.
    // Jika tidak, 'rx' akan terus menunggu karena mengira masih ada tx yang aktif.
    drop(tx);

    // --- THREAD PENAMPIL (Konsumen Tunggal) ---
    let t_printer = thread::spawn(move || {
        for received in rx {
            println!("[LAYAR] -> {}", received);
        }
    });

    // Menunggu semua thread selesai
    for t in reader_threads {
        t.join().unwrap();
    }
    t_printer.join().unwrap();
    
    println!("Program Multithreading Selesai.");
}