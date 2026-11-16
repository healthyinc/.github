#!/usr/bin/env python3
"""Declarative configuration for the Healthy Inc. (@healthyinc) profile pipeline.

Defines organization-scoped domain classification rules, technology stack badges,
and baseline contributor display metadata for the commercial engineering profile.
"""

ORG_NAME = "healthyinc"
REPO_FULL_NAME = "healthyinc/.github"

MATRIX_SUBTITLE = "Active Ecosystem Capability Overview"
MATRIX_HEADERS = (
    "Core Engineering Domain",
    "Technology & Tooling Stack",
    "Domain Scope & Focus",
)

STATS_HEADING = "### 📈 Global Ecosystem Activity & Infrastructure"
VELOCITY_UNIT_LABEL = "Commits across active engineering workstreams"
ACTIVE_CONTRIBUTORS_LABEL = "Active Developers"
MIN_DISPLAY_ACTIVE_CONTRIBUTORS = 5

# Ordered baseline maintainers displayed in the circular avatar section.
# Any additional organization member who merges commits to a default branch
# within the rolling 30-day window is appended automatically.
CORE_COLLABORATORS = [
    ("Chali-healthy", "Chali (@Chali-healthy)"),
    ("anbhimi", "Ananth (@anbhimi)"),
    ("pradeeban", "Dr. Pradeeban Kathiravelu (@pradeeban)"),
    ("imvenkat178", "Venkata Reddy Bhimireddy (@imvenkat178)"),
    ("karthiksathishjeemain", "Karthik Sathish (@karthiksathishjeemain)"),
]
AUTO_INCLUDE_ALL_ORG_MEMBERS = False

BADGE_LIBRARY = {
    "solana": "![Solana](https://img.shields.io/badge/Solana_SVM-14F195?style=flat-square&logo=solana&logoColor=black)",
    "rust": "![Rust Anchor](https://img.shields.io/badge/Rust_Anchor-000000?style=flat-square&logo=rust&logoColor=white)",
    "wormhole": "![Wormhole](https://img.shields.io/badge/Wormhole_Bridge-000000?style=flat-square&logo=circle&logoColor=00FFFF)",
    "tlsnotary": "![TLSNotary](https://img.shields.io/badge/TLSNotary_zkTLS-3F51B5?style=flat-square&logo=letsencrypt&logoColor=white)",
    "chainlink": "![Chainlink](https://img.shields.io/badge/Chainlink_Oracle-375BD2?style=flat-square&logo=chainlink&logoColor=white)",
    "ethereum": "![Ethereum EVM](https://img.shields.io/badge/Ethereum_EVM-3C3C3D?style=flat-square&logo=ethereum&logoColor=white)",
    "solidity": "![Solidity](https://img.shields.io/badge/Solidity-363636?style=flat-square&logo=solidity&logoColor=white)",
    "typescript": "![TypeScript](https://img.shields.io/badge/TypeScript-2B7489?style=flat-square&logo=typescript&logoColor=white)",
    "eclipse": "![Eclipse SVM](https://img.shields.io/badge/Eclipse_SVM-000000?style=flat-square&logo=e&logoColor=14F195)",
    "shadow": "![Shadow Drive](https://img.shields.io/badge/Shadow_DePIN-7E57C2?style=flat-square&logo=serverless&logoColor=white)",
    "circom": "![Circom ZK](https://img.shields.io/badge/Circom_ZK-FF5722?style=flat-square&logo=webassembly&logoColor=white)",
    "python": "![Python](https://img.shields.io/badge/Python-3572A5?style=flat-square&logo=python&logoColor=white)",
    "go": "![Go](https://img.shields.io/badge/Go_Lang-00ADD8?style=flat-square&logo=go&logoColor=white)",
    "pytorch": "![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)",
    "fastapi": "![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)",
    "bmad": "![BMAD Orchestrator](https://img.shields.io/badge/BMAD_Agentic-6A1B9A?style=flat-square&logo=target&logoColor=white)",
    "vllm": "![vLLM Inference](https://img.shields.io/badge/vLLM-4CAF50?style=flat-square&logo=openai&logoColor=white)",
    "react_native": "![React Native](https://img.shields.io/badge/React_Native-61DAFB?style=flat-square&logo=react&logoColor=black)",
    "expo": "![Expo](https://img.shields.io/badge/Expo-000020?style=flat-square&logo=expo&logoColor=white)",
    "kotlin": "![Kotlin](https://img.shields.io/badge/Kotlin-7F52FF?style=flat-square&logo=kotlin&logoColor=white)",
    "swift": "![Swift](https://img.shields.io/badge/Swift-FA7343?style=flat-square&logo=swift&logoColor=white)",
    "nextjs": "![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat-square&logo=next.js&logoColor=white)",
    "fhir": "![FHIR / HL7](https://img.shields.io/badge/FHIR_HL7-E91E63?style=flat-square&logo=health-icons&logoColor=white)",
    "nitro": "![AWS Nitro](https://img.shields.io/badge/Nitro_Enclaves-FF9900?style=flat-square&logo=amazon-aws&logoColor=white)",
    "tls": "![mTLS Security](https://img.shields.io/badge/Zero--Trust_mTLS-0288D1?style=flat-square&logo=letsencrypt&logoColor=white)",
    "docker": "![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)",
    "shell": "![Shell](https://img.shields.io/badge/Shell-4EAA25?style=flat-square&logo=gnu-bash&logoColor=white)",
    "hipaa": "![HIPAA Zero-Trust](https://img.shields.io/badge/HIPAA_Zero--Trust-000000?style=flat-square&logo=shield&logoColor=white)",
}

