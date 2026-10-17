import os
import json
import argparse
import requests
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

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
USER_PROMPTS_DIR = PROJECT_ROOT / "prompts" / "userPrompts"
modelName = args.model.replace("/", "_")
OUT_DIR = PROJECT_ROOT / "data" / args.system / modelName / args.promptFile
OUT_DIR.mkdir(parents=True, exist_ok=True)

# LOAD API KEY
load_dotenv()
apiKey = os.getenv("OPENROUTER_API_KEY")
if not apiKey:
    raise ValueError("Set OPENROUTER_API_KEY before running this script.")

# LOAD PROMPTS
with open( USER_PROMPTS_DIR / f"{args.promptFile}.json", encoding="utf-8") as file: 
    promts = json.load(file)
    #print(promts)

with open( SYSTEM_PROMPTS_DIR / f"{args.system}.json", encoding="utf-8") as file: 
    systemPrompt = json.load(file)
    #print(systemPromt)

# CREATE LOG
date = datetime.now().strftime("%Y-%m-%d_%H-%M")
log = PROJECT_ROOT / "logs" / f"{args.promptFile}_{modelName}_{date}.json"
results = []

#-------------------------------------------------------------------------------------------------------------------

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

                        #"tags":{
                         #    "tag1": p[3], #! Seleccionar etiquetas y decidir estructura de respuesta
                          #   "tag2": p[4],
                           #  "tag3": p[5],
                            # "tag4": p[6],
                        #},

                    "responses": answer
                }
    

    outFile = OUT_DIR / f"{modelName}_{p[1]}_{p[0]}.json"
    with open(outFile, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    results.append(r.json())
    with open(log, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)