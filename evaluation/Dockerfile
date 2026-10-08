FROM python:3.11-slim
COPY runner.py /runner.py
USER 65534:65534
ENTRYPOINT ["python", "-I", "-B", "/runner.py"]
