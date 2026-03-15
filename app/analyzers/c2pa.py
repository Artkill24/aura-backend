"""
AURA — C2PA Content Credentials Checker (EU AI Act Art. 50)
Verifica presenza e validità di manifest C2PA nei video.
"""
import json
from typing import Dict, Any


def check_c2pa(video_path: str) -> Dict[str, Any]:
    result = {
        "has_manifest":    False,
        "manifest_valid":  False,
        "is_ai_generated": False,
        "producer":        None,
        "assertions":      [],
        "ingredients":     [],
        "soft_binding":    False,
        "c2pa_score":      0.35,
        "flags":           [],
        "error":           None,
    }

    try:
        import c2pa

        try:
            reader = c2pa.Reader(video_path)
            manifest_json = reader.json()
        except Exception as e:
            err = str(e).lower()
            if "manifestnotfound" in err or "no jumbf" in err or "not found" in err:
                result["flags"].append({
                    "type": "NO_C2PA_MANIFEST",
                    "detail": "Nessun manifest C2PA — provenance non verificabile (EU AI Act Art. 50)",
                    "severity": "MEDIUM",
                })
                result["c2pa_score"] = 0.35
            else:
                result["error"] = str(e)
                result["c2pa_score"] = 0.20
            return result

        if not manifest_json:
            result["flags"].append({
                "type": "NO_C2PA_MANIFEST",
                "detail": "Manifest C2PA vuoto",
                "severity": "MEDIUM",
            })
            result["c2pa_score"] = 0.35
            return result

        data = json.loads(manifest_json)
        result["has_manifest"] = True

        active_label = data.get("active_manifest", "")
        manifests    = data.get("manifests", {})
        active       = manifests.get(active_label, {})

        result["producer"] = active.get("claim_generator", "")

        assertions = active.get("assertions", [])
        result["assertions"] = [a.get("label", "") for a in assertions]

        for a in assertions:
            label = a.get("label", "")
            if "ai.generated" in label or "c2pa.ai" in label:
                result["is_ai_generated"] = True
                result["flags"].append({
                    "type": "C2PA_AI_GENERATED",
                    "detail": f"Manifest dichiara contenuto AI-generated: {label}",
                    "severity": "HIGH",
                })

        soft_binding = any(
            "hash" in a.get("label","").lower() or "binding" in a.get("label","").lower()
            for a in assertions
        )
        result["soft_binding"] = soft_binding
        if not soft_binding:
            result["flags"].append({
                "type": "NO_SOFT_BINDING",
                "detail": "Manifest C2PA senza hash binding — possibile re-embedding fraudolento",
                "severity": "MEDIUM",
            })

        ingredients = active.get("ingredients", [])
        result["ingredients"] = [i.get("title", "") for i in ingredients]
        if len(ingredients) > 2:
            result["flags"].append({
                "type": "MULTIPLE_EDITS",
                "detail": f"Rilevate {len(ingredients)} modifiche nella catena C2PA",
                "severity": "LOW",
            })

        validation_status = active.get("validation_status", [])
        has_error = any(s.get("code", "").endswith(".failed") for s in validation_status)
        result["manifest_valid"] = not has_error

        if has_error:
            result["flags"].append({
                "type": "C2PA_SIGNATURE_INVALID",
                "detail": "Firma C2PA non valida — manifest potenzialmente alterato",
                "severity": "HIGH",
            })
            result["c2pa_score"] = 0.75
        elif result["is_ai_generated"]:
            result["c2pa_score"] = 0.60
        else:
            result["c2pa_score"] = 0.05

    except ImportError:
        result["error"] = "c2pa-python not installed"
        result["c2pa_score"] = 0.20

    return result
