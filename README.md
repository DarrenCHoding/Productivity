# Productivity

Aplikasi productivity pribadi berbasis web, untuk dipakai sendiri di komputer Anda.

**Tahap 1: daftar tugas**
- Tambah, edit, hapus, dan tandai tugas selesai. Tugas yang sudah selesai tetap bisa dilihat dan dikembalikan.
- Tanggal jatuh tempo (opsional) dan prioritas (penting/biasa). Tugas yang terlambat diberi warna merah.
- Halaman **Hari ini** berisi tugas yang jatuh tempo hari ini dan yang terlambat, dengan tugas penting di atas.
- Halaman **Semua tugas**.
- **Kategori** (misalnya Kerja, Pribadi, Kuliah) yang bisa dipakai untuk memfilter tugas.
- Semua data tersimpan permanen di satu file database di komputer Anda.

**Tahap 2** (sedang dikerjakan, satu fitur per langkah)
- **Timer fokus** (pomodoro): 25 menit fokus, 5 menit istirahat. Durasinya bisa diubah, timer bisa dikaitkan ke satu tugas, dan total waktu fokus tiap tugas tercatat.

---

## 1. Persiapan (cukup sekali)

Aplikasi ini hanya butuh **Python 3.8 atau lebih baru**. Tidak ada paket lain yang perlu dipasang.

Cek apakah Python sudah terpasang. Buka **Terminal** (Mac/Linux) atau **Command Prompt** (Windows), lalu ketik:

```
python3 --version
```

Di Windows, ketik `python --version`. Kalau muncul tulisan seperti `Python 3.12.1`, Python sudah siap.

Kalau belum ada, unduh dari **https://www.python.org/downloads/** lalu pasang.
> **Penting untuk Windows:** di layar pertama pemasangan, centang **"Add python.exe to PATH"**.

## 2. Mengunduh aplikasi

Pilih salah satu cara:

- **Pakai Git** (disarankan, supaya mudah memperbarui nanti):
  ```
  git clone https://github.com/darrenchoding/productivity.git
  cd productivity
  ```
- **Tanpa Git:** buka halaman repositori di GitHub, klik tombol hijau **Code**, pilih **Download ZIP**, lalu ekstrak. Setelah itu buka Terminal atau Command Prompt di folder hasil ekstrak.

## 3. Menjalankan aplikasi

Di dalam folder aplikasi, jalankan **satu perintah** ini:

| Sistem | Perintah |
|---|---|
| Mac / Linux / Raspberry Pi | `python3 server.py` |
| Windows | `python server.py` |

Browser akan terbuka otomatis ke **http://localhost:8000**. Kalau tidak terbuka, buka alamat itu secara manual.

Selama aplikasi dipakai, **jendela terminal harus tetap terbuka**. Untuk menghentikan aplikasi, klik jendela terminal lalu tekan **Ctrl+C**.

## 4. Cara pakai singkat

- **Menambah tugas:** ketik judul di kolom "Tambah tugas baru…", lalu tekan Enter. Di bawah kolom itu Anda bisa memilih tanggal, menekan tombol **Penting**, dan memilih kategori.
  Di halaman *Hari ini*, tanggal tugas baru otomatis diisi hari ini.
- **Menandai selesai:** klik lingkaran di kiri tugas. Klik lagi untuk mengembalikannya menjadi belum selesai. Tugas yang sudah selesai ada di bagian **Selesai** di bawah daftar (klik judulnya untuk membuka).
- **Mengedit:** klik judul tugas, atau ikon pensil.
- **Menghapus:** ikon tempat sampah, atau tombol **Hapus** di jendela edit.
- **Kategori:** buat, ganti nama, dan hapus kategori di menu **Kategori**. Menghapus kategori **tidak** menghapus tugasnya; tugas itu hanya menjadi "tanpa kategori".
- **Filter:** klik nama kategori di deretan tombol di atas daftar tugas.

### Timer fokus

