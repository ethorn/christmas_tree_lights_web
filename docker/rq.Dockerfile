
FROM python:3.6

# WORKDIR /usr/src/app

# COPY requirements.txt ./
RUN pip install rq
RUN pip install rq-dashboard

#CMD ["rq", "worker"]