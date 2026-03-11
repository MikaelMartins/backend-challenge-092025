from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from schemas.request_schemas import AnalyzeFeedRequest
from sentiment_analyzer import analyze_feed as run_feed_analysis

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(req: Request, exc: RequestValidationError):
  """
  Mapeia erros de validação para os códigos HTTP e payloads esperados.
  """
  for error in exc.errors():
    message = str(error.get("msg"))
    if "UNSUPPORTED_TIME_WINDOW" in message:
      return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
          "error": "Valor de janela temporal não suportado na versão atual",
          "code": "UNSUPPORTED_TIME_WINDOW",
        },
      )
    if "INVALID_TIMESTAMP" in message:
      return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
          "error": "Timestamp em formato inválido",
          "code": "INVALID_TIMESTAMP",
        },
      )
    if "TIME_WINDOW_MUST_BE_POSITIVE" in message:
      return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
          "error": "Valor de janela temporal deve ser maior que zero",
          "code": "INVALID_TIME_WINDOW",
        },
      )

  return JSONResponse(
    status_code=status.HTTP_400_BAD_REQUEST,
    content={
      "error": "Payload inválido",
      "detail": exc.errors(),
    }
  )

@app.post("/analyze-feed")
async def analyze_feed(data: AnalyzeFeedRequest):
  return run_feed_analysis(data.messages, data.time_window_minutes)
