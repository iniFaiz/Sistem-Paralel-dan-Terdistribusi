use std::fs::File;
use std::io::{BufRead, BufReader};
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

fn main() {
    // Jalankan ini sekali saja jika file belum ada
    // buat_file_dummy(); 

    // Membuat channel komunikasi antar-thread
    let (tx, rx) = mpsc::channel();

    // --- THREAD PEMBACA (Produsen) ---
    let t_reader = thread::spawn(move || {
        println!("[READER] Mulai membaca file...");
        let file = File::open("data.txt").expect("File tidak ditemukan");
        let reader = BufReader::new(file);

        for line in reader.lines() {
            let data = line.expect("Gagal membaca baris");
            thread::sleep(Duration::from_millis(50)); // Simulasi waktu baca
            
            // Mengirim data ke channel
            tx.send(data).expect("Gagal mengirim data");
        }
        println!("[READER] Selesai membaca file.");
        // tx akan otomatis di-drop (dihancurkan) saat thread ini selesai.
        // Ini memberi sinyal ke rx bahwa tidak ada lagi data yang akan datang.
    });

    // --- THREAD PENAMPIL (Konsumen) ---
    let t_printer = thread::spawn(move || {
        println!("[PRINTER] Mulai menampilkan data...");
        // rx akan terus menerima data sampai semua tx di-drop
        for received in rx {
            println!("[LAYAR] -> {}", received);
        }
        println!("[PRINTER] Selesai menampilkan data.");
    });

    // Menunggu kedua thread selesai
    t_reader.join().unwrap();
    t_printer.join().unwrap();
    println!("Program Selesai.");
}