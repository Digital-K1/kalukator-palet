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

def izracunaj_parni_naklad_po_vrstnem_redu(vozilo, seznam_vnosov):
    """
    Algoritem, ki strogo spoštuje vrstni red dodajanja palet.
    Pravilno štosira dvonivojske palete in jih postavlja v pare brez vnaprejšnjega sortiranja.
    """
    talna_mesta = []
    zacasni_kos_29m = 0
    zacasni_kos_2m = 0
    
    # Prva faza: Gremo skozi vnose točno v zaporedju, kot so bili dodani,
    # in tvorimo talna mesta (štosamo dvonivojske, enonivojske pa takoj dajo talno mesto)
    for p in seznam_vnosov:
        if p.ime == "2.9-Metrska":
            zacasni_kos_29m += 1
            if zacasni_kos_29m == 2:
                talna_mesta.append({'paleta': p, 'kosi': 2})
                zacasni_kos_29m = 0
        elif p.ime == "2-Metrska":
            zacasni_kos_2m += 1
            if zacasni_kos_2m == 2:
                talna_mesta.append({'paleta': p, 'kosi': 2})
                zacasni_kos_2m = 0
        else:
            # Preden dodamo enonivojsko paleto, moramo zapreti morebitne osamljene dvonivojske palete na tleh
            if zacasni_kos_29m == 1:
                iskani = [x for x in seznam_vnosov if x.ime == "2.9-Metrska"]
                talna_mesta.append({'paleta': iskani[0] if iskani else p, 'kosi': 1})
                zacasni_kos_29m = 0
            if zacasni_kos_2m == 1:
                iskani = [x for x in seznam_vnosov if x.ime == "2-Metrska"]
                talna_mesta.append({'paleta': iskani[0] if iskani else p, 'kosi': 1})
                zacasni_kos_2m = 0
                
            talna_mesta.append({'paleta': p, 'kosi': 1})
            
    # Če je na koncu ostala še kakšna osamljena dvonivojska paleta (samo 1 kos v štosu)
    if zacasni_kos_29m == 1:
        iskani = [x for x in seznam_vnosov if x.ime == "2.9-Metrska"]
        if iskani: talna_mesta.append({'paleta': iskani[0], 'kosi': 1})
    if zacasni_kos_2m == 1:
        iskani = [x for x in seznam_vnosov if x.ime == "2-Metrska"]
        if iskani: talna_mesta.append({'paleta': iskani[0], 'kosi': 1})

    izbrane_palete = []
    preostanek_tovora_mesta = []
    trenutni_x = 0
    
    # Druga faza: Zlaganje pripravljenih talnih mest v pare (Leva in Desna stran)
    while len(talna_mesta) > 0:
        mesto1 = talna_mesta.pop(0)
        p1 = mesto1['paleta']
        
        # Par ulovimo iz naslednjega elementa na listi (brez iskanja po celi bazi, da ostane vrstni red)
        mesto2 = talna_mesta.pop(0) if len(talna_mesta) > 0 else None
        p2 = mesto2['paleta'] if mesto2 else None
        
        potrebna_dolzina = p1.poraba_dolzine
        if p2 and p2.poraba_dolzine > potrebna_dolzina:
            potrebna_dolzina = p2.poraba_dolzine
            
        if trenutni_x + potrebna_dolzina <= vozilo.dolzina:
            # Naložimo LEVO stran
            for nivo in range(1, mesto1['kosi'] + 1):
                izbrane_palete.append((trenutni_x, 0, p1.poraba_dolzine, 120, nivo, p1.ime, p1.barva))
                
            # Naložimo DESNO stran
            if mesto2:
                for nivo in range(1, mesto2['kosi'] + 1):
                    izbrane_palete.append((trenutni_x, 120, p2.poraba_dolzine, 120, nivo, p2.ime, p2.barva))
                    
            trenutni_x += potrebna_dolzina
        else:
            preostanek_tovora_mesta.append(mesto1)
            if mesto2:
                preostanek_tovora_mesta.append(mesto2)
            preostanek_tovora_mesta.extend(talna_mesta)
            break

    preostanek_kosi = {'Standard': 0, 'Večja': 0, 'Posebna': 0, '2-Metrska': 0, '2.9-Metrska': 0}
    for m in preostanek_tovora_mesta:
        preostanek_kosi[m['paleta'].ime] += m['kosi']
        
    return izbrane_palete, preostanek_kosi

