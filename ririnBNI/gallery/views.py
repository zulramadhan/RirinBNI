from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# ========== HALAMAN UTAMA ==========
def daftar_nasabah(request):
    nasabah = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT no_urut, nama_debitur, id_debitur, id_pinjaman, 
                no_telepon, email, alamat, tanggal_lahir, nik, password
                FROM data_nasabah 
                WHERE nama_debitur IS NOT NULL 
                AND LENGTH(nama_debitur) > 2
                AND nama_debitur NOT LIKE '%ZZ%'
                AND nama_debitur NOT LIKE '%aci%'
                ORDER BY no_urut
            """)
            nasabah = cursor.fetchall()
    except Exception:
        pass
    
    context = {
        'nasabah_list': nasabah,
        'total_nasabah': len(nasabah)
    }
    return render(request, 'data_nasabah.html', context)

def login_nasabah(request):
    if request.method == 'POST':
        nik = request.POST.get('nik')
        password = request.POST.get('password')
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT no_urut, nama_debitur, nik, password 
                FROM data_nasabah 
                WHERE nik = %s
            """, [nik])
            row = cursor.fetchone()
        
        if row:
            db_password = row[3]
            if password == db_password:
                request.session['nasabah_id'] = row[0]
                request.session['nasabah_nik'] = nik
                request.session['nasabah_nama'] = row[1]
                return redirect('dashboard_nasabah')
        
        return render(request, 'nasabah/login.html', {'error': 'NIK atau password salah'})
    
    return render(request, 'nasabah/login.html')

def dashboard_nasabah(request):
    if not request.session.get('nasabah_id'):
        return redirect('login_nasabah')
    return render(request, 'nasabah/dashboard.html')

def login_administrator(request):
    if request.method == 'POST':
        nik = request.POST.get('nik')
        password = request.POST.get('password')
        if nik == "123456" and password == "123456":
            request.session['administrator_id'] = 1
            request.session['administrator_nik'] = nik
            request.session['administrator_nama'] = 'Administrator BNI'
            return redirect('dashboard_administrator')
    return render(request, 'administrator/adminlogin.html')

def dashboard_administrator(request):
    if not request.session.get('administrator_id'):
        return redirect('login_administrator')
    context = {
        'nama_admin': request.session.get('administrator_nama', 'Administrator'),
        'nik_admin': request.session.get('administrator_nik', ''),
    }
    return render(request, 'administrator/dashboard.html', context)

        


# ========== API UNTUK NASABAH ==========
def api_nasabah_profil(request):
    if not request.session.get('nasabah_id'):
        return JsonResponse({'success': False, 'error': 'Not logged in'}, status=401)
    
    nasabah_id = request.session.get('nasabah_id')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT no_urut, nama_debitur, nik, email, no_telepon, alamat, 
                tanggal_lahir, limit_pinjaman, jumlah_pinjaman, sisa_pinjaman
                FROM data_nasabah 
                WHERE no_urut = %s
            """, [nasabah_id])
            row = cursor.fetchone()
        
        if row:
            data = {
                'id_nasabah': row[0],
                'nama_lengkap': row[1],
                'nik': row[2],
                'email': row[3] if row[3] else '-',
                'no_telepon': row[4] if row[4] else '-',
                'alamat': row[5] if row[5] else '-',
                'tanggal_lahir': str(row[6]) if row[6] else '-',
                'limit_pinjaman': float(row[7]) if row[7] else 0,
                'jumlah_pinjaman': float(row[8]) if row[8] else 0,
                'sisa_pinjaman': float(row[9]) if row[9] else 0,
                'saldo_aktif': (float(row[7]) if row[7] else 0) - (float(row[8]) if row[8] else 0)
            }
            return JsonResponse({'success': True, 'data': data})
        else:
            return JsonResponse({'success': False, 'error': 'Nasabah tidak ditemukan'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def api_nasabah_pinjaman(request):
    if not request.session.get('nasabah_id'):
        return JsonResponse({'success': False, 'error': 'Not logged in'}, status=401)
    
    nasabah_id = request.session.get('nasabah_id')
    
    try:
        with connection.cursor() as cursor:
            # Ambil dari database
            cursor.execute("""
                SELECT id_pinjaman, id_debitur, jumlah_pinjaman, bunga, tenor, 
                       cicilan_perbulan, sisa_pinjaman, tanggal_pinjaman, status,
                       tanggal_pwlunasan
                FROM data_nasabah 
                WHERE no_urut = %s
            """, [nasabah_id])
            row = cursor.fetchone()
        
        if row and row[2] > 0:  # Ada pinjaman
            tanggal_mulai = row[7]
            tenor_bulan = row[4] or 0
            
            if tanggal_mulai and tenor_bulan:
                if isinstance(tanggal_mulai, str):
                    tanggal_mulai = datetime.strptime(tanggal_mulai, '%Y-%m-%d').date()
                tanggal_selesai = tanggal_mulai + relativedelta(months=tenor_bulan)
                tanggal_selesai_str = tanggal_selesai.strftime('%Y-%m-%d')
            else:
                tanggal_selesai_str = '-'
            
            data = {
                'id_pinjaman': row[0] if row[0] else '-',
                'id_nasabah': row[1] if row[1] else '-',
                'jumlah_pinjaman': float(row[2]) if row[2] else 0,
                'bunga': float(row[3]) if row[3] else 0,
                'tenor': int(row[4]) if row[4] else 0,
                'cicilan_perbulan': float(row[5]) if row[5] else 0,
                'sisa_pinjaman': float(row[6]) if row[6] else 0,
                'tanggal_mulai': str(row[7]) if row[7] else '-',
                'tanggal_selesai': tanggal_selesai_str,
                'status': row[8] if row[8] else 'AKTIF'
            }
            return JsonResponse({'success': True, 'data': data})
        else:
            # Nasabah belum punya pinjaman
            return JsonResponse({
                'success': True, 
                'data': {
                    'id_pinjaman': '-',
                    'id_nasabah': str(nasabah_id),
                    'jumlah_pinjaman': 0,
                    'bunga': 0,
                    'tenor': 0,
                    'cicilan_perbulan': 0,
                    'sisa_pinjaman': 0,
                    'tanggal_mulai': '-',
                    'tanggal_selesai': '-',
                    'status': 'TIDAK AKTIF'
                }
            })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def api_nasabah_riwayat(request):
    if not request.session.get('nasabah_id'):
        return JsonResponse({'success': False, 'error': 'Not logged in'}, status=401)
    
    nasabah_id = request.session.get('nasabah_id')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COALESCE(tgl_bayar, NOW()), 
                    COALESCE(periode, '-'), 
                    COALESCE(nominal, 0), 
                    COALESCE(metode, '-'), 
                    COALESCE(status, 'SUCCESS')
                FROM riwayat_pembayaran 
                WHERE id_nasabah = %s
                ORDER BY tgl_bayar DESC
                LIMIT 10
            """, [nasabah_id])
            rows = cursor.fetchall()
            
            data = []
            for row in rows:
                data.append({
                    'tgl_bayar': str(row[0]) if row[0] else '-',
                    'periode': row[1],
                    'nominal': float(row[2]) if row[2] else 0,
                    'metode': row[3],
                    'status': row[4]
                })
            return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': True, 'data': []})


