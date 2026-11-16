import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

st.set_page_config(page_title="Kalkulator Naklada", page_icon="🚚", layout="wide")

class Vozilo:
    def __init__(self, ime, dolzina_m):
        self.ime = ime
        self.dolzina = int(dolzina_m * 100)
        self.sirina = 244

class VrstaPalete:
    def __init__(self, ime, sirina_m, dolzina_m, barva, dvonivojsko=False):
        self.ime = ime
        v_mera1, v_mera2 = int(sirina_m * 100), int(dolzina_m * 100)
        self.poraba_dolzine = v_mera1 if v_mera1 != 120 else v_mera2
        self.barva = barva
        self.dvonivojsko = dvonivojsko

# Definicija vseh vaših palet
pal_std = VrstaPalete("Standard", 1.25, 1.20, '#ffadad')
pal_vec = VrstaPalete("Večja", 1.40, 1.20, '#ffd166')
pal_pos = VrstaPalete("Posebna", 1.50, 1.20, '#a8dadc')
pal_2m  = VrstaPalete("2-Metrska", 2.00, 1.20, '#9bf6ff', dvonivojsko=True)
pal_29m = VrstaPalete("2.9-Metrska", 2.90, 1.20, '#bdb2ff', dvonivojsko=True)
baza_palet = {"Standard (1.25m)": pal_std, "Večja (1.40m)": pal_vec, "Posebna (1.50m)": pal_pos, "2-Metrska": pal_2m, "2.9-Metrska": pal_29m}

if 'tovor_lista' not in st.session_state:
    st.session_state.tovor_lista = []

# 1. STRANSKA VRSTICA (VNOSI)
st.sidebar.header("1. Nastavitve")
vse_konfiguracije = {
    "Tandem 1 (7.7m + 7.7m)": (Vozilo("Kamion Tandem 1", 7.7), Vozilo("Prikolica Tandem 1", 7.7)),
    "Tandem 2 (7.3m + 8.1m)": (Vozilo("Kamion Tandem 2", 7.3), Vozilo("Prikolica Tandem 2", 8.1)),
    "Tandem 3 (6.0m + 9.0m)": (Vozilo("Kamion Tandem 3", 6.0), Vozilo("Prikolica Tandem 3", 9.0)),
    "Šleper (13.6m)": (Vozilo("Šleper", 13.6), None),
    "Solo Kamion (7.1m)": (Vozilo("Solo Kamion", 7.1), None)
}
izbira_vozila = st.sidebar.selectbox("Izberite vozilo:", list(vse_konfiguracije.keys()))
kamion, prikolica = vse_konfiguracije[izbira_vozila]

st.sidebar.header("2. Dodajanje palet")
izbran_tip = st.sidebar.selectbox("Vrsta palete:", list(baza_palet.keys()))
kolicina = st.sidebar.number_input("Količina kosov:", min_value=1, value=1, step=1)

if st.sidebar.button("➕ Dodaj na listo"):
    for _ in range(kolicina):
        st.session_state.tovor_lista.append(baza_palet[izbran_tip])
    st.rerun()

if st.sidebar.button("🗑️ Počisti listo"):
    st.session_state.tovor_lista = []
    st.rerun()

# 2. LOGIKA NAKLADANJA (IZRAČUN)
def preracunaj(vozilo, tovor):
    talna_mesta, izbrane, trenutni_x = [], [], 0
    stevec_29m, stevec_2m = 0, 0
    
    # Štosanje dvonivojskih palet po vrstnem redu
    for p in tovor:
        if p.ime == "2.9-Metrska":
            stevec_29m += 1
            if stevec_29m == 2: talna_mesta.append({'p': p, 'k': 2}); stevec_29m = 0
        elif p.ime == "2-Metrska":
            stevec_2m += 1
            if stevec_2m == 2: talna_mesta.append({'p': p, 'k': 2}); stevec_2m = 0
        else:
            if stevec_29m == 1: talna_mesta.append({'p': pal_29m, 'k': 1}); stevec_29m = 0
            if stevec_2m == 1: talna_mesta.append({'p': pal_2m, 'k': 1}); stevec_2m = 0
            talna_mesta.append({'p': p, 'k': 1})
            
    if stevec_29m == 1: talna_mesta.append({'p': pal_29m, 'k': 1})
    if stevec_2m == 1: talna_mesta.append({'p': pal_2m, 'k': 1})

    # Polnjenje bočnih vrst (Leva in Desna stran)
    while len(talna_mesta) > 0:
        m1 = talna_mesta.pop(0)
        m2 = talna_mesta.pop(0) if len(talna_mesta) > 0 else None
        
        potrebna_d = max(m1['p'].poraba_dolzine, m2['p'].poraba_dolzine if m2 else 0)
        
        if trenutni_x + potrebna_d <= vozilo.dolzina:
            for n in range(1, m1['k'] + 1): izbrane.append((trenutni_x, 0, m1['p'].poraba_dolzine, 120, n, m1['p'].ime, m1['p'].barva))
            if m2:
                for n in range(1, m2['k'] + 1): izbrane.append((trenutni_x, 120, m2['p'].poraba_dolzine, 120, n, m2['p'].ime, m2['p'].barva))
            trenutni_x += potrebna_d
        else:
            talna_mesta.insert(0, m1)
            if m2: talna_mesta.insert(1, m2)
            break
            
    ostanek = []
    for m in talna_mesta:
        for _ in range(m['k']): ostanek.append(m['p'])
    return izbrane, ostanek

