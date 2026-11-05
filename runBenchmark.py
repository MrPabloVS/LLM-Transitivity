import os
import json
import argparse
import requests
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

from dataset_validation import load_dataset

#-------------------------------------------------------------------------------------------------------------------

# PARSER
p = argparse.ArgumentParser() 
p.add_argument("promptFile") 
p.add_argument("--system", default="zeroShot")
p.add_argument("--model", default="openai/gpt-4o-mini")
args = p.parse_args()

# PROYECT DIRS
PROJECT_ROOT = Path(__file__).resolve().parent
SYSTEM_PROMPTS_DIR = PROJECT_ROOT / "prompts" / "systemPrompts"
DATASETS_DIR = PROJECT_ROOT / "datasets"
modelName = args.model.replace("/", "_")
OUT_DIR = PROJECT_ROOT / "data" / args.system / modelName / args.promptFile

# Validate every case before loading credentials or creating output files.
try:
    promts = load_dataset(DATASETS_DIR / f"{args.promptFile}.json")
except ValueError as error:
    p.error(str(error))

# LOAD API KEY
load_dotenv()
apiKey = os.getenv("OPENROUTER_API_KEY")
if not apiKey:
    raise ValueError("Set OPENROUTER_API_KEY before running this script.")

# LOAD PROMPTS
with open( SYSTEM_PROMPTS_DIR / f"{args.system}.json", encoding="utf-8") as file: 
    systemPrompt = json.load(file)
    #print(systemPromt)

# CREATE LOG
OUT_DIR.mkdir(parents=True, exist_ok=True)
date = datetime.now().strftime("%Y-%m-%d_%H-%M")
log = PROJECT_ROOT / "logs" / f"{args.promptFile}_{modelName}_{date}.json"
results = []

#-------------------------------------------------------------------------------------------------------------------

tIndex = 0 #? indice es temporal para no sobre escribir nombres, pensar bien nombre o armar indice con enumerate

#* Input
for p in promts:
    r = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {apiKey}"},
    json={"model": args.model,
           "messages": [
               {"role": "system", "content": systemPrompt[0]},
               {"role": "user", "content": p[2]}
               ]},
)
#* Output
    answer = r.json()["choices"][0]["message"]["content"]

    data = {
                    "userPrompt": p[2],
                    "system_prompt": systemPrompt[0],
                    "model": args.model,
                    "id": p[1],

                        "tags":{
                             "frecuency": p[3], #! Tiempo verbal y frecuencia en el nombre de archivo
                             "verbal time": p[4],
                             "conectors": p[5],
                             "validity": p[6],
                             "cononic": p[7],
                        },

                    "responses": answer
                }
    
    tIndex = tIndex + 1 #?
    #outFile = OUT_DIR / f"{modelName}_{p[1]}_{p[0]}.json" #! Pensar una convencion de nombramiento exhaustiva
    outFile = OUT_DIR / f"{modelName}_{tIndex}_{p[0]}_{p[3]}_{p[4]}.json" #? Borrar con tIndex
    with open(outFile, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    results.append(r.json())
    with open(log, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

print("Finished calls")
