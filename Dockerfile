# Gunakan imej Python rasmi yang ringan
FROM python:3.11-slim

# Pasang ffmpeg dan bersihkan cache untuk kurangkan saiz
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Tetapkan direktori kerja
WORKDIR /app

# Salin fail keperluan dulu supaya cache Docker berfungsi
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin kesemua fail aplikasi
COPY . .

# Arahan untuk jalankan bot
CMD ["python", "bot.py"]
