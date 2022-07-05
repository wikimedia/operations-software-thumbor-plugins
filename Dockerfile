FROM docker-registry.wikimedia.org/wikimedia-buster

# debian setup

RUN apt clean
RUN apt update
RUN apt install libcurl4-openssl-dev libssl-dev ffmpeg exiftool libvips-tools xcftools djvulibre-bin librsvg2-bin xvfb xauth imagemagick webp gifsicle libjpeg-turbo-progs libexiv2-dev python-all-dev libboost-python-dev pkg-config libcairo2-dev libjpeg-dev libgif-dev python3 git ca-certificates python3-pip python3-setuptools python3-wheel build-essential nodejs npm libopenblas-base liblapack3 liblapack-dev libopenblas-dev gfortran libwebp-dev ghostscript -y

# 3d2png setup

WORKDIR /srv
RUN git clone https://github.com/wikimedia/3d2png.git
WORKDIR /srv/3d2png
RUN npm install --unsafe-perm -g .
RUN which 3d2png

# copy Wikimedia_Thumbor

WORKDIR /srv/wikimedia_thumbor
COPY . .

# requirements

RUN pip3 install -r requirements.txt
RUN pip3 install -r requirements-dev.txt

# install and run

RUN python3 setup.py install
CMD thumbor --port 8800 --conf=thumbor.conf -a wikimedia_thumbor.app.App