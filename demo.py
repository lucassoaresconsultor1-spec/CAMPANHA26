"""Gerador de DADOS FICTÍCIOS para demonstração.

Os dados saem exatamente no mesmo formato da planilha real
(respostas do Google Forms + abas EQUIPE, BAIRROS e SECOES),
então o painel processa demo e dados reais pelo mesmo caminho.
Nenhum nome, telefone ou documento aqui pertence a pessoas reais.
"""
import random
from datetime import date, datetime, timedelta
from urllib.parse import quote_plus

import pandas as pd

COLUNAS_RESPOSTAS = [
    "Carimbo de data/hora",
    "Multiplicador",
    "Nome completo",
    "Título de eleitor",
    "CPF",
    "Data de nascimento",
    "Sexo",
    "WhatsApp",
    "Bairro",
    "Número da seção",
    "Possui veículo?",
    "Modelo do veículo",
    "Cor do veículo",
    "Placa",
    "Como pode apoiar?",
    "Consentimento (LGPD)",
]

OPCAO_ADESIVO = "Adesivo no veículo"
OPCAO_BANDEIRA = "Bandeira"
OPCAO_DIA_E = "Trabalho no dia da eleição"

LIDERES = [
    "Bebeto", "Ana Paula", "Marcos Vinícius", "Rose", "Diego",
    "Jorge", "Cida", "Paulinho", "Tereza", "Washington",
    "Kelly", "Robson", "Neide", "Fabiano", "Sandra Lúcia",
]
# força de cada liderança (deixa o ranking variado)
FORCA_LIDER = [1.25, 1.15, 1.1, 1.05, 1.0, 1.0, 0.95, 0.95, 0.9, 0.9, 0.85, 0.8, 0.75, 0.65, 0.55]

# Lista de exemplo — confira e ajuste com a lista oficial de bairros.
BAIRROS = [
    ("Centro", 10), ("Parque Hotel", 6), ("Iguabinha", 6), ("Praia Seca", 5),
    ("Bananeiras", 5), ("Coqueiral", 4), ("Areal", 4), ("Pontinha", 4),
    ("Ponte dos Leites", 4), ("Outeiro", 3), ("Mataruna", 3), ("Fazendinha", 3),
    ("São Vicente de Paulo", 3), ("Hospício", 3), ("Vila Capri", 2), ("Parati", 2),
    ("Morro Grande", 2), ("Barbudo", 2), ("XV de Novembro", 2), ("Viaduto", 2),
    ("Rio do Limão", 1), ("Três Vendas", 1), ("Sobradinho", 0), ("Boa Perna", 0),
]

NOMES_M = [
    "Lucas", "Jean", "Carlos", "Rafael", "Thiago", "Wellington", "Roberto", "Márcio",
    "Felipe", "Renato", "Igor", "Paulo", "Vitor", "Edson", "Gustavo", "Leandro",
    "André", "Hugo", "Sérgio", "Fábio", "Otávio", "José", "Antônio", "Francisco",
    "João", "Pedro", "Luiz", "Marcelo", "Ricardo", "Eduardo", "Rodrigo", "Leonardo",
    "Bruno", "Daniel", "Mateus", "Gabriel", "Alexandre", "Fernando", "Sebastião",
    "Raimundo", "Manoel", "Cláudio", "Adriano", "Wagner", "Anderson", "Rogério",
    "Valdir", "Gilberto", "Mário", "Davi", "Samuel", "Caio", "Vinícius", "Diogo",
    "Emerson", "Juliano", "Nelson", "Ronaldo", "Severino", "Josias",
]
NOMES_F = [
    "Fernanda", "Patrícia", "Bruna", "Juliana", "Camila", "Sandra", "Luana", "Débora",
    "Simone", "Aline", "Kátia", "Cláudia", "Mônica", "Tânia", "Priscila", "Viviane",
    "Larissa", "Elaine", "Raquel", "Sílvia", "Maria", "Ana", "Francisca", "Antônia",
    "Adriana", "Márcia", "Aparecida", "Luciana", "Vanessa", "Jéssica", "Letícia",
    "Beatriz", "Gabriela", "Rosângela", "Cristiane", "Eliane", "Fátima", "Rita", "Vera",
    "Lúcia", "Helena", "Isabela", "Carla", "Daniela", "Tatiane", "Josiane", "Rosana",
    "Michele", "Regina", "Sônia", "Natália", "Amanda", "Bianca", "Rafaela", "Sueli",
    "Neusa", "Ivone", "Marlene", "Edna", "Graça",
]
SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira",
    "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes",
    "Fernandes", "Vieira", "Barbosa", "Rocha", "Dias", "Nascimento", "Andrade",
    "Moreira", "Nunes", "Marques", "Machado", "Mendes", "Freitas", "Cardoso", "Ramos",
    "Gonçalves", "Santana", "Teixeira", "Moraes", "Correia", "Pinto", "Cavalcanti",
    "Monteiro", "Batista", "Campos", "Azevedo", "Reis", "Matos", "Siqueira", "Coelho",
    "Brito", "Pacheco", "Quintanilha", "Viana",
]

