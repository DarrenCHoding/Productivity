# Productivity

Aplikasi productivity pribadi berbasis web, untuk dipakai sendiri di komputer Anda.

**Tahap 1: daftar tugas**
- Tambah, edit, hapus, dan tandai tugas selesai. Tugas yang sudah selesai tetap bisa dilihat dan dikembalikan.
- Tanggal jatuh tempo (opsional) dan prioritas (penting/biasa). Tugas yang terlambat diberi warna merah.
- Halaman **Hari ini** berisi tugas yang jatuh tempo hari ini dan yang terlambat, dengan tugas penting di atas.
- Halaman **Semua tugas**.
- **Kategori** (misalnya Kerja, Pribadi, Kuliah) yang bisa dipakai untuk memfilter tugas.
- Semua data tersimpan permanen di satu file database di komputer Anda.

**Tahap 2**
- **Timer fokus** (pomodoro): 25 menit fokus, 5 menit istirahat. Durasinya bisa diubah, timer bisa dikaitkan ke satu tugas, dan total waktu fokus tiap tugas tercatat.
- *Belum dibuat:* tugas berulang, habit tracker, catatan cepat, pencarian & filter.

**Tahap 3**
- **Ekspor & cadangan:** unduh seluruh data ke satu file, pulihkan dari file itu, dan cadangan otomatis setiap hari (7 hari terakhir disimpan).
- *Belum dibuat:* pilihan tema & shortcut keyboard, kalender, statistik mingguan, pengingat, akses dari perangkat lain dengan PIN & PWA.