- Buka menu **Fokus**, lalu tekan **Mulai**. Timer tetap berjalan walaupun Anda pindah halaman atau memuat ulang browser. Sisa waktunya terlihat di menu samping dan di judul tab browser.
- **Jeda** untuk berhenti sebentar dan **Lanjutkan** untuk meneruskan. **Lewati** pindah ke fase berikutnya (fokus ↔ istirahat). **Berhenti** mengembalikan timer ke awal.
- **Mengaitkan ke tugas:** pilih tugas di "Sedang mengerjakan", atau buka tugas (klik judulnya) lalu tekan **Mulai fokus**. Selama timer berjalan, tugas tidak bisa diganti; jeda dulu kalau ingin menggantinya.
- Saat waktu fokus habis, terdengar bunyi dan sesi itu dicatat. Fase istirahat lalu disiapkan dan menunggu Anda menekan **Mulai**.
- Kalau Anda menekan **Berhenti** atau **Lewati** di tengah sesi fokus, waktu yang sudah berjalan tetap dicatat, asalkan sudah lebih dari 1 menit.
- **Total waktu fokus** tiap tugas tampil di daftar tugas (ikon jam) dan di jendela edit tugas. Riwayat sesi hari ini ada di bawah timer; sesi yang salah bisa dihapus dari sana.
- **Mengubah durasi:** buka **Atur durasi** di bawah halaman Fokus. Kalau timer sedang berjalan, durasi baru berlaku mulai sesi berikutnya.
- **Notifikasi:** supaya tetap diberi tahu saat bekerja di jendela lain, klik **Aktifkan notifikasi** di bawah halaman Fokus. Fitur ini hanya tersedia saat aplikasi dibuka lewat `localhost`.

## 5. Di mana data saya disimpan?

Semua data ada di **satu file**:

```
data/productivity.db
```

(di dalam folder aplikasi). Lokasi lengkapnya juga ditampilkan di terminal setiap kali aplikasi dijalankan, pada baris `File data`.

- Setiap perubahan **langsung disimpan** ke file ini. Data tidak hilang saat browser ditutup, aplikasi dihentikan, atau komputer dimatikan.
- **Backup:** hentikan aplikasi (Ctrl+C), lalu salin file `productivity.db` ke tempat lain, misalnya flashdisk atau Google Drive.
- **Memulihkan backup:** hentikan aplikasi, taruh salinan backup di `data/productivity.db`, lalu jalankan lagi.
- **Mulai dari nol:** hentikan aplikasi, lalu hapus atau pindahkan file `data/productivity.db`. File baru yang kosong dibuat otomatis saat aplikasi dijalankan lagi.
- File ini sengaja **tidak ikut masuk Git**, jadi data pribadi Anda tidak akan ter-upload ke GitHub.

### Cadangan otomatis saat ada fitur baru

Kalau versi baru aplikasi perlu mengubah struktur database, aplikasi **otomatis membuat cadangan** sebelum mengubah apa pun. Cadangan disimpan di:

```
data/backups/productivity-<tanggal-jam>-sebelum-v<nomor>.db
```

Terminal juga menampilkan lokasinya saat cadangan dibuat. Kalau ada masalah setelah pembaruan, hentikan aplikasi lalu salin file cadangan itu menjadi `data/productivity.db`. Cadangan lama yang sudah tidak diperlukan boleh dihapus.

## 6. Pilihan tambahan

| Perintah | Kegunaan |
|---|---|
| `python3 server.py --port 8001` | Pakai port lain kalau 8000 sudah dipakai program lain |
| `python3 server.py --no-browser` | Jangan buka browser otomatis |
| `python3 server.py --host 0.0.0.0` | Izinkan perangkat lain di jaringan rumah membuka aplikasi (lihat bagian 7) |

Lokasi file data bisa diganti lewat variabel lingkungan `PRODUCTIVITY_DB`, misalnya:
`PRODUCTIVITY_DB=/home/saya/tugas.db python3 server.py`

## 7. Membuka dari tablet atau perangkat lain (nanti)

Secara bawaan, aplikasi hanya bisa dibuka dari komputer yang menjalankannya. Untuk membukanya dari tablet di jaringan Wi-Fi rumah yang sama:

1. Jalankan `python3 server.py --host 0.0.0.0`.
2. Cari alamat IP komputer Anda. Di Windows ketik `ipconfig` dan lihat "IPv4 Address". Di Mac buka System Settings → Wi-Fi → Details. Di Linux/Raspberry Pi ketik `hostname -I`.
3. Di browser tablet, buka `http://<alamat-IP>:8000`, misalnya `http://192.168.1.10:8000`.
4. Kalau tidak bisa terbuka, izinkan Python di firewall komputer (Windows biasanya menanyakannya saat pertama kali).