MODELOS = [
    ("Gol", 8), ("Onix", 8), ("HB20", 7), ("Ka", 6), ("Palio", 5), ("Uno", 6),
    ("Strada", 4), ("Saveiro", 3), ("Fiesta", 3), ("Sandero", 4), ("Argo", 3),
    ("Mobi", 4), ("Kwid", 4), ("Celta", 4), ("Fox", 3), ("Corolla", 2), ("Civic", 1),
    ("Hilux", 1), ("Spin", 2), ("Prisma", 3), ("CG 160", 4), ("Biz", 2),
]
CORES = [("Branco", 8), ("Prata", 8), ("Preto", 6), ("Cinza", 5), ("Vermelho", 3),
         ("Azul", 2), ("Bege", 1), ("Verde", 1)]

TIPOS_LOCAL = ["Escola Municipal", "Colégio Estadual", "Centro Educacional", "Escola Estadual", "CIEP"]

FAIXAS_IDADE = [((16, 17), 3), ((18, 24), 13), ((25, 34), 19), ((35, 44), 20), ((45, 59), 26), ((60, 84), 19)]


def _peso(rng, itens):
    valores = [i for i, _ in itens]
    pesos = [p for _, p in itens]
    return rng.choices(valores, weights=pesos, k=1)[0]


def _cpf(rng, valido=True, pontuado=True):
    base = [rng.randint(0, 9) for _ in range(9)]
    if len(set(base)) == 1:
        base[0] = (base[0] + 1) % 10

    def dv(nums):
        soma = sum(n * w for n, w in zip(nums, range(len(nums) + 1, 1, -1)))
        r = (soma * 10) % 11
        return 0 if r == 10 else r

    d1 = dv(base)
    d2 = dv(base + [d1])
    nums = base + [d1, d2]
    if not valido:
        nums[-1] = (nums[-1] + 1) % 10
    s = "".join(str(n) for n in nums)
    return f"{s[:3]}.{s[3:6]}.{s[6:9]}-{s[9:]}" if pontuado else s


def _titulo(rng, valido=True):
    corpo = "".join(str(rng.randint(0, 9)) for _ in range(8)) + "03" + "".join(str(rng.randint(0, 9)) for _ in range(2))
    if not valido:
        corpo = corpo[:-1]
    if rng.random() < 0.5:
        return f"{corpo[:4]} {corpo[4:8]} {corpo[8:]}"
    return corpo


def _telefone(rng, usados):
    # Prefixo 900xx: números claramente fictícios
    while True:
        meio = f"900{rng.randint(0, 99):02d}"
        fim = f"{rng.randint(0, 9999):04d}"
        if (meio, fim) not in usados:
            usados.add((meio, fim))
            break
    estilo = rng.random()
    if estilo < 0.6:
        return f"(22) {meio}-{fim}"
    if estilo < 0.85:
        return f"22{meio}{fim}"
    return f"22 {meio} {fim}"


def _placa(rng):
    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    l3 = "".join(rng.choice(letras) for _ in range(3))
    if rng.random() < 0.7:
        return f"{l3}{rng.randint(0, 9)}{rng.choice(letras)}{rng.randint(0, 99):02d}"
    return f"{l3}-{rng.randint(0, 9999):04d}"


def _nome(rng, sexo):
    pool = NOMES_F if sexo == "F" else NOMES_M
    primeiro = rng.choice(pool)
    if rng.random() < 0.25:
        segundo = rng.choice(pool)
        if segundo != primeiro:
            primeiro = f"{primeiro} {segundo}"
    s1, s2 = rng.sample(SOBRENOMES, 2)
    if rng.random() < 0.3:
        s1 = rng.choice(["da Silva", "dos Santos", "de Souza", "da Costa", "de Oliveira", "da Rocha", "dos Reis",
                         "de Almeida", "do Nascimento", "de Freitas"])
    return f"{primeiro} {s1} {s2}"


