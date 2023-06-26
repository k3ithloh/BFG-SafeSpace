FROM python:3-slim as build
WORKDIR /BUILDFORGOODSAFESPACE
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY . /BUILDFORGOODSAFESPACE
EXPOSE 80
CMD [ "python", "./main.py" ]
