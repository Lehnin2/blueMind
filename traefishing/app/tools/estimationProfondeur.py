import xarray as xr
import os

def obtenir_profondeur(fichier_nc, latitude, longitude):
    if not os.path.isfile(fichier_nc):
        print(f"❌ Fichier introuvable : {fichier_nc}")
        return None

    try:
        # Try default engine; fallback to netCDF4 then h5netcdf if needed
        ds = None
        try:
            ds = xr.open_dataset(fichier_nc)
        except Exception as e_default:
            print(f"⚠️ Default xarray engine failed ({e_default}), retrying with netCDF4 engine")
            try:
                ds = xr.open_dataset(fichier_nc, engine="netcdf4")
            except Exception as e_netcdf4:
                print(f"⚠️ netCDF4 engine failed ({e_netcdf4}), retrying with h5netcdf engine")
                try:
                    ds = xr.open_dataset(fichier_nc, engine="h5netcdf")
                except Exception as e_h5:
                    print(f"❌ All xarray engines failed ({e_h5})")
        # If no engine succeeded, return None
        if ds is None:
            return None
        # Select nearest elevation point
        point = ds.sel(lat=latitude, lon=longitude, method="nearest")
        profondeur = float(point['elevation'].values)
        ds.close()
        return profondeur
    except Exception as e:
        print("❌ Erreur lors de la lecture du fichier :", e)
        return None

def interface_utilisateur():
    print("🌊 Outil de profondeur maritime - Tunisie 🌊")

    # 🔧 Met ici le chemin exact vers ton fichier .nc
    # Utilise soit un chemin absolu, soit un chemin relatif depuis ce script
    fichier_nc = os.path.join("C:\\", "Users", "user", "OneDrive", "Bureau", "multi-agent system", "data", "carte_marine_tunisie.nc")

    print(f"📁 Chargement du fichier : {fichier_nc}\n")

    while True:
        try:
            lat = float(input("📍 Latitude (ex: 36.8) : "))
            lon = float(input("📍 Longitude (ex: 10.2) : "))

            profondeur = obtenir_profondeur(fichier_nc, lat, lon)

            if profondeur is not None:
                if profondeur < 0:
                    print(f"🌐 Profondeur : {abs(profondeur):.2f} m sous le niveau de la mer.\n")
                else:
                    print(f"🌍 Altitude : {profondeur:.2f} m au-dessus du niveau de la mer.\n")

        except ValueError:
            print("⚠️ Valeur invalide. Entrez des chiffres.")

        choix = input("🔁 Tester un autre point ? (o/n) : ").strip().lower()
        if choix != 'o':
            print("👋 Fin du programme.")
            break

# Lancer le programme
if __name__ == "__main__":
    interface_utilisateur()
