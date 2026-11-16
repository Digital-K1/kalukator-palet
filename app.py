import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math

# Nastavitev naslova in ikone spletne strani
st.set_page_config(page_title="Parni Kalkulator Naklada Palet", page_icon="🚚", layout="wide")

class Vozilo:
    def __init__(self, ime, dolzina_m, sirina_cm=244, visina_cm=285):
        self.ime = ime
        self.dolzina = int(dolzina_m * 100)
        self.sirina = sirina_cm
        self.visina = visina_cm

class VrstaPalete:
    def __init__(self, ime, sirina_m, dolzina_m, barva, dvonivojsko=False, vedno_dvonivojsko=False):
        self.ime = ime
        self.fiksna_sirina = 120  # Vedno 1.20m v širino kamiona
        vnesena_mera_1 = int(sirina_m * 100)
        vnesena_mera_2 = int(dolzina_m * 100)
        self.poraba_dolzine = vnesena_mera_1 if vnesena_mera_1 != 120 else vnesena_mera_2
        self.barva = barva
        self.dvonivojsko = dvonivojsko
        self.vedno_dvonivojsko = vedno_dvonivojsko

def izracunaj_parni_naklad(vozilo, n_std, n_vec, n_pos, n_2m, n_29m, pal_std, pal_vec, pal_pos, pal_2m, pal_29m):
    """
    Napredni algoritem za parno zlaganje, ki pravilno 'štosa' dvonivojske palete
    in kombinira krajše palete za zapolnitev preostalega prostora.
    """
    # Najprej pretvorimo kose v talna mesta (vrste), saj se 2m in 2.9m zlagata vedno po 2 kosa v višino
    # Vsak par dveh kosov zasede 1 talno mesto na eni strani (levo ali desno)
    mesta_29m = math.ceil(n_29m / 2)
    mesta_2m = math.ceil(n_2m / 2)
    
    # Ustvarimo seznam vseh talnih mest, ki jih moramo postaviti (z informacijo o kosih na njih)
    talna_mesta = []
    
    # Dodamo mesta za 2.9-Metrske
    za_razdelit_29m = n_29m
    for _ in range(mesta_29m):
        kosi = 2 if za_razdelit_29m >= 2 else 1
        talna_mesta.append({'paleta': pal_29m, 'kosi': kosi})
        za_razdelit_29m -= kosi
        
    # Dodamo mesta za 2-Metrske
    za_razdelit_2m = n_2m
    for _ in range(mesta_2m):
        kosi = 2 if za_razdelit_2m >= 2 else 1
        talna_mesta.append({'paleta': pal_2m, 'kosi': kosi})
        za_razdelit_2m -= kosi
        
    # Enonivojske palete zasedejo vsaka svoje talno mesto (1 kos = 1 mesto)
    for _ in range(n_pos): talna_mesta.append({'paleta': pal_pos, 'kosi': 1})
    for _ in range(n_vec): talna_mesta.append({'paleta': pal_vec, 'kosi': 1})
    for _ in range(n_std): talna_mesta.append({'paleta': pal_std, 'kosi': 1})
    
    # Razvrstimo talna mesta od najdaljših proti najkrajšim za optimalno zapolnjevanje stene
    talna_mesta = sorted(talna_mesta, key=lambda x: x['paleta'].poraba_dolzine, reverse=True)
    
    izbrane_palete = []
    preostanek_tovora_mesta = []
    
    trenutni_x = 0
    
    while len(talna_mesta) > 0:
        # Vzamemo najdaljše razpoložljivo mesto za levo stran
        mesto1 = talna_mesta.pop(0)
        p1 = mesto1['paleta']
        
        # Iskanje najboljšega para za desno stran, ki se ujema po dolžini ali je krajši,
        # da maksimalno zapolnimo širino tovornjaka brez praznin
        indeks_para = -1
        for idx, m_potencialni in enumerate(talna_mesta):
            if m_potencialni['paleta'].poraba_dolzine <= p1.poraba_dolzine:
                indeks_para = idx
                break
                
        mesto2 = talna_mesta.pop(indeks_para) if indeks_para != -1 else None
        p2 = mesto2['paleta'] if mesto2 else None
        
        # Dolžina te celotne vrste je določena z najdaljšo paleto v paru (večinoma p1)
        potrebna_dolzina = p1.poraba_dolzine
        
        # Preverimo, ali vrsta sploh še paše po dolžini v vozilo
        if trenutni_x + potrebna_dolzina <= vozilo.dolzina:
            # Naložimo LEVO stran
            for nivo in range(1, mesto1['kosi'] + 1):
                izbrane_palete.append((trenutni_x, 0, p1.poraba_dolzine, 120, nivo, p1.ime, p1.bar))
                
            # Naložimo DESNO stran (če obstaja sopotnik v vrsti)
            if mesto2:
                for nivo in range(1, mesto2['kosi'] + 1):
                    izbrane_palete.append((trenutni_x, 120, p2.poraba_dolzine, 120, nivo, p2.ime, p2.barva))
                    
            trenutni_x += necesaria_dolzina
        else:
            # Če ne paše več, vrnemo mesta nazaj v preostanek
            preostanek_tovora_mesta.append(mesto1)
            if mesto2:
                preostanek_tovora_mesta.append(mesto2)
            preostanek_tovora_mesta.extend(talna_mesta)
            break
            
    # Preostanek mest nazaj pretvorimo v število kosov za izpis napake
    preostanek_kosi = {'Standard': 0, 'Večja': 0, 'Posebna': 0, '2-Metrska': 0, '2.9-Metrska': 0}
    for m in preostanek_tovora_mesta:
        preostanek_kosi[m['paleta'].ime] += m['kosi']
        
    return izbrane_palete, preostanek_kosi