# 3. PRIKAZ REZULTATOV IN VIZUALIZACIJA
st.title("🚚 Kalkulator Naklada po Vrstnem Redu")

if len(st.session_state.tovor_lista) > 0:
    kam_palete, kam_ostanek = preracunaj(kamion, st.session_state.tovor_lista)
    prik_palete, končni_ostanek = [], kam_ostanek
    
    if prikolica and len(kam_ostanek) > 0:
        prik_palete, končni_ostanek = preracunaj(prikolica, kam_ostanek)

    # Izpis statusa naklada
    if len(končni_ostanek) > 0:
        st.error(f"⚠️ Zmanjkalo prostora za {len(končni_ostanek)} palet!")
    else:
        st.success("✅ Vse palete so uspešno naložene v parih in poštopane!")

    # Izris tlorisa
    fig, ax = plt.subplots(figsize=(16, 5))
    ax.set_aspect('equal')
    
    # Izris Kamiona
    ax.add_patch(patches.Rectangle((0, 0), kamion.dolzina, 244, linewidth=2, edgecolor='black', facecolor='none'))
    ax.axhline(y=120, color='gray', linestyle=':', alpha=0.5)
    for (x, y, w, h, nivo, ime, barva) in kam_palete:
        vzor = '///' if nivo == 2 else None
        ax.add_patch(patches.Rectangle((x, y), w, h, linewidth=1, edgecolor='black', facecolor=barva, hatch=vzor, alpha=0.8))
        ax.text(x + w/2, y + h/2, f"{ime}\nN{nivo}", color='black', ha='center', va='center', fontsize=7, weight='bold')

    # Izris Prikolice (če obstaja)
    if prikolica:
        sx = kamion.dolzina + 150
        ax.add_patch(patches.Rectangle((sx, 0), prikolica.dolzina, 244, linewidth=2, edgecolor='black', facecolor='none'))
        ax.axhline(y=sx+120, color='gray', linestyle=':', alpha=0.5) # Sredinska črta prikolice
        for (x, y, w, h, nivo, ime, barva) in prik_palete:
            vzor = '///' if nivo == 2 else None
            ax.add_patch(patches.Rectangle((sx + x, y), w, h, linewidth=1, edgecolor='black', facecolor=barva, hatch=vzor, alpha=0.8))
            ax.text(sx + x + w/2, y + h/2, f"{ime}\nN{nivo}", color='black', ha='center', va='center', fontsize=7, weight='bold')

    # Legenda pod grafom
    legenda = [patches.Patch(facecolor=p.barva, edgecolor='black', label=f"{p.ime} ({p.poraba_dolzine/100}m)") for p in [pal_std, pal_vec, pal_pos, pal_2m, pal_29m]]
    legenda.extend([patches.Patch(facecolor='white', edgecolor='black', label='N1 = Spodaj'), patches.Patch(facecolor='white', edgecolor='black', hatch='///', label='N2 = Zgoraj')])
    
    ax.set_xlim(-50, kamion.dolzina + (150 + prikolica.dolzina if prikolica else 0) + 50)
    ax.set_ylim(-20, 260)
    ax.legend(handles=legenda, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=4, fancybox=True, shadow=True)
    plt.tight_layout()
    st.pyplot(fig)
else:
    st.info("💡 Na levi strani izberite paleto in kliknite gumb, da sestavite svojo nakladalno listo.")
