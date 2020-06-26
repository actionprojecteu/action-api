FROM python:3.8
ADD . ./opt/
WORKDIR /opt/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD ["python","daemon.py"]

# sudo docker build -t action-daemon .
# sudo docker stop myaction-daemon
# sudo docker rm myaction-daemon
# sudo docker run --name myaction-daemon -v /var/log/action:/opt/log -v /home/action-api/img:/opt/img -d action-daemon


# sudo docker run -d -p 27017:27017 -v /home/databases/mongoData:/data/db mongo

