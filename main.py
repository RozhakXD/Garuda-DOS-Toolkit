import argparse
import sys
import os
import yaml
from urllib.parse import urlparse

from garuda.core.engine import GarudaEngine

def display_disclaimer():
    """
    Menampilkan pesan disclaimer pada saat program dijalankan.

    Behavior:
        - Menampilkan peringatan kepada pengguna untuk menggunakan tool ini secara bertanggung jawab.
        - Menyatakan bahwa tool ini dibuat untuk tujuan edukasi dan pengujian keamanan siber.
    """
    print("━" * 60)
    print("PERINGATAN: Gunakan tool ini secara bertanggung jawab.")
    print("Tool ini dibuat untuk tujuan edukasi dan pengujian keamanan siber.")
    print("Penulis tidak bertanggung jawab atas penyalahgunaan apa pun.")
    print("━" * 60, "\n")

def create_argument_parser() -> argparse.ArgumentParser:
    """
    Membuat dan mengkonfigurasi parser untuk argumen command-line.

    Returns:
        argparse.ArgumentParser: Parser yang dikonfigurasi untuk membaca argumen CLI.

    Behavior:
        - Menyediakan opsi untuk menentukan target, metode serangan, file konfigurasi, dan parameter lainnya.
        - Menampilkan contoh penggunaan di bagian epilog.
    """
    parser = argparse.ArgumentParser(
        description="Garuda: Toolkit Pengujian Beban Tingkat Lanjut.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Contoh penggunaan:\n"
            "  python main.py --config config.example.yaml\n"
            "  python main.py http://target.com -m http-flood -c 500\n"
            "  python main.py --config config.yaml -c 1000  (override koneksi)"
        )
    )
    parser.add_argument("target", nargs='?', default=None, help="URL target lengkap (contoh: http://example.com).")
    parser.add_argument("-m", "--method", choices=['http-flood', 'slowloris', 'mixed'], help="Metode serangan yang akan digunakan.")
    
    parser.add_argument("--config", help="Jalur ke file konfigurasi YAML.")
    parser.add_argument("--attacks", nargs='+', choices=['http-flood', 'slowloris'], help="(Hanya untuk mode 'mixed') Daftar serangan yang akan digabungkan.")
    parser.add_argument("-c", "--connections", type=int, help="Jumlah koneksi simultan per serangan.")
    parser.add_argument("-d", "--duration", type=int, help="Durasi serangan dalam detik.")
    parser.add_argument("--confirm-target", help="Konfirmasi nama domain target untuk mencegah kesalahan.")
    parser.add_argument("--stealth", action='store_true', help="Aktifkan mode siluman (hanya untuk http-flood).")
    return parser

def main():
    """
    Titik masuk utama yang sekarang mendukung file konfigurasi.

    Behavior:
        - Menampilkan disclaimer kepada pengguna.
        - Membaca argumen dari command-line dan/atau file konfigurasi YAML.
        - Menggabungkan argumen dari CLI dan file konfigurasi.
        - Memvalidasi argumen yang diperlukan seperti target dan metode serangan.
        - Memulai serangan menggunakan `GarudaEngine`.

    Exceptions:
        - Menghentikan program jika file konfigurasi tidak ditemukan.
        - Menampilkan pesan kesalahan jika argumen tidak valid atau terjadi kesalahan selama eksekusi.
    """
    display_disclaimer()
    
    parser = create_argument_parser()
    args = parser.parse_args()
    
    config_from_file = {}
    if args.config:
        if not os.path.exists(args.config):
            print(f"[FATAL] File konfigurasi tidak ditemukan: {args.config}", file=sys.stderr)
            sys.exit(1)
        with open(args.config, 'r') as f:
            config_from_file = yaml.safe_load(f) or {}

    final_args = argparse.Namespace()
    
    for key, value in config_from_file.items():
        setattr(final_args, key, value)
        
    for key, value in vars(args).items():
        if value is not None and value is not False:
            setattr(final_args, key, value)

    if not getattr(final_args, 'target', None) or not getattr(final_args, 'method', None):
        parser.error("argumen 'target' dan '-m/--method' wajib diisi (baik via CLI atau file config).")
    
    if final_args.method == 'mixed' and not getattr(final_args, 'attacks', None):
        parser.error("argumen --attacks wajib diisi saat menggunakan metode 'mixed'.")
        
    if not hasattr(final_args, 'connections'): final_args.connections = 100
    if not hasattr(final_args, 'duration'): final_args.duration = 60
    if not hasattr(final_args, 'stealth'): final_args.stealth = False

    target_domain = urlparse(final_args.target).hostname
    if getattr(final_args, 'confirm_target', None) and final_args.confirm_target != target_domain:
        print(f"[ERROR] Nama domain pada --confirm-target ('{final_args.confirm_target}') tidak cocok dengan target ('{target_domain}').", file=sys.stderr)
        sys.exit(1)

    try:
        engine = GarudaEngine(final_args)
        engine.start()
        print("\n[SUCCESS] Sesi serangan telah selesai dengan normal.")
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n[FATAL] Terjadi kesalahan yang tidak terduga: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()