import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

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
        # Da bo v kodi popolnoma jasno: fiksiramo fiksno mero 1.20m, ki gre vedno v širino kamiona
        # Druga mera (druga dimenzija) pa določa porabo dolžine vozila.
        self.fiksna_sirina = 120  # Vedno 1.20m (dve skupaj naneseta 2.40m, kar gre v 2.44m širine)
        # Poraba dolžine je tista mera, ki ni 1.20m
        vnesena_mera_1 = int(sirina_m * 100)
        vnesena_mera_2 = int(dolzina_m * 100)
        self.poraba_dolzine = vnesena_mera_1 if vnesena_mera_1 != 120 else vnesena_mera_2
        
        self.barva = barva
        self.dvonivojsko = dvonivojsko
        self.vedno_dvonivojsko = vedno_dvonivojsko

def izracunaj_parni_naklad(vozilo, seznam_palet):
    """
    Algoritem, ki palete strogo razporeja v PARU (Leva in Desna stran kamiona).
    Ker sta dve paleti široki 2x120cm = 240cm, se popolnoma prilegata v širino 244cm.
    """
    izbrane_palete = []
    preostanek_tovora = []
    
    # Razvrstimo tovor od najdaljših palet proti najkrajšim, da se dolžina vozila bolje izkoristi
    urejen_seznam = sorted(seznam_palet, key=lambda p: p.poraba_dolzine, reverse=True)
    
    trenutni_x = 0  # Pozicija po dolžini kamiona
    
    # Delamo v korakih po dve paleti hkrati (par leva + desna)
    i = 0
    while i < len(urejen_seznam):
        paleta1 = urejen_seznam[i]
        
        # Preverimo, ali imamo na voljo še drugo paleto za par
        ima_par = (i + 1 < len(urejen_seznam))
        paleta2 = urejen_seznam[i+1] if ima_par else None
        
        # Določimo, koliko dolžine bo ta vrsta porabila (maksimalno dolžino med obema v paru)
        potrebna_dolzina = paleta1.poraba_dolzine
        if paleta2 and paleta2.poraba_dolzine > potrebna_dolzina:
            potrebna_dolzina = paleta2.poraba_dolzine
            
        # Preverimo, ali imamo v vozilu sploh še dovolj dolžine za to vrsto
        if trenutni_x + potrebna_dolzina <= vozilo.dolzina:
            # 1. Naložimo PRVO paleto na LEVO stran (y=0 do y=120)
            nivoji1 = 2 if (paleta1.dvonivojsko or paleta1.vedno_dvonivojsko) else 1
            izbrane_palete.append((trenutni_x, 0, paleta1.poraba_dolzine, 120, 1, paleta1.ime, paleta1.barva))
            if nivoji1 == 2:
                izbrane_palete.append((trenutni_x, 0, paleta1.poraba_dolzine, 120, 2, paleta1.ime, paleta1.barva))
            
            # 2. Naložimo DRUGO paleto na DESNO stran (y=120 do y=240), če obstaja
            if paleta2:
                nivoji2 = 2 if (paleta2.dvonivojsko or paleta2.vedno_dvonivojsko) else 1
                izbrane_palete.append((trenutni_x, 120, paleta2.poraba_dolzine, 120, 1, paleta2.ime, paleta2.barva))
                if nivoji2 == 2:
                    izbrane_palete.append((trenutni_x, 120, paleta2.poraba_dolzine, 120, 2, paleta2.ime, paleta2.barva))
                i += 2  # Uspešno naložen cel par (dve paleti)
            else:
                i += 1  # Naložena samo ena paleta, ker je zmanjkalo tovora v seznamu
                
            # Premaknemo se naprej po dolžini kamiona za naslednjo vrsto
            trenutni_x += potrebna_dolzina
        else:
            # Če vrsta ne gre več v kamion, gre celoten preostanek tovora med nenaložene
            preostanek_tovora.extend(urejen_seznam[i:])
            break
            
    return izbrane_palete, preostanek_tovora

# --- SPLETNI VMESNIK (UI) ---
st.title("🚚 Parni Kalkulator in Načrtovalec Naklada Palet")
st.write("Optimizirano za vzporedno nakladanje dveh palet (širine 1.20m) na levo in desno stran tovornjaka (skupaj 2.40m v širino 2.44m).")

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

# Definicija palet (Mera 1.20m se vedno obravnava kot širina posamezne palete za bočni par)
pal_standard = VrstaPalete("Standard", 1.25, 1.20, barva='#ffadad', dvonivojsko=False)
pal_vecja = VrstaPalete("Večja", 1.40, 1.20, barva='#ffd166', dvonivojsko=False)
pal_posebna = VrstaPalete("Posebna", 1.50, 1.20, barva='#a8dadc', dvonivojsko=False)
pal_dvometerska = VrstaPalete("2-Metrska", 2.00, 1.20, barva='#9bf6ff', vedno_dvonivojsko=True)
pal_trimeterska = VrstaPalete("2.9-Metrska", 2.90, 1.20, barva='#bdb2ff', vedno_dvonivojsko=True)
baza_vseh_palet = [pal_standard, pal_vecja, pal_posebna, pal_dvometerska, pal_trimeterska]

