from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import sys
from io import StringIO
import traceback
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    code: str


def execute_python_code(code: str) -> dict:
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        exec(code, {})
        output = sys.stdout.getvalue()
        return {"success": True, "output": output}
    except Exception:
        output = traceback.format_exc()
        return {"success": False, "output": output}
    finally:
        sys.stdout = old_stdout


def extract_error_lines(traceback_str: str) -> List[int]:
    """
    Parse line numbers directly from traceback.
    Looks for patterns like: File "<string>", line 3
    """
    pattern = r'File "<string>", line (\d+)'
    matches = re.findall(pattern, traceback_str)
    # Return unique line numbers in order, as integers
    seen = set()
    result = []
    for m in matches:
        n = int(m)
        if n not in seen:
            seen.add(n)
            result.append(n)
    return result


@app.post("/code-interpreter")
async def code_interpreter(request: CodeRequest):
    if not request.code or not request.code.strip():
        raise HTTPException(status_code=422, detail="Code cannot be empty")

    execution = execute_python_code(request.code)

    if execution["success"]:
        return JSONResponse(content={
            "error": [],
            "result": execution["output"]
        })

    # Parse error lines directly from traceback
    error_lines = extract_error_lines(execution["output"])

    return JSONResponse(content={
        "error": error_lines,
        "result": execution["output"]
    })