@csrf_exempt
@require_http_methods(["POST"])
def api_nasabah_bayar(request):
    if not request.session.get('nasabah_id'):
        return JsonResponse({'success': False, 'error': 'Not logged in'}, status=401)
    
    try:
        data = json.loads(request.body)
        angsuran_id = data.get('angsuran_id')  # 1, 2, atau 3 (bulan ke-berapa)
        metode = data.get('metode')
        nasabah_id = request.session.get('nasabah_id')
        
        with connection.cursor() as cursor:
            # Ambil data tagihan nasabah
            cursor.execute("""
                SELECT tagihan_bulan, tagihan_jumlah, tagihan_status, 
                       jumlah_pinjaman, sisa_pinjaman, cicilan_perbulan
                FROM data_nasabah 
                WHERE no_urut = %s
            """, [nasabah_id])
            row = cursor.fetchone()
            
            if not row:
                return JsonResponse({'success': False, 'error': 'Data nasabah tidak ditemukan'})
            
            # Parse tagihan (format: "Bulan ke-1, Bulan ke-2, Bulan ke-3")
            tagihan_bulan_list = row[0].split(', ') if row[0] else []
            tagihan_jumlah = float(row[1]) if row[1] else 0
            tagihan_status_list = row[2].split(', ') if row[2] else []
            sisa_pinjaman = float(row[4]) if row[4] else 0
            
            # Cek apakah angsuran_id valid
            if angsuran_id > len(tagihan_bulan_list):
                return JsonResponse({'success': False, 'error': 'Tagihan tidak ditemukan'})
            
            idx = angsuran_id - 1
            
            # Cek apakah sudah lunas
            if tagihan_status_list[idx] == 'Lunas':
                return JsonResponse({'success': False, 'error': 'Tagihan ini sudah lunas!'})
            
            # Update status tagihan jadi Lunas
            tagihan_status_list[idx] = 'Lunas'
            
            # Update sisa pinjaman
            sisa_pinjaman_baru = sisa_pinjaman - tagihan_jumlah
            if sisa_pinjaman_baru < 0:
                sisa_pinjaman_baru = 0
            
            # Update ke database
            cursor.execute("""
                UPDATE data_nasabah 
                SET tagihan_status = %s,
                    sisa_pinjaman = %s,
                    status = CASE WHEN %s <= 0 THEN 'LUNAS' ELSE 'AKTIF' END
                WHERE no_urut = %s
            """, [', '.join(tagihan_status_list), sisa_pinjaman_baru, sisa_pinjaman_baru, nasabah_id])
            
            # Simpan ke riwayat pembayaran
            cursor.execute("""
                INSERT INTO riwayat_pembayaran (id_nasabah, periode, nominal, metode, status, tgl_bayar)
                VALUES (%s, %s, %s, %s, 'SUCCESS', CURRENT_TIMESTAMP)
            """, [nasabah_id, tagihan_bulan_list[idx], tagihan_jumlah, metode])
            
            return JsonResponse({
                'success': True, 
                'message': f'Pembayaran {tagihan_bulan_list[idx]} sebesar Rp {int(tagihan_jumlah):,} berhasil!',
                'sisa_pinjaman': sisa_pinjaman_baru
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ========== API UNTUK ADMINISTRATOR ==========

# API 1: Data Nasabah (tabel utama)
def api_administrator_nasabah(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT no_urut, nama_debitur, id_debitur, id_pinjaman, 
                       COALESCE(no_telepon, '-'), 
                       COALESCE(email, '-'), 
                       COALESCE(alamat, '-'), 
                       tanggal_lahir, 
                       COALESCE(nik, '-'), 
                       COALESCE(limit_pinjaman, 0) as limit_pinjaman,  -- <-- WAJIB ADA!
                       COALESCE(password, '-')
                FROM data_nasabah 
                WHERE nama_debitur IS NOT NULL 
                AND LENGTH(nama_debitur) > 2
                ORDER BY no_urut
            """)
            rows = cursor.fetchall()
            
            data = []
            for row in rows:
                data.append({
                    'no_urut': row[0],
                    'nama_debitur': row[1],
                    'id_debitur': row[2],
                    'id_pinjaman': row[3],
                    'no_telepon': row[4],
                    'email': row[5],
                    'alamat': row[6],
                    'tanggal_lahir': str(row[7]) if row[7] else '-',
                    'nik': row[8],
                    'limit_pinjaman': float(row[9]) if row[9] else 0,  # <-- index ke-9
                    'password': row[10]
                })
            return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# API 2: SEMUA DATA TABEL TAMBAHAN (Tanggal Pinjaman, Jaminan, HT, Kluise) dalam 1 API
def api_administrator_all_extra_tables(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    -- Tanggal Pinjaman (pake TO_CHAR buat konversi date ke string)
                    COALESCE(TO_CHAR(tanggal_pinjaman, 'YYYY-MM-DD'), '') as tanggal_pinjaman,
                    COALESCE(TO_CHAR(tanggal_pwlunasan, 'YYYY-MM-DD'), '') as tanggal_pelunasan,
                    COALESCE(tipe_pinjaman, '') as tipe_pinjaman,
                    COALESCE(bunga, 0) as bunga,
                    COALESCE(no_skk, '') as no_skk,
                    COALESCE(TO_CHAR(tanggal_skk, 'YYYY-MM-DD'), '') as tanggal_skk,
                    COALESCE(no_pk_perjanjian, '') as no_pk_perjanjian,
                    COALESCE(TO_CHAR(tanggal_pk, 'YYYY-MM-DD'), '') as tanggal_pk,
                    
                    -- Jaminan (pake tgl_agunan)
                    COALESCE(jaminan, '') as jaminan,
                    COALESCE(no_agunan, '') as no_agunan,
                    COALESCE(TO_CHAR(tgl_agunan, 'YYYY-MM-DD'), '') as tanggal_agunan,
                    COALESCE(nama_pemilik_agunan, '') as nama_pemilik_agunan,
                    
                    -- HT (pake tgl_ht)
                    COALESCE(jenis_pengikat, '') as jenis_pengikat,
                    COALESCE(no_ht, '') as no_ht,
                    COALESCE(TO_CHAR(tgl_ht, 'YYYY-MM-DD'), '') as tanggal_ht,
                    COALESCE(no_asuransi, '') as no_asuransi,
                    COALESCE(asuransi, '') as asuransi,
                    
                    -- Lokasi Kluise
                    COALESCE(kluise_1, '') as kluise_1,
                    COALESCE(kluise_2, '') as kluise_2,
                    COALESCE(lemari_file, '') as lemari_file,
                    COALESCE(no_file, '') as no_file,
                    COALESCE(keterangan, '') as keterangan
                    
                FROM data_nasabah 
                WHERE nama_debitur IS NOT NULL
                ORDER BY no_urut
            """)
            rows = cursor.fetchall()
            
            data = []
            for row in rows:
                data.append({
                    # Tanggal Pinjaman
                    'tanggal_pinjaman': row[0] if row[0] else '-',
                    'tanggal_pelunasan': row[1] if row[1] else '-',
                    'tipe_pinjaman': row[2] if row[2] else '-',
                    'bunga': float(row[3]) if row[3] else 0,
                    'no_skk': row[4] if row[4] else '-',
                    'tanggal_skk': row[5] if row[5] else '-',
                    'no_pk_perjanjian': row[6] if row[6] else '-',
                    'tanggal_pk': row[7] if row[7] else '-',
                    
                    # Jaminan
                    'jaminan': row[8] if row[8] else '-',
                    'no_agunan': row[9] if row[9] else '-',
                    'tanggal_agunan': row[10] if row[10] else '-',
                    'nama_pemilik_agunan': row[11] if row[11] else '-',
                    
                    # HT
                    'jenis_pengikat': row[12] if row[12] else '-',
                    'no_ht': row[13] if row[13] else '-',
                    'tanggal_ht': row[14] if row[14] else '-',
                    'no_asuransi': row[15] if row[15] else '-',
                    'asuransi': row[16] if row[16] else '-',
                    
                    # Kluise
                    'kluise_1': row[17] if row[17] else '-',
                    'kluise_2': row[18] if row[18] else '-',
                    'lemari_file': row[19] if row[19] else '-',
                    'no_file': row[20] if row[20] else '-',
                    'keterangan': row[21] if row[21] else '-'
                })
            
            return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': True, 'data': [], 'error': str(e)})


    # API: Data Pinjaman Semua Nasabah
def api_administrator_pinjaman(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COALESCE(id_pinjaman, '-') as id_pinjaman,
                    COALESCE(id_debitur, '-') as id_nasabah,
                    COALESCE(nama_debitur, '-') as nama_nasabah,
                    COALESCE(jumlah_pinjaman, 0) as jumlah_pinjaman,
                    COALESCE(bunga, 0) as bunga,
                    COALESCE(tenor, 0) as tenor,
                    COALESCE(cicilan_perbulan, 0) as cicilan_perbulan,
                    COALESCE(sisa_pinjaman, 0) as sisa_pinjaman,
                    CASE 
                        WHEN COALESCE(jumlah_pinjaman, 0) = 0 THEN 'BELUM ADA PINJAMAN'
                        WHEN COALESCE(sisa_pinjaman, 0) <= 0 THEN 'LUNAS'
                        ELSE 'AKTIF'
                    END as status
                FROM data_nasabah 
                WHERE nama_debitur IS NOT NULL 
                AND LENGTH(nama_debitur) > 2
                ORDER BY no_urut
            """)
            rows = cursor.fetchall()
            
            data = []
            for row in rows:
                data.append({
                    'id_pinjaman': row[0],
                    'id_nasabah': row[1],
                    'nama_nasabah': row[2],
                    'jumlah_pinjaman': float(row[3]) if row[3] else 0,
                    'bunga': float(row[4]) if row[4] else 0,
                    'tenor': int(row[5]) if row[5] else 0,
                    'cicilan_perbulan': float(row[6]) if row[6] else 0,
                    'sisa_pinjaman': float(row[7]) if row[7] else 0,
                    'status': row[8]
                })
            return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# API 4: Dashboard Stats
def api_administrator_dashboard(request):
    try:
        with connection.cursor() as cursor:
            # Total nasabah
            cursor.execute("""
                SELECT COUNT(*) FROM data_nasabah 
                WHERE nama_debitur IS NOT NULL 
                AND LENGTH(nama_debitur) > 2
            """)
            total_nasabah = cursor.fetchone()[0] or 0
            
            # Total pinjaman aktif
            cursor.execute("""
                SELECT COALESCE(SUM(jumlah_pinjaman), 0) FROM data_nasabah 
                WHERE sisa_pinjaman > 0 AND jumlah_pinjaman > 0
            """)
            total_pinjaman_aktif = float(cursor.fetchone()[0] or 0)
            
            # Total pendapatan
            cursor.execute("""
                SELECT COALESCE(SUM(jumlah_pinjaman * bunga / 100), 0) FROM data_nasabah 
                WHERE sisa_pinjaman > 0
            """)
            total_pendapatan = float(cursor.fetchone()[0] or 0)
            
            # Transaksi terbaru
            cursor.execute("""
                SELECT 
                    COALESCE(tanggal_pinjaman, NOW()) as tanggal,
                    nama_debitur as nasabah,
                    'PEMBAYARAN' as jenis,
                    COALESCE(cicilan_perbulan, 0) as jumlah,
                    CASE WHEN sisa_pinjaman <= 0 THEN 'LUNAS' ELSE 'AKTIF' END as status
                FROM data_nasabah 
                WHERE nama_debitur IS NOT NULL 
                AND cicilan_perbulan > 0
                ORDER BY tanggal_pinjaman DESC
                LIMIT 5
            """)
            transaksi_rows = cursor.fetchall()
            transaksi_terbaru = []
            for row in transaksi_rows:
                transaksi_terbaru.append({
                    'tanggal': str(row[0]) if row[0] else '-',
                    'nasabah': row[1],
                    'jenis': row[2],
                    'jumlah': float(row[3]) if row[3] else 0,
                    'status': row[4]
                })
            
            # Chart data
            cursor.execute("""
                SELECT 
                    TO_CHAR(DATE_TRUNC('month', tanggal_pinjaman), 'YYYY-MM') as bulan,
                    COUNT(*) as jumlah_pinjaman,
                    SUM(jumlah_pinjaman * bunga / 100) as pendapatan_bunga
                FROM data_nasabah 
                WHERE tanggal_pinjaman IS NOT NULL
                GROUP BY DATE_TRUNC('month', tanggal_pinjaman)
                ORDER BY bulan DESC
                LIMIT 6
            """)
            chart_rows = cursor.fetchall()
            
            chart_data = {
                'bulan': [],
                'jumlah_pinjaman': [],
                'pendapatan_bunga': []
            }
            
            for row in reversed(chart_rows):
                chart_data['bulan'].append(row[0])
                chart_data['jumlah_pinjaman'].append(float(row[1]) if row[1] else 0)
                chart_data['pendapatan_bunga'].append(float(row[2]) if row[2] else 0)
            
            return JsonResponse({
                'success': True,
                'total_nasabah': total_nasabah,
                'total_pinjaman_aktif': total_pinjaman_aktif,
                'total_pendapatan': total_pendapatan,
                'transaksi_terbaru': transaksi_terbaru,
                'chart_data': chart_data
            })
    except Exception as e:
        return JsonResponse({
            'success': True,
            'total_nasabah': 0,
            'total_pinjaman_aktif': 0,
            'total_pendapatan': 0,
            'transaksi_terbaru': [],
            'chart_data': {'bulan': [], 'jumlah_pinjaman': [], 'pendapatan_bunga': []}
        })



        # ========== API UNTUK STATISTIK TIPE PINJAMAN (DIAGRAM LINGKARAN) ==========
def api_administrator_tipe_pinjaman_stats(request):
    """API untuk mendapatkan statistik tipe pinjaman untuk diagram lingkaran"""
    try:
        with connection.cursor() as cursor:
            # Query untuk menghitung jumlah nasabah berdasarkan tipe pinjaman
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN tipe_pinjaman IS NULL OR tipe_pinjaman = '' THEN 'Belum Ditentukan'
                        WHEN tipe_pinjaman = 'KUR' THEN 'KUR'
                        WHEN tipe_pinjaman = 'KPR' THEN 'KPR'
                        WHEN tipe_pinjaman = 'KTA' THEN 'KTA'
                        ELSE tipe_pinjaman
                    END as tipe,
                    COUNT(*) as jumlah
                FROM data_nasabah 
                WHERE nama_debitur IS NOT NULL 
                AND LENGTH(nama_debitur) > 2
                GROUP BY 
                    CASE 
                        WHEN tipe_pinjaman IS NULL OR tipe_pinjaman = '' THEN 'Belum Ditentukan'
                        WHEN tipe_pinjaman = 'KUR' THEN 'KUR'
                        WHEN tipe_pinjaman = 'KPR' THEN 'KPR'
                        WHEN tipe_pinjaman = 'KTA' THEN 'KTA'
                        ELSE tipe_pinjaman
                    END
                ORDER BY jumlah DESC
            """)
            rows = cursor.fetchall()
            
            data = {
                'labels': [],
                'data': []
            }
            
            for row in rows:
                tipe = row[0]
                jumlah = row[1]
                data['labels'].append(tipe)
                data['data'].append(jumlah)
            
            return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e), 'data': {'labels': [], 'data': []}})