# --- SPLETNI VMESNIK (UI) ---
st.title("🚚 Parni Kalkulator Naklada Palet po Vrstnem Redu")
st.write("Palete se zlagajo natančno v takšnem zaporedju, kot jih dodajate na listo (od kabine proti zadku).")

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
baza_palet_dict = {
    "Standard (1.25m)": pal_standard,
    "Večja (1.40m)": pal_vecja,
    "Posebna (1.50m)": pal_posebna,
    "2-Metrska (vedno 2 nivoja)": pal_dvometerska,
    "2.9-Metrska (vedno 2 nivoja)": pal_trimeterska
}

# Seja za shranjevanje seznama dodanih palet
if 'tovor_lista' not in st.session_state:
    st.session_state.tovor_lista = []

# 2. Dinamično dodajanje palet na listo
st.sidebar.header("2. Dodajanje palet na listo")
izbran_tip_vnos = st.sidebar.selectbox("Izberite vrsto palete za dodajanje:", list(baza_palet_dict.keys()))
kolicina_za_dodat = st.sidebar.number_input("Količina kosov za dodajanje:", min_value=1, value=1, step=1)

if st.sidebar.button("➕ Dodaj paleto na listo"):
    paleta_obj = baza_palet_dict[izbran_tip_vnos]
    for _ in range(kolicina_za_dodat):
        st.session_state.tovor_lista.append(paleta_obj)
    st.rerun()

if st.sidebar.button("🗑️ Počisti celoten tovor"):
    st.session_state.tovor_lista = []
    st.rerun()

# Prikaz trenutne liste naloženih stvari v stranski vrstici
if len(st.session_state.tovor_lista) > 0:
    st.sidebar.subheader("Trenutni tovor na listi:")
    izpis_stevec = {}
    for p in st.session_state.tovor_lista:
        izpis_stevec[p.ime] = izpis_stevec.get(p.ime, 0) + 1
    for k, v in izpis_stevec.items():
        st.sidebar.write(f"- {v}x {k} paleta")

# IZRAČUN IN GRAFIKA
if len(st.session_state.tovor_lista) > 0:
    palete_kamion, manjka_kamion = izracunaj_parni_naklad_po_vrstnem_redu(kamion, st.session_state.tovor_lista)
    
    palete_prikolica = []
    manjka_skupaj = manjka_kamion.copy()
    
    if prikolica and sum(manjka_kamion.values()) > 0:
        ostanek_za_prikolico = []
        for _ in range(manjka_kamion['Standard']): ostanek_za_prikolico.append(pal_standard)
        for _ in range(manjka_kamion['Večja']): ostanek_za_prikolico.append(pal_vecja)
        for _ in range(manjka_kamion['Posebna']): ostanek_za_prikolico.append(pal_posebna)
        for _ in range(manjka_kamion['2-Metrska']): ostanek_za_prikolico.append(pal_dvometerska)
        for _ in range(manjka_kamion['2.9-Metrska']): ostanek_za_prikolico.append(pal_trimeterska)
        
        palete_prikolica, manjka_skupaj = izracunaj_parni_naklad_po_vrstnem_redu(prikolica, ostanek_za_prikolico)
        
    # Prikaz rezultatov
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
        else:
            st.success("✅ Vse dodane palete so uspešno razporejene po vašem vrstnem redu!")

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
baza_vseh_palet = [pal_standard, pal_vecja, pal_posebna, pal_dvometerska, pal_trimeterska]
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
st.info("💡 V stranski vrstici na levi strani izberite vrsto palete in kliknite gumb 'Dodaj paleto na listo' za simulacijo vašega vrstnega reda nakladanja.")
