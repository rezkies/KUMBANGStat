from datetime import datetime
import pandas as pd
import streamlit as st
import requests
import json

# Load housing data from local JSON file
with open("data_perumahan.json", "r", encoding="utf-8") as f:
    housing_data = json.load(f)

st.title("🏡 Perumahan Report Viewer")

# Step 1: Select Kecamatan
kecamatan_list = sorted(set(item["kecamatan"] for item in housing_data))
selected_kecamatan = st.selectbox("Pilih Kecamatan", kecamatan_list)

# Step 2: Select Perumahan (filtered by Kecamatan)
perumahan_list = sorted(set(
    item["namaPerumahan"] for item in housing_data if item["kecamatan"] == selected_kecamatan
))
selected_perumahan = st.selectbox("Pilih Pengembang", perumahan_list)

# Step 3: Submit
if st.button("Lihat Laporan"):
    # Find matching location
    matched = [
        item for item in housing_data
        if item["kecamatan"] == selected_kecamatan and item["namaPerumahan"] == selected_perumahan
    ]

    if matched:
        lokasi = matched[0]
        id_lokasi = lokasi["idLokasi"]
        st.info(f"Mengambil data untuk ID Lokasi: {id_lokasi}")

        # Fetch JSON from URL
        url = f"https://sikumbang.tapera.go.id/lokasi-perumahan/{id_lokasi}/json"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            st.subheader("📋 Laporan Perumahan")
            # Extract main details
            detail = data["detail"]
            bangunan = data["bangunan"]

            st.subheader("📋 Informasi Umum")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Nama Perumahan:** {detail['namaPerumahan']}")
                st.markdown(f"**Pengembang:** {detail['namaPengembang']}")
                st.markdown(f"**NPWP Pengembang:** {detail['npwpPengembang']}")
            with col2:
                kantor = detail["kantorPemasaran"][0] if detail.get("kantorPemasaran") else {}
                st.markdown(f"**Alamat:** {detail.get('alamat','-')}")
                st.markdown(f"**No. Telepon:** {kantor.get('noTelp', '-')}")
                st.markdown(f"**Email:** {kantor.get('email', '-')}")

            # Siteplan Image
            if detail.get("siteplan"):
                st.subheader("🗺️ Siteplan Perumahan")
                st.image(detail["siteplan"], use_container_width=True)

            # Map from koordinat
            st.subheader("🗺️ Lokasi Perumahan")
            if detail.get("koordinatPerumahan"):
                try:
                    lat, lon = map(float, detail["koordinatPerumahan"].split(","))
                    st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))
                except:
                    st.warning("Koordinat tidak valid.")

            # Resume by Status
            st.subheader("📊 Ringkasan Bangunan berdasarkan Status")

            status_counts = pd.Series([b["status"] for b in bangunan]).value_counts().rename_axis("Status").reset_index(name="Jumlah")
            st.dataframe(status_counts, use_container_width=True)
            st.bar_chart(status_counts.set_index("Status"))

            # Filter terjual buildings
            terjual_bangunan = [b for b in bangunan if b["status"] == "terjual"]

            # Resume chart: jumlah terjual per tahun
            if terjual_bangunan:
                st.subheader("📈 Jumlah Rumah Terjual per Tahun")
                df_chart = pd.DataFrame([
                    {"tahun": datetime.strptime(b["tanggalTerjual"], "%Y-%m-%d").year}
                    for b in terjual_bangunan
                ])
                chart_data = df_chart["tahun"].value_counts().sort_index().rename_axis("Tahun").reset_index(name="Jumlah Terjual")
                st.bar_chart(chart_data.set_index("Tahun"))

                # Tabel Bangunan Terjual
                st.subheader("📑 Daftar Rumah Terjual")
                df_table = pd.DataFrame([
                    {
                        "Blok": b.get("blok", {}).get("blok", "-"),
                        "Nomor": b.get("nomor", "-"),
                        "Harga": f"Rp{b.get('tipe', {}).get('harga', 0):,}".replace(",", "."),
                        "Tanggal Terjual": datetime.strptime(b["tanggalTerjual"], "%Y-%m-%d").strftime("%d-%m-%Y") if b.get("tanggalTerjual") else "-"
                    }
                    for b in terjual_bangunan
                ])
                st.dataframe(df_table, use_container_width=True)
            else:
                st.warning("Tidak ada data bangunan terjual.")

        except requests.RequestException as e:
            st.error(f"Gagal mengambil data: {e}")
    else:
        st.warning("Tidak ditemukan data yang cocok.")