@csrf_exempt
@require_http_methods(["POST"])
def api_administrator_tambah_nasabah(request):
    try:
        data = json.loads(request.body)
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT COALESCE(MAX(no_urut), 0) + 1 FROM data_nasabah")
            next_no_urut = cursor.fetchone()[0]
            
            id_debitur = f"DB-{next_no_urut:03d}"
            id_pinjaman = f"LN-{next_no_urut:03d}"
            
            cursor.execute("""
                INSERT INTO data_nasabah (
                    no_urut, nama_debitur, id_debitur, id_pinjaman, 
                    no_telepon, email, alamat, tanggal_lahir, nik, password,
                    jumlah_pinjaman, bunga, tenor, cicilan_perbulan, sisa_pinjaman
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                next_no_urut,
                data.get('nama_lengkap'),
                id_debitur,
                id_pinjaman,
                data.get('no_telepon'),
                data.get('email'),
                data.get('alamat', '-'),
                data.get('tanggal_lahir') or None,
                data.get('nik'),
                data.get('password'),
                0, 0, 0, 0, 0
            ])
            
            return JsonResponse({'success': True, 'message': 'Nasabah berhasil ditambahkan'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def api_administrator_ubah_role(request):
    try:
        data = json.loads(request.body)
        return JsonResponse({'success': True, 'message': 'Role berhasil diubah'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})






# ========== TAMBAHKAN FUNGSI HAPUS NASABAH DI SINI ==========
@csrf_exempt
@require_http_methods(["POST"])
def api_administrator_hapus_nasabah(request):
    try:
        data = json.loads(request.body)
        no_urut = data.get('no_urut')
        
        with connection.cursor() as cursor:
            # Cek apakah nasabah ada
            cursor.execute("SELECT no_urut FROM data_nasabah WHERE no_urut = %s", [no_urut])
            if not cursor.fetchone():
                return JsonResponse({'success': False, 'error': 'Nasabah tidak ditemukan'})
            
            # Hapus nasabah
            cursor.execute("DELETE FROM data_nasabah WHERE no_urut = %s", [no_urut])
        
        return JsonResponse({'success': True, 'message': 'Nasabah berhasil dihapus'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# API 2: Tanggal Pinjaman (5 tabel tambahan - PART 1)
def api_administrator_tanggal_pinjaman(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COALESCE(tanggal_pinjaman, '-'), 
                       COALESCE(tanggal_pelunasan, '-'),
                       COALESCE(tipe_pinjaman, '-'),
                       COALESCE(bunga, 0),
                       COALESCE(no_skk, '-'),
                       COALESCE(tanggal_skk, '-'),
                       COALESCE(no_pk_perjanjian, '-'),
                       COALESCE(tanggal_pk, '-')
                FROM data_nasabah 
                WHERE nama_debitur IS NOT NULL
                ORDER BY no_urut
            """)
            rows = cursor.fetchall()
            
            data = []
            for row in rows:
                data.append({
                    'tanggal_pinjaman': str(row[0]) if row[0] else '-',
                    'tanggal_pelunasan': str(row[1]) if row[1] else '-',
                    'tipe_pinjaman': row[2],
                    'bunga': float(row[3]) if row[3] else 0,
                    'no_skk': row[4],
                    'tanggal_skk': str(row[5]) if row[5] else '-',
                    'no_pk_perjanjian': row[6],
                    'tanggal_pk': str(row[7]) if row[7] else '-'
                })
            return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': True, 'data': []})

