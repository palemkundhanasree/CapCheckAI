from pathlib import Path
from typing import Dict, Any


def check_content_credentials(file_path: Path) -> Dict[str, Any]:
    """
    Checks image bytes for C2PA / JUMBF (JPEG Universal Metadata Box Format) boxes
    and Content Credentials signatures.
    """
    provenance = {
        "has_c2pa": False,
        "c2pa_status": "No Content Credentials manifest found",
        "manifest_issuer": None,
        "is_ai_declared": False,
        "provenance_actions": []
    }

    try:
        with open(file_path, "rb") as f:
            # Read first 1MB of file where headers and metadata boxes reside
            head_bytes = f.read(1024 * 1024)

            # C2PA manifest marker checks (jumb, c2pa, c2ma)
            if b"c2pa" in head_bytes or b"jumb" in head_bytes:
                provenance["has_c2pa"] = True
                provenance["c2pa_status"] = "C2PA Content Credentials Manifest Present"

                # Check for standard C2PA digital source types
                if b"trainedAlgorithmicMedia" in head_bytes or b"compositeSynthetic" in head_bytes:
                    provenance["is_ai_declared"] = True
                    provenance["provenance_actions"].append("Declared AI-generated via C2PA digital source type")

                if b"Adobe" in head_bytes:
                    provenance["manifest_issuer"] = "Adobe Content Authenticity Initiative"
                elif b"Truepic" in head_bytes:
                    provenance["manifest_issuer"] = "Truepic"
                elif b"Microsoft" in head_bytes:
                    provenance["manifest_issuer"] = "Microsoft Azure AI Provenance"
                else:
                    provenance["manifest_issuer"] = "Generic C2PA Signer"

    except Exception:
        pass

    return provenance
