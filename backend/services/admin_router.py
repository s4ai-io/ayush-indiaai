import json
import os
import datetime
import httpx
import asyncio
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from services.ayurgenix_service import ayurgenix_service
from utils.llm_config import get_llm
from config import ASR_REQUEST_TIMEOUT

admin_router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'src', 'data')
AUDIO_DIR = os.path.join(DATA_DIR, 'audio files')
EVALS_DIR = os.path.join(BASE_DIR, 'logs', 'evaluations')

os.makedirs(EVALS_DIR, exist_ok=True)

EXTRACTION_PROMPT = """
You are an AI Clinical Assistant. Your task is to extract clinical information from the following doctor-patient consultation transcript.

TRANSCRIPT:
{transcript}

EXTRACT the following fields in valid JSON format:
- symptoms: (string, comma-separated)
- disease: (string, the PROPER English medical name of the diagnosis, e.g. "Anemia", "Insomnia", "Respiratory Disorder")
- prakriti: (one of: Vata, Pitta, Kapha, Vata-Pitta, Pitta-Kapha, Vata-Kapha)
- vikriti: (one of: Vata, Pitta, Kapha)

RULES:
1. ALL field values MUST be in English.
2. If a field is not mentioned, use null or an empty string.
3. Return ONLY the JSON object.
"""

from fastapi.responses import StreamingResponse, FileResponse

@admin_router.get("/audio/{filename}", tags=["Admin"])
async def get_audio_file(filename: str):
    """Serve audio files from the ground truth audio directory."""
    audio_path = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(audio_path, media_type="audio/wav")