# API 3: Jaminan
def api_administrator_jaminan(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COALESCE(jaminan, '-'),
                       COALESCE(no_agunan, '-'),
                       COALESCE(tanggal_agunan, '-'),
                       COALESCE(nama_pemilik_agunan, '-')
                FROM data_nasabah 
                WHERE nama_debitur IS NOT NULL
                ORDER BY no_urut
            """)
            rows = cursor.fetchall()
            
            data = []
            for row in rows:
                data.append({
                    'jaminan': row[0],
                    'no_agunan': row[1],
                    'tanggal_agunan': str(row[2]) if row[2] else '-',
                    'nama_pemilik_agunan': row[3]
                })
            return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': True, 'data': []})

# API 4: HT
def api_administrator_ht(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COALESCE(jenis_pengikat, '-'),
                       COALESCE(no_ht, '-'),
                       COALESCE(tanggal_ht, '-'),
                       COALESCE(no_asuransi, '-'),
                       COALESCE(asuransi, '-')
                FROM data_nasabah 
                WHERE nama_debitur IS NOT NULL
                ORDER BY no_urut
            """)
            rows = cursor.fetchall()
            
            data = []
            for row in rows:
                data.append({
                    'jenis_pengikat': row[0],
                    'no_ht': row[1],
                    'tanggal_ht': str(row[2]) if row[2] else '-',
                    'no_asuransi': row[3],
                    'asuransi': row[4]
                })
            return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': True, 'data': []})

