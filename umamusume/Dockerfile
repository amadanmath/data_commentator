FROM registry.hf.space/plachta-vits-umamusume-voice-synthesizer:latest

EXPOSE 8002

RUN pip install flask asgiref

COPY api.py api.py

ENTRYPOINT ["uvicorn", "--host", "0.0.0.0", "--port", "59125", "api:asgi_app"]
