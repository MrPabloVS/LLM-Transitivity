# LLM-Transitivity

## Instructions for running the benchmark  
1. Check for python instalation bu running on the terminal: python --version. If it fails, Download Python from python.org/downloads. Then close and reopen the terminal.  
2. Run on the terminal: python -m pip install requests python-dotenv  
3. Create a file named exactly .env in the project folder and write your API KEY like this: OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxx  
4. Run the benchmark as follows: python runBenchmark.py HS --system zeroShot --model anthropic/claude-sonnet-4.5   
 - HS is the user prompts file name without .json  
 - --system picks the system prompt file (default zeroShot).  
 - --model picks the model, in provider/model format from openrouter.ai/models (default openai/gpt-4o-mini). 


## Contributors:  
Eduardo Barrio  
Bruno Da Ré  
Pablo Vazquez Soldano  
Lourdes De Carolis  
Tomas Gomez Ansede  
Guadalupe Fernández Fagioli  
Nadia Belén Martínez Szego  
Sofia de Arias Vargas  
Lourdes Nazarena Toneatti