# API 5: Lokasi Kluise
def api_administrator_kluise(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COALESCE(kluise_1, '-'),
                       COALESCE(kluise_2, '-'),
                       COALESCE(lemari_file, '-'),
                       COALESCE(no_file, '-'),
                       COALESCE(keterangan, '-')
                FROM data_nasabah 
                WHERE nama_debitur IS NOT NULL
                ORDER BY no_urut
            """)
            rows = cursor.fetchall()
            
            data = []
            for row in rows:
                data.append({
                    'kluise_1': row[0],
                    'kluise_2': row[1],
                    'lemari_file': row[2],
                    'no_file': row[3],
                    'keterangan': row[4]
                })
            return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': True, 'data': []})


# API 7: Dashboard Stats
def api_administrator_dashboard(request):
    try:
        with connection.cursor() as cursor:
            # Total nasabah
            cursor.execute("""
                SELECT COUNT(*) FROM data_nasabah 
                WHERE nama_debitur IS NOT NULL 
                AND LENGTH(nama_debitur) > 2
            """)
            total_nasabah = cursor.fetchone()[0] or 0
            
            # Total pinjaman aktif
            cursor.execute("""
                SELECT COALESCE(SUM(jumlah_pinjaman), 0) FROM data_nasabah 
                WHERE sisa_pinjaman > 0 AND jumlah_pinjaman > 0
            """)
            total_pinjaman_aktif = float(cursor.fetchone()[0] or 0)
            
            # Total pendapatan
            cursor.execute("""
                SELECT COALESCE(SUM(jumlah_pinjaman * bunga / 100), 0) FROM data_nasabah 
                WHERE sisa_pinjaman > 0
            """)
            total_pendapatan = float(cursor.fetchone()[0] or 0)
            
            # Transaksi terbaru
            cursor.execute("""
                SELECT 
                    COALESCE(tanggal_pinjaman, NOW()) as tanggal,
                    nama_debitur as nasabah,
                    'PEMBAYARAN' as jenis,
                    COALESCE(cicilan_perbulan, 0) as jumlah,
                    CASE WHEN sisa_pinjaman <= 0 THEN 'LUNAS' ELSE 'AKTIF' END as status
                FROM data_nasabah 
                WHERE nama_debitur IS NOT NULL 
                AND cicilan_perbulan > 0
                ORDER BY tanggal_pinjaman DESC
                LIMIT 5
            """)
            transaksi_rows = cursor.fetchall()
            transaksi_terbaru = []
            for row in transaksi_rows:
                transaksi_terbaru.append({
                    'tanggal': str(row[0]) if row[0] else '-',
                    'nasabah': row[1],
                    'jenis': row[2],
                    'jumlah': float(row[3]) if row[3] else 0,
                    'status': row[4]
                })
            
            # Chart data
            cursor.execute("""
                SELECT 
                    TO_CHAR(DATE_TRUNC('month', tanggal_pinjaman), 'YYYY-MM') as bulan,
                    COUNT(*) as jumlah_pinjaman,
                    SUM(jumlah_pinjaman * bunga / 100) as pendapatan_bunga
                FROM data_nasabah 
                WHERE tanggal_pinjaman IS NOT NULL
                GROUP BY DATE_TRUNC('month', tanggal_pinjaman)
                ORDER BY bulan DESC
                LIMIT 6
            """)
            chart_rows = cursor.fetchall()
            
            chart_data = {
                'bulan': [],
                'jumlah_pinjaman': [],
                'pendapatan_bunga': []
            }
            
            for row in reversed(chart_rows):
                chart_data['bulan'].append(row[0])
                chart_data['jumlah_pinjaman'].append(float(row[1]) if row[1] else 0)
                chart_data['pendapatan_bunga'].append(float(row[2]) if row[2] else 0)
            
            return JsonResponse({
                'success': True,
                'total_nasabah': total_nasabah,
                'total_pinjaman_aktif': total_pinjaman_aktif,
                'total_pendapatan': total_pendapatan,
                'transaksi_terbaru': transaksi_terbaru,
                'chart_data': chart_data
            })
    except Exception as e:
        return JsonResponse({
            'success': True,
            'total_nasabah': 0,
            'total_pinjaman_aktif': 0,
            'total_pendapatan': 0,
            'transaksi_terbaru': [],
            'chart_data': {'bulan': [], 'jumlah_pinjaman': [], 'pendapatan_bunga': []}
        })
        

@csrf_exempt
@require_http_methods(["POST"])
def api_administrator_tambah_nasabah_lengkap(request):
    try:
        data = json.loads(request.body)
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT COALESCE(MAX(no_urut), 0) + 1 FROM data_nasabah")
            next_no_urut = cursor.fetchone()[0]
            
            id_debitur = f"DB-{next_no_urut:03d}"
            id_pinjaman = f"LN-{next_no_urut:03d}"
            
            # PERBAIKAN DI SINI - konversi ke int dulu
            tanggal_selesai = None
            tanggal_pinjaman = data.get('tanggal_pinjaman')
            tenor = data.get('tenor') or 0
            
            # Pastikan tenor adalah integer
            try:
                tenor_int = int(tenor)
            except (ValueError, TypeError):
                tenor_int = 0
            
            if tanggal_pinjaman and tenor_int > 0:
                from dateutil.relativedelta import relativedelta
                tgl_pinjam = datetime.strptime(tanggal_pinjaman, '%Y-%m-%d').date()
                tanggal_selesai = tgl_pinjam + relativedelta(months=tenor_int)
                tanggal_selesai = tanggal_selesai.strftime('%Y-%m-%d')
            
            cursor.execute("""
                INSERT INTO data_nasabah (
                    no_urut, nama_debitur, id_debitur, id_pinjaman, 
                    no_telepon, email, alamat, tanggal_lahir, nik, password,
                    tanggal_pinjaman, tanggal_pwlunasan, tipe_pinjaman, bunga, no_skk, 
                    tanggal_skk, no_pk_perjanjian, tanggal_pk, jumlah_pinjaman, 
                    tenor, cicilan_perbulan, sisa_pinjaman, status,
                    jaminan, no_agunan, tgl_agunan, nama_pemilik_agunan,
                    jenis_pengikat, no_ht, tgl_ht, no_asuransi, asuransi,
                    kluise_1, kluise_2, lemari_file, no_file, keterangan,
                    limit_pinjaman, tanggal_selesai
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                         %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                         %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                         %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                next_no_urut,
                data.get('nama_lengkap'),
                id_debitur,
                id_pinjaman,
                data.get('no_telepon'),
                data.get('email'),
                data.get('alamat'),
                data.get('tanggal_lahir'),
                data.get('nik'),
                data.get('password'),
                data.get('tanggal_pinjaman'),
                data.get('tanggal_pelunasan'),
                data.get('tipe_pinjaman'),
                data.get('bunga'),
                data.get('no_skk'),
                data.get('tanggal_skk'),
                data.get('no_pk_perjanjian'),
                data.get('tanggal_pk'),
                int(data.get('jumlah_pinjaman') or 0),
                tenor_int,  # PAKAI tenor_int yang sudah integer
                int(data.get('cicilan_perbulan') or 0),
                int(data.get('sisa_pinjaman') or 0),
                data.get('status') or 'BELUM AKTIF',
                data.get('jaminan'),
                data.get('no_agunan'),
                data.get('tgl_agunan'),
                data.get('nama_pemilik_agunan'),
                data.get('jenis_pengikat'),
                data.get('no_ht'),
                data.get('tgl_ht'),
                data.get('no_asuransi'),
                data.get('asuransi'),
                data.get('kluise_1'),
                data.get('kluise_2'),
                data.get('lemari_file'),
                data.get('no_file'),
                data.get('keterangan'),
                int(data.get('jumlah_pinjaman') or 0),
                tanggal_selesai
            ])
            
            return JsonResponse({'success': True, 'message': 'Nasabah berhasil ditambahkan'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



        # ========== TAMBAHKAN FUNGSI UPDATE NASABAH DI SINI (setelah api_administrator_tambah_nasabah_lengkap) ==========
# ========== FUNGSI UPDATE NASABAH YANG BENAR ==========
@csrf_exempt
@require_http_methods(["POST"])
def api_administrator_update_nasabah(request):
    """API untuk update data nasabah - HANYA update field yang dikirim (tidak kosong)"""
    try:
        data = json.loads(request.body)
        no_urut = data.get('no_urut')
        
        if not no_urut:
            return JsonResponse({'success': False, 'error': 'ID nasabah tidak ditemukan'})
        
        with connection.cursor() as cursor:
            # Cek apakah nasabah ada
            cursor.execute("SELECT no_urut FROM data_nasabah WHERE no_urut = %s", [no_urut])
            if not cursor.fetchone():
                return JsonResponse({'success': False, 'error': 'Nasabah tidak ditemukan'})
            
            # Mapping field database -> key JSON dari frontend
            field_mapping = {
                'nik': 'nik',
                'nama_debitur': 'nama_lengkap',
                'no_telepon': 'no_telepon',
                'email': 'email',
                'alamat': 'alamat',
                'tanggal_lahir': 'tanggal_lahir',
                'password': 'password',
                'tanggal_pinjaman': 'tanggal_pinjaman',
                'tanggal_pwlunasan': 'tanggal_pelunasan',
                'tipe_pinjaman': 'tipe_pinjaman',
                'bunga': 'bunga',
                'no_skk': 'no_skk',
                'tanggal_skk': 'tanggal_skk',
                'no_pk_perjanjian': 'no_pk_perjanjian',
                'tanggal_pk': 'tanggal_pk',
                'jumlah_pinjaman': 'jumlah_pinjaman',
                'tenor': 'tenor',
                'cicilan_perbulan': 'cicilan_perbulan',
                'sisa_pinjaman': 'sisa_pinjaman',
                'status': 'status',
                'jaminan': 'jaminan',
                'no_agunan': 'no_agunan',
                'tgl_agunan': 'tgl_agunan',
                'nama_pemilik_agunan': 'nama_pemilik_agunan',
                'jenis_pengikat': 'jenis_pengikat',
                'no_ht': 'no_ht',
                'tgl_ht': 'tgl_ht',
                'no_asuransi': 'no_asuransi',
                'asuransi': 'asuransi',
                'kluise_1': 'kluise_1',
                'kluise_2': 'kluise_2',
                'lemari_file': 'lemari_file',
                'no_file': 'no_file',
                'keterangan': 'keterangan'
            }
            
            # Kumpulkan field yang akan diupdate (HANYA yang dikirim dari frontend)
            update_fields = []
            params = []
            
            for db_field, json_key in field_mapping.items():
                if json_key in data:
                    value = data[json_key]
                    # HANYA update jika value tidak None dan tidak empty string
                    if value is not None and value != '':
                        update_fields.append(f"{db_field} = %s")
                        params.append(value)
            
            if not update_fields:
                return JsonResponse({'success': True, 'message': 'Tidak ada data yang diupdate'})
            
            # Eksekusi UPDATE dinamis
            sql = f"UPDATE data_nasabah SET {', '.join(update_fields)} WHERE no_urut = %s"
            params.append(no_urut)
            cursor.execute(sql, params)
            
            return JsonResponse({'success': True, 'message': 'Data nasabah berhasil diupdate'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})






        # ========== FUNGSI UPDATE LIMIT PINJAMAN NASABAH ==========
@csrf_exempt
@require_http_methods(["POST"])
def api_administrator_update_limit(request):
    """API untuk mengupdate limit pinjaman nasabah"""
    try:
        data = json.loads(request.body)
        no_urut = data.get('no_urut')
        limit_baru = data.get('limit_pinjaman')
        
        if not no_urut:
            return JsonResponse({'success': False, 'error': 'ID nasabah tidak ditemukan'})
        
        if limit_baru is None:
            return JsonResponse({'success': False, 'error': 'Limit pinjaman harus diisi'})
        
        with connection.cursor() as cursor:
            # Cek nasabah ada
            cursor.execute("SELECT no_urut, limit_pinjaman FROM data_nasabah WHERE no_urut = %s", [no_urut])
            row = cursor.fetchone()
            if not row:
                return JsonResponse({'success': False, 'error': 'Nasabah tidak ditemukan'})
            
            # Update limit
            cursor.execute("""
                UPDATE data_nasabah 
                SET limit_pinjaman = %s 
                WHERE no_urut = %s
            """, [limit_baru, no_urut])
            
            return JsonResponse({'success': True, 'message': f'Limit pinjaman berhasil diupdate menjadi Rp {int(limit_baru):,}'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})