def gerar_demo(seed=2026, hoje=None):
    """Retorna um dict com as 4 abas brutas (DataFrames de texto)."""
    rng = random.Random(seed)
    hoje = hoje or date.today()
    agora = datetime.combine(hoje, datetime.min.time()) + timedelta(hours=19)

    # ---- SECOES ---------------------------------------------------------
    secoes, secoes_por_bairro = [], {}
    numero = 1
    homenageados = set()
    for bairro, peso in BAIRROS:
        n_locais = 1 if peso <= 2 else (2 if peso <= 5 else 3)
        for _ in range(n_locais):
            while True:
                tit = rng.choice(["Prof.", "Prof.ª", "Dr.", "", ""])
                pessoa = rng.choice(NOMES_F if tit == "Prof.ª" else NOMES_M + NOMES_F)
                nome_local = f"{rng.choice(TIPOS_LOCAL)} {tit + ' ' if tit else ''}{pessoa} {rng.choice(SOBRENOMES)}"
                if nome_local not in homenageados:
                    homenageados.add(nome_local)
                    break
            mapa = "https://www.google.com/maps/search/?api=1&query=" + quote_plus(f"{nome_local}, {bairro}, Araruama RJ")
            for _ in range(rng.randint(3, 7)):
                secoes.append({"Seção": str(numero), "Local de votação": nome_local, "Bairro": bairro, "Link do mapa": mapa})
                secoes_por_bairro.setdefault(bairro, []).append(numero)
                numero += 1

    bairros_ativos = [(b, p) for b, p in BAIRROS if p > 0]

    # ---- EQUIPE ---------------------------------------------------------
    usados_nomes, usados_tel = set(), set()
    equipe, plano = [], []
    for i_lider, lider in enumerate(LIDERES):
        tel_lider = _telefone(rng, usados_tel)
        n_mult = rng.randint(5, 10)
        for j in range(n_mult):
            if lider == "Bebeto" and j < 3:
                nome_mult = ["Lucas Andrade", "Jean Carvalho", "Carlos Mendes"][j]
            else:
                while True:
                    sx = rng.choice("MF")
                    nome_mult = f"{rng.choice(NOMES_F if sx == 'F' else NOMES_M)} {rng.choice(SOBRENOMES)}"
                    if nome_mult not in usados_nomes:
                        break
            usados_nomes.add(nome_mult)
            equipe.append({"Multiplicador": nome_mult, "Líder": lider, "WhatsApp": _telefone(rng, usados_tel),
                           "WhatsApp do líder": tel_lider})

            r = rng.random()
            if r < 0.10:
                n = rng.randint(0, 3)
            elif r < 0.30:
                n = rng.randint(4, 9)
            elif r < 0.70:
                n = rng.randint(10, 15)
            elif r < 0.92:
                n = rng.randint(15, 20)
            else:
                n = rng.randint(21, 28)
            n = max(0, round(n * FORCA_LIDER[i_lider]))
            if lider == "Bebeto" and j < 3:
                n = [24, 21, 18][j]
            inicio = hoje - timedelta(days=rng.randint(55, 84))
            if rng.random() < 0.15:
                fim = hoje - timedelta(days=rng.randint(8, 24))
            else:
                fim = hoje - timedelta(days=rng.randint(0, 3))
            plano.append({"mult": nome_mult, "n": n, "inicio": inicio, "fim": fim,
                          "casa": _peso(rng, bairros_ativos)})

    # Multiplicador que ainda não foi lançado na aba EQUIPE (para o alerta)
    plano.append({"mult": "Josué Martins", "n": 4, "inicio": hoje - timedelta(days=20),
                  "fim": hoje - timedelta(days=2), "casa": "Areal"})

    # ---- RESPOSTAS ------------------------------------------------------
    linhas = []
    for p in plano:
        dias = max(1, (p["fim"] - p["inicio"]).days)
        for k in range(p["n"]):
            u = 1.0 if k == 0 else rng.random() ** 0.55  # o último cadastro cai no fim da atividade
            dia = p["inicio"] + timedelta(days=int(u * dias))
            momento = datetime.combine(dia, datetime.min.time()) + timedelta(
                hours=rng.randint(8, 21), minutes=rng.randint(0, 59), seconds=rng.randint(0, 59))
            momento = min(momento, agora)

            sexo = "F" if rng.random() < 0.53 else "M"
            faixa = _peso(rng, FAIXAS_IDADE)
            idade = rng.randint(faixa[0], faixa[1])
            nasc = hoje - timedelta(days=int(idade * 365.25) + rng.randint(1, 360))
            bairro = p["casa"] if rng.random() < 0.6 else _peso(rng, bairros_ativos)
            secao = rng.choice(secoes_por_bairro[bairro])

            tem_veiculo = rng.random() < 0.22
            apoios = []
            if tem_veiculo and rng.random() < 0.5:
                apoios.append(OPCAO_ADESIVO)
            if rng.random() < 0.12:
                apoios.append(OPCAO_BANDEIRA)
            if rng.random() < (0.35 if tem_veiculo else 0.12):
                apoios.append(OPCAO_DIA_E)

            cpf_r = rng.random()
            cpf = "" if cpf_r < 0.01 else _cpf(rng, valido=cpf_r >= 0.03, pontuado=rng.random() < 0.6)
            tel = _telefone(rng, usados_tel) if rng.random() > 0.01 else "22 9912"

            linhas.append({
                "_t": momento,
                "Carimbo de data/hora": momento.strftime("%d/%m/%Y %H:%M:%S"),
                "Multiplicador": p["mult"],
                "Nome completo": _nome(rng, sexo) if rng.random() > 0.08 else _nome(rng, sexo).upper(),
                "Título de eleitor": _titulo(rng, valido=rng.random() > 0.01),
                "CPF": cpf,
                "Data de nascimento": "" if rng.random() < 0.03 else nasc.strftime("%d/%m/%Y"),
                "Sexo": "" if rng.random() < 0.02 else ("Feminino" if sexo == "F" else "Masculino"),
                "WhatsApp": tel,
                "Bairro": bairro if rng.random() > 0.05 else bairro.upper(),
                "Número da seção": str(secao),
                "Possui veículo?": "Sim" if tem_veiculo else "Não",
                "Modelo do veículo": _peso(rng, MODELOS) if tem_veiculo else "",
                "Cor do veículo": _peso(rng, CORES) if tem_veiculo else "",
                "Placa": _placa(rng) if tem_veiculo else "",
                "Como pode apoiar?": ", ".join(apoios),
                "Consentimento (LGPD)": "Sim, autorizo",
            })

    # ---- Duplicatas propositais (para a aba Duplicatas) ------------------
    mults_por_lider = {}
    for e in equipe:
        mults_por_lider.setdefault(e["Líder"], []).append(e["Multiplicador"])
    lider_de = {e["Multiplicador"]: e["Líder"] for e in equipe}

    def outro_mult(mult):
        lider = lider_de.get(mult)
        lideres = [lid for lid in LIDERES if lid != lider]
        return rng.choice(mults_por_lider[rng.choice(lideres)])

    base = list(linhas)
    extras = []
    for _ in range(8):   # mesma pessoa cadastrada por outra liderança
        orig = rng.choice(base)
        c = dict(orig)
        c["Multiplicador"] = outro_mult(orig["Multiplicador"])
        c["_t"] = min(orig["_t"] + timedelta(days=rng.randint(1, 12), hours=rng.randint(0, 5)), agora)
        c["Nome completo"] = orig["Nome completo"].upper() if rng.random() < 0.5 else orig["Nome completo"]
        extras.append(c)
    for _ in range(4):   # mesmo multiplicador enviou duas vezes
        orig = rng.choice(base)
        c = dict(orig)
        c["_t"] = min(orig["_t"] + timedelta(minutes=rng.randint(1, 9)), agora)
        extras.append(c)
    for _ in range(4):   # homônimo (mesmo nome, outra pessoa)
        orig = rng.choice(base)
        c = dict(rng.choice(base))
        c["Nome completo"] = orig["Nome completo"]
        c["CPF"] = _cpf(rng)
        c["Título de eleitor"] = _titulo(rng)
        c["WhatsApp"] = _telefone(rng, usados_tel)
        c["_t"] = min(orig["_t"] + timedelta(days=rng.randint(1, 20)), agora)
        extras.append(c)
    for _ in range(4):   # família com o mesmo telefone
        orig = rng.choice(base)
        sexo = rng.choice("MF")
        c = dict(orig)
        c["Nome completo"] = _nome(rng, sexo)
        c["Sexo"] = "Feminino" if sexo == "F" else "Masculino"
        c["CPF"] = _cpf(rng)
        c["Título de eleitor"] = _titulo(rng)
        c["Data de nascimento"] = (hoje - timedelta(days=rng.randint(18 * 365, 70 * 365))).strftime("%d/%m/%Y")
        c["_t"] = min(orig["_t"] + timedelta(days=rng.randint(0, 6), hours=1), agora)
        extras.append(c)
    for c in extras:
        c["Carimbo de data/hora"] = c["_t"].strftime("%d/%m/%Y %H:%M:%S")

    todas = sorted(linhas + extras, key=lambda r: r["_t"])
    respostas = pd.DataFrame([{k: r[k] for k in COLUNAS_RESPOSTAS} for r in todas], columns=COLUNAS_RESPOSTAS)

    return {
        "respostas": respostas,
        "equipe": pd.DataFrame(equipe, columns=["Multiplicador", "Líder", "WhatsApp", "WhatsApp do líder"]),
        "bairros": pd.DataFrame({"Bairro": [b for b, _ in BAIRROS]}),
        "secoes": pd.DataFrame(secoes, columns=["Seção", "Local de votação", "Bairro", "Link do mapa"]),
    }
