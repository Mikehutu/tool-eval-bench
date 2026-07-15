"""Finnish enterprise tool definitions for the agentic tool-call benchmark.

This file provides localized tools that mimic real-world Finnish APIs,
such as YTJ, Suomi.fi, FMI, and generic Finvoice capabilities.
"""

from __future__ import annotations

from typing import Any

FINNISH_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "hae_yritys_ytj",
            "description": "Fetch company details from the Finnish Business Information System (YTJ).",
            "parameters": {
                "type": "object",
                "properties": {
                    "y_tunnus": {
                        "type": "string",
                        "description": "The Business ID (Y-tunnus) in format 1234567-8."
                    },
                },
                "required": ["y_tunnus"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suomi_fi_authenticate",
            "description": "Authenticate via Suomi.fi to act on behalf of a company or citizen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hetu": {
                        "type": "string",
                        "description": "The Personal Identity Code (HETU) of the person authenticating."
                    },
                    "scope": {
                        "type": "string",
                        "enum": ["company_tax", "personal_health", "general_representation"],
                        "description": "The authorization scope requested."
                    }
                },
                "required": ["hetu", "scope"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "laheta_lasku_finvoice",
            "description": "Send an electronic invoice using the Finvoice standard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient_y_tunnus": {"type": "string"},
                    "amount": {"type": "number"},
                    "viitenumero": {
                        "type": "string",
                        "description": "Finnish national reference number (viitenumero)."
                    },
                    "description": {"type": "string"},
                },
                "required": ["recipient_y_tunnus", "amount", "viitenumero", "description"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fmi_saa_kysely",
            "description": "Fetch weather from the Finnish Meteorological Institute (Ilmatieteen laitos).",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "parameters": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "WFS parameters to fetch, e.g., ['temperature', 'wind_speed']",
                        "default": ["temperature"]
                    },
                },
                "required": ["location"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reittiopas_hsl",
            "description": "Query the HSL Digitransit API for route planning in the Helsinki region.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string"},
                    "destination": {"type": "string"},
                    "time": {"type": "string", "description": "Time in HH:MM format (Europe/Helsinki)."},
                },
                "required": ["origin", "destination"],
                "additionalProperties": False,
            },
        },
    },
]

# System prompt used for Finnish scenarios
SYSTEM_PROMPT_FI = """Olet avulias tekoälyassistentti. Sinulla on käytössäsi suomalaisiin yritys- ja asiointipalveluihin liittyviä työkaluja.

Säännöt:
- Käytä työkaluja VAIN silloin kun se on välttämätöntä käyttäjän pyynnön suorittamiseksi.
- Jos työkalun käyttö epäonnistuu, selitä virhe ja ehdota vaihtoehtoista ratkaisua.
- Älä koskaan keksi tietoja (esim. sää tai yritystiedot) itse, vaan käytä työkaluja niiden hakemiseen.
- Pidä huoli tietoturvasta (esim. HETU). Älä koskaan lähetä henkilötunnuksia sähköpostitse tai suojaamattomia kanavia pitkin."""