> Aplikasi ini **tidak memakai login**. Gunakan `--host 0.0.0.0` hanya di jaringan rumah yang Anda percaya, jangan di Wi-Fi umum.

## 8. Masalah umum

- **`python3` / `python` tidak dikenali:** Python belum terpasang, atau di Windows lupa mencentang "Add python.exe to PATH". Pasang ulang Python dan centang pilihan itu.
- **"Port 8000 sedang dipakai program lain":** aplikasi mungkin sudah berjalan di jendela lain. Tutup jendela itu, atau pakai `--port 8001`.
- **Tampilan tidak berubah setelah memperbarui kode:** tekan Ctrl+F5 (Mac: Cmd+Shift+R) di browser.
- **Muncul pesan "Tidak bisa terhubung ke server":** jendela terminal aplikasi tertutup atau aplikasi dihentikan. Jalankan lagi.

---

## Untuk pengembangan

### Teknologi

- **Python** (pustaka bawaan saja): server web (`http.server`) dan database (`sqlite3`).
- **SQLite**: database dalam satu file.
- **HTML, CSS, JavaScript biasa**: tanpa *framework* dan tanpa langkah *build*.

### Struktur folder

```
server.py                 titik masuk: python3 server.py
app/
  db.py                   koneksi SQLite + daftar migrasi (perubahan struktur tabel)
  router.py               pengatur alamat API
  server.py               melayani /api/... dan file tampilan
  api/
    tasks.py              API tugas
    categories.py         API kategori
    focus.py              API riwayat sesi fokus
    settings.py           API pengaturan (misalnya durasi timer)
    system.py             /api/health
static/
  index.html              kerangka halaman
  css/style.css           tampilan
  js/
    app.js                daftar halaman & navigasi
    api.js                semua pemanggilan ke server
    focus-timer.js        mesin timer fokus (tetap berjalan di halaman mana pun)
    dates.js, ui.js, icons.js, events.js   fungsi bantu
    components/           bagian tampilan yang dipakai ulang (baris tugas, form, dll.)
    views/                satu file per halaman (today.js, all-tasks.js, focus.js, categories.js)
tests/                    uji otomatis
data/                     file database (tidak masuk Git)
```

### Menambah fitur baru (misalnya timer fokus)

1. **Database:** tambahkan satu entri baru di **akhir** daftar `MIGRATIONS` di `app/db.py`. Jangan mengubah entri lama. Migrasi baru dijalankan otomatis saat server dinyalakan (setelah cadangan dibuat), dan data lama tetap aman.
   Pengaturan sederhana tidak butuh tabel baru: cukup tambahkan entri di `SETTINGS` (`app/api/settings.py`).
2. **API:** buat `app/api/timer.py` yang memakai `@route(...)`, lalu tambahkan namanya di `app/api/__init__.py`.
3. **Tampilan:** tambahkan fungsi pemanggil di `static/js/api.js`, buat `static/js/views/timer.js`, lalu daftarkan di `VIEWS` pada `static/js/app.js`. Menu samping akan bertambah otomatis.

### Daftar API

| Metode | Alamat | Keterangan |
|---|---|---|
| GET | `/api/tasks` | Daftar tugas. Filter: `?status=open\|done\|all`, `?view=today&today=YYYY-MM-DD`, `?category=<id>\|none` |
| POST | `/api/tasks` | Tambah tugas: `title`, `due_date`, `priority` (`normal`/`high`), `category_id` |
| GET / PATCH / DELETE | `/api/tasks/<id>` | Ambil / ubah sebagian / hapus tugas (PATCH juga menerima `done`) |
| GET / POST | `/api/categories` | Daftar kategori (dengan jumlah tugas) / buat kategori: `name` |
| PATCH / DELETE | `/api/categories/<id>` | Ganti nama / hapus kategori |
| GET / PATCH | `/api/settings` | Baca / ubah pengaturan (`focus_work_minutes`, `focus_break_minutes`) |
| GET | `/api/focus/sessions` | Riwayat sesi fokus (`?date=YYYY-MM-DD` untuk satu hari) |
| POST | `/api/focus/sessions` | Catat sesi: `duration_seconds`, `task_id` (opsional), `completed` |
| DELETE | `/api/focus/sessions/<id>` | Hapus satu sesi dari riwayat |

### Menjalankan uji otomatis

```
python3 -m unittest
```

Uji memakai database sementara, jadi data asli Anda tidak tersentuh.
