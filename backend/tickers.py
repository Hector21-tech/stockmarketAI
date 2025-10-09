"""
Swedish Tickers Configuration
Mapping of Swedish stock tickers to Yahoo Finance symbols
"""

# Mapping for svenska aktier (ticker -> Yahoo symbol)
SWEDISH_TICKERS = {
    # OMX30 - De 30 största aktierna på Stockholmsbörsen
    "VOLVO-B": "VOLV-B.ST",
    "VOLVO B": "VOLV-B.ST",
    "VOLV-B": "VOLV-B.ST",
    "VOLV B": "VOLV-B.ST",

    "HM-B": "HM-B.ST",
    "HM B": "HM-B.ST",
    "H&M-B": "HM-B.ST",
    "H&M B": "HM-B.ST",

    "ERIC-B": "ERIC-B.ST",
    "ERIC B": "ERIC-B.ST",

    "ABB": "ABB.ST",
    "AZN": "AZN.ST",

    "INVE-B": "INVE-B.ST",  # Investor B
    "INVE B": "INVE-B.ST",
    "INVESTOR-B": "INVE-B.ST",
    "INVESTOR B": "INVE-B.ST",

    "SEB-A": "SEB-A.ST",
    "SEB A": "SEB-A.ST",

    "SWED-A": "SWED-A.ST",  # Swedbank A
    "SWED A": "SWED-A.ST",

    "ATCO-A": "ATCO-A.ST",  # Atlas Copco A
    "ATCO A": "ATCO-A.ST",
    "ATCO-B": "ATCO-B.ST",  # Atlas Copco B
    "ATCO B": "ATCO-B.ST",

    "HEXA-B": "HEXA-B.ST",  # Hexagon B
    "HEXA B": "HEXA-B.ST",

    "SAND": "SAND.ST",  # Sandvik

    "SKF-B": "SKF-B.ST",
    "SKF B": "SKF-B.ST",

    "ALFA": "ALFA.ST",  # Alfa Laval

    "ASSA-B": "ASSA-B.ST",  # ASSA ABLOY B
    "ASSA B": "ASSA-B.ST",

    "EQT": "EQT.ST",  # EQT (Private Equity)

    "HUS-B": "HUSQ-B.ST",  # Husqvarna B (correct symbol)
    "HUS B": "HUSQ-B.ST",

    "SECU-B": "SECU-B.ST",  # Securitas B
    "SECU B": "SECU-B.ST",

    # Banker & Finans
    "SHB-A": "SHB-A.ST",  # Handelsbanken A
    "SHB A": "SHB-A.ST",
    "NDA-SE": "NDA-SE.ST",  # Nordea
    "NDA SE": "NDA-SE.ST",

    # Telekom & Tech
    "TELIA": "TELIA.ST",
    "SINCH": "SINCH.ST",
    "ESSITY-B": "ESSITY-B.ST",
    "ESSITY B": "ESSITY-B.ST",

    # Industri & Manufacturing
    "ELUX-B": "ELUX-B.ST",  # Electrolux B
    "ELUX B": "ELUX-B.ST",
    "GETI-B": "GETI-B.ST",  # Getinge B
    "GETI B": "GETI-B.ST",
    "SKA-B": "SKA-B.ST",  # Skanska B
    "SKA B": "SKA-B.ST",
    "BOL": "BOL.ST",  # Boliden
    "SSAB-A": "SSAB-A.ST",  # SSAB A
    "SSAB A": "SSAB-A.ST",
    "SSAB-B": "SSAB-B.ST",  # SSAB B
    "SSAB B": "SSAB-B.ST",

    # Fastighet
    "FABG": "FABG.ST",  # Fabege
    "SBB-B": "SBB-B.ST",  # Samhallsbyggnadsbolaget B
    "SBB B": "SBB-B.ST",
    "CAST": "CAST.ST",  # Castellum
    "WIHL": "WIHL.ST",  # Wihlborgs

    # Konsument & Retail
    "ICA": "ICA.ST",  # ICA Gruppen
    "AXFO": "AXFO.ST",  # Axfood

    # Hälsovård & Pharma
    "SWMA": "SWMA.ST",  # Swedish Match (delisted, but keep for historical)

    # Gaming & Betting
    "EVO": "EVO.ST",  # Evolution
    "KINV-B": "KINV-B.ST",  # Kinnevik B
    "KINV B": "KINV-B.ST",
    "MTG-B": "MTG-B.ST",  # Modern Times Group B
    "MTG B": "MTG-B.ST",

    # Telecom & Internet
    "TEL2-B": "TEL2-B.ST",  # Tele2 B
    "TEL2 B": "TEL2-B.ST",

    # Materials & Mining
    "LUND": "LUND.ST",  # Lundin Mining

    # Energy
    "EQNR": "EQNR.ST",  # Equinor (Norwegian but traded in Stockholm)
}

# OMX30 Index - De 30 största aktierna (lista för quick add)
OMX30_TICKERS = [
    "VOLVO-B",      # AB Volvo
    "ERIC-B",       # Ericsson
    "ABB",          # ABB Ltd
    "AZN",          # AstraZeneca
    "ATCO-A",       # Atlas Copco A
    "ATCO-B",       # Atlas Copco B
    "INVE-B",       # Investor
    "HM-B",         # H&M
    "HEXA-B",       # Hexagon
    "SAND",         # Sandvik
    "ASSA-B",       # ASSA ABLOY
    "SEB-A",        # SEB
    "SWED-A",       # Swedbank
    "SHB-A",        # Handelsbanken
    "NDA-SE",       # Nordea
    "SKF-B",        # SKF
    "ALFA",         # Alfa Laval
    "BOL",          # Boliden
    "EVO",          # Evolution
    "ESSITY-B",     # Essity
    "SKA-B",        # Skanska
    "TELIA",        # Telia Company
    "TEL2-B",       # Tele2
    "GETI-B",       # Getinge
    "ELUX-B",       # Electrolux
    # "ICA",          # ICA Gruppen (NO DATA - possibly delisted)
    "KINV-B",       # Kinnevik
    "EQT",          # EQT
    "HUS-B",        # Husqvarna B (fixed symbol)
    "SECU-B",       # Securitas
]
