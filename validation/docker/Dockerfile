# Disposable Container for AuraCode Evaluation Harness
# Multi-arch minimal runner with non-root identity and sterile execution environment

FROM python:3.13-slim

# Create unprivileged evaluator user and workspace directories
RUN groupadd -g 1000 evaluator && \
    useradd -u 1000 -g evaluator -m -s /bin/bash evaluator && \
    mkdir -p /workspace /evaluator/protected && \
    chown -R evaluator:evaluator /workspace

USER evaluator
WORKDIR /workspace

ENV PYTHONUNBUFFERED=1
ENV TARGET_WORKSPACE=/workspace
ENV PYTHONPATH=/workspace

CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]
