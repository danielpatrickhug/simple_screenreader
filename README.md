# Simple ScreenReader
```
A simple screenreader that uses OpenAI TT2S API to convert the text in your copy buffer into audio files
```

## How to run
1. Set your OPENAI_API_KEY in the terminal
```bash
$OPENAI_API_KEY=sk-...
export OPENAI_API_KEY  
```

2. create venv(optional), install requirements and run the python script
```bash
python3.12 -m venv venv && source venv/bin/activate && pip install -U pip setuptools wheel
pip install -r requirements.txt
python screenreader.py
```

3. Use the screen reader.
- Highlight a piece of text and run your copy command(`command + c` on mac), wait and listen to audio.