# --- SPLETNI VMESNIK (UI) ---
st.title("🚚 Parni Kalkulator in Načrtovalec Naklada Palet")
st.write("Simetrično in ravno nakladanje s pametnim zlaganjem v višino (štosanjem) in kombiniranjem dolžin.")

# 1. Izbira tovornjaka
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

# 2. Vnos količin
st.sidebar.header("2. Vnos količine palet (Kosi)")
n_std = st.sidebar.number_input(f"Standardne (1.25m dolžina)", min_value=0, value=0, step=1)
n_vec = st.sidebar.number_input(f"Večje (1.40m dolžina)", min_value=0, value=0, step=1)
n_pos = st.sidebar.number_input(f"Posebne (1.50m dolžina)", min_value=0, value=0, step=1)
n_2m = st.sidebar.number_input(f"2-Metrske (Skupno število kosov)", min_value=0, value=0, step=1)
n_29m = st.sidebar.number_input(f"2.9-Metrske (Skupno število kosov)", min_value=0, value=0, step=1)

skupno_kosov_vnos = n_std + n_vec + n_pos + n_2m + n_29m

if skupno_kosov_vnos > 0:
    # Izračun za kamion
    palete_kamion, manjka_kamion = izracunaj_parni_naklad(
        kamion, n_std, n_vec, n_pos, n_2m, n_29m, 
        pal_standard, pal_vecja, pal_posebna, pal_dvometerska, pal_trimeterska
    )
    
    # Izračun za prikolico z ostankom tovora (če prikolica sploh obstaja)
    palete_prikolica = []
    manjka_skupaj = manjka_kamion.copy()
    
    if prikolica and sum(manjka_kamion.values()) > 0:
        palete_prikolica, manjka_skupaj = izracunaj_parni_naklad(
            prikolica, manjka_kamion['Standard'], manjka_kamion['Večja'], manjka_kamion['Posebna'], 
            manjka_kamion['2-Metrska'], manjka_kamion['2.9-Metrska'],
            pal_standard, pal_vecja, pal_posebna, pal_dvometerska, pal_trimeterska
        )
        
    # Kartice z rezultati
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label=f"Naloženo na {kamion.ime}", value=f"{len(palete_kamion)} kosov")
    with col2:
        if prikolica:
            st.metric(label=f"Naloženo na {prikolica.ime}", value=f"{len(palete_prikolica)} kosov")
        else:
            st.metric(label="Prikolica", value="Ni vključena")
    with col3:
        skupno_manjka = sum(manjka_skupaj.values())
        if skupno_manjka > 0:
            st.error(f"⚠️ Zmanjkalo prostora za: {skupno_manjka} kosov")
            for kljuc, vrednost in manjka_skupaj.items():
                if vrednost > 0:
                    st.write(f" - {vrednost}x {kljuc} paleta")
        else:
            st.success("✅ Vse palete so uspešno naložene in poštopane!")

    # Izris grafike
    fig, ax = plt.subplots(figsize=(16, 5))
    ax.set_aspect('equal')
    razmik = 150 
    
    # Kamion
    ax.add_patch(patches.Rectangle((0, 0), kamion.dolzina, kamion.sirina, linewidth=2, edgecolor='black', facecolor='none'))
    ax.plot([0, kamion.dolzina], [120, 120], color='gray', linestyle=':', alpha=0.5)
    
    for (x, y, w, h, nivo, ime, barva) in palete_kamion:
        vzorec = '///' if nivo == 2 else None
        ax.add_patch(patches.Rectangle((x, y), w, h, linewidth=1, edgecolor='#2b2d42', facecolor=barva, hatch=vzorec, alpha=0.8))
        ax.text(x + w/2, y + h/2, f"{ime}\nN{nivo}", color='black', ha='center', va='center', fontsize=7, weight='bold')
        
    # Prikolica
    if prikolica:
        start_xb = kamion.dolzina + razmik
        ax.add_patch(patches.Rectangle((start_xb, 0), prikolica.dolzina, prikolica.sirina, linewidth=2, edgecolor='black', facecolor='none'))
        ax.plot([start_xb, start_xb + prikolica.dolzina], [120, 120], color='gray', linestyle=':', alpha=0.5)
        
        for (x, y, w, h, nivo, ime, barva) in palete_prikolica:
            vzorec = '///' if nivo == 2 else None
            ax.add_patch(patches.Rectangle((start_xb + x, y), w, h, linewidth=1, edgecolor='#2b2d42', facecolor=barva, hatch=vzorec, alpha=0.8))
            ax.text(start_xb + x + w/2, y + h/2, f"{ime}\nN{nivo}", color='black', ha='center', va='center', fontsize=7, weight='bold')

    # Legenda spodaj

legenda_elementi = [patches.Patch(facecolor=p.barva, edgecolor='#2b2d42', label=f"{p.ime} ({p.poraba_dolzine/100}m)") for p in baza_vseh_palet]
legenda_elementi.append(patches.Patch(facecolor='white', edgecolor='black', label='N1 = Spodnja paleta'))
legenda_elementi.append(patches.Patch(facecolor='white', edgecolor='black', hatch='///', label='N2 = Zgornja paleta (Zloženo)'))
skupna_dolzina = kamion.dolzina + (razmik + prikolica.dolzina if prikolica else 0)
ax.set_xlim(-50, skupna_dolzina + 50)
ax.set_ylim(-20, 260)
ax.legend(handles=legenda_elementi, loc='upper center', bbox_to_anchor=(0.5, -0.18), ncol=3, fancybox=True, shadow=True)
plt.tight_layout()
st.pyplot(fig)
else:
st.info("💡 V stranski vrstici na levi strani izberite vrsto tovornjaka in vnesite količino palet za izračun.")