**Tahap 4**
- **Tes otomatis** untuk fungsi-fungsi penting, termasuk mesin timer di browser. Lihat bagian [Tes otomatis](#tes-otomatis).
- *Belum dibuat:* proyek & subtugas, input cepat, rencana harian, tinjauan mingguan, kalender eksternal, mode meja.

**Tahap 5: fitur AI** (sedang dikerjakan, satu fitur per langkah)
- **Fondasi AI** (opsional): pengaturan fitur AI, pilihan model, batas pemakaian bulanan, dan perkiraan biaya. Lihat bagian [9. Fitur AI](#9-fitur-ai-opsional).

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
- **Mulai dari nol:** hentikan aplikasi, lalu hapus atau pindahkan file `data/productivity.db`. File baru yang kosong dibuat otomatis saat aplikasi dijalankan lagi.
- File ini sengaja **tidak ikut masuk Git**, jadi data pribadi Anda tidak akan ter-upload ke GitHub.

### Mengunduh dan memulihkan data

Buka menu **Pengaturan** → bagian **Data & cadangan**.

- **Unduh data:** menyimpan seluruh data (tugas, kategori, riwayat fokus, pengaturan) ke satu file, misalnya `productivity-cadangan-2026-10-04-1530.db`. Simpan file ini di tempat aman, misalnya flashdisk atau Google Drive. Sebaiknya lakukan ini secara rutin, karena cadangan otomatis (di bawah) tersimpan di komputer yang sama.
- **Pulihkan dari file:** tekan **Pilih file…**, pilih file cadangan yang pernah Anda unduh, lalu konfirmasi. Seluruh data saat ini **diganti** dengan isi file itu.
  - Sebelum diganti, file diperiksa dulu. File yang bukan cadangan Productivity, rusak, atau dibuat oleh versi aplikasi yang lebih baru akan ditolak, dan data Anda tidak berubah.
  - Data saat ini **selalu dicadangkan dulu** (muncul di daftar sebagai "Sebelum pemulihan"), jadi pemulihan yang salah bisa dibatalkan dengan memulihkan cadangan itu.
  - File cadangan dari versi aplikasi yang lebih lama boleh dipakai; strukturnya diperbarui otomatis.

### Cadangan otomatis

Aplikasi menyimpan cadangan sendiri ke folder:

```
data/backups/
```

Lokasi lengkapnya ditampilkan di terminal (baris `Cadangan`) dan di halaman Pengaturan.

| Nama file | Kapan dibuat | Berapa lama disimpan |
|---|---|---|
| `productivity-harian-<tanggal>.db` | Sekali sehari, saat aplikasi berjalan | **7 hari terakhir**; yang lebih lama dihapus otomatis |
| `productivity-<tanggal-jam>-sebelum-pemulihan.db` | Sebelum data dipulihkan dari cadangan | Tidak dihapus otomatis |
| `productivity-<tanggal-jam>-sebelum-v<nomor>.db` | Sebelum struktur database diubah karena ada fitur baru | Tidak dihapus otomatis |

- Cadangan harian dibuat saat aplikasi dinyalakan (kalau hari itu belum ada), lalu diperiksa lagi setiap 30 menit. Kalau aplikasi dibiarkan menyala melewati tengah malam, cadangan hari berikutnya ikut dibuat. Kalau aplikasi tidak dinyalakan sama sekali pada suatu hari, hari itu tidak punya cadangan, karena memang tidak ada data yang berubah.
- **Memulihkan cadangan otomatis:** di halaman Pengaturan, bagian **Cadangan otomatis**, tekan **Pulihkan** pada cadangan yang diinginkan.
- Cadangan "sebelum pemulihan" dan "sebelum pembaruan" yang sudah tidak diperlukan boleh Anda hapus sendiri dari folder itu.
- **Kalau aplikasi tidak bisa dibuka sama sekali:** hentikan aplikasi (Ctrl+C), salin salah satu file dari `data/backups/` menjadi `data/productivity.db`, lalu jalankan lagi.

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

## 9. Fitur AI (opsional)

Aplikasi bisa memakai **Claude** dari Anthropic untuk fitur-fitur pintar. Fitur ini **opsional dan berbayar** (bayar sesuai pemakaian). Tanpa AI, semua fitur lain tetap bekerja penuh. Kalau API key kosong, paket belum terpasang, internet mati, atau batas bulanan tercapai, hanya fitur AI yang menampilkan pesan; aplikasi tetap berjalan.

> **Penting:** API key ibarat kata sandi yang bisa memakai saldo Anda. Jangan pernah menempelkannya ke chat, email, atau GitHub. Simpan **hanya** di file `.env` seperti langkah di bawah.

### Langkah 1: buat API key

1. Buka **https://platform.claude.com**, lalu daftar atau masuk. (Langganan claude.ai **terpisah** dari API; API dibayar sendiri sesuai pemakaian.)
2. Buka menu **Billing**, lalu isi kredit. Untuk mulai, $5 sudah cukup untuk pemakaian pribadi berminggu-minggu.
3. *(Disarankan)* Di menu **Limits**, atur batas belanja bulanan sebagai pengaman kedua, selain batas di aplikasi ini.
4. Buka menu **API keys**, lalu tekan **Create key**. Beri nama, misalnya `Productivity di laptop`.
5. **Salin** key yang muncul (diawali `sk-ant-`). Key hanya ditampilkan **sekali**; kalau terlewat, buat key baru saja.

### Langkah 2: taruh API key di file `.env`

1. Di folder aplikasi, salin file contoh menjadi `.env`:
   - Mac / Linux / Raspberry Pi: `cp .env.example .env`
   - Windows (Command Prompt): `copy .env.example .env`
2. Buka file `.env` dengan editor teks biasa (Notepad di Windows; di Mac pakai TextEdit lalu pilih Format → Make Plain Text).
3. Tempelkan key **langsung setelah** tanda `=`, tanpa spasi dan tanpa tanda kutip:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxx...
   ```
4. Simpan file.
5. *(Cek)* Jalankan `git status`. File `.env` **tidak boleh** muncul di daftar itu. File ini sudah diatur supaya diabaikan Git, jadi tidak akan pernah ter-upload ke GitHub.

**Kalau key sampai bocor** (misalnya tidak sengaja dibagikan): buka platform.claude.com → **API keys**, hapus key itu, buat key baru, lalu ganti isi `.env`.

### Langkah 3: pasang paket `anthropic` (sekali saja)

Fitur AI butuh **Python 3.10 atau lebih baru** dan satu paket resmi dari Anthropic:

```
python3 -m pip install -r requirements.txt
```

(Windows: `python -m pip install -r requirements.txt`.)

*Di Raspberry Pi OS versi baru*, perintah di atas bisa ditolak dengan pesan `externally-managed-environment`. Kalau begitu, pakai lingkungan Python tersendiri:

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python server.py          (jalankan aplikasi dengan perintah ini)
```

### Langkah 4: jalankan ulang & nyalakan

1. Hentikan aplikasi (Ctrl+C), lalu jalankan lagi. File `.env` hanya dibaca saat aplikasi dinyalakan.
2. Buka **Pengaturan** → bagian **Fitur AI**. Status harus berbunyi **"Siap dipakai"**. Kalau belum, pesannya menjelaskan apa yang kurang.
3. Nyalakan **Nyalakan fitur AI**, lalu tekan **Uji koneksi**. Ini mengirim satu permintaan kecil (kurang dari $0,01). Kalau berhasil, muncul kotak bertanda **Jawaban AI**.

### Model yang dipakai dan perkiraan biaya

Aplikasi memakai dua model, dan keduanya bisa diganti di Pengaturan:

| Pekerjaan | Model bawaan | Alasan | Harga per 1 juta token (masukan / keluaran) |
|---|---|---|---|
| **Tugas sederhana**, misalnya menafsirkan input cepat | Claude **Haiku 4.5** | Model tercepat dan termurah; cukup untuk mengenali tanggal, prioritas, kategori | $1 / $5 |
| **Perencanaan & asisten** | Claude **Opus 5.5** | Model yang dianjurkan Anthropic untuk pekerjaan yang butuh penalaran | $4 / $20 |
| *(pilihan lain)* | Claude **Sonnet 5.5** | Setengah harga Opus, masih cerdas; pilih ini kalau ingin lebih hemat | $2 / $10 |

"Token" kira-kira sepotong kata. 1 juta token setara ratusan halaman teks. Perkiraan biaya untuk fitur-fitur AI yang direncanakan:

| Pemakaian | Perkiraan per kali |
|---|---|
| Menafsirkan satu kalimat input cepat (Haiku 4.5) | ± $0,002 |
| Memecah satu tugas menjadi subtugas (Opus 5.5) | ± $0,04 |
| Menyusun rencana hari ini (Opus 5.5) | ± $0,08 |
| Satu pertanyaan ke asisten (Opus 5.5) | ± $0,05 |
| Ringkasan tinjauan mingguan (Opus 5.5) | ± $0,08 |

Untuk **pemakaian pribadi sehari-hari**, misalnya 10 input cepat, 1 rencana harian, dan beberapa pertanyaan ke asisten per hari, perkiraannya **$5–12 per bulan** dengan Opus 5.5, atau **$3–6 per bulan** dengan Sonnet 5.5. Pemakaian ringan (input cepat dan rencana harian saja) sekitar **$3 per bulan**. Batas bawaan di aplikasi **$5 per bulan**; ubah sesuai kebutuhan. Untuk gambaran dalam rupiah, kalikan dengan kurs dolar saat ini.

Catatan:
- Angka di halaman Pengaturan adalah **perkiraan** dari jumlah token. Tagihan resmi ada di platform.claude.com (menu **Usage**).
- Saat batas bulanan tercapai, fitur AI berhenti sampai awal bulan berikutnya. Permintaan yang sedang berjalan tetap diselesaikan, jadi pemakaian bisa sedikit melewati batas.
- Untuk Sonnet 5.5 dan Opus 5.5, fitur **cadangan otomatis** Anthropic (*fallbacks*) aktif. Kalau model menolak sebuah permintaan karena filter keamanannya, Anthropic otomatis meneruskannya ke model lain yang sesuai. Biayanya ikut dihitung.
- Claude Haiku 4.5 masih aktif, tapi model lama suatu saat dipensiunkan (Anthropic memberi tahu minimal 60 hari sebelumnya). Kalau itu terjadi, aplikasi menampilkan "Model … tidak tersedia"; cukup pilih Sonnet 5.5 di Pengaturan.

### Privasi & keamanan

- Semua permintaan ke Claude dikirim **dari server** (komputer Anda), tidak pernah langsung dari browser. API key tidak pernah dikirim ke browser.
- Yang dikirim ke Anthropic hanya data yang dibutuhkan untuk permintaan itu, bukan seluruh database.
- Yang dicatat aplikasi hanya jumlah token dan perkiraan biaya per bulan, bukan isi pertanyaan atau jawaban.
- Setiap hasil AI ditandai **"Usulan AI"** dan tidak mengubah data apa pun tanpa persetujuan Anda.

### Masalah umum fitur AI

| Pesan | Penyebab & solusi |
|---|---|
| "API key belum diisi" | File `.env` belum ada, key belum ditempel, atau aplikasi belum dijalankan ulang setelah mengisi `.env`. |
| "Paket 'anthropic' belum terpasang" | Lakukan Langkah 3, lalu jalankan ulang aplikasi. |
| "API key ditolak" | Key salah ketik, terpotong, atau sudah dihapus. Buat key baru dan ganti isi `.env`. |
| "Kredit akun Anthropic Anda habis" | Isi ulang di platform.claude.com → **Billing**. |
| "Tidak bisa terhubung ke layanan AI" | Internet mati. Fitur lain tetap bisa dipakai. |
| "Batas pemakaian AI bulan ini sudah tercapai" | Tunggu bulan depan, atau naikkan batas di Pengaturan. |

## Untuk pengembangan

### Teknologi

- **Python** (pustaka bawaan saja): server web (`http.server`) dan database (`sqlite3`).
- **SQLite**: database dalam satu file.
- **HTML, CSS, JavaScript biasa**: tanpa *framework* dan tanpa langkah *build*.
- **Opsional, khusus fitur AI:** paket resmi `anthropic` (lihat `requirements.txt`). Aplikasi tetap berjalan tanpa paket ini.

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
    backup.py             API ekspor, pemulihan, dan daftar cadangan
    ai.py                 API status fitur AI & uji koneksi
  backup.py               logika cadangan & pemulihan, termasuk cadangan harian
  ai.py                   satu-satunya pintu ke Claude API (pemeriksaan, batas bulanan, pesan error, biaya)
  ai_models.py            daftar model Claude & harganya
  env.py                  membaca file .env (API key)
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
    views/                satu file per halaman (today.js, all-tasks.js, focus.js, categories.js, settings.js)
tests/                    tes otomatis Python (python3 -m unittest)
  js/                     tes kode tampilan (JavaScript), dijalankan otomatis bila Node.js ada
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
| GET | `/api/backup/export` | Unduh seluruh data (file `.db`) |
| POST | `/api/backup/restore` | Pulihkan dari file yang diunggah (`Content-Type: application/octet-stream`) |
| GET | `/api/backup/automatic` | Daftar cadangan di `data/backups/` |
| POST | `/api/backup/automatic/restore` | Pulihkan dari salah satu cadangan itu: `name` |
| GET | `/api/ai/status` | Keadaan fitur AI, model, batas & pemakaian bulan ini (tanpa API key) |
| POST | `/api/ai/test` | Uji koneksi ke Claude: `tier` (`simple` / `smart`) |

### Tes otomatis

Tes otomatis memeriksa bahwa fungsi-fungsi penting aplikasi masih bekerja dengan benar. Jalankan di folder aplikasi dengan **satu perintah**:

```
python3 -m unittest
```

(Di Windows: `python -m unittest`.)

**Membaca hasilnya:**
- Baris terakhir `OK` berarti semua tes lolos.
- `OK (skipped=1)` juga berarti lolos; tes JavaScript dilewati karena Node.js belum terpasang (lihat di bawah).
- `FAILED (failures=…)` berarti ada yang rusak. Di atasnya tertulis nama tes yang gagal dan alasannya.

Tes memakai **database sementara**, jadi data asli Anda tidak tersentuh, dan aplikasi boleh tetap berjalan saat tes dijalankan.

**Yang diuji:**

| Bagian | File tes | Contoh yang diperiksa |
|---|---|---|
| Tugas | `tests/test_tasks.py` | tambah/edit/hapus, selesai & dikembalikan, deadline, prioritas, urutan, halaman "Hari ini" |
| Kategori | `tests/test_categories.py` | buat/ganti nama/hapus, filter, menghapus kategori tidak menghapus tugas |
| Timer fokus (server) | `tests/test_focus.py` | durasi, pencatatan sesi, total fokus per tugas |
| Timer fokus (browser) | `tests/js/focus-timer.test.mjs` | hitung mundur, jeda, berhenti, lewati, tetap jalan setelah halaman dimuat ulang, selesai saat aplikasi tertutup, dua tab tidak mencatat ganda |
| Tanggal di tampilan | `tests/js/dates.test.mjs` | "Terlambat 2 hari", "Besok", akhir bulan/tahun, tahun kabisat, pergantian jam musim panas |
| Cadangan & pemulihan | `tests/test_backup.py` | unduh lalu pulihkan, file salah/rusak ditolak, cadangan harian (7 terakhir) |
| Database | `tests/test_db.py` | pembaruan struktur tanpa kehilangan data, cadangan sebelum pembaruan |
| Data permanen | `tests/test_persistence.py` | data tetap ada setelah server dimatikan paksa lalu dinyalakan lagi |
| Server | `tests/test_system.py` | jenis file benar, file di luar folder `static/` tidak bisa dibuka, batas ukuran data |
| Fitur AI | `tests/test_ai.py` | AI mati / key kosong / batas tercapai tidak memanggil AI, perhitungan biaya, API key tidak bocor ke browser, `.env` diabaikan Git |
| Fitur AI + SDK asli | `tests/test_ai_sdk.py` | bentuk permintaan SDK `anthropic` yang sebenarnya dan terjemahan error (key ditolak, model tidak ada, server sibuk, internet mati); dilewati bila paket belum terpasang |

**Tes JavaScript (opsional):** tes bagian browser (timer & tanggal) butuh [Node.js](https://nodejs.org/) versi 22 atau lebih baru. Node.js **tidak** dibutuhkan untuk menjalankan aplikasi. Kalau belum terpasang, tes ini dilewati dan tes lainnya tetap berjalan. Tes ini dijalankan dua kali dengan zona waktu berbeda, supaya perhitungan tanggal terbukti benar di mana pun. Untuk menjalankannya sendiri: `node --test "tests/js/*.test.mjs"`.

**Tes tidak pernah memanggil Claude API sungguhan.** `tests/__init__.py` mengosongkan API key dan mengarahkan alamat API ke alamat lokal yang tidak ada. Tes AI memakai "Claude tiruan" atau server Anthropic tiruan di komputer sendiri, jadi tidak ada biaya.

**Aturan saat menambah fitur:** setiap fitur baru disertai tes baru, dan `python3 -m unittest` harus `OK` sebelum perubahan di-commit.