@admin_router.get("/evaluate-voice", tags=["Admin"])
async def evaluate_voice_accuracy():
    """
    Full pipeline evaluation with StreamingResponse for real-time progress tracking.
    """
    async def event_generator():
        try:
            ground_truth_path = os.path.join(DATA_DIR, 'ground_truth.json')
            if not os.path.exists(ground_truth_path):
                yield f"data: {json.dumps({'type': 'error', 'detail': 'ground_truth.json not found'})}\n\n"
                return

            with open(ground_truth_path, 'r', encoding='utf-8') as f:
                ground_truth_data = json.load(f)

            modal_asr_url = os.getenv("MODAL_ASR_URL")
            if not modal_asr_url:
                yield f"data: {json.dumps({'type': 'error', 'detail': 'MODAL_ASR_URL not configured'})}\n\n"
                return

            llm = get_llm()
            results = []
            total_files = len(ground_truth_data)
            
            # Initial event to set total
            yield f"data: {json.dumps({'type': 'progress', 'current': 0, 'total': total_files, 'percent': 0})}\n\n"

            for i, item in enumerate(ground_truth_data):
                audio_filename = item.get("Audio-file name")
                if not audio_filename:
                    continue
                    
                # Progress update at start of each file
                progress_data = {
                    'type': 'progress', 
                    'current': i + 1, 
                    'total': total_files, 
                    'file': audio_filename,
                    'percent': int(((i) / total_files) * 100)
                }
                yield f"data: {json.dumps(progress_data)}\n\n"

                audio_path = os.path.join(AUDIO_DIR, audio_filename)
                
                # Extract ground truth early for use in error results
                gt_data = {
                    "disease": item.get("Disease", ""),
                    "symptoms": item.get("Symptoms", []),
                    "prakriti": item.get("Prakriti", ""),
                    "doshas": item.get("Doshas", "")
                }

                if not os.path.exists(audio_path):
                    results.append({
                        "file": audio_filename,
                        "error": "Audio file not found",
                        "status": "skipped",
                        "ground_truth": gt_data,
                        "extraction": {"error": "Skipped (file missing)"}
                    })
                    continue

                # 1. Transcribe
                transcription = ""
                try:
                    with open(audio_path, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                    
                    lang_name = audio_filename.split('_')[0].lower() if '_' in audio_filename else None
                    lang_map = {
                        "hindi": "hi", "gujarati": "gu", "bengali": "bn", "punjabi": "pa",
                        "kannada": "kn", "tamil": "ta", "telugu": "te", "malayalam": "ml",
                        "marathi": "mr", "english": "en"
                    }
                    lang = lang_map.get(lang_name, lang_name)
                    
                    async with httpx.AsyncClient(timeout=ASR_REQUEST_TIMEOUT) as client:
                        files = {"audio": (audio_filename, audio_bytes, "audio/wav")}
                        data = {"language": lang} if lang else {}
                        resp = await client.post(modal_asr_url, data=data, files=files)
                    
                    if resp.status_code != 200:
                        raise Exception(f"ASR failed: {resp.text}")
                    transcription = resp.json().get("text", "")
                except Exception as e:
                    results.append({
                        "file": audio_filename,
                        "language": lang if 'lang' in locals() else None,
                        "error": f"Transcription failed: {str(e)}",
                        "status": "error",
                        "ground_truth": gt_data,
                        "extraction": {"error": "Failed at transcription"}
                    })
                    continue

                # 2. Extract
                try:
                    from llama_index.core.llms import ChatMessage
                    prompt = EXTRACTION_PROMPT.format(transcript=transcription)
                    llm_resp = await llm.achat([ChatMessage(role="user", content=prompt)])
                    extraction_text = llm_resp.message.content
                    
                    import re
                    json_match = re.search(r'\{.*\}', extraction_text, re.DOTALL)
                    if json_match:
                        extraction = json.loads(json_match.group(0))
                    else:
                        extraction = {"error": "Failed to parse JSON from LLM"}
                except Exception as e:
                    extraction = {"error": f"Extraction failed: {str(e)}"}

                # 3. Enhanced Scoring Logic
                from difflib import SequenceMatcher
                def get_fuzzy_ratio(a, b):
                    if not a or not b: return 0
                    return SequenceMatcher(None, str(a).lower().strip(), str(b).lower().strip()).ratio() * 100

                gt_disease = item.get("Disease", "")
                gt_symptoms = item.get("Symptoms", [])
                gt_doshas = item.get("Doshas", "")
                gt_prakriti = item.get("Prakriti", "")

                ex_disease = extraction.get("disease", "")
                ex_symptoms = extraction.get("symptoms", "")
                ex_doshas = extraction.get("vikriti", "")
                ex_prakriti = extraction.get("prakriti", "")

                disease_score = get_fuzzy_ratio(gt_disease, ex_disease)
                symptoms_score = 0
                if gt_symptoms:
                    ex_symp_list = [s.strip().lower() for s in str(ex_symptoms).split(',') if s.strip()]
                    matches = 0
                    for gt_s in gt_symptoms:
                        gt_s_lower = gt_s.lower()
                        if any(gt_s_lower in es or es in gt_s_lower for es in ex_symp_list):
                            matches += 1
                    symptoms_score = (matches / len(gt_symptoms)) * 100
                elif not gt_symptoms and not ex_symptoms:
                    symptoms_score = 100

                dosha_score = 100 if str(gt_doshas).lower().strip() == str(ex_doshas).lower().strip() else 0
                prakriti_score = 100 if str(gt_prakriti).lower().strip() == str(ex_prakriti).lower().strip() else 0

                total_score = (disease_score * 0.4) + (symptoms_score * 0.4) + (dosha_score * 0.1) + (prakriti_score * 0.1)
                is_match = total_score >= 80

                results.append({
                    "file": audio_filename,
                    "language": lang,
                    "ground_truth": {
                        "disease": gt_disease,
                        "symptoms": gt_symptoms,
                        "prakriti": gt_prakriti,
                        "doshas": gt_doshas
                    },
                    "transcription": transcription,
                    "extraction": extraction,
                    "score": round(total_score, 1),
                    "is_match": is_match,
                    "status": "completed"
                })

            # Summary Metrics
            completed_runs = [r for r in results if r.get("status") == "completed"]
            avg_accuracy = sum(r["score"] for r in completed_runs) / len(completed_runs) if completed_runs else 0
            
            summary = {
                "total": total_files,
                "processed": len(completed_runs),
                "avg_accuracy": round(avg_accuracy, 1),
                "accuracy": round(avg_accuracy, 1) 
            }

            report = {
                "timestamp": datetime.datetime.now().isoformat(),
                "summary": summary,
                "results": results
            }

            # Save report
            report_filename = f"voice_eval_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(os.path.join(EVALS_DIR, report_filename), 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)

            yield f"data: {json.dumps({'type': 'complete', 'report': report})}\n\n"

        except Exception as e:
            print(f"Error in evaluate_voice_accuracy stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