DEFAULT_DOMAIN = "HealthTech & Mobile Ecosystem"

DOMAINS = [
    {
        "name": "DeFi & Web3 Tokenomics",
        "badges": [
            "solana", "rust", "eclipse", "shadow", "chainlink",
            "wormhole", "tlsnotary", "ethereum", "solidity", "circom", "typescript",
        ],
        "scope": "SVM/EVM Smart Contracts, Habitcoin Tokenomics, DePIN Storage & Circom ZK Circuits",
        "keywords": [
            "token", "web3", "solana", "evm", "defi", "habitcoin", "bioblock",
            "bio-block", "depin", "contract", "crypto", "blockchain", "shadow",
            "eclipse", "circom", "zk", "anchor", "erc",
        ],
        "languages": ["solidity", "rust", "circom"],
    },
    {
        "name": "Agentic AI & LLM Systems",
        "badges": ["python", "go", "pytorch", "fastapi", "bmad", "vllm"],
        "scope": "Multi-Agent Orchestration, Intelligent Data Object (IDO) Modeling, Predictive Health Analytics & Go Microservices",
        "keywords": [
            "ai", "llm", "agent", "model", "intelligence", "data-lab", "harness",
            "machine learning", "ml", "bmad", "golang", "go", "ido", "rag",
            "orchestrat", "reconnaissance",
        ],
        "languages": ["python", "jupyter notebook", "go"],
    },
    {
        "name": "HealthTech & Mobile Ecosystem",
        "badges": ["react_native", "expo", "kotlin", "swift", "nextjs", "fhir"],
        "scope": "Mobile Telehealth App, Android/iOS Wrappers, FHIR/EHR Data Federation & Clinical Portals",
        "keywords": [
            "app-mvp", "hospital", "telehealth", "fhir", "hl7", "expo",
            "customer-demo", "mvp-demo", "portal", "patient",
        ],
        "languages": ["kotlin", "swift", "java", "dart", "objective-c", "typescript", "javascript"],
    },
    {
        "name": "Cybersecurity & Compliance",
        "badges": ["nitro", "tls", "docker", "shell", "hipaa"],
        "scope": "Automated Threat Verification Harnesses, HIPAA Zero-Trust Control Enclaves & Hardware Isolation",
        "keywords": [
            "security", "threat", "audit", "defense", "posture", "cyber",
            "zero-trust", "hipaa", "compliance", "nitro", "enclave", "deployment",
        ],
        "languages": ["shell", "dockerfile", "powershell", "batchfile"],
    },
]
