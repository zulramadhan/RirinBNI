from django.db import models

class DataNasabah(models.Model):
    no_urut = models.IntegerField(null=True, blank=True)
    nama_debitur = models.CharField(max_length=255)
    id_debitur = models.CharField(max_length=50, unique=True)
    id_pinjaman = models.CharField(max_length=50, unique=True)
    no_telepon = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    alamat = models.TextField(blank=True, null=True)
    tanggal_lahir = models.DateField(blank=True, null=True)
    nik = models.CharField(max_length=20, unique=True, null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        db_table = 'data_nasabah'
        managed = False
    
    def __str__(self):
        return self.nama_debitur