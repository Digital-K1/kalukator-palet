import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Nastavitev naslova in ikone spletne strani
st.set_page_config(page_title="Kalkulator Naklada Palet", page_icon="🚚", layout="wide")

class Vozilo:
    def __init__(self, ime, dolzina_m, sirina_cm=244, visina_cm=285):
        self.ime = ime
        self.dolzina = int(dolzina_m * 100)
        self.sirina = sirina_cm
        self.visina = visina_cm

class VrstaPalete:
    def __init__(self, ime, sirina_m, dolzina_m, barva, dvonivojsko=False, vedno_dvonivojsko=False):
        self.ime = ime
        self.sirina = int(sirina_m * 100)
        self.dolzina = int(dolzina_m * 100)
        self.barva = barva
        self.dvonivojsko = dvonivojsko
        self.vedno_dvonivojsko = vedno_dvonivojsko

def napredni_izracun_zlaganja(vozilo, seznam_palet_za_nalog):
    izbrane_palete = []
    trenutni_x = 0
    trenutni_y = 0
    maks_y_v_vrsti = 0
    
    urejen_seznam = sorted(seznam_palet_za_nalog, key=lambda p: p.dolzina * p.sirina, reverse=True)
    preostanek_tovora = []

    for paleta in urejen_seznam:
        w, h = paleta.dolzina, paleta.sirina
        if trenutni_x + w > vozilo.dolzina or trenutni_y + h > vozilo.sirina:
            if trenutni_x + h <= vozilo.dolzina and trenutni_y + w <= vozilo.sirina:
                w, h = paleta.sirina, paleta.dolzina
        
        if trenutni_y + h <= vozilo.sirina and trenutni_x + w <= vozilo.dolzina:
            izbrane_palete.append((trenutni_x, trenutni_y, w, h, 1, paleta.ime, paleta.barva))
            if paleta.dvonivojsko or paleta.vedno_dvonivojsko:
                izbrane_palete.append((trenutni_x, trenutni_y, w, h, 2, paleta.ime, paleta.barva))
            trenutni_y += h
            if w > maks_y_v_vrsti:
                maks_y_v_vrsti = w
        else:
            trenutni_x += maks_y_v_vrsti
            trenutni_y = 0
            maks_y_v_vrsti = 0
            
            w, h = paleta.dolzina, paleta.sirina
            if trenutni_x + w > vozilo.dolzina or trenutni_y + h > vozilo.sirina:
                if trenutni_x + h <= vozilo.dolzina and trenutni_y + w <= vozilo.sirina:
                    w, h = paleta.sirina, paleta.dolzina
                    
            if trenutni_x + w <= vozilo.dolzina and trenutni_y + h <= vozilo.sirina:
                izbrane_palete.append((trenutni_x, trenutni_y, w, h, 1, paleta.ime, paleta.barva))
                if paleta.dvonivojsko or paleta.vedno_dvonivojsko:
                    izbrane_palete.append((trenutni_x, trenutni_y, w, h, 2, paleta.ime, paleta.barva))
                trenutni_y += h
                maks_y_v_vrsti = w
            else:
                preostanek_tovora.append(paleta)

    return izbrane_palete, preostanek_tovora

# --- SPLETNI VMESNIK (UI) ---
st.title("🚚 Inteligentni Kalkulator in Vizualizacija Naklada Palet")
st.write("Spletna aplikacija za optimalno razporeditev mešanega tovora v vozila.")

# Stranska vrstica za izbiro tovornjaka
st.sidebar.header("1. Izbira tovornega vozila")
vse_konfiguracije = {
    "Tandem 1 (7.7m + 7.7m)": (Vozilo("Kamion Tandem 1", 7.7), Vozilo("Prikolica Tandem 1", 7.7)),
    "Tandem 2 (7.3m + 8.1m)": (Vozilo("Kamion Tandem 2", 7.3), Vozilo("Prikolica Tandem 2", 8.1)),
    "Tandem 3 (6.0m + 9.0m)": (Vozilo("Kamion Tandem 3", 6.0), Vozilo("Prikolica Tandem 3", 9.0)),
    "Šleper (13.6m)": (Vozilo("Šleper", 13.6), None),
    "Solo Kamion (7.1m)": (Vozilo("Solo Kamion", 7.1), None)
}
izbira_vozila = st.sidebar.selectbox("Izberite konfiguracijo voznega parka:", list(vse_konfiguracije.keys()))
kamion, prikolica = vse_konfiguracije[izbira_vozila]

# Definicija palet
pal_standard = VrstaPalete("Standard", 1.25, 1.20, barva='#ffadad', dvonivojsko=False)
pal_vecja = VrstaPalete("Večja", 1.40, 1.20, barva='#ffd166', dvonivojsko=False)
pal_posebna = VrstaPalete("Posebna", 1.50, 1.20, barva='#a8dadc', dvonivojsko=False)
pal_dvometerska = VrstaPalete("2-Metrska", 2.00, 1.20, barva='#9bf6ff', vedno_dvonivojsko=True)
pal_trimeterska = VrstaPalete("2.9-Metrska", 2.90, 1.20, barva='#bdb2ff', vedno_dvonivojsko=True)
baza_vseh_palet = [pal_standard, pal_vecja, pal_posebna, pal_dvometerska, pal_trimeterska]

