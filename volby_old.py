import math
# Zaokrouhlování nahoru
def round_decimals_up(number:float, decimals:int=2):
    """
    Returns a value rounded up to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return math.ceil(number)

    factor = 10 ** decimals
    return math.ceil(number * factor) / factor

import xml.etree.ElementTree as ET
tree = ET.parse('vysledky.xml') # Načtení .xml souboru s výsledky voleb
root = tree.getroot()

class Strana:
    def __init__(self, name, s_count, votes, number) -> None:
        self.name = name
        # Nastavení volební klauzule podle počtu stran
        if s_count == 1:
            self.threshold = 0.05
        elif s_count == 2:
            self.threshold = 0.08
        else:
            self.threshold = 0.11
        self.votes = votes
        self.region_split = {}
        self.votes_remain = {}
        self.all_votes_remain = 0
        self.number = number

    def checkThreshold(self):
        global all_votes
        if self.votes / all_votes > self.threshold:
            return True
        else:
            return False

class Kraj:
    def __init__(self, name, mandates) -> None:
        self.name = name
        self.votes = 0
        self.mandates = mandates
        self.mandates_remain = mandates
    
    def getVoteNumber(self):
        self.vote_number = round(self.votes / (self.mandates + 2)) # Výpočet krajského volebního čísla

    # Rozdělení mandátů dle prvního skrutinia
    def prvniSkrutinium(self):
        global strany
        global all_votes_remain
        global all_mandates_remain
        self.mandatesSplit = {}
        self.zbytek = []
        
        for i in strany:
            self.mandatesSplit[strany[i].name] = 0
            for number in range(1,self.mandates+1):
                self.zbytek.append([strany[i].name, number ,round_decimals_up(strany[i].region_split[self.name] / number)])
        
        self.sorted_zbytek = sorted(self.zbytek, key=lambda x: x[2], reverse=True)
        for n in range(0,self.mandates):
            self.mandatesSplit[self.sorted_zbytek[n][0]] = self.mandatesSplit[self.sorted_zbytek[n][0]] + 1

                
strany = {}
for i in range(1, len(root[len(root)-1])): # Projede všechny strany, ale přeskočí 0, na které jsou data o účasti
    votes = int(root[len(root)-1][i][0].attrib["HLASY"])
    name = root[len(root)-1][i].attrib["NAZ_STR"]
    number = int(root[len(root)-1][i].attrib["KSTRANA"])

    strany[number] = Strana(name, 1, votes, number)  # Vytvoří stranu s přečtenými daty

all_votes = int(root[len(root)-1][0].attrib["PLATNE_HLASY"]) # len(root-1) vyhodí poslední položku, což je celá ČR

# Výpočet rozdělení mandátů na kraje
rep_mandate_number = round(all_votes / 200) # Výpočet republikového mandátového čísla
region_mandates = {} # Počet mandátů v krajích (pro pozdější přidání do objektu)
zbytky_regions = [] # Zbytky hlasů v krajích po dělení
total_region = 0
for i in range(len(root)-1):
    region_mandates[root[i].attrib["NAZ_KRAJ"]] = int(int(root[i][0].attrib["PLATNE_HLASY"]) / rep_mandate_number) # Rozdělení mandátů do kraje
    zbytky_regions.append([root[i].attrib["NAZ_KRAJ"], int(root[i][0].attrib["PLATNE_HLASY"]) % rep_mandate_number]) # Zbytek hlasů po dělení v kraji
    total_region = total_region + region_mandates[root[i].attrib["NAZ_KRAJ"]] # Celkový počet rozdělených mandátů aktualizovat

if total_region < 200: # Pokud nebyly rozděleny všechny mandáty
    sorted_zbytky_regions = sorted(zbytky_regions, key=lambda x: x[1], reverse=True) # Seřazení zbytků
    counter = 0
    while total_region < 200: # Dokud nerozdělíme všechny mandáty
        region_mandates[sorted_zbytky_regions[counter][0]] = region_mandates[sorted_zbytky_regions[counter][0]] + 1 # Přiřazení mandátu kraji s největším zbytekm
        total_region = total_region + 1
        counter = counter + 1 # Počítadlo cyklů

while True:
    # Zjistit strany, které nemají dostatečné procento hlasů
    disqualified = []
    for i in strany:
        if strany[i].checkThreshold():
            pass
        else:
            disqualified.append(i)
    if len(strany)-len(disqualified) >= 2 :
        break
    else:
        for i in strany:
            strany[i].threshold = strany[i].threshold - 0.01    # Pokud projdou méně jak 2 strany, tak snížit klauzuli o 1%

# Smazat stramy s nedostatečným počtem hlasů
for i in disqualified:
    del strany[i]

kraje = []
for i in range(len(root)-1):
    name = root[i].attrib["NAZ_KRAJ"]
    mandates = int(region_mandates[root[i].attrib["NAZ_KRAJ"]]) # Přidat mandáty do kraje z našeho předchozího výpočtu

    kraje.append(Kraj(name, mandates))

# Do každé strany zapíšeme, kolik dostala hlasů v určitém kraji
for n in range(len(kraje)):
    for m in range(1, len(root[n])):
        if int(root[n][m].attrib["KSTRANA"]) in strany:
            strany[int(root[n][m].attrib["KSTRANA"])].region_split[kraje[n].name] = int(root[n][m][0].attrib["HLASY"])
            kraje[n].votes = kraje[n].votes + int(root[n][m][0].attrib["HLASY"]) # Zjištení celkového počtu hlasů v kraji pro strany, co prošly do prvního skrutinia
    kraje[n].getVoteNumber() # Získat krajské volební číslo

all_votes_remain = 0
for n in range(len(kraje)):
    all_votes_remain = all_votes_remain + kraje[n].votes    # Výpočet všech hlasů pro strany, co prošly do prvního skrutinia
all_mandates_remain = 0
# Výpočet mandátů dle prvního skrutinia
for i in range(len(kraje)):
    kraje[i].prvniSkrutinium()


# Vypsat rozdělení mandátů dle stran
for i in strany:
    total = 0
    for n in range(len(kraje)):
        total = total + kraje[n].mandatesSplit[strany[i].name]
    print(strany[i].name + ": " + str(total))

# Dodělat: odbrávání mandátů, vyřešit problém? moc mandátů na kraj, počet stran v koalici