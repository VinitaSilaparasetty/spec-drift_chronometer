FROM public.ecr.aws/lambda/python:3.12

# Copy requirements first to leverage Docker cache
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the core engine and governance logic
COPY . ${LAMBDA_TASK_ROOT}

# Set the handler for the Warden Engine
CMD ["main.handler"]