# Vnos količin na spletni strani preko polj za vnos številk
st.sidebar.header("2. Vnos količine palet")
n_std = st.sidebar.number_input(f"Standardne ({pal_standard.sirina/100}m x {pal_standard.dolzina/100}m)", min_value=0, value=0, step=1)
n_vec = st.sidebar.number_input(f"Večje ({pal_vecja.sirina/100}m x {pal_vecja.dolzina/100}m)", min_value=0, value=0, step=1)
n_pos = st.sidebar.number_input(f"Posebne ({pal_posebna.sirina/100}m x {pal_posebna.dolzina/100}m)", min_value=0, value=0, step=1)
n_2m = st.sidebar.number_input(f"2-Metrske (vedno 2 nivoja)", min_value=0, value=0, step=1)
n_29m = st.sidebar.number_input(f"2.9-Metrske (vedno 2 nivoja)", min_value=0, value=0, step=1)

# Izračun ob pritisku na gumb ali ob spremembi vnosov
trenutni_tovor = ([pal_standard]*n_std + [pal_vecja]*n_vec + [pal_posebna]*n_pos + 
                  [pal_dvometerska]*n_2m + [pal_trimeterska]*n_29m)

if len(trenutni_tovor) > 0:
    palete_kamion, preostanek = napredni_izracun_zlaganja(kamion, trenutni_tovor)
    palete_prikolica = []
    if prikolica and preostanek:
        palete_prikolica, preostanek = napredni_izracun_zlaganja(prikolica, preostanek)
        
    # Prikaz rezultatov v obliki kartic na spletni strani
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label=f"Naloženo na {kamion.ime}", value=f"{len(palete_kamion)} kosov")
    with col2:
        if prikolica:
            st.metric(label=f"Naloženo na {prikolica.ime}", value=f"{len(palete_prikolica)} kosov")
        else:
            st.metric(label="Prikolica", value="Ni vključena")
    with col3:
        if preostanek:
            st.error(f"⚠️ Nenaloženih ostalo: {len(preostanek)} palet!")
        else:
            st.success("✅ Ves tovor je uspešno naložen!")

    # Izris grafa neposredno v spletno aplikacijo
    fig, ax = plt.subplots(figsize=(16, 6))
    ax.set_aspect('equal')
    razmik = 150 
    
    # Kamion
    ax.add_patch(patches.Rectangle((0, 0), kamion.dolzina, kamion.sirina, linewidth=2, edgecolor='black', facecolor='none'))
    for (x, y, w, h, nivo, ime, barva) in palete_kamion:
        vzorec = '///' if nivo == 2 else None
        ax.add_patch(patches.Rectangle((x, y), w, h, linewidth=1, edgecolor='#2b2d42', facecolor=barva, hatch=vzorec, alpha=0.8))
        ax.text(x + w/2, y + h/2, f"{ime}\nN{nivo}", color='black', ha='center', va='center', fontsize=7, weight='bold')
        
    # Prikolica
    if prikolica:
        start_xb = kamion.dolzina + razmik
        ax.add_patch(patches.Rectangle((start_xb, 0), prikolica.dolzina, prikolica.sirina, linewidth=2, edgecolor='black', facecolor='none'))
        for (x, y, w, h, nivo, ime, barva) in palete_prikolica:
            vzorec = '///' if nivo == 2 else None
            ax.add_patch(patches.Rectangle((start_xb + x, y), w, h, linewidth=1, edgecolor='#2b2d42', facecolor=barva, hatch=vzorec, alpha=0.8))
            ax.text(start_xb + x + w/2, y + h/2, f"{ime}\nN{nivo}", color='black', ha='center', va='center', fontsize=7, weight='bold')

    # Legenda pod grafom
    legenda_elementi = [patches.Patch(facecolor=p.barva, edgecolor='#2b2d42', label=f"{p.ime} ({p.sirina/100}m x {p.dolzina/100}m)") for p in baza_vseh_palet]
    legenda_elementi.append(patches.Patch(facecolor='white', edgecolor='black', label='N1 = Spodnji nivo'))
    legenda_elementi.append(patches.Patch(facecolor='white', edgecolor='black', hatch='///', label='N2 = Zgornji nivo'))

    skupna_dolzina = kamion.dolzina + (razmik + prikolica.dolzina if prikolica else 0)
    ax.set_xlim(-50, skupna_dolzina + 50)
    ax.set_ylim(-30, 270)
    ax.legend(handles=legenda_elementi, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fancybox=True, shadow=True)
    plt.tight_layout()
    
    # Streamlit funkcija za prikaz grafa na spletni strani
    st.pyplot(fig)

else:
    st.info("💡 V stranski vrstici na levi strani izberite vozilo in vnesite količino palet za prikaz načrta nakladanja.")