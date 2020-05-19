FROM python:3.8
ADD . ./opt/
WORKDIR /opt/
EXPOSE 5000
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python","manage.py","runprodserver"]

# sudo docker build -t action-api .
# docker run --name myaction-api -v /var/log/action:/opt/log -v /home/action/img-dmptool:/opt/img -p 5000:5000 --link mongodb:mongo -d action-api