# Vnos količin na spletni strani
st.sidebar.header("2. Vnos količine palet")
n_std = st.sidebar.number_input(f"Standardne (1.25m dolžina x 1.20m)", min_value=0, value=0, step=1)
n_vec = st.sidebar.number_input(f"Večje (1.40m dolžina x 1.20m)", min_value=0, value=0, step=1)
n_pos = st.sidebar.number_input(f"Posebne (1.50m dolžina x 1.20m)", min_value=0, value=0, step=1)
n_2m = st.sidebar.number_input(f"2-Metrske (2.00m dolžina - vedno 2 nivoja)", min_value=0, value=0, step=1)
n_29m = st.sidebar.number_input(f"2.9-Metrske (2.90m dolžina - vedno 2 nivoja)", min_value=0, value=0, step=1)

# Sestavljanje seznama celotnega naročila
trenutni_tovor = ([pal_standard]*n_std + [pal_vecja]*n_vec + [pal_posebna]*n_pos + 
                  [pal_dvometerska]*n_2m + [pal_trimeterska]*n_29m)

if len(trenutni_tovor) > 0:
    # Izračun parne razporeditve za kamion
    palete_kamion, preostanek = izracunaj_parni_naklad(kamion, trenutni_tovor)
    
    # Izračun parne razporeditve za prikolico (če obstaja)
    palete_prikolica = []
    if prikolica and preostanek:
        palete_prikolica, preostanek = izracunaj_parni_naklad(prikolica, preostanek)
        
    # Prikaz številčnih podatkov / kartic uspeha
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
            st.error(f"⚠️ V vozilih je zmanjkalo prostora! Ostalo je še {len(preostanek)} palet.")
        else:
            st.success("✅ Vse palete so uspešno in simetrično naložene v parih!")

    # Izris grafičnega tlorisa
    fig, ax = plt.subplots(figsize=(16, 5))
    ax.set_aspect('equal')
    razmik = 150 
    
    # Izris Kamiona
    ax.add_patch(patches.Rectangle((0, 0), kamion.dolzina, kamion.sirina, linewidth=2, edgecolor='black', facecolor='none'))
    # Sredinska ločilna črta za lažjo predstavo leve in desne strani kamiona
    ax.plot([0, kamion.dolzina], [120, 120], color='gray', linestyle=':', alpha=0.5)
    
    for (x, y, w, h, nivo, ime, barva) in palete_kamion:
        vzorec = '///' if nivo == 2 else None
        ax.add_patch(patches.Rectangle((x, y), w, h, linewidth=1, edgecolor='#2b2d42', facecolor=barva, hatch=vzorec, alpha=0.8))
        ax.text(x + w/2, y + h/2, f"{ime}\nN{nivo}", color='black', ha='center', va='center', fontsize=7, weight='bold')
        
    # Izris Prikolice
    if prikolica:
        start_xb = kamion.dolzina + razmik
        ax.add_patch(patches.Rectangle((start_xb, 0), prikolica.dolzina, prikolica.sirina, linewidth=2, edgecolor='black', facecolor='none'))
        ax.plot([start_xb, start_xb + prikolica.dolzina], [120, 120], color='gray', linestyle=':', alpha=0.5)
        
        for (x, y, w, h, nivo, ime, barva) in palete_prikolica:
            vzorec = '///' if nivo == 2 else None
            ax.add_patch(patches.Rectangle((start_xb + x, y), w, h, linewidth=1, edgecolor='#2b2d42', facecolor=barva, hatch=vzorec, alpha=0.8))
            ax.text(start_xb + x + w/2, y + h/2, f"{ime}\nN{nivo}", color='black', ha='center', va='center', fontsize=7, weight='bold')

    # Nastavitve in dinamična legenda pod grafom
    legenda_elementi = [patches.Patch(facecolor=p.barva, edgecolor='#2b2d42', label=f"{p.ime} ({p.poraba_dolzine/100}m porabe dolžine)") for p in baza_vseh_palet]
    legenda_elementi.append(patches.Patch(facecolor='white', edgecolor='black', label='N1 = Spodnja paleta'))
    legenda_elementi.append(patches.Patch(facecolor='white', edgecolor='black', hatch='///', label='N2 = Zgornja paleta (Dvonivojsko)'))

    skupna_dolzina = kamion.dolzina + (razmik + prikolica.dolzina if prikolica else 0)
    ax.set_xlim(-50, skupna_dolzina + 50)
    ax.set_ylim(-20, 260)
    
    ax.legend(handles=legenda_elementi, loc='upper center', bbox_to_anchor=(0.5, -0.18), ncol=3, fancybox=True, shadow=True)
    plt.tight_layout()
    
    st.pyplot(fig)

else:
    st.info("💡 V stranski vrstici na levi strani izberite vrsto tovornjaka in vnesite količino palet za izračun simetričnega naklada.")
