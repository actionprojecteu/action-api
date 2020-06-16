FROM python:3.8
ADD . ./opt/
WORKDIR /opt/
EXPOSE 5000
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python","manage.py","runprodserver"]

# sudo docker build -t action-api .
# sudo docker stop myaction-api
# sudo docker rm myaction-api
# sudo docker run --name myaction-api -v /var/log/action:/opt/log -v /home/action-api/img:/opt/img -p 5000:5000 -d action-api


# sudo docker run -d -p 27017:27017 -v /home/databases/mongoData:/data/db mongo

