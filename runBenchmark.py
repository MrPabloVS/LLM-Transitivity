import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SYSTEM_PROMPTS_DIR = PROJECT_ROOT / "prompts" / "systemPrompts"
USER_PROMPTS_DIR = PROJECT_ROOT / "prompts" / "userPrompts"
DATA_DIR = PROJECT_ROOT / "data"

SYSTEM_PROMPT_FILES = {
    "zeroShot": SYSTEM_PROMPTS_DIR / "zeroShot.json",
    "chainOfThought": SYSTEM_PROMPTS_DIR / "chainOfThought.json",
}

USER_PROMPT_FILES = {
    "HS": USER_PROMPTS_DIR / "HS.json",

}

#! Hay que decidir modelos a evaluar 
MODEL_LIST = {
     
}

#* Funciones
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("Set OPENROUTER_API_KEY before running this script.")

def loadSystemPrompt(name: str) -> str:
    path = SYSTEM_PROMPT_FILES[name]
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data["system_prompt"]


#? En desuso, revisar si conviene usar
def load_user_prompts(name: str) -> str:
    path = SYSTEM_PROMPT_FILES[name]
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    prompts = []
    for entry in data:
        category, prompt_id, text = entry[0], entry[1], entry[2]
        prompts.append({"category": category, "id": prompt_id, "text": text})
    return prompts

DATA_DIR.mkdir(parents=True, exist_ok=True)



#? En uso como alternativa a load_user_prompts
with open( USER_PROMPTS_DIR / "HS.json") as file:
    promts = json.load(file)

#print(data)


#* Input
for p in promts:
    #print(prompt)
    #! Hacer llamdas genericas, buscar alternativa a la libreria de OpenAI y revisar que usa Holiday
    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )

    response = client.chat.completions.create(
        model="openai/gpt-5.4-mini",
        messages=[
            {
                "role": "system",
                "content": loadSystemPrompt("zeroShot"),
            },
            {
                "role": "user",
                "content": p[2],
            },
        ],
        max_completion_tokens=300,
    )


#* Output
    answer = response.choices[0].message.content
    print(answer)
    #print(load_system_prompt("zeroShot"))
    #print(json.load("/userPrompts/HS.json"))
    #print(load_user_prompts("HS"))
    #print(USER_PROMPT_FILES["HS"])

    data = {
                    "user_prompt": p[2],
                    "system_prompt": loadSystemPrompt("zeroShot"),
                    "model": "openai/gpt-5.4-mini",

                        "tags":{
                             "tag1": p[3], #! Seleccionar etiquetas y decidir estructura de respuesta
                             "tag2": p[4],
                             "tag3": p[5],
                             "tag4": p[6],
                        },

                    "responses": answer
                }
    

    out_file = DATA_DIR / f"{p[1]}_{p[0]}.json"
    with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


    if response.usage:
        print(
            f"\nTokens used - Input: {response.usage.prompt_tokens}, "
            f"Output: {response.usage.completion_tokens}, "
            f"Total: {response.usage.total_tokens}"
        )