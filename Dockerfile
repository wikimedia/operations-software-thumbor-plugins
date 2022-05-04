FROM debian:stretch

# debian setup

RUN apt clean
RUN apt update && apt install python-pip -y
RUN apt install libcurl4-openssl-dev libssl-dev ffmpeg exiftool libvips-tools xcftools djvulibre-bin librsvg2-bin xvfb imagemagick webp gifsicle libjpeg-turbo-progs libexiv2-dev libboost-python-dev pkg-config libcairo2-dev libjpeg-dev libgif-dev -y

RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get install build-essential nodejs -y

# 3d2png setup

WORKDIR /srv
RUN apt install git -y
RUN git clone https://github.com/wikimedia/3d2png.git
WORKDIR /srv/3d2png
RUN npm install --unsafe-perm -g .
RUN which 3d2png

# copy Wikimedia_Thumbor

WORKDIR /srv/wikimedia_thumbor
COPY . .

# requirements

RUN pip install -r requirements.txt
RUN pip install -r requirements-dev.txt

# tests

RUN pip install pyssim
RUN pip install urllib3
RUN apt-get install python-pyexiv2-doc -y

# install and run

RUN python setup.py install
CMD thumbor --port 8800 --conf=thumbor.conf -a wikimedia_thumbor.